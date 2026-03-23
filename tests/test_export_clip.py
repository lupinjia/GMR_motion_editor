"""
测试导出功能
"""

import sys
import os
import tempfile

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 直接从模块导入，避免__init__中的其他导入
import importlib.util
spec = importlib.util.spec_from_file_location("gmr_manager", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'gui', 'gmr_manager.py'))
gmr_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gmr_module)
GMRDataManager = gmr_module.GMRDataManager

import numpy as np


def test_export_clip():
    """测试导出裁剪功能"""
    print("Testing export clip functionality...")
    
    # 创建测试数据
    test_data = {
        'fps': 30,
        'root_pos': np.random.randn(100, 3),
        'root_rot': np.random.randn(100, 4),
        'dof_pos': np.random.randn(100, 29),
        'local_body_pos': np.random.randn(100, 24, 3),
        'link_body_list': ['link1', 'link2']
    }
    
    # 创建数据管理器并加载数据
    manager = GMRDataManager()
    manager.data = test_data
    
    print(f"Loaded data: {len(test_data['root_pos'])} frames at {test_data['fps']} fps")
    
    # 裁剪数据
    clip_start = 10
    clip_end = 50
    print(f"Clipping from frame {clip_start} to {clip_end}...")
    
    clip_data = manager.clip(clip_start, clip_end)
    
    print(f"Clip data keys: {list(clip_data.keys())}")
    print(f"Clip data fps: {clip_data.get('fps', 'NOT FOUND')}")
    print(f"Clip data frames: {len(clip_data.get('root_pos', []))}")
    
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
        temp_path = f.name
    
    try:
        print(f"Saving to {temp_path}...")
        manager.save(temp_path, clip_data)
        print("Save successful!")
        
        # 重新加载验证
        manager2 = GMRDataManager()
        loaded_data = manager2.load(temp_path)
        
        print(f"Reloaded data: {len(loaded_data['root_pos'])} frames at {loaded_data['fps']} fps")
        assert len(loaded_data['root_pos']) == 40, f"Expected 40 frames, got {len(loaded_data['root_pos'])}"
        
        print("✓ Export clip test PASSED")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Export Clip")
    print("=" * 60)
    
    try:
        test_export_clip()
        print("=" * 60)
        print("All tests PASSED! ✓")
        print("=" * 60)
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
