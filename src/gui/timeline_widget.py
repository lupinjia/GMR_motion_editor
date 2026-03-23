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
        self.timeline_canvas.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc;")
        
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
        
        self.timeline_canvas.total_frames = self.total_frames
        self.timeline_canvas.clip_end = self.clip_end
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
        # 默认fps 30
        fps = 30
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
