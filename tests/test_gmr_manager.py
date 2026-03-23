"""
测试GMRDataManager
"""

import numpy as np
import pickle
import tempfile
import os
import sys

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 直接从模块导入，避免__init__中的其他导入
import importlib.util
spec = importlib.util.spec_from_file_location("gmr_manager", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'gui', 'gmr_manager.py'))
gmr_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gmr_module)
GMRDataManager = gmr_module.GMRDataManager


def test_load_valid_file():
    """Test loading a valid GMR file"""
    print("Testing load_valid_file...")
    
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
        
        assert result['fps'] == 30, f"Expected fps=30, got {result['fps']}"
        assert result['root_pos'].shape == (100, 3), f"Wrong shape: {result['root_pos'].shape}"
        assert len(result['frames']) == 100, f"Wrong frame count: {len(result['frames'])}"
        print("✓ load_valid_file PASSED")
    finally:
        os.unlink(temp_path)


def test_clip_data():
    """Test clipping motion data"""
    print("Testing clip_data...")
    
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
    
    assert clipped['root_pos'].shape == (40, 3), f"Wrong clipped shape: {clipped['root_pos'].shape}"
    assert len(clipped['frames']) == 40, f"Wrong clipped frame count: {len(clipped['frames'])}"
    print("✓ clip_data PASSED")


def test_clip_invalid_range():
    """Test clipping with invalid range"""
    print("Testing clip_invalid_range...")
    
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
    assert len(clipped['frames']) == 40, f"Wrong frame count: {len(clipped['frames'])}"
    print("✓ clip_invalid_range PASSED")


def test_get_metadata():
    """Test getting metadata"""
    print("Testing get_metadata...")
    
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
    assert meta['fps'] == 60, f"Wrong fps: {meta['fps']}"
    assert meta['frame_count'] == 120, f"Wrong frame count: {meta['frame_count']}"
    assert meta['dof_count'] == 15, f"Wrong dof count: {meta['dof_count']}"
    assert meta['duration'] == 2.0, f"Wrong duration: {meta['duration']}"
    print("✓ get_metadata PASSED")


def test_save_and_reload():
    """Test saving and reloading data"""
    print("Testing save_and_reload...")
    
    # Create and load test data
    test_data = {
        'fps': 30,
        'root_pos': np.random.randn(50, 3),
        'root_rot': np.random.randn(50, 4),
        'dof_pos': np.random.randn(50, 20),
        'local_body_pos': np.random.randn(50, 24, 3),
        'link_body_list': ['link1', 'link2', 'link3']
    }
    
    manager = GMRDataManager()
    manager.data = test_data
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
        temp_path = f.name
    
    try:
        manager.save(temp_path)
        
        # Reload with new manager
        manager2 = GMRDataManager()
        result = manager2.load(temp_path)
        
        assert result['fps'] == 30
        assert np.array_equal(result['root_pos'], test_data['root_pos'])
        print("✓ save_and_reload PASSED")
    finally:
        os.unlink(temp_path)


if __name__ == '__main__':
    print("=" * 50)
    print("Running GMRDataManager Tests")
    print("=" * 50)
    
    try:
        test_load_valid_file()
        test_clip_data()
        test_clip_invalid_range()
        test_get_metadata()
        test_save_and_reload()
        
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
