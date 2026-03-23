"""
测试处理边缘情况的 GMR 数据（缺少可选字段或字段形状异常）
"""

import sys
import os
import tempfile
import numpy as np

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 直接从模块导入
import importlib.util
spec = importlib.util.spec_from_file_location("gmr_manager", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'gui', 'gmr_manager.py'))
gmr_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gmr_module)
GMRDataManager = gmr_module.GMRDataManager


def test_minimal_data():
    """测试最少数据（只有必需字段）"""
    print("Testing minimal data (no optional fields)...")
    
    test_data = {
        'fps': 30.0,
        'root_pos': np.random.randn(100, 3),
        'root_rot': np.random.randn(100, 4),
        'dof_pos': np.random.randn(100, 29),
    }
    
    manager = GMRDataManager()
    manager.data = test_data
    
    # 测试裁剪
    clip_data = manager.clip(10, 50)
    
    assert len(clip_data['root_pos']) == 40
    assert clip_data['local_body_pos'] is None
    assert clip_data['link_body_list'] is None
    
    # 测试保存
    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
        temp_path = f.name
    
    try:
        manager.save(temp_path, clip_data)
        
        # 验证保存的数据
        import pickle
        with open(temp_path, 'rb') as f:
            saved = pickle.load(f)
        
        assert 'local_body_pos' not in saved
        assert 'link_body_list' not in saved
        
        print("✓ minimal_data PASSED")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_zero_dimensional_array():
    """测试 0 维数组字段"""
    print("Testing zero-dimensional array field...")
    
    test_data = {
        'fps': 30.0,
        'root_pos': np.random.randn(100, 3),
        'root_rot': np.random.randn(100, 4),
        'dof_pos': np.random.randn(100, 29),
        'local_body_pos': np.array(0.0),  # 0维数组
        'link_body_list': None,
    }
    
    manager = GMRDataManager()
    manager.load_from_data(test_data)
    
    # 0维数组应该被处理为 None
    assert manager.data['local_body_pos'] is None
    
    # 测试裁剪
    clip_data = manager.clip(10, 50)
    assert clip_data['local_body_pos'] is None
    
    print("✓ zero_dimensional_array PASSED")


def test_load_with_none_fields():
    """测试加载时包含 None 字段"""
    print("Testing load with None fields...")
    
    test_data = {
        'fps': 60.0,
        'root_pos': np.random.randn(200, 3),
        'root_rot': np.random.randn(200, 4),
        'dof_pos': np.random.randn(200, 29),
        'local_body_pos': None,
        'link_body_list': None,
    }
    
    manager = GMRDataManager()
    manager.load_from_data(test_data)
    
    assert manager.data['local_body_pos'] is None
    assert manager.data['link_body_list'] is None
    
    # 测试完整流程
    clip_data = manager.clip(50, 100)
    
    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
        temp_path = f.name
    
    try:
        manager.save(temp_path, clip_data)
        
        # 重新加载
        manager2 = GMRDataManager()
        loaded = manager2.load(temp_path)
        
        assert len(loaded['root_pos']) == 50
        assert 'local_body_pos' not in loaded or loaded.get('local_body_pos') is None
        
        print("✓ load_with_none_fields PASSED")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# 给 GMRDataManager 添加辅助方法用于测试
if not hasattr(GMRDataManager, 'load_from_data'):
    def load_from_data(self, data):
        """直接从字典加载数据（用于测试）"""
        import pickle
        import tempfile
        
        # 保存到临时文件再加载
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            pickle.dump(data, f)
            temp_path = f.name
        
        try:
            return self.load(temp_path)
        finally:
            os.unlink(temp_path)
    
    GMRDataManager.load_from_data = load_from_data


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Edge Cases")
    print("=" * 60)
    
    try:
        test_minimal_data()
        test_zero_dimensional_array()
        test_load_with_none_fields()
        
        print("=" * 60)
        print("All tests PASSED! ✓")
        print("=" * 60)
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
