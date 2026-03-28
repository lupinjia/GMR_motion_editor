"""
步态周期检测模块

根据运动数据估计完整的步态周期（同一脚两次触地之间的时间）。
包括支撑相和摆动相的总时间。
"""

import numpy as np
from typing import Optional, Tuple, List
from scipy import signal


class GaitCycleDetector:
    """
    步态周期检测器
    
    检测完整的步态周期：从一次足跟着地到下一次同一足跟着地的时间。
    这包括：
    - 支撑相（Stance phase）：脚接触地面的时间
    - 摆动相（Swing phase）：脚在空中摆动的时间
    
    检测方法：
    1. 使用根节点垂直位置（root_pos[:, 2]）的极小值检测双腿支撑期
    2. 使用根节点垂直速度（root_lin_vel[:, 2]）的零交叉验证
    3. 结合垂直加速度确认触地事件
    4. 通过峰值间隔的一致性验证步态周期
    """
    
    def __init__(self):
        self.gait_period: Optional[float] = None  # 步态周期（秒）
        self.gait_frequency: Optional[float] = None  # 步态频率（Hz）
        self.confidence: float = 0.0  # 检测置信度 (0-1)
        self.details: dict = {}  # 详细信息
        self.touchdown_indices: List[int] = []  # 触地事件帧索引
    
    def detect(self, data: dict) -> Optional[float]:
        """
        检测步态周期
        
        Args:
            data: 包含运动数据的字典，必须包含以下key：
                - fps: 帧率
                - root_pos: 根节点位置 [N, 3] (使用z轴)
                - root_lin_vel: 根节点线速度 [N, 3] (使用z轴)
        
        Returns:
            步态周期（秒），如果检测失败返回None
        """
        try:
            # 检查必要的数据是否存在
            if not self._validate_data(data):
                return None
            
            fps = data['fps']
            n_frames = len(data['root_pos'])
            duration = n_frames / fps
            
            # 如果数据太短，无法检测周期（至少需要2个完整周期）
            if duration < 1.5:  # 假设最快步频约0.75秒/步
                return None
            
            # 提取垂直运动信号
            root_pos_z = data['root_pos'][:, 2]
            root_vel_z = data['root_lin_vel'][:, 2]
            
            # 计算垂直加速度（速度的差分）
            root_acc_z = np.diff(root_vel_z, prepend=root_vel_z[0]) * fps
            
            # 方法1: 基于根节点垂直位置的极小值（双腿支撑期）
            period_pos, confidence_pos, touchdowns_pos = self._detect_by_position_minima(
                root_pos_z, fps
            )
            
            # 方法2: 基于根节点垂直速度的负峰值（向下速度最大）
            period_vel, confidence_vel, touchdowns_vel = self._detect_by_velocity_peaks(
                root_vel_z, fps
            )
            
            # 方法3: 基于垂直加速度的正峰值（触地冲击）
            period_acc, confidence_acc, touchdowns_acc = self._detect_by_acceleration_peaks(
                root_acc_z, fps
            )
            
            # 方法4: 基于零速度交叉（从负到正，即身体开始上升）
            period_zc, confidence_zc, touchdowns_zc = self._detect_by_zero_crossing(
                root_vel_z, root_pos_z, fps
            )
            
            # 综合决策
            periods = []
            confidences = []
            all_touchdowns = []
            
            if period_pos is not None and 0.4 <= period_pos <= 2.0:
                periods.append(period_pos)
                confidences.append(confidence_pos * 1.2)  # 位置极小值通常最可靠
                all_touchdowns.append(touchdowns_pos)
            
            if period_vel is not None and 0.4 <= period_vel <= 2.0:
                periods.append(period_vel)
                confidences.append(confidence_vel * 1.0)
                all_touchdowns.append(touchdowns_vel)
            
            if period_acc is not None and 0.4 <= period_acc <= 2.0:
                periods.append(period_acc)
                confidences.append(confidence_acc * 0.8)  # 加速度容易受噪声影响
                all_touchdowns.append(touchdowns_acc)
            
            if period_zc is not None and 0.4 <= period_zc <= 2.0:
                periods.append(period_zc)
                confidences.append(confidence_zc * 0.9)
                all_touchdowns.append(touchdowns_zc)
            
            if len(periods) == 0:
                return None
            
            # 加权平均计算最终周期
            total_weight = sum(confidences)
            self.gait_period = sum(p * c for p, c in zip(periods, confidences)) / total_weight
            self.gait_frequency = 1.0 / self.gait_period
            
            # 计算综合置信度
            # 基于：1) 各方法的一致性 2) 检测到的事件数量
            period_std = np.std(periods)
            period_mean = np.mean(periods)
            consistency = 1.0 - min(1.0, period_std / (period_mean + 1e-10))
            
            # 使用最多事件的触地检测结果
            best_touchdowns = max(all_touchdowns, key=len) if all_touchdowns else []
            self.touchdown_indices = best_touchdowns
            
            event_confidence = min(1.0, len(best_touchdowns) / 10.0)
            self.confidence = (consistency * 0.6 + event_confidence * 0.4) * min(1.0, total_weight / 4.0)
            
            # 保存详细信息
            self.details = {
                'period_by_position': period_pos,
                'confidence_position': confidence_pos,
                'touchdowns_position': len(touchdowns_pos),
                'period_by_velocity': period_vel,
                'confidence_velocity': confidence_vel,
                'touchdowns_velocity': len(touchdowns_vel),
                'period_by_acceleration': period_acc,
                'confidence_acceleration': confidence_acc,
                'touchdowns_acceleration': len(touchdowns_acc),
                'period_by_zerocross': period_zc,
                'confidence_zerocross': confidence_zc,
                'touchdowns_zerocross': len(touchdowns_zc),
                'final_period': self.gait_period,
                'final_confidence': self.confidence,
                'num_touchdowns': len(best_touchdowns),
                'duration': duration
            }
            
            return self.gait_period
            
        except Exception as e:
            print(f"Error in gait cycle detection: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _validate_data(self, data: dict) -> bool:
        """验证数据是否完整"""
        required_keys = ['fps', 'root_pos', 'root_lin_vel']
        
        for key in required_keys:
            if key not in data:
                print(f"Missing required key: {key}")
                return False
            if data[key] is None:
                print(f"Key {key} is None")
                return False
        
        # 检查数据长度是否一致
        n_frames = len(data['root_pos'])
        if len(data['root_lin_vel']) != n_frames:
            return False
        
        return True
    
    def _detect_by_position_minima(self, root_pos_z: np.ndarray, fps: float) -> Tuple[Optional[float], float, List[int]]:
        """
        基于根节点垂直位置极小值检测
        
        双腿支撑期（双脚都在地面）时，身体重心最低，对应垂直位置的极小值。
        这是检测完整步态周期最可靠的方法。
        """
        try:
            # 平滑信号去除噪声
            window_size = min(7, len(root_pos_z) // 20)
            if window_size > 2:
                smoothed = signal.savgol_filter(root_pos_z, window_size, 3)
            else:
                smoothed = root_pos_z.copy()
            
            # 寻找极小值（谷值）
            # 使用 prominence 确保找到显著的低谷
            pos_std = np.std(smoothed)
            pos_mean = np.mean(smoothed)
            
            minima, properties = signal.find_peaks(
                -smoothed,  # 取负寻找极小值
                prominence=pos_std * 0.1,  # 最小突出度
                distance=int(0.3 * fps),  # 最小间距0.3秒（假设最快步频）
                width=(1, int(0.5 * fps))  # 宽度范围
            )
            
            if len(minima) < 2:
                return None, 0.0, []
            
            # 计算相邻极小值之间的时间间隔（即步态周期）
            intervals = np.diff(minima) / fps
            
            if len(intervals) == 0:
                return None, 0.0, []
            
            # 使用中位数作为周期估计（对异常值更鲁棒）
            period = np.median(intervals)
            
            # 计算一致性（变异系数）
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            consistency = 1.0 - min(1.0, std_interval / (mean_interval + 1e-10))
            
            # 置信度基于：1) 检测到的事件数量 2) 周期一致性
            num_events = len(minima)
            confidence = min(1.0, num_events / 8.0) * consistency
            
            return period, confidence, minima.tolist()
            
        except Exception as e:
            print(f"Error in position minima detection: {e}")
            return None, 0.0, []
    
    def _detect_by_velocity_peaks(self, root_vel_z: np.ndarray, fps: float) -> Tuple[Optional[float], float, List[int]]:
        """
        基于根节点垂直速度峰值检测
        
        在足跟着地时，身体向下速度达到最大（负方向）。
        """
        try:
            # 平滑信号
            window_size = min(5, len(root_vel_z) // 30)
            if window_size > 2:
                smoothed = signal.savgol_filter(root_vel_z, window_size, 2)
            else:
                smoothed = root_vel_z.copy()
            
            # 寻找负峰值（向下速度最大）
            vel_std = np.std(smoothed)
            
            # 向下速度为负值，寻找最小值（最负）
            minima, properties = signal.find_peaks(
                -smoothed,
                height=vel_std * 0.5,  # 至少0.5个标准差的向下速度
                distance=int(0.3 * fps),
                prominence=vel_std * 0.2
            )
            
            if len(minima) < 2:
                return None, 0.0, []
            
            # 计算间隔
            intervals = np.diff(minima) / fps
            period = np.median(intervals)
            
            # 计算置信度
            consistency = 1.0 - min(1.0, np.std(intervals) / (np.mean(intervals) + 1e-10))
            confidence = min(1.0, len(minima) / 8.0) * consistency
            
            return period, confidence, minima.tolist()
            
        except Exception as e:
            print(f"Error in velocity peak detection: {e}")
            return None, 0.0, []
    
    def _detect_by_acceleration_peaks(self, root_acc_z: np.ndarray, fps: float) -> Tuple[Optional[float], float, List[int]]:
        """
        基于垂直加速度峰值检测
        
        足跟着地时会产生向上的加速度冲击（正峰值）。
        """
        try:
            # 平滑加速度信号（高频噪声较多）
            window_size = min(7, len(root_acc_z) // 20)
            if window_size > 2:
                smoothed = signal.savgol_filter(root_acc_z, window_size, 3)
            else:
                smoothed = root_acc_z.copy()
            
            acc_std = np.std(smoothed)
            acc_mean = np.mean(smoothed)
            
            # 寻找正峰值（向上加速度）
            peaks, properties = signal.find_peaks(
                smoothed,
                height=acc_mean + acc_std * 1.0,  # 至少1个标准差高于均值
                distance=int(0.3 * fps),
                prominence=acc_std * 0.5
            )
            
            if len(peaks) < 2:
                return None, 0.0, []
            
            intervals = np.diff(peaks) / fps
            period = np.median(intervals)
            
            consistency = 1.0 - min(1.0, np.std(intervals) / (np.mean(intervals) + 1e-10))
            confidence = min(1.0, len(peaks) / 8.0) * consistency * 0.9  # 加速度方法稍低权重
            
            return period, confidence, peaks.tolist()
            
        except Exception as e:
            print(f"Error in acceleration peak detection: {e}")
            return None, 0.0, []
    
    def _detect_by_zero_crossing(self, root_vel_z: np.ndarray, root_pos_z: np.ndarray, fps: float) -> Tuple[Optional[float], float, List[int]]:
        """
        基于零速度交叉检测
        
        从负速度（向下）到正速度（向上）的零交叉，对应身体开始上升的时刻。
        这通常发生在双腿支撑期之后。
        """
        try:
            # 平滑速度信号
            window_size = min(5, len(root_vel_z) // 30)
            if window_size > 2:
                smoothed = signal.savgol_filter(root_vel_z, window_size, 2)
            else:
                smoothed = root_vel_z.copy()
            
            # 寻找从负到正的零交叉
            zero_crossings = []
            for i in range(1, len(smoothed)):
                if smoothed[i-1] < 0 and smoothed[i] >= 0:
                    # 确认此时身体处于较低位置（排除摆动期的假阳性）
                    if root_pos_z[i] < np.mean(root_pos_z):
                        zero_crossings.append(i)
            
            if len(zero_crossings) < 2:
                return None, 0.0, []
            
            # 检查间隔是否合理
            intervals = np.diff(zero_crossings) / fps
            valid_intervals = [iv for iv in intervals if 0.4 <= iv <= 2.0]
            
            if len(valid_intervals) < 1:
                return None, 0.0, []
            
            period = np.median(valid_intervals)
            
            consistency = 1.0 - min(1.0, np.std(valid_intervals) / (np.mean(valid_intervals) + 1e-10))
            confidence = min(1.0, len(zero_crossings) / 8.0) * consistency
            
            return period, confidence, zero_crossings
            
        except Exception as e:
            print(f"Error in zero crossing detection: {e}")
            return None, 0.0, []
    
    def get_gait_info_str(self) -> str:
        """获取步态信息的字符串表示"""
        if self.gait_period is None:
            return "Gait cycle: Not detected"
        
        info = f"Gait: {self.gait_period:.3f}s"
        if self.confidence > 0:
            info += f" (conf: {self.confidence:.0%})"
        
        return info
    
    def get_detailed_info(self) -> str:
        """获取详细的步态信息"""
        if self.gait_period is None:
            return "步态周期未检测到"
        
        info_lines = [
            f"步态周期: {self.gait_period:.3f} 秒",
            f"步态频率: {self.gait_frequency:.2f} Hz",
            f"置信度: {self.confidence:.1%}",
            f"检测到的触地事件: {len(self.touchdown_indices)} 次",
            ""
        ]
        
        if self.details:
            info_lines.append("检测方法详情:")
            if self.details.get('period_by_position'):
                info_lines.append(f"  - 位置极小值法: {self.details['period_by_position']:.3f}s "
                                f"(置信度 {self.details['confidence_position']:.1%}, "
                                f"事件数 {self.details['touchdowns_position']})")
            if self.details.get('period_by_velocity'):
                info_lines.append(f"  - 速度峰值法: {self.details['period_by_velocity']:.3f}s "
                                f"(置信度 {self.details['confidence_velocity']:.1%}, "
                                f"事件数 {self.details['touchdowns_velocity']})")
            if self.details.get('period_by_acceleration'):
                info_lines.append(f"  - 加速度峰值法: {self.details['period_by_acceleration']:.3f}s "
                                f"(置信度 {self.details['confidence_acceleration']:.1%}, "
                                f"事件数 {self.details['touchdowns_acceleration']})")
            if self.details.get('period_by_zerocross'):
                info_lines.append(f"  - 零交叉法: {self.details['period_by_zerocross']:.3f}s "
                                f"(置信度 {self.details['confidence_zerocross']:.1%}, "
                                f"事件数 {self.details['touchdowns_zerocross']})")
        
        return "\n".join(info_lines)
    
    def reset(self):
        """重置检测器状态"""
        self.gait_period = None
        self.gait_frequency = None
        self.confidence = 0.0
        self.details = {}
        self.touchdown_indices = []
