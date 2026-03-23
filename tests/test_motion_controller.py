"""
测试MotionController
"""

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication

# 直接从模块导入，避免__init__中的其他导入
import importlib.util
spec = importlib.util.spec_from_file_location("motion_controller", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'gui', 'motion_controller.py'))
mc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc_module)
MotionController = mc_module.MotionController


def test_initial_state():
    """Test initial controller state"""
    print("Testing initial_state...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    controller = MotionController()
    
    assert controller.is_playing is False
    assert controller.current_frame == 0
    assert controller.playback_speed == 1.0
    assert controller.loop is True
    
    print("✓ initial_state PASSED")


def test_set_frame_count():
    """Test setting total frames"""
    print("Testing set_frame_count...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    controller = MotionController()
    controller.set_frame_count(100)
    
    assert controller.total_frames == 100
    assert controller.clip_end == 100
    
    print("✓ set_frame_count PASSED")


def test_set_clip_range():
    """Test setting clip range"""
    print("Testing set_clip_range...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    controller = MotionController()
    controller.set_frame_count(100)
    controller.set_clip_range(10, 50)
    
    assert controller.clip_start == 10
    assert controller.clip_end == 50
    
    print("✓ set_clip_range PASSED")


def test_play_pause():
    """Test play/pause functionality"""
    print("Testing play_pause...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    controller = MotionController()
    
    # 初始为暂停
    assert controller.is_playing is False
    
    # 开始播放
    controller.play()
    assert controller.is_playing is True
    
    # 暂停
    controller.pause()
    assert controller.is_playing is False
    
    # 切换
    controller.toggle_playback()
    assert controller.is_playing is True
    controller.toggle_playback()
    assert controller.is_playing is False
    
    print("✓ play_pause PASSED")


def test_next_frame():
    """Test advancing to next frame"""
    print("Testing next_frame...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    controller = MotionController()
    controller.set_frame_count(100)
    controller.set_clip_range(0, 100)
    
    controller.next_frame()
    assert controller.current_frame == 1
    
    print("✓ next_frame PASSED")


def test_prev_frame():
    """Test going to previous frame"""
    print("Testing prev_frame...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    controller = MotionController()
    controller.set_frame_count(100)
    controller.current_frame = 10
    
    controller.prev_frame()
    assert controller.current_frame == 9
    
    print("✓ prev_frame PASSED")


def test_go_to_start():
    """Test go to start of clip"""
    print("Testing go_to_start...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    controller = MotionController()
    controller.set_frame_count(100)
    controller.set_clip_range(20, 80)
    controller.current_frame = 50
    
    controller.go_to_start()
    assert controller.current_frame == 20
    
    print("✓ go_to_start PASSED")


def test_go_to_end():
    """Test go to end of clip"""
    print("Testing go_to_end...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    controller = MotionController()
    controller.set_frame_count(100)
    controller.set_clip_range(20, 80)
    controller.current_frame = 50
    
    controller.go_to_end()
    # End frame is exclusive, so we should be at clip_end - 1
    assert controller.current_frame == 79
    
    print("✓ go_to_end PASSED")


def test_set_playback_speed():
    """Test setting playback speed"""
    print("Testing set_playback_speed...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    controller = MotionController()
    
    controller.set_playback_speed(2.0)
    assert controller.playback_speed == 2.0
    
    controller.set_playback_speed(0.5)
    assert controller.playback_speed == 0.5
    
    # Test limits
    controller.set_playback_speed(5.0)  # Should be clamped to 3.0
    assert controller.playback_speed == 3.0
    
    controller.set_playback_speed(0.05)  # Should be clamped to 0.1
    assert controller.playback_speed == 0.1
    
    print("✓ set_playback_speed PASSED")


def test_set_loop():
    """Test setting loop mode"""
    print("Testing set_loop...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    controller = MotionController()
    
    assert controller.loop is True
    
    controller.set_loop(False)
    assert controller.loop is False
    
    controller.set_loop(True)
    assert controller.loop is True
    
    print("✓ set_loop PASSED")


if __name__ == '__main__':
    print("=" * 50)
    print("Running MotionController Tests")
    print("=" * 50)
    
    try:
        test_initial_state()
        test_set_frame_count()
        test_set_clip_range()
        test_play_pause()
        test_next_frame()
        test_prev_frame()
        test_go_to_start()
        test_go_to_end()
        test_set_playback_speed()
        test_set_loop()
        
        print("=" * 50)
        print("All tests PASSED! ✓")
        print("=" * 50)
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
