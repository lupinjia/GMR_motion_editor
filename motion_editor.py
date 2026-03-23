#!/usr/bin/env python3
"""
GMR Motion Editor - 启动脚本

用法:
    python motion_editor.py [可选的.pkl文件路径]
    
示例:
    python motion_editor.py
    python motion_editor.py /path/to/motion_data.pkl
"""

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from gui import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("GMR Motion Editor")
    app.setApplicationVersion("1.0")
    
    window = MainWindow()
    window.show()
    
    # 如果提供了文件路径，自动打开
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            # 延迟加载，确保窗口已显示
            QTimer.singleShot(100, lambda: window.open_file_at_path(file_path))
        else:
            print(f"Warning: File not found: {file_path}")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
