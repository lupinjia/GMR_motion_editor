"""
Motion Editor - GMR机器人运动数据可视化编辑器

提供机器人运动数据的可视化和编辑功能。
"""

from .gmr_manager import GMRDataManager
from .motion_controller import MotionController
from .timeline_widget import TimelineWidget
from .main_window import MainWindow

__version__ = "1.0.0"

__all__ = [
    'GMRDataManager',
    'MotionController',
    'TimelineWidget',
    'MainWindow',
]

