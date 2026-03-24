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
        
        # 加载所有字段，保留原始数据
        self.data = {}
        
        # 必需字段
        required_fields = ['fps', 'root_pos', 'root_rot', 'dof_pos']
        for field in required_fields:
            if field in raw_data:
                self.data[field] = raw_data[field]
        
        # 加载所有其他可用字段
        for key, value in raw_data.items():
            if key not in self.data and key != 'frames':
                self.data[key] = value
        
        # 处理local_body_pos和link_body_list字段（如果存在但无效）
        local_body_pos = self.data.get('local_body_pos')
        if local_body_pos is not None and not (hasattr(local_body_pos, 'shape') and len(local_body_pos.shape) >= 1):
            self.data['local_body_pos'] = None
            
        link_body_list = self.data.get('link_body_list')
        if link_body_list is not None and not isinstance(link_body_list, (list, tuple)):
            self.data['link_body_list'] = None
        
        # 添加方便访问的帧列表
        if 'root_pos' in self.data:
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
        
        # 创建干净的输出数据（排除内部字段）
        output_data = {}
        internal_fields = {'frames'}  # 内部辅助字段不保存
        
        for key, value in data.items():
            if key not in internal_fields and value is not None:
                output_data[key] = value
        
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
        
        # 裁剪各数组（处理所有字段）
        clipped_data = {}
        internal_fields = {'frames'}
        
        for key, value in self.data.items():
            if key in internal_fields:
                continue
            
            if isinstance(value, np.ndarray):
                # 数组字段需要裁剪
                if value.shape[0] == len(self.data['root_pos']):
                    clipped_data[key] = value[start_frame:end_frame]
                else:
                    # 如果不是帧维度的数组，原样保留
                    clipped_data[key] = value
            elif isinstance(value, (list, tuple)) and len(value) == len(self.data['root_pos']):
                # 列表/元组且长度为帧数
                clipped_data[key] = value[start_frame:end_frame]
            else:
                # 其他字段原样保留
                clipped_data[key] = value
        
        # 添加新的frames列表
        clipped_data['frames'] = list(range(end_frame - start_frame))
        
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
