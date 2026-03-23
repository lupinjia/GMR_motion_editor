#!/usr/bin/env python3
"""
路径配置工具 - 将GMR项目路径添加到sys.path
"""

import sys
import os

def setup_gmr_path():
    """
    设置GMR项目路径，使motion_editor可以导入GMR模块
    """
    # 获取GMR项目根目录（当前目录的父目录）
    gmr_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if gmr_root not in sys.path:
        sys.path.insert(0, gmr_root)
    
    return gmr_root

def setup_motion_editor_path():
    """
    设置motion_editor自己的src路径
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, 'src')
    
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    return src_path
