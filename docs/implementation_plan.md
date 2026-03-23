# GMR可视化编辑器实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个基于PyQt6的GMR机器人运动数据可视化编辑器，支持导入、剪辑和导出GMR格式数据。

**Architecture:** 采用PyQt6构建GUI主窗口，复用现有MuJoCo RobotMotionViewer进行3D渲染（独立窗口）。核心组件包括主窗口、时间轴控件、运动控制器和数据管理器，组件间通过PyQt信号/槽通信。

**Tech Stack:** Python 3.10+, PyQt6, MuJoCo, NumPy, pickle

---

## 文件结构

```
general_motion_retargeting/gui/
├── __init__.py                 # 模块初始化，导出主要类
├── gmr_manager.py             # GMR数据加载/保存/裁剪
├── motion_controller.py       # 播放控制逻辑
├── timeline_widget.py         # 时间轴自定义控件
├── widgets.py                 # 通用UI控件
└── main_window.py             # 主窗口（最后实现）

scripts/
└── gmr_visualizer.py          # 启动脚本
```

---

## Task 1: 创建GUI模块基础结构

**Files:**
- Create: `general_motion_retargeting/gui/__init__.py`

- [ ] **Step 1: 创建模块初始化文件**

```python
"""
GMR Visualizer GUI Module

提供机器人运动数据的可视化和编辑功能。
"""

from .gmr_manager import GMRDataManager
from .motion_controller import MotionController
from .timeline_widget import TimelineWidget
from .main_window import MainWindow

__all__ = [
    'GMRDataManager',
    'MotionController', 
    'TimelineWidget',
    'MainWindow',
]
```

- [ ] **Step 2: 验证模块可导入**

Run: `cd /home/lupinjia/GMR && python -c "from general_motion_retargeting.gui import GMRDataManager, MotionController, TimelineWidget, MainWindow; print('Import OK')"`

Expected: 可能显示ImportError（因为文件还不存在），这是预期的

- [ ] **Step 3: Commit**

```bash
git add general_motion_retargeting/gui/__init__.py
git commit -m "feat: create gui module structure"
```

---

## Task 2: 实现GMRDataManager

**Files:**
- Create: `general_motion_retargeting/gui/gmr_manager.py`
- Test: `tests/test_gui/test_gmr_manager.py` (新建tests/test_gui目录)

- [ ] **Step 1: 创建测试目录和文件**

```bash
mkdir -p tests/test_gui
```

- [ ] **Step 2: 编写测试**

```python
# tests/test_gui/test_gmr_manager.py
import pytest
import numpy as np
import pickle
import tempfile
import os
from general_motion_retargeting.gui.gmr_manager import GMRDataManager


class TestGMRDataManager:
    def test_load_valid_file(self):
        """Test loading a valid GMR file"""
        # Create test data
        test_data = {
            'fps': 30,
            'root_pos': np.random.randn(100, 3),
            'root_rot': np.random.randn(100, 4),
            'dof_pos': np.random.randn(100, 29),
            'local_body_pos': np.random.randn(100, 24, 3),
            'link_body_list': ['link1', 'link2']
        }
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            pickle.dump(test_data, f)
            temp_path = f.name
        
        try:
            manager = GMRDataManager()
            result = manager.load(temp_path)
            
            assert result['fps'] == 30
            assert result['root_pos'].shape == (100, 3)
            assert len(result['frames']) == 100
        finally:
            os.unlink(temp_path)
    
    def test_clip_data(self):
        """Test clipping motion data"""
        test_data = {
            'fps': 30,
            'root_pos': np.random.randn(100, 3),
            'root_rot': np.random.randn(100, 4),
            'dof_pos': np.random.randn(100, 29),
            'local_body_pos': np.random.randn(100, 24, 3),
            'link_body_list': ['link1', 'link2']
        }
        
        manager = GMRDataManager()
        manager.data = test_data
        
        # Clip from frame 10 to 50
        clipped = manager.clip(10, 50)
        
        assert clipped['root_pos'].shape == (40, 3)
        assert len(clipped['frames']) == 40
    
    def test_clip_invalid_range(self):
        """Test clipping with invalid range"""
        test_data = {
            'fps': 30,
            'root_pos': np.random.randn(100, 3),
            'root_rot': np.random.randn(100, 4),
            'dof_pos': np.random.randn(100, 29),
            'local_body_pos': np.random.randn(100, 24, 3),
            'link_body_list': ['link1', 'link2']
        }
        
        manager = GMRDataManager()
        manager.data = test_data
        
        # Start > end should swap them
        clipped = manager.clip(50, 10)
        assert len(clipped['frames']) == 40
    
    def test_get_metadata(self):
        """Test getting metadata"""
        test_data = {
            'fps': 60,
            'root_pos': np.random.randn(120, 3),
            'root_rot': np.random.randn(120, 4),
            'dof_pos': np.random.randn(120, 15),
            'local_body_pos': np.random.randn(120, 24, 3),
            'link_body_list': ['link1', 'link2']
        }
        
        manager = GMRDataManager()
        manager.data = test_data
        
        meta = manager.get_metadata()
        assert meta['fps'] == 60
        assert meta['frame_count'] == 120
        assert meta['dof_count'] == 15
        assert meta['duration'] == 2.0  # 120 frames at 60fps
```

