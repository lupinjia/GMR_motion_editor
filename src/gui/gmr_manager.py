"""
GMR数据管理器

处理GMR格式机器人运动数据的加载、保存和剪辑。
"""

import pickle
import numpy as np
from typing import Dict, Any, Tuple


class GMRDataManager:
    """管理GMR格式运动数据"""
    
    def __init__(self):
        self.data = None
        self.file_path = None
    
    def load(self, file_path: str) -> Dict[str, Any]:
        """
        加载GMR pickle文件
        
        Args:
            file_path: pickle文件路径
            
        Returns:
            包含运动数据的字典
        """
        with open(file_path, 'rb') as f:
            raw_data = pickle.load(f)
        
        # 转换为标准格式（处理可选字段）
        self.data = {
            'fps': raw_data['fps'],
            'root_pos': raw_data['root_pos'],
            'root_rot': raw_data['root_rot'],  # xyzw format
            'dof_pos': raw_data['dof_pos'],
        }
        
        # 处理可选字段，检查是否为有效的数组
        local_body_pos = raw_data.get('local_body_pos')
        if local_body_pos is not None and hasattr(local_body_pos, 'shape') and len(local_body_pos.shape) >= 1:
            self.data['local_body_pos'] = local_body_pos
        else:
            self.data['local_body_pos'] = None
            
        link_body_list = raw_data.get('link_body_list')
        if link_body_list is not None and isinstance(link_body_list, (list, tuple)):
            self.data['link_body_list'] = link_body_list
        else:
            self.data['link_body_list'] = None
        
        # 添加方便访问的帧列表
        frame_count = len(self.data['root_pos'])
        self.data['frames'] = list(range(frame_count))
        
        self.file_path = file_path
        return self.data
    
    def save(self, file_path: str, data: Dict[str, Any] = None) -> None:
        """
        保存GMR数据到pickle文件
        
        Args:
            file_path: 保存路径
            data: 要保存的数据，默认使用当前加载的数据
        """
        if data is None:
            data = self.data
        
        if data is None:
            raise ValueError("No data to save")
        
        # 创建干净的输出数据（只包含实际存在的字段）
        output_data = {
            'fps': data['fps'],
            'root_pos': data['root_pos'],
            'root_rot': data['root_rot'],
            'dof_pos': data['dof_pos'],
        }
        
        # 只添加不为None的可选字段（使用 .get() 避免 KeyError）
        if data.get('local_body_pos') is not None:
            output_data['local_body_pos'] = data['local_body_pos']
        if data.get('link_body_list') is not None:
            output_data['link_body_list'] = data['link_body_list']
        
        with open(file_path, 'wb') as f:
            pickle.dump(output_data, f)
    
    def clip(self, start_frame: int, end_frame: int) -> Dict[str, Any]:
        """
        裁剪运动数据
        
        Args:
            start_frame: 起始帧（包含）
            end_frame: 结束帧（不包含）
            
        Returns:
            裁剪后的数据字典
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        # 确保范围有效
        if start_frame > end_frame:
            start_frame, end_frame = end_frame, start_frame
        
        start_frame = max(0, start_frame)
        end_frame = min(end_frame, len(self.data['root_pos']))
        
        # 裁剪各数组（处理可选字段）
        clipped_data = {
            'fps': self.data['fps'],
            'root_pos': self.data['root_pos'][start_frame:end_frame],
            'root_rot': self.data['root_rot'][start_frame:end_frame],
            'dof_pos': self.data['dof_pos'][start_frame:end_frame],
            'frames': list(range(end_frame - start_frame))
        }
        
        # 处理可选字段
        if self.data.get('local_body_pos') is not None:
            clipped_data['local_body_pos'] = self.data['local_body_pos'][start_frame:end_frame]
        else:
            clipped_data['local_body_pos'] = None
            
        if self.data.get('link_body_list') is not None:
            clipped_data['link_body_list'] = self.data['link_body_list']
        else:
            clipped_data['link_body_list'] = None
        
        return clipped_data
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取当前数据的元信息
        
        Returns:
            包含fps、帧数、DOF数、时长等信息的字典
        """
        if self.data is None:
            return {}
        
        frame_count = len(self.data['root_pos'])
        fps = self.data['fps']
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'dof_count': self.data['dof_pos'].shape[1] if len(self.data['dof_pos'].shape) > 1 else 0,
            'duration': frame_count / fps,
            'file_path': self.file_path,
        }
    
    def get_frame(self, frame_idx: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        获取指定帧的数据
        
        Args:
            frame_idx: 帧索引
            
        Returns:
            (root_pos, root_rot, dof_pos) 元组
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        if frame_idx < 0 or frame_idx >= len(self.data['root_pos']):
            raise IndexError(f"Frame index {frame_idx} out of range")
        
        return (
            self.data['root_pos'][frame_idx],
            self.data['root_rot'][frame_idx],
            self.data['dof_pos'][frame_idx]
        )
