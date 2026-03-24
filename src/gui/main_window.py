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
from .wave_widget import WaveformWindow, WaveformDockWidget
from . import config

# 设置GMR路径并导入模块
config.setup_gmr_path()

# 导入GMR项目中的机器人相关模块
try:
    from general_motion_retargeting import RobotMotionViewer, ROBOT_XML_DICT
    GMR_AVAILABLE = True
    # 从ROBOT_XML_DICT获取机器人列表
    ROBOT_LIST = list(ROBOT_XML_DICT.keys())
except ImportError as e:
    GMR_AVAILABLE = False
    ROBOT_LIST = []
    print(f"Warning: GMR modules not available. Some features will be disabled.")
    print(f"Please check your GMR_ROOT_PATH setting in src/gui/config.py")
    print(f"Error: {e}")


class MainWindow(QMainWindow):
    """GMR可视化编辑器主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("GMR Motion Editor")
        self.setMinimumSize(800, 400)
        
        # 检查GMR路径配置
        self.check_gmr_config()
        
        # 组件
        self.data_manager = GMRDataManager()
        self.motion_controller = MotionController()
        self.viewer = None
        
        # 当前状态
        self.current_file = None
        self.current_robot = None
        
        # 波形显示窗口
        self.waveform_window = None
        
        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()
        self.connect_signals()
    
    def check_gmr_config(self):
        """检查GMR路径配置"""
        is_valid, message = config.validate_gmr_path()
        if not is_valid:
            print(f"\n{'='*60}")
            print("GMR Path Configuration Error")
            print(f"{'='*60}")
            print(message)
            print(f"\nPlease edit: motion_editor/src/gui/config.py")
            print(f"Set GMR_ROOT_PATH to your GMR installation directory")
            print(f"{'='*60}\n")
    
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
        if GMR_AVAILABLE and ROBOT_LIST:
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
        
        view_menu.addSeparator()
        
        # 波形显示窗口
        waveform_action = QAction("&Waveform Display", self)
        waveform_action.setShortcut(QKeySequence("Ctrl+W"))
        waveform_action.triggered.connect(self.open_waveform_window)
        view_menu.addAction(waveform_action)
        
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
            self.timeline.set_fps(meta['fps'])  # 设置帧率用于时间计算
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

            # 如果波形窗口已打开，更新数据
            if self.waveform_window is not None and self.waveform_window.isVisible():
                self.waveform_window.update_data()
                self.waveform_window.set_current_frame(0)

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
            # 获取裁剪范围
            clip_start = self.timeline.clip_start
            clip_end = self.timeline.clip_end
            
            print(f"Export clip: start={clip_start}, end={clip_end}")
            print(f"Data fps: {self.data_manager.data.get('fps', 'NOT FOUND')}")
            print(f"Data frames: {len(self.data_manager.data.get('root_pos', []))}")
            
            # 获取裁剪数据
            clip_data = self.data_manager.clip(clip_start, clip_end)
            
            # 验证裁剪数据
            if clip_data is None:
                raise ValueError("Clip data is None")
            
            if 'fps' not in clip_data:
                raise ValueError("Clip data missing 'fps' field")
            
            # 保存裁剪数据
            self.data_manager.save(file_path, clip_data)
            
            # 计算时长
            clip_duration = (clip_end - clip_start) / clip_data['fps']
            self.statusbar.showMessage(
                f"Exported clip: {clip_start}-{clip_end} "
                f"({clip_duration:.2f}s) to {file_path}")
        except Exception as e:
            import traceback
            error_detail = f"Failed to export clip:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_detail)  # 打印到控制台
            QMessageBox.critical(self, "Error", f"Failed to export clip:\n{str(e)}")
    
    def init_viewer(self):
        """初始化MuJoCo viewer"""
        if not GMR_AVAILABLE:
            QMessageBox.warning(self, "Warning", "GMR modules not available. Cannot initialize 3D viewer.")
            return
        
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
        
        # 更新波形窗口的当前帧位置
        if self.waveform_window is not None and self.waveform_window.isVisible():
            self.waveform_window.set_current_frame(frame)
    
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
    
    def open_waveform_window(self):
        """打开波形显示窗口"""
        # 检查波形窗口是否已存在且可见
        if self.waveform_window is not None and self.waveform_window.isVisible():
            # 如果已存在，只是激活它
            self.waveform_window.raise_()
            self.waveform_window.activateWindow()
            return
        
        # 创建新的波形窗口（独立窗口，不设置父对象）
        self.waveform_window = WaveformWindow(None, self.data_manager)
        
        # 如果已经加载了数据，更新可用keys
        if self.data_manager.data is not None:
            self.waveform_window.update_data()
            # 同步当前帧位置
            self.waveform_window.set_current_frame(self.motion_controller.current_frame)
        
        self.waveform_window.show()
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "About GMR Motion Editor",
            "<h2>GMR Motion Editor</h2>"
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
        if self.waveform_window is not None:
            self.waveform_window.close()
        event.accept()
    
    def open_file_at_path(self, file_path: str):
        """在指定路径打开文件（用于命令行参数）"""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Warning", f"File not found: {file_path}")
            return
        
        try:
            self.data_manager.load(file_path)
            self.current_file = file_path
            
            # 更新UI
            meta = self.data_manager.get_metadata()
            self.timeline.set_frame_count(meta['frame_count'])
            self.timeline.set_fps(meta['fps'])  # 设置帧率用于时间计算
            self.motion_controller.set_frame_count(meta['frame_count'])
            self.motion_controller.set_fps(meta['fps'])
            
            # 更新信息标签
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