- [ ] **Step 3: 运行测试，验证失败**

Run: `cd /home/lupinjia/GMR && python -m pytest tests/test_gui/test_gmr_manager.py -v`

Expected: 4 tests FAIL with ImportError (GMRDataManager not found)

- [ ] **Step 4: 实现GMRDataManager**

```python
# general_motion_retargeting/gui/gmr_manager.py
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
        
        # 转换为标准格式
        self.data = {
            'fps': raw_data['fps'],
            'root_pos': raw_data['root_pos'],
            'root_rot': raw_data['root_rot'],  # xyzw format
            'dof_pos': raw_data['dof_pos'],
            'local_body_pos': raw_data['local_body_pos'],
            'link_body_list': raw_data['link_body_list'],
        }
        
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
        
        # 创建干净的输出数据（不包含辅助字段）
        output_data = {
            'fps': data['fps'],
            'root_pos': data['root_pos'],
            'root_rot': data['root_rot'],
            'dof_pos': data['dof_pos'],
            'local_body_pos': data['local_body_pos'],
            'link_body_list': data['link_body_list'],
        }
        
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
        
        # 裁剪各数组
        clipped_data = {
            'fps': self.data['fps'],
            'root_pos': self.data['root_pos'][start_frame:end_frame],
            'root_rot': self.data['root_rot'][start_frame:end_frame],
            'dof_pos': self.data['dof_pos'][start_frame:end_frame],
            'local_body_pos': self.data['local_body_pos'][start_frame:end_frame],
            'link_body_list': self.data['link_body_list'],
            'frames': list(range(end_frame - start_frame))
        }
        
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
```

- [ ] **Step 5: 运行测试，验证通过**

Run: `cd /home/lupinjia/GMR && python -m pytest tests/test_gui/test_gmr_manager.py -v`

Expected: 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add general_motion_retargeting/gui/gmr_manager.py tests/test_gui/test_gmr_manager.py
git commit -m "feat: implement GMRDataManager for loading/saving/clipping motion data"
```

---

## Task 3: 实现TimelineWidget

**Files:**
- Create: `general_motion_retargeting/gui/timeline_widget.py`
- Test: `tests/test_gui/test_timeline_widget.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_gui/test_timeline_widget.py
import pytest
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from general_motion_retargeting.gui.timeline_widget import TimelineWidget

# 创建QApplication（PyQt6需要）
@pytest.fixture(scope='module')
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestTimelineWidget:
    def test_initial_state(self, app):
        """Test initial widget state"""
        widget = TimelineWidget()
        assert widget.total_frames == 100  # default
        assert widget.current_frame == 0
        assert widget.clip_start == 0
        assert widget.clip_end == 100
    
    def test_set_frame_count(self, app):
        """Test setting total frame count"""
        widget = TimelineWidget()
        widget.set_frame_count(200)
        assert widget.total_frames == 200
        assert widget.clip_end == 200
    
    def test_set_current_frame(self, app):
        """Test setting current frame"""
        widget = TimelineWidget()
        widget.set_frame_count(100)
        widget.set_current_frame(50)
        assert widget.current_frame == 50
    
    def test_set_clip_range(self, app):
        """Test setting clip range"""
        widget = TimelineWidget()
        widget.set_frame_count(100)
        widget.set_clip_range(20, 80)
        assert widget.clip_start == 20
        assert widget.clip_end == 80
