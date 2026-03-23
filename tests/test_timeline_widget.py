"""
测试TimelineWidget
"""

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# 直接从模块导入，避免__init__中的其他导入
import importlib.util
spec = importlib.util.spec_from_file_location("timeline_widget", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'gui', 'timeline_widget.py'))
timeline_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timeline_module)
TimelineWidget = timeline_module.TimelineWidget


def test_initial_state():
    """Test initial widget state"""
    print("Testing initial_state...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    widget = TimelineWidget()
    
    assert widget.total_frames == 100, f"Expected 100, got {widget.total_frames}"
    assert widget.current_frame == 0, f"Expected 0, got {widget.current_frame}"
    assert widget.clip_start == 0, f"Expected 0, got {widget.clip_start}"
    assert widget.clip_end == 100, f"Expected 100, got {widget.clip_end}"
    
    print("✓ initial_state PASSED")


def test_set_frame_count():
    """Test setting total frame count"""
    print("Testing set_frame_count...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    widget = TimelineWidget()
    widget.set_frame_count(200)
    
    assert widget.total_frames == 200, f"Expected 200, got {widget.total_frames}"
    assert widget.clip_end == 200, f"Expected 200, got {widget.clip_end}"
    
    print("✓ set_frame_count PASSED")


def test_set_current_frame():
    """Test setting current frame"""
    print("Testing set_current_frame...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    widget = TimelineWidget()
    widget.set_frame_count(100)
    widget.set_current_frame(50)
    
    assert widget.current_frame == 50, f"Expected 50, got {widget.current_frame}"
    
    print("✓ set_current_frame PASSED")


def test_set_clip_range():
    """Test setting clip range"""
    print("Testing set_clip_range...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    widget = TimelineWidget()
    widget.set_frame_count(100)
    widget.set_clip_range(20, 80)
    
    assert widget.clip_start == 20, f"Expected 20, got {widget.clip_start}"
    assert widget.clip_end == 80, f"Expected 80, got {widget.clip_end}"
    
    print("✓ set_clip_range PASSED")


if __name__ == '__main__':
    print("=" * 50)
    print("Running TimelineWidget Tests")
    print("=" * 50)
    
    try:
        test_initial_state()
        test_set_frame_count()
        test_set_current_frame()
        test_set_clip_range()
        
        print("=" * 50)
        print("All tests PASSED! ✓")
        print("=" * 50)
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
