"""
波形显示控件

用于显示GMR数据中各key的波形图，支持多维度数据和当前帧指示器。
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont


class SingleDimensionWaveform(QWidget):
    """
    单个维度的波形显示控件
    
    波形占据整个区域，文字信息显示在角落
    """

    def __init__(self, parent=None, dim_index=0, dim_name=""):
        super().__init__(parent)

        self.dim_index = dim_index
        self.dim_name = dim_name
        self.data = None
        self.current_frame = 0
        self.total_frames = 0
        self.data_min = 0.0
        self.data_max = 0.0

        # 颜色方案
        self.color = QColor(30, 144, 255)  # 默认蓝色

        # 设置大小
        self.setMinimumHeight(60)
        self.setMaximumHeight(80)

    def set_data(self, data, color=None):
        """
        设置数据

        Args:
            data: 1D numpy数组 [frames]
            color: 波形颜色
        """
        self.data = data
        if color is not None:
            self.color = color

        if data is not None and len(data) > 0:
            self.total_frames = len(data)
            self.data_min = float(np.min(data))
            self.data_max = float(np.max(data))
        else:
            self.total_frames = 0
            self.data_min = 0.0
            self.data_max = 0.0

        self.update()

    def set_current_frame(self, frame):
        """设置当前帧"""
        self.current_frame = frame
        self.update()

    def paintEvent(self, event):
        """绘制事件 - 绘制波形和文字信息"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # 背景
        painter.fillRect(self.rect(), QColor(45, 45, 45))

        # 如果没有数据，显示提示
        if self.data is None or len(self.data) < 2:
            painter.setPen(QPen(QColor(150, 150, 150)))
            font = QFont("Arial", 9)
            painter.setFont(font)
            painter.drawText(10, height // 2 + 4, f"{self.dim_name}: No data")
            painter.end()
            return

        # 边距
        margin_x = 10
        margin_y = 5
        graph_width = width - 2 * margin_x
        graph_height = height - 2 * margin_y

        # 数据范围
        data_min = self.data_min
        data_max = self.data_max
        if data_max == data_min:
            data_max = data_min + 1

        # 绘制网格线（横向）
        painter.setPen(QPen(QColor(60, 60, 60), 1, Qt.PenStyle.DotLine))
        for i in range(1, 3):
            y = margin_y + (graph_height * i) // 3
            painter.drawLine(margin_x, y, margin_x + graph_width, y)

        # 绘制波形
        pen = QPen(self.color, 1.5)
        painter.setPen(pen)

        n_points = len(self.data)
        points = []
        for i in range(n_points):
            x = margin_x + (i * graph_width) // max(1, n_points - 1)
            normalized = (self.data[i] - data_min) / (data_max - data_min)
            # 留出上下边距
            normalized = 0.1 + normalized * 0.8
            y = margin_y + graph_height - int(normalized * graph_height)
            points.append((x, y))

        # 绘制线段
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])

        # 绘制当前帧指示器（黄色竖线）
        if self.total_frames > 0:
            x = margin_x + (self.current_frame * graph_width) // max(1, self.total_frames - 1)
            painter.setPen(QPen(QColor(255, 255, 0), 2))
            painter.drawLine(x, margin_y, x, margin_y + graph_height)

        # 在左上角绘制文字信息（叠加在波形上）
        # 绘制半透明背景
        info_bg_rect = (10, 2, 200, 45)
        painter.fillRect(*info_bg_rect, QColor(0, 0, 0, 160))

        # 维度名称（粗体，带颜色）
        font_name = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font_name)
        painter.setPen(QPen(self.color))
        painter.drawText(14, 16, self.dim_name)

        # 统计信息（白色小字）
        font_info = QFont("Arial", 8)
        painter.setFont(font_info)

        # 当前值（绿色突出显示）
        painter.setPen(QPen(QColor(100, 255, 100)))
        if 0 <= self.current_frame < len(self.data):
            current_val = float(self.data[self.current_frame])
            painter.drawText(14, 30, f"Cur: {current_val:.4f}")
        else:
            painter.drawText(14, 30, "Cur: --")

        # 最小值和最大值
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.drawText(100, 30, f"Min: {data_min:.4f}")
        painter.drawText(100, 42, f"Max: {data_max:.4f}")

        painter.end()