```

- [ ] **Step 2: 运行测试，验证失败**

Run: `cd /home/lupinjia/GMR && python -m pytest tests/test_gui/test_timeline_widget.py -v`

Expected: Tests FAIL with ImportError

- [ ] **Step 3: 实现TimelineWidget**

```python
# general_motion_retargeting/gui/timeline_widget.py
"""
时间轴控件

提供可视化时间轴，支持当前帧指示和裁剪范围选择。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QSlider, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush


class TimelineWidget(QWidget):
    """
    自定义时间轴控件
    
    包含：
    - 播放进度条（可拖动）
    - 裁剪范围手柄（蓝色起点，红色终点）
    - 当前帧指示器（黄色竖线）
    - 帧数显示
    """
    
    # 信号
    current_frame_changed = pyqtSignal(int)  # 当前帧改变
    clip_range_changed = pyqtSignal(int, int)  # 裁剪范围改变 (start, end)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.total_frames = 100
        self.current_frame = 0
        self.clip_start = 0
        self.clip_end = 100
        
        # 拖拽状态
        self.dragging = None  # 'progress', 'start_handle', 'end_handle'
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 信息显示
        info_layout = QHBoxLayout()
        
        self.frame_label = QLabel("Frame: 0 / 100")
        self.time_label = QLabel("Time: 0.00s / 3.33s")
        self.clip_label = QLabel("Clip: 0 - 100")
        
        info_layout.addWidget(self.frame_label)
        info_layout.addStretch()
        info_layout.addWidget(self.time_label)
        info_layout.addStretch()
        info_layout.addWidget(self.clip_label)
        
        layout.addLayout(info_layout)
        
        # 时间轴画布
        self.timeline_canvas = TimelineCanvas(self)
        self.timeline_canvas.setMinimumHeight(60)
        self.timeline_canvas.setFrameStyle(QFrame.Shape.StyledPanel)
        
        # 连接信号
        self.timeline_canvas.frame_changed.connect(self.on_canvas_frame_changed)
        self.timeline_canvas.clip_changed.connect(self.on_canvas_clip_changed)
        
        layout.addWidget(self.timeline_canvas)
        
        # 裁剪控制
        clip_layout = QHBoxLayout()
        clip_layout.addWidget(QLabel("Clip Start:"))
        
        self.start_spinbox = QSpinBox()
        self.start_spinbox.setRange(0, 99999)
        self.start_spinbox.valueChanged.connect(self.on_start_spinbox_changed)
        clip_layout.addWidget(self.start_spinbox)
        
        clip_layout.addWidget(QLabel("End:"))
        
        self.end_spinbox = QSpinBox()
        self.end_spinbox.setRange(0, 99999)
        self.end_spinbox.valueChanged.connect(self.on_end_spinbox_changed)
        clip_layout.addWidget(self.end_spinbox)
        
        clip_layout.addStretch()
        
        layout.addLayout(clip_layout)
        
        self.update_labels()
    
    def set_frame_count(self, count: int):
        """设置总帧数"""
        self.total_frames = max(1, count)
        self.clip_end = self.total_frames
        self.current_frame = min(self.current_frame, self.total_frames - 1)
        
        self.start_spinbox.setRange(0, self.total_frames - 1)
        self.end_spinbox.setRange(0, self.total_frames)
        self.end_spinbox.setValue(self.clip_end)
        
        self.timeline_canvas.update()
        self.update_labels()
    
    def set_current_frame(self, frame: int):
        """设置当前帧"""
        self.current_frame = max(0, min(frame, self.total_frames - 1))
        self.timeline_canvas.current_frame = self.current_frame
        self.timeline_canvas.update()
        self.update_labels()
    
    def set_clip_range(self, start: int, end: int):
        """设置裁剪范围"""
        self.clip_start = max(0, min(start, self.total_frames - 1))
        self.clip_end = max(self.clip_start + 1, min(end, self.total_frames))
        
        self.start_spinbox.setValue(self.clip_start)
        self.end_spinbox.setValue(self.clip_end)
        
        self.timeline_canvas.clip_start = self.clip_start
        self.timeline_canvas.clip_end = self.clip_end
        self.timeline_canvas.update()
        self.update_labels()
    
    def on_canvas_frame_changed(self, frame: int):
        """画布帧改变回调"""
        self.current_frame = frame
        self.update_labels()
        self.current_frame_changed.emit(frame)
    
    def on_canvas_clip_changed(self, start: int, end: int):
        """画布裁剪范围改变回调"""
        self.clip_start = start
        self.clip_end = end
        self.start_spinbox.setValue(start)
        self.end_spinbox.setValue(end)
        self.update_labels()
        self.clip_range_changed.emit(start, end)
    
    def on_start_spinbox_changed(self, value: int):
        """起始帧输入框改变"""
        if value >= self.clip_end:
            value = self.clip_end - 1
            self.start_spinbox.setValue(value)
        self.set_clip_range(value, self.clip_end)
    
    def on_end_spinbox_changed(self, value: int):
        """结束帧输入框改变"""
        if value <= self.clip_start:
            value = self.clip_start + 1
            self.end_spinbox.setValue(value)
        self.set_clip_range(self.clip_start, value)
    
    def update_labels(self):
        """更新标签显示"""
        fps = 30  # 默认fps，实际应从数据获取
        current_time = self.current_frame / fps
        total_time = self.total_frames / fps
        
        self.frame_label.setText(f"Frame: {self.current_frame} / {self.total_frames}")
        self.time_label.setText(f"Time: {current_time:.2f}s / {total_time:.2f}s")
        self.clip_label.setText(f"Clip: {self.clip_start} - {self.clip_end}")


class TimelineCanvas(QWidget):
    """
    时间轴画布
    
    绘制时间轴、裁剪手柄和当前帧指示器。
    """
    
    frame_changed = pyqtSignal(int)
    clip_changed = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.parent_widget = parent
        self.total_frames = 100
        self.current_frame = 0
        self.clip_start = 0
        self.clip_end = 100
        
        self.dragging = None
        self.drag_start_x = 0
        
        self.setMouseTracking(True)
    
    def paintEvent(self, event):
        """绘制时间轴"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 背景
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        # 时间轴主轨道
        track_y = height // 2
        track_height = 10
        
        # 绘制轨道背景
        painter.fillRect(20, track_y - track_height//2, width - 40, track_height, QColor(200, 200, 200))
        
        # 绘制裁剪区域（高亮）
        start_x = self.frame_to_x(self.clip_start)
        end_x = self.frame_to_x(self.clip_end)
        painter.fillRect(start_x, track_y - track_height//2, end_x - start_x, track_height, 
                        QColor(100, 150, 255, 100))
        
        # 绘制当前帧指示器（黄色竖线）
        current_x = self.frame_to_x(self.current_frame)
        pen = QPen(QColor(255, 200, 0), 2)
        painter.setPen(pen)
        painter.drawLine(current_x, 5, current_x, height - 5)
        
        # 绘制起点手柄（蓝色）
        start_handle_rect = self.get_handle_rect(self.clip_start)
        painter.fillRect(start_handle_rect, QColor(50, 100, 255))
        
        # 绘制终点手柄（红色）
        end_handle_rect = self.get_handle_rect(self.clip_end)
        painter.fillRect(end_handle_rect, QColor(255, 80, 80))
        
        painter.end()
    
    def frame_to_x(self, frame: int) -> int:
        """帧索引转换为x坐标"""
        width = self.width() - 40
        ratio = frame / max(1, self.total_frames - 1)
        return int(20 + ratio * width)
    
    def x_to_frame(self, x: int) -> int:
        """x坐标转换为帧索引"""
        width = self.width() - 40
        ratio = max(0, min(1, (x - 20) / width))
        return int(ratio * (self.total_frames - 1))
    
    def get_handle_rect(self, frame: int) -> QRect:
        """获取手柄的矩形区域"""
        x = self.frame_to_x(frame)
        y = self.height() // 2
        return QRect(x - 5, y - 15, 10, 30)
    
    def mousePressEvent(self, event):
        """鼠标按下"""
        pos = event.pos()
        
        # 检查是否点击了起点手柄
        if self.get_handle_rect(self.clip_start).contains(pos):
            self.dragging = 'start_handle'
        # 检查是否点击了终点手柄
        elif self.get_handle_rect(self.clip_end).contains(pos):
            self.dragging = 'end_handle'
        # 点击时间轴主体
        elif 20 <= pos.x() <= self.width() - 20:
            self.dragging = 'progress'
            frame = self.x_to_frame(pos.x())
            self.set_current_frame(frame)
        
        self.drag_start_x = pos.x()
    
    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self.dragging is None:
            return
        
        pos = event.pos()
        frame = self.x_to_frame(pos.x())
        
        if self.dragging == 'progress':
            self.set_current_frame(frame)
        elif self.dragging == 'start_handle':
            frame = min(frame, self.clip_end - 1)
            self.clip_start = max(0, frame)
            self.clip_changed.emit(self.clip_start, self.clip_end)
        elif self.dragging == 'end_handle':
            frame = max(frame, self.clip_start + 1)
            self.clip_end = min(self.total_frames, frame)
            self.clip_changed.emit(self.clip_start, self.clip_end)
        
        self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        self.dragging = None
    
    def set_current_frame(self, frame: int):
        """设置当前帧"""
        self.current_frame = max(0, min(frame, self.total_frames - 1))
        self.frame_changed.emit(self.current_frame)
        self.update()
    
    def resizeEvent(self, event):
        """窗口大小改变"""
        super().resizeEvent(event)
        self.update()
```

- [ ] **Step 4: 运行测试**

Run: `cd /home/lupinjia/GMR && python -m pytest tests/test_gui/test_timeline_widget.py -v`

Expected: Tests PASS (可能需要调整测试代码以适配实际实现)

- [ ] **Step 5: Commit**

```bash
git add general_motion_retargeting/gui/timeline_widget.py tests/test_gui/test_timeline_widget.py
git commit -m "feat: implement TimelineWidget with clip range selection"
```

---

## Task 4: 实现MotionController

**Files:**
- Create: `general_motion_retargeting/gui/motion_controller.py`
- Test: `tests/test_gui/test_motion_controller.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_gui/test_motion_controller.py
import pytest
import sys
from PyQt6.QtWidgets import QApplication
from unittest.mock import Mock, MagicMock
from general_motion_retargeting.gui.motion_controller import MotionController


@pytest.fixture(scope='module')
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestMotionController:
    def test_initial_state(self, app):
        """Test initial controller state"""
        controller = MotionController()
        assert controller.is_playing is False
        assert controller.current_frame == 0
        assert controller.playback_speed == 1.0
        assert controller.loop is True
    
    def test_set_frame_count(self, app):
        """Test setting total frames"""
        controller = MotionController()
        controller.set_frame_count(100)
        assert controller.total_frames == 100
    
    def test_set_clip_range(self, app):
        """Test setting clip range"""
        controller = MotionController()
        controller.set_frame_count(100)
        controller.set_clip_range(10, 50)
        assert controller.clip_start == 10
        assert controller.clip_end == 50
    
    def test_play_pause(self, app):
        """Test play/pause functionality"""
        controller = MotionController()
        
        # 初始为暂停
        assert controller.is_playing is False
        
        # 开始播放
        controller.play()
        assert controller.is_playing is True
        
        # 暂停
        controller.pause()
        assert controller.is_playing is False
    
    def test_next_frame(self, app):
        """Test advancing to next frame"""
        controller = MotionController()
        controller.set_frame_count(100)
        controller.set_clip_range(0, 100)
        
        controller.next_frame()
        assert controller.current_frame == 1
    
    def test_prev_frame(self, app):
        """Test going to previous frame"""
        controller = MotionController()
        controller.set_frame_count(100)
        controller.current_frame = 10
        
        controller.prev_frame()
        assert controller.current_frame == 9
    
    def test_go_to_start(self, app):
        """Test go to start of clip"""
        controller = MotionController()
        controller.set_frame_count(100)
        controller.set_clip_range(20, 80)
        controller.current_frame = 50
        
        controller.go_to_start()
        assert controller.current_frame == 20
    
    def test_go_to_end(self, app):
        """Test go to end of clip"""
        controller = MotionController()
        controller.set_frame_count(100)
        controller.set_clip_range(20, 80)
        controller.current_frame = 50
        
        controller.go_to_end()
        # End frame is exclusive, so we should be at clip_end - 1
        assert controller.current_frame == 79
```

- [ ] **Step 2: 运行测试，验证失败**

Run: `cd /home/lupinjia/GMR && python -m pytest tests/test_gui/test_motion_controller.py -v`

Expected: Tests FAIL with ImportError

- [ ] **Step 3: 实现MotionController**

```python
# general_motion_retargeting/gui/motion_controller.py
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
```

- [ ] **Step 4: 运行测试**

Run: `cd /home/lupinjia/GMR && python -m pytest tests/test_gui/test_motion_controller.py -v`

Expected: Tests PASS

- [ ] **Step 5: Commit**

```bash
git add general_motion_retargeting/gui/motion_controller.py tests/test_gui/test_motion_controller.py
git commit -m "feat: implement MotionController with playback and frame navigation"
```

---

## Task 5: 实现MainWindow（主窗口）

**Files:**
- Create: `general_motion_retargeting/gui/main_window.py`
- Test: 集成测试，手动验证

- [ ] **Step 1: 实现MainWindow**

```python
# general_motion_retargeting/gui/main_window.py
"""
主窗口

整合所有组件的主界面。
"""

import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QPushButton, QComboBox, QSlider, QFileDialog,
    QMessageBox, QApplication, QSpinBox, QDoubleSpinBox,
    QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence

from .gmr_manager import GMRDataManager
from .motion_controller import MotionController
from .timeline_widget import TimelineWidget
from general_motion_retargeting import RobotMotionViewer, ROBOT_XML_DICT
from general_motion_retargeting.params import ROBOT_LIST


class MainWindow(QMainWindow):
    """GMR可视化编辑器主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("GMR Visualizer")
        self.setMinimumSize(800, 600)
        
        # 组件
        self.data_manager = GMRDataManager()
        self.motion_controller = MotionController()
        self.viewer = None
        
        # 当前状态
        self.current_file = None
        self.current_robot = None
        
        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()
        self.connect_signals()
    
    def init_ui(self):
        """初始化UI"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 机器人选择区
        robot_group = QGroupBox("Robot")
        robot_layout = QHBoxLayout(robot_group)
        
        robot_layout.addWidget(QLabel("Select Robot:"))
        
        self.robot_combo = QComboBox()
        self.robot_combo.addItems(ROBOT_LIST)
        self.robot_combo.currentTextChanged.connect(self.on_robot_changed)
        robot_layout.addWidget(self.robot_combo)
        
        robot_layout.addStretch()
        
        self.info_label = QLabel("No file loaded")
        robot_layout.addWidget(self.info_label)
        
        layout.addWidget(robot_group)
        
        # 控制区
        control_group = QGroupBox("Playback Controls")
        control_layout = QHBoxLayout(control_group)
        
        # 播放按钮
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setCheckable(True)
        self.play_btn.clicked.connect(self.toggle_playback)
        control_layout.addWidget(self.play_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_playback)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addSpacing(20)
        
        # 导航按钮
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setToolTip("Previous Frame (←)")
        self.prev_btn.clicked.connect(self.prev_frame)
        control_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("⏭")
        self.next_btn.setToolTip("Next Frame (→)")
        self.next_btn.clicked.connect(self.next_frame)
        control_layout.addWidget(self.next_btn)
        
        self.start_btn = QPushButton("⏮⏮")
        self.start_btn.setToolTip("Go to Start (Home)")
        self.start_btn.clicked.connect(self.go_to_start)
        control_layout.addWidget(self.start_btn)
        
        self.end_btn = QPushButton("⏭⏭")
        self.end_btn.setToolTip("Go to End (End)")
        self.end_btn.clicked.connect(self.go_to_end)
        control_layout.addWidget(self.end_btn)
        
        control_layout.addSpacing(20)
        
        # 速度控制
        control_layout.addWidget(QLabel("Speed:"))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 3.0)
        self.speed_spin.setValue(1.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.valueChanged.connect(self.on_speed_changed)
        control_layout.addWidget(self.speed_spin)
        
        # 循环开关
        self.loop_check = QCheckBox("Loop")
        self.loop_check.setChecked(True)
        self.loop_check.stateChanged.connect(self.on_loop_changed)
        control_layout.addWidget(self.loop_check)
        
        control_layout.addStretch()
        
        layout.addWidget(control_group)
        
        # 时间轴
        self.timeline = TimelineWidget()
        layout.addWidget(self.timeline)
        
        # 底部操作区
        action_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📤 Export Clip")
        self.export_btn.clicked.connect(self.export_clip)
        self.export_btn.setEnabled(False)
        action_layout.addWidget(self.export_btn)
        
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
    
    def init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        
        # File菜单
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        export_action = QAction("&Export Clip...", self)
        export_action.triggered.connect(self.export_clip)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View菜单
        view_menu = menubar.addMenu("&View")
        
        reset_view_action = QAction("&Reset View", self)
        reset_view_action.triggered.connect(self.reset_view)
        view_menu.addAction(reset_view_action)
        
        toggle_loop_action = QAction("&Toggle Loop", self)
        toggle_loop_action.setCheckable(True)
        toggle_loop_action.setChecked(True)
        toggle_loop_action.triggered.connect(self.loop_check.setChecked)
        view_menu.addAction(toggle_loop_action)
        
        # Help菜单
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # 可添加常用操作的快捷按钮
    
    def init_statusbar(self):
        """初始化状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.statusbar.showMessage("Ready")
    
    def connect_signals(self):
        """连接信号"""
        # 时间轴 -> 控制器
        self.timeline.current_frame_changed.connect(self.on_timeline_frame_changed)
        self.timeline.clip_range_changed.connect(self.on_timeline_clip_changed)
        
        # 控制器 -> UI
        self.motion_controller.frame_changed.connect(self.on_controller_frame_changed)
        self.motion_controller.playback_started.connect(self.on_playback_started)
        self.motion_controller.playback_paused.connect(self.on_playback_paused)
        
        # 设置控制器回调
        self.motion_controller.set_callbacks(
            get_frame_data=self.get_frame_data,
            send_to_viewer=self.send_to_viewer
        )
    
    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open GMR File", "", "Pickle Files (*.pkl);;All Files (*)")
        
        if not file_path:
            return
        
        try:
            self.data_manager.load(file_path)
            self.current_file = file_path
            
            # 更新UI
            meta = self.data_manager.get_metadata()
            self.timeline.set_frame_count(meta['frame_count'])
            self.motion_controller.set_frame_count(meta['frame_count'])
            self.motion_controller.set_fps(meta['fps'])
            
            # 更新信息标签
            robot = self.robot_combo.currentText()
            info = f"File: {os.path.basename(file_path)} | "
            info += f"Frames: {meta['frame_count']} | "
            info += f"DOF: {meta['dof_count']} | "
            info += f"Duration: {meta['duration']:.2f}s | "
            info += f"FPS: {meta['fps']}"
            self.info_label.setText(info)
            
            self.export_btn.setEnabled(True)
            self.statusbar.showMessage(f"Loaded: {file_path}")
            
            # 初始化viewer
            self.init_viewer()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
    
    def save_file(self):
        """保存文件"""
        if not self.current_file:
            self.save_file_as()
            return
        
        try:
            self.data_manager.save(self.current_file)
            self.statusbar.showMessage(f"Saved: {self.current_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    def save_file_as(self):
        """另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save GMR File", "", "Pickle Files (*.pkl);;All Files (*)")
        
        if not file_path:
            return
        
        try:
            self.data_manager.save(file_path)
            self.current_file = file_path
            self.statusbar.showMessage(f"Saved: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    def export_clip(self):
        """导出裁剪片段"""
        if not self.data_manager.data:
            QMessageBox.warning(self, "Warning", "No data loaded")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Clip", "", "Pickle Files (*.pkl);;All Files (*)")
        
        if not file_path:
            return
        
        try:
            clip_data = self.data_manager.clip(
                self.timeline.clip_start,
                self.timeline.clip_end
            )
            self.data_manager.save(file_path, clip_data)
            
            clip_duration = (self.timeline.clip_end - self.timeline.clip_start) / self.data_manager.data['fps']
            self.statusbar.showMessage(
                f"Exported clip: {self.timeline.clip_start}-{self.timeline.clip_end} "
                f"({clip_duration:.2f}s) to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export clip:\n{str(e)}")
    
    def init_viewer(self):
        """初始化MuJoCo viewer"""
        robot_type = self.robot_combo.currentText()
        
        if not robot_type or robot_type not in ROBOT_XML_DICT:
            return
        
        try:
            if self.viewer is not None:
                self.viewer.close()
            
            meta = self.data_manager.get_metadata()
            
            self.viewer = RobotMotionViewer(
                robot_type=robot_type,
                camera_follow=True,
                motion_fps=meta['fps']
            )
            
            # 显示第一帧
            frame_data = self.get_frame_data(0)
            if frame_data:
                self.send_to_viewer(*frame_data)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize viewer:\n{str(e)}")
    
    def on_robot_changed(self, robot_name):
        """机器人类型改变"""
        if self.data_manager.data:
            self.init_viewer()
    
    def toggle_playback(self):
        """切换播放/暂停"""
        self.motion_controller.toggle_playback()
    
    def stop_playback(self):
        """停止播放"""
        self.motion_controller.stop()
        self.play_btn.setChecked(False)
        self.play_btn.setText("▶ Play")
    
    def prev_frame(self):
        """上一帧"""
        self.motion_controller.prev_frame()
        self.update_viewer()
    
    def next_frame(self):
        """下一帧"""
        self.motion_controller.next_frame()
        self.update_viewer()
    
    def go_to_start(self):
        """跳到开始"""
        self.motion_controller.go_to_start()
        self.update_viewer()
    
    def go_to_end(self):
        """跳到结束"""
        self.motion_controller.go_to_end()
        self.update_viewer()
    
    def on_speed_changed(self, value):
        """播放速度改变"""
        self.motion_controller.set_playback_speed(value)
    
    def on_loop_changed(self, state):
        """循环状态改变"""
        self.motion_controller.set_loop(state == Qt.CheckState.Checked.value)
    
    def on_timeline_frame_changed(self, frame):
        """时间轴帧改变"""
        self.motion_controller.set_current_frame(frame)
        self.update_viewer()
    
    def on_timeline_clip_changed(self, start, end):
        """时间轴裁剪范围改变"""
        self.motion_controller.set_clip_range(start, end)
    
    def on_controller_frame_changed(self, frame):
        """控制器帧改变"""
        self.timeline.set_current_frame(frame)
        self.update_viewer()
    
    def on_playback_started(self):
        """播放开始"""
        self.play_btn.setChecked(True)
        self.play_btn.setText("⏸ Pause")
        self.statusbar.showMessage("Playing...")
    
    def on_playback_paused(self):
        """播放暂停"""
        self.play_btn.setChecked(False)
        self.play_btn.setText("▶ Play")
        self.statusbar.showMessage("Paused")
    
    def get_frame_data(self, frame_idx):
        """获取帧数据（供控制器回调）"""
        try:
            return self.data_manager.get_frame(frame_idx)
        except:
            return None
    
    def send_to_viewer(self, root_pos, root_rot, dof_pos):
        """发送数据到viewer（供控制器回调）"""
        if self.viewer is None:
            return
        
        try:
            # root_rot从xyzw转换为wxyz（MuJoCo格式）
            root_rot_wxyz = root_rot[[3, 0, 1, 2]]
            
            self.viewer.step(
                root_pos=root_pos,
                root_rot=root_rot_wxyz,
                dof_pos=dof_pos,
                rate_limit=False,
                follow_camera=True
            )
        except Exception as e:
            print(f"Viewer error: {e}")
    
    def update_viewer(self):
        """更新viewer显示"""
        frame_data = self.get_frame_data(self.motion_controller.current_frame)
        if frame_data:
            self.send_to_viewer(*frame_data)
    
    def reset_view(self):
        """重置视图"""
        if self.viewer:
            # 重新初始化viewer
            self.init_viewer()
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "About GMR Visualizer",
            "<h2>GMR Visualizer</h2>"
            "<p>Version 1.0</p>"
            "<p>A GUI tool for visualizing and editing GMR robot motion data.</p>"
            "<p>Built with PyQt6 and MuJoCo</p>")
    
    def keyPressEvent(self, event):
        """键盘事件"""
        key = event.key()
        
        if key == Qt.Key.Key_Space:
            self.toggle_playback()
        elif key == Qt.Key.Key_Left:
            self.prev_frame()
        elif key == Qt.Key.Key_Right:
            self.next_frame()
        elif key == Qt.Key.Key_Home:
            self.go_to_start()
        elif key == Qt.Key.Key_End:
            self.go_to_end()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.viewer is not None:
            self.viewer.close()
        event.accept()
```

- [ ] **Step 2: 更新__init__.py**

修改`general_motion_retargeting/gui/__init__.py`确保导入正确：

```python
"""
GMR Visualizer GUI Module

提供机器人运动数据的可视化和编辑功能。
"""

from .gmr_manager import GMRDataManager
from .motion_controller import MotionController
from .timeline_widget import TimelineWidget
from .main_window import MainWindow

__all__ = [
    'GMRDataManager',
    'MotionController', 
    'TimelineWidget',
    'MainWindow',
]
```

- [ ] **Step 3: 创建启动脚本**

```python
# scripts/gmr_visualizer.py
#!/usr/bin/env python3
"""
GMR可视化编辑器启动脚本

用法:
    python scripts/gmr_visualizer.py [可选的.pkl文件路径]
"""

import sys
from PyQt6.QtWidgets import QApplication
from general_motion_retargeting.gui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GMR Visualizer")
    app.setApplicationVersion("1.0")
    
    window = MainWindow()
    window.show()
    
    # 如果提供了文件路径，自动打开
    if len(sys.argv) > 1:
        window.current_file = sys.argv[1]
        # 这里需要修改open_file逻辑或使用其他方式加载
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 验证启动脚本可运行**

Run: `cd /home/lupinjia/GMR && python -c "from general_motion_retargeting.gui import MainWindow; print('Import OK')"`

Expected: Import OK

- [ ] **Step 5: Commit**

```bash
git add general_motion_retargeting/gui/main_window.py general_motion_retargeting/gui/__init__.py scripts/gmr_visualizer.py
git commit -m "feat: implement MainWindow and application entry point"
```

---

## Task 6: 更新README文档

**Files:**
- Modify: `README.md` (添加GMR可视化编辑器部分)

- [ ] **Step 1: 在README.md中添加使用说明**

在README.md的合适位置（如在## Usage部分后）添加：

```markdown
### GMR Visualizer GUI

我们提供了一个图形化界面工具用于可视化和编辑GMR运动数据。

#### 启动可视化编辑器

```bash
python scripts/gmr_visualizer.py
```

#### 功能特性

- **导入/导出**: 支持加载和保存 `.pkl` 格式的GMR运动数据
- **可视化**: 使用MuJoCo实时渲染机器人运动
- **剪辑**: 简单的起止时间裁剪功能，导出选定片段
- **多机器人支持**: 支持项目中所有17种机器人模型

#### 界面说明

1. **机器人选择**: 从下拉菜单选择对应的机器人类型
2. **播放控制**: 
   - ▶ Play / ⏸ Pause: 播放/暂停
   - ⏹ Stop: 停止并重置到起始位置
   - ⏮ / ⏭: 上一帧/下一帧
   - ⏮⏮ / ⏭⏭: 跳到裁剪范围开始/结束
3. **时间轴**:
   - 蓝色手柄: 裁剪起点
   - 红色手柄: 裁剪终点
   - 黄色竖线: 当前帧位置
4. **导出**: 点击"📤 Export Clip"导出裁剪后的片段

#### 快捷键

- `Space`: 播放/暂停
- `← / →`: 上一帧/下一帧
- `Home`: 跳到裁剪范围开始
- `End`: 跳到裁剪范围结束
- `Ctrl+O`: 打开文件
- `Ctrl+S`: 保存文件
- `Ctrl+Shift+S`: 另存为

#### 示例工作流程

1. 运行 `python scripts/gmr_visualizer.py`
2. File → Open，选择一个 `.pkl` 运动数据文件
3. 在机器人选择下拉框中选择对应的机器人类型
4. 点击播放按钮查看运动
5. 拖动时间轴上的蓝色和红色手柄设置裁剪范围
6. 点击"Export Clip"导出裁剪后的片段
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add GMR Visualizer GUI usage instructions to README"
```

---

## 手动测试验证清单

实施完成后，请按照以下清单进行验证：

- [ ] 1. 启动应用：`python scripts/gmr_visualizer.py`
- [ ] 2. 打开一个.pkl文件，验证数据正确加载
- [ ] 3. 选择对应的机器人，验证MuJoCo viewer窗口弹出并显示第一帧
- [ ] 4. 点击Play按钮，验证运动正常播放
- [ ] 5. 拖动时间轴手柄设置裁剪范围
- [ ] 6. 点击Export Clip导出文件
- [ ] 7. 重新打开导出的文件，验证数据正确
- [ ] 8. 测试所有快捷键功能
- [ ] 9. 测试File菜单的所有选项
- [ ] 10. 测试多机器人切换功能

---

## 依赖安装

确保已安装PyQt6：

```bash
pip install PyQt6
```

其他依赖已在现有GMR项目中安装。

---

**计划完成时间估计:** 约4-6小时（按顺序完成任务）

**建议：** 使用superpowers:subagent-driven-development或superpowers:executing-plans执行此计划。
