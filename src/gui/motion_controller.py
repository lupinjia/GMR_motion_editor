"""
运动控制器

管理运动数据的播放、暂停、帧导航和与MuJoCo viewer的通信。
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import numpy as np
from typing import Optional, Callable


class MotionController(QObject):
    """
    运动播放控制器
    
    功能：
    - 播放/暂停控制
    - 帧率管理
    - 循环播放
    - 播放速度调整
    - 与viewer通信
    """
    
    # 信号
    frame_changed = pyqtSignal(int)  # 当前帧改变
    playback_started = pyqtSignal()  # 开始播放
    playback_paused = pyqtSignal()   # 暂停播放
    playback_finished = pyqtSignal()  # 播放完成（非循环模式）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 播放状态
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        
        # 播放设置
        self.fps = 30
        self.playback_speed = 1.0
        self.loop = True
        
        # 裁剪范围
        self.clip_start = 0
        self.clip_end = 0
        
        # 定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_timeout)
        
        # 回调函数（用于获取帧数据和发送到viewer）
        self.get_frame_data_callback: Optional[Callable] = None
        self.send_to_viewer_callback: Optional[Callable] = None
    
    def set_frame_count(self, count: int):
        """设置总帧数"""
        self.total_frames = count
        # 重置裁剪范围到最开始和最末尾
        self.clip_start = 0
        self.clip_end = count
        self.current_frame = 0
    
    def set_fps(self, fps: int):
        """设置播放帧率"""
        self.fps = fps
        if self.is_playing:
            # 重新启动定时器以应用新帧率
            self.stop_timer()
            self.start_timer()
    
    def set_playback_speed(self, speed: float):
        """设置播放速度（0.5 = 半速, 1.0 = 正常, 2.0 = 双倍）"""
        self.playback_speed = max(0.1, min(speed, 3.0))
        if self.is_playing:
            self.stop_timer()
            self.start_timer()
    
    def set_loop(self, loop: bool):
        """设置是否循环播放"""
        self.loop = loop
    
    def set_clip_range(self, start: int, end: int):
        """设置裁剪范围"""
        self.clip_start = max(0, min(start, self.total_frames - 1))
        self.clip_end = max(self.clip_start + 1, min(end, self.total_frames))
        
        # 确保当前帧在裁剪范围内
        if self.current_frame < self.clip_start:
            self.set_current_frame(self.clip_start)
        elif self.current_frame >= self.clip_end:
            self.set_current_frame(self.clip_end - 1)
    
    def set_callbacks(self, 
                     get_frame_data: Optional[Callable] = None,
                     send_to_viewer: Optional[Callable] = None):
        """设置回调函数"""
        self.get_frame_data_callback = get_frame_data
        self.send_to_viewer_callback = send_to_viewer
    
    def play(self):
        """开始播放"""
        if not self.is_playing:
            self.is_playing = True
            self.start_timer()
            self.playback_started.emit()
    
    def pause(self):
        """暂停播放"""
        if self.is_playing:
            self.is_playing = False
            self.stop_timer()
            self.playback_paused.emit()
    
    def toggle_playback(self):
        """切换播放/暂停状态"""
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def stop(self):
        """停止播放并重置到起始位置"""
        self.pause()
        self.go_to_start()
    
    def start_timer(self):
        """启动播放定时器"""
        interval = int(1000 / (self.fps * self.playback_speed))
        self.timer.start(interval)
    
    def stop_timer(self):
        """停止播放定时器"""
        self.timer.stop()
    
    def on_timer_timeout(self):
        """定时器回调 - 推进到下一帧"""
        self.next_frame()
        
        # 发送数据到viewer
        if self.send_to_viewer_callback:
            frame_data = self.get_current_frame_data()
            if frame_data:
                self.send_to_viewer_callback(*frame_data)
    
    def set_current_frame(self, frame: int):
        """设置当前帧"""
        self.current_frame = max(self.clip_start, min(frame, self.clip_end - 1))
        self.frame_changed.emit(self.current_frame)
    
    def next_frame(self):
        """前进一帧"""
        next_f = self.current_frame + 1
        
        if next_f >= self.clip_end:
            if self.loop:
                next_f = self.clip_start
            else:
                self.pause()
                self.playback_finished.emit()
                return
        
        self.set_current_frame(next_f)
    
    def prev_frame(self):
        """后退一帧"""
        prev_f = self.current_frame - 1
        
        if prev_f < self.clip_start:
            if self.loop:
                prev_f = self.clip_end - 1
            else:
                prev_f = self.clip_start
        
        self.set_current_frame(prev_f)
    
    def go_to_start(self):
        """跳到裁剪范围起始位置"""
        self.set_current_frame(self.clip_start)
    
    def go_to_end(self):
        """跳到裁剪范围结束位置"""
        self.set_current_frame(self.clip_end - 1)
    
    def get_current_frame_data(self):
        """
        获取当前帧的数据
        
        Returns:
            (root_pos, root_rot, dof_pos) 元组，或 None
        """
        if self.get_frame_data_callback:
            return self.get_frame_data_callback(self.current_frame)
        return None
    
    def seek_to_time(self, time_sec: float):
        """跳转到指定时间（秒）"""
        frame = int(time_sec * self.fps)
        self.set_current_frame(frame)