class MultiDimensionWaveformWidget(QWidget):
    """
    多维度波形显示控件
    
    为每个维度创建一个单独的行，显示波形和统计信息
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.data = None
        self.key_name = ""
        self.current_frame = 0
        self.dimension_widgets = []
        
        # 颜色方案
        self.colors = [
            QColor(255, 99, 71),    # 番茄红
            QColor(60, 179, 113),   # 中海绿
            QColor(30, 144, 255),   # 道奇蓝
            QColor(255, 165, 0),    # 橙色
            QColor(147, 112, 219),  # 中紫
            QColor(255, 20, 147),   # 深粉红
            QColor(0, 206, 209),    # 深青色
            QColor(255, 215, 0),    # 金色
            QColor(220, 20, 60),    # 猩红
            QColor(32, 178, 170),   # 浅海绿
            QColor(138, 43, 226),   # 蓝紫
            QColor(255, 140, 0),    # 深橙
            QColor(0, 255, 127),    # 春绿
            QColor(255, 105, 180),  # 热粉
            QColor(64, 224, 208),   # 绿松石
            QColor(255, 69, 0),     # 橙红
        ]
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(2)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加弹性空间
        self.main_layout.addStretch()
    
    def clear(self):
        """清除所有维度显示"""
        # 移除所有现有的维度控件
        for widget in self.dimension_widgets:
            self.main_layout.removeWidget(widget)
            widget.deleteLater()
        self.dimension_widgets.clear()
    
    def set_data(self, data, key_name=""):
        """
        设置数据
        
        Args:
            data: numpy数组
            key_name: key名称
        """
        self.clear()
        self.data = data
        self.key_name = key_name
        
        if data is None or not isinstance(data, np.ndarray) or data.size == 0:
            return
        
        # 确定维度数量
        if len(data.shape) == 1:
            # 1D数据: [frames]
            num_dims = 1
            data_list = [data]
            dim_names = ["Value"]
        elif len(data.shape) == 2:
            # 2D数据: [frames, dims]
            num_dims = data.shape[1]
            data_list = [data[:, i] for i in range(num_dims)]
            dim_names = [f"Dim {i}" for i in range(num_dims)]
        elif len(data.shape) == 3:
            # 3D数据: [frames, bodies, 3] - 展平为 [frames, bodies*3]
            flat_data = data.reshape(data.shape[0], -1)
            num_dims = flat_data.shape[1]
            data_list = [flat_data[:, i] for i in range(num_dims)]
            # 生成有意义的名称，如 "Body 0 X", "Body 0 Y", etc.
            dim_names = []
            coords = ['X', 'Y', 'Z']
            for body in range(data.shape[1]):
                for coord in coords[:data.shape[2]]:
                    dim_names.append(f"Body {body} {coord}")
        else:
            # 高维数据
            flat_data = data.reshape(data.shape[0], -1)
            num_dims = min(flat_data.shape[1], 32)  # 最多显示32个维度
            data_list = [flat_data[:, i] for i in range(num_dims)]
            dim_names = [f"Dim {i}" for i in range(num_dims)]
        
        # 为每个维度创建控件
        for i in range(num_dims):
            color = self.colors[i % len(self.colors)]
            dim_widget = SingleDimensionWaveform(self, dim_index=i, dim_name=dim_names[i])
            dim_widget.set_data(data_list[i], color)
            dim_widget.set_current_frame(self.current_frame)

            # 在弹性空间之前插入
            self.main_layout.insertWidget(self.main_layout.count() - 1, dim_widget)
            self.dimension_widgets.append(dim_widget)
    
    def set_current_frame(self, frame):
        """设置当前帧"""
        self.current_frame = frame
        for widget in self.dimension_widgets:
            widget.set_current_frame(frame)


class WaveformCanvas(QWidget):
    """
    波形绘制画布（保留用于兼容性）
    
    功能：
    - 绘制数据波形
    - 显示当前帧位置（黄色竖线）
    - 支持多维度数据（每个维度不同颜色）
    - 自适应缩放
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.data = None  # numpy数组或None
        self.current_frame = 0
        self.total_frames = 0
        self.key_name = ""
        self.data_shape = ()
        
        # 颜色方案（支持最多12个维度）
        self.colors = [
            QColor(255, 99, 71),    # 番茄红
            QColor(60, 179, 113),   # 中海绿
            QColor(30, 144, 255),   # 道奇蓝
            QColor(255, 165, 0),    # 橙色
            QColor(147, 112, 219),  # 中紫
            QColor(255, 20, 147),   # 深粉红
            QColor(0, 206, 209),    # 深青色
            QColor(255, 215, 0),    # 金色
            QColor(220, 20, 60),    # 猩红
            QColor(32, 178, 170),   # 浅海绿
            QColor(138, 43, 226),   # 蓝紫
            QColor(255, 140, 0),    # 深橙
        ]
        
        self.setMinimumHeight(200)
        
    def set_data(self, data, key_name=""):
        """
        设置要显示的数据
        
        Args:
            data: numpy数组或None
            key_name: 数据key名称
        """
        self.data = data
        self.key_name = key_name
        
        if data is not None and isinstance(data, np.ndarray):
            self.total_frames = data.shape[0] if data.shape[0] > 0 else 0
            self.data_shape = data.shape
        else:
            self.total_frames = 0
            self.data_shape = ()
        
        self.update()
    
    def set_current_frame(self, frame):
        """设置当前帧位置"""
        self.current_frame = frame
        self.update()
    
    def paintEvent(self, event):
        """绘制波形"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 背景
        painter.fillRect(self.rect(), QColor(40, 40, 40))
        
        # 如果没有数据或数据为None，显示提示信息
        if self.data is None:
            self._draw_no_data_message(painter, width, height, "No data available (None)")
            return
        
        if not isinstance(self.data, np.ndarray):
            self._draw_no_data_message(painter, width, height, f"Unsupported data type: {type(self.data).__name__}")
            return
        
        if self.data.size == 0:
            self._draw_no_data_message(painter, width, height, "Empty data array")
            return
        
        # 绘制波形
        try:
            self._draw_waveform(painter, width, height)
        except Exception as e:
            self._draw_no_data_message(painter, width, height, f"Error drawing waveform: {str(e)}")
        
        painter.end()
    
    def _draw_no_data_message(self, painter, width, height, message):
        """绘制无数据提示信息"""
        painter.setPen(QPen(QColor(200, 200, 200)))
        font = QFont("Arial", 12)
        painter.setFont(font)
        
        # 计算文本居中位置
        text_rect = painter.boundingRect(0, 0, width, height, Qt.AlignmentFlag.AlignCenter, message)
        x = (width - text_rect.width()) // 2
        y = (height - text_rect.height()) // 2 + text_rect.height() // 2
        
        painter.drawText(x, y, message)
    
    def _draw_waveform(self, painter, width, height):
        """绘制波形图"""
        margin = 40
        graph_width = width - 2 * margin
        graph_height = height - 2 * margin
        
        # 绘制边框
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRect(margin, margin, graph_width, graph_height)
        
        # 绘制网格线
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        for i in range(1, 5):
            y = margin + (graph_height * i) // 5
            painter.drawLine(margin, y, margin + graph_width, y)
        
        # 确定数据维度
        if len(self.data_shape) == 1:
            # 1D数据: [frames]
            num_dims = 1
            data_to_plot = [self.data]
        elif len(self.data_shape) == 2:
            # 2D数据: [frames, dims]
            num_dims = min(self.data_shape[1], len(self.colors))
            data_to_plot = [self.data[:, i] for i in range(num_dims)]
        elif len(self.data_shape) == 3:
            # 3D数据: [frames, bodies, 3] - 展平为 [frames, bodies*3]
            flat_data = self.data.reshape(self.data_shape[0], -1)
            num_dims = min(flat_data.shape[1], len(self.colors))
            data_to_plot = [flat_data[:, i] for i in range(num_dims)]
        else:
            # 高维数据，展平
            flat_data = self.data.reshape(self.data_shape[0], -1)
            num_dims = min(flat_data.shape[1], len(self.colors))
            data_to_plot = [flat_data[:, i] for i in range(num_dims)]
        
        # 绘制每个维度的波形
        for dim_idx, dim_data in enumerate(data_to_plot):
            color = self.colors[dim_idx % len(self.colors)]
            self._draw_single_waveform(painter, dim_data, color, margin, graph_width, graph_height, dim_idx)
        
        # 绘制当前帧指示器（黄色竖线）
        if self.total_frames > 0:
            x = margin + (self.current_frame * graph_width) // max(1, self.total_frames - 1)
            painter.setPen(QPen(QColor(255, 255, 0), 2))
            painter.drawLine(x, margin, x, margin + graph_height)
        
        # 绘制图例
        self._draw_legend(painter, num_dims, width, margin)
    
    def _draw_single_waveform(self, painter, data, color, margin, graph_width, graph_height, dim_idx):
        """绘制单个维度的波形"""
        if len(data) == 0:
            return
        
        # 计算数据范围
        data_min = np.min(data)
        data_max = np.max(data)
        
        if data_max == data_min:
            data_max = data_min + 1  # 避免除以零
        
        # 绘制波形线
        pen = QPen(color, 1.5)
        painter.setPen(pen)
        
        n_points = len(data)
        if n_points < 2:
            return
        
        # 计算点的坐标
        points = []
        for i in range(n_points):
            x = margin + (i * graph_width) // max(1, n_points - 1)
            # 归一化到 [margin, margin + graph_height]，并反转Y轴
            normalized = (data[i] - data_min) / (data_max - data_min)
            y = margin + graph_height - int(normalized * graph_height)
            points.append((x, y))
        
        # 绘制线段
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
    
    def _draw_legend(self, painter, num_dims, width, margin):
        """绘制图例"""
        if num_dims <= 1:
            return
        
        legend_x = margin
        legend_y = 10
        item_width = 80
        
        for i in range(min(num_dims, 8)):  # 最多显示8个图例
            x = legend_x + (i % 4) * item_width
            y = legend_y + (i // 4) * 20
            
            # 绘制颜色块
            painter.fillRect(x, y, 12, 12, self.colors[i])
            
            # 绘制标签
            painter.setPen(QPen(QColor(200, 200, 200)))
            painter.drawText(x + 16, y + 10, f"Dim {i}")


class WaveformWindow(QWidget):
    """
    波形显示窗口
    
    包含：
    - 下拉框选择要显示的数据key
    - 多维度波形显示（每行一个维度）
    - 数据信息展示
    """
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(None)  # 不设置父窗口，使其成为独立窗口
        
        self.parent_window = parent  # 保存父窗口引用，但不作为Qt父对象
        self.data_manager = data_manager
        self.current_frame = 0
        
        self.setWindowTitle("Waveform Display")
        self.setMinimumSize(900, 600)
        
        # 设置窗口标志，使其成为独立工具窗口，保持在主窗口之上
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 控制区
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Select Data:"))
        
        # 下拉框
        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(300)
        self.key_combo.currentTextChanged.connect(self.on_key_changed)
        control_layout.addWidget(self.key_combo)
        
        control_layout.addStretch()
        
        # 数据信息标签
        self.info_label = QLabel("No data loaded")
        self.info_label.setStyleSheet("color: #888;")
        control_layout.addWidget(self.info_label)
        
        layout.addLayout(control_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #555;")
        layout.addWidget(line)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 多维度波形控件
        self.multi_waveform = MultiDimensionWaveformWidget()
        scroll.setWidget(self.multi_waveform)
        
        layout.addWidget(scroll)
        
        # 状态栏
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # 加载可用的key
        self.load_available_keys()
    
    def load_available_keys(self):
        """加载可用的数据key"""
        self.key_combo.clear()

        if self.data_manager is None or self.data_manager.data is None:
            self.key_combo.addItem("No data available")
            self.key_combo.setEnabled(False)
            return

        self.key_combo.setEnabled(True)

        # 获取所有key（包括所有类型，不只是numpy数组）
        available_keys = []

        for key in self.data_manager.data.keys():
            # 跳过内部辅助字段
            if key == 'frames':
                continue
            available_keys.append(key)

        # 按字母顺序排序
        available_keys.sort()

        if available_keys:
            self.key_combo.addItems(available_keys)
            self.status_label.setText(f"Loaded {len(available_keys)} data keys")
        else:
            self.key_combo.addItem("No valid keys found")
    
    def on_key_changed(self, key_name):
        """选择的key改变"""
        if not key_name or key_name in ["No data available", "No valid keys found"]:
            self.multi_waveform.clear()
            self.info_label.setText("No data selected")
            return

        # 获取数据
        try:
            if self.data_manager is None or self.data_manager.data is None:
                self.multi_waveform.clear()
                self.info_label.setText("No data loaded")
                return

            # 安全地获取数据
            if key_name not in self.data_manager.data:
                self.multi_waveform.clear()
                self.info_label.setText(f"Key '{key_name}' not found")
                return

            data = self.data_manager.data[key_name]

            # 检查数据是否为None
            if data is None:
                self.multi_waveform.clear()
                self.info_label.setText(f"Key '{key_name}' has no value (None)")
                self.status_label.setText(f"Selected: {key_name} - Value is None")
                return

            # 尝试将标量转换为数组
            if np.isscalar(data):
                # 标量值（如fps），创建一个恒定值的数组
                if self.data_manager.data is not None and 'root_pos' in self.data_manager.data:
                    # 使用root_pos的帧数作为长度
                    num_frames = len(self.data_manager.data['root_pos'])
                else:
                    num_frames = 100  # 默认值

                scalar_array = np.full(num_frames, data)
                self.multi_waveform.set_data(scalar_array, key_name)
                self.multi_waveform.set_current_frame(self.current_frame)

                self.info_label.setText(f"Scalar: {data} | Frames: {num_frames}")
                self.status_label.setText(f"Selected: {key_name} = {data}")
                return

            # 检查数据类型
            if not isinstance(data, np.ndarray):
                self.multi_waveform.clear()
                self.info_label.setText(f"Key '{key_name}' - Type: {type(data).__name__} (not displayable)")
                self.status_label.setText(f"Selected: {key_name} - Unsupported type: {type(data).__name__}")
                return

            # 检查数据是否为空
            if data.size == 0:
                self.multi_waveform.clear()
                self.info_label.setText(f"Key '{key_name}' - Empty array")
                self.status_label.setText(f"Selected: {key_name} - Empty array")
                return

            # 设置数据到多维度波形控件
            self.multi_waveform.set_data(data, key_name)
            self.multi_waveform.set_current_frame(self.current_frame)

            # 更新信息标签
            shape_str = "x".join(str(x) for x in data.shape)
            dtype_str = str(data.dtype)
            num_dims = 1 if len(data.shape) == 1 else data.shape[1] if len(data.shape) == 2 else data.shape[1] * data.shape[2] if len(data.shape) == 3 else "many"
            self.info_label.setText(f"Shape: [{shape_str}] | Type: {dtype_str} | Frames: {data.shape[0]} | Dimensions: {num_dims}")
            self.status_label.setText(f"Selected: {key_name} | {num_dims} dimension(s)")

        except Exception as e:
            import traceback
            error_msg = f"Error loading key '{key_name}': {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            self.multi_waveform.clear()
            self.info_label.setText(error_msg)
            self.status_label.setText(f"Error: {str(e)}")
    
    def set_current_frame(self, frame):
        """设置当前帧（从主窗口调用）"""
        self.current_frame = frame
        self.multi_waveform.set_current_frame(frame)
    
    def update_data(self):
        """数据改变时更新（从主窗口调用）"""
        current_key = self.key_combo.currentText()
        self.load_available_keys()

        # 尝试恢复之前的选择
        if current_key and current_key != "No data available":
            index = self.key_combo.findText(current_key)
            if index >= 0:
                self.key_combo.setCurrentIndex(index)
            else:
                # 如果之前的选择不可用，触发一次change事件
                self.on_key_changed(self.key_combo.currentText())
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 通知主窗口波形窗口已关闭
        if self.parent_window is not None and hasattr(self.parent_window, 'waveform_window'):
            self.parent_window.waveform_window = None
        event.accept()


class WaveformDockWidget(QWidget):
    """
    可停靠的波形显示控件（用于集成到主窗口）
    """
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        
        self.data_manager = data_manager
        self.current_frame = 0
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 控制区
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Data:"))
        
        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(200)
        self.key_combo.currentTextChanged.connect(self.on_key_changed)
        control_layout.addWidget(self.key_combo)
        
        control_layout.addStretch()
        
        self.info_label = QLabel("No data")
        self.info_label.setStyleSheet("font-size: 10px; color: #888;")
        control_layout.addWidget(self.info_label)
        
        layout.addLayout(control_layout)
        
        # 多维度波形控件
        self.multi_waveform = MultiDimensionWaveformWidget()
        layout.addWidget(self.multi_waveform)
    
    def load_available_keys(self):
        """加载可用的数据key"""
        self.key_combo.clear()

        if self.data_manager is None or self.data_manager.data is None:
            self.key_combo.addItem("No data")
            self.key_combo.setEnabled(False)
            return

        self.key_combo.setEnabled(True)

        # 获取所有key（排除内部辅助字段）
        available_keys = [k for k in self.data_manager.data.keys() if k != 'frames']
        available_keys.sort()

        if available_keys:
            self.key_combo.addItems(available_keys)
    
    def on_key_changed(self, key_name):
        """选择的key改变"""
        if not key_name or key_name == "No data":
            self.multi_waveform.clear()
            self.info_label.setText("No data")
            return

        try:
            if self.data_manager is None or self.data_manager.data is None:
                self.multi_waveform.clear()
                self.info_label.setText("No data")
                return

            if key_name not in self.data_manager.data:
                self.multi_waveform.clear()
                self.info_label.setText(f"Key '{key_name}' not found")
                return

            data = self.data_manager.data[key_name]

            # 异常处理
            if data is None:
                self.multi_waveform.clear()
                self.info_label.setText(f"'{key_name}' = None")
                return

            # 处理标量值
            if np.isscalar(data):
                if self.data_manager.data is not None and 'root_pos' in self.data_manager.data:
                    num_frames = len(self.data_manager.data['root_pos'])
                else:
                    num_frames = 100

                scalar_array = np.full(num_frames, data)
                self.multi_waveform.set_data(scalar_array, key_name)
                self.multi_waveform.set_current_frame(self.current_frame)
                self.info_label.setText(f"{key_name} = {data}")
                return

            if not isinstance(data, np.ndarray):
                self.multi_waveform.clear()
                self.info_label.setText(f"'{key_name}' = {type(data).__name__}")
                return

            if data.size == 0:
                self.multi_waveform.clear()
                self.info_label.setText(f"'{key_name}' = empty")
                return

            self.multi_waveform.set_data(data, key_name)
            self.multi_waveform.set_current_frame(self.current_frame)

            shape_str = "x".join(str(x) for x in data.shape)
            self.info_label.setText(f"[{shape_str}] {str(data.dtype)}")

        except Exception as e:
            self.multi_waveform.clear()
            self.info_label.setText(f"Error: {str(e)}")
    
    def set_current_frame(self, frame):
        """设置当前帧"""
        self.current_frame = frame
        self.multi_waveform.set_current_frame(frame)
    
    def update_data(self):
        """数据改变时更新"""
        current_key = self.key_combo.currentText()
        self.load_available_keys()

        if current_key and current_key != "No data":
            index = self.key_combo.findText(current_key)
            if index >= 0:
                self.key_combo.setCurrentIndex(index)
            else:
                self.on_key_changed(self.key_combo.currentText())
