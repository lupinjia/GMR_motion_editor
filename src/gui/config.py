"""
配置文件

用户需要在此手动设置GMR项目的根目录路径
"""

import os

# ============================================================
# 用户配置区域 - 请修改下面的路径
# ============================================================

# GMR项目的根目录路径
# 示例:
#   GMR_ROOT_PATH = "/home/username/GMR"
#   GMR_ROOT_PATH = "C:/Users/username/Documents/GMR"
#   GMR_ROOT_PATH = "/home/lupinjia/GMR"

# 如果需要手动设置，请修改下面这一行
# GMR_ROOT_PATH = "/path/to/your/GMR"

# 自动检测：获取motion_editor的父目录作为GMR根目录
# 当前文件路径: motion_editor/src/gui/config.py
# 向上四级: gui/ -> src/ -> motion_editor/ -> GMR根目录
_current_file = os.path.abspath(__file__)
_auto_detected_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_current_file))))

# 验证自动检测的路径是否有效（是否包含general_motion_retargeting目录）
if os.path.exists(os.path.join(_auto_detected_path, "general_motion_retargeting", "__init__.py")):
    GMR_ROOT_PATH = _auto_detected_path
else:
    GMR_ROOT_PATH = "/home/lupinjia/GMR"

# ============================================================
# 以下代码自动处理路径配置，无需修改
# ============================================================

def setup_gmr_path():
    """
    设置GMR项目路径到sys.path
    返回是否设置成功
    """
    import sys
    
    if not GMR_ROOT_PATH:
        return False, "GMR_ROOT_PATH not configured"
    
    if not os.path.exists(GMR_ROOT_PATH):
        return False, f"GMR path does not exist: {GMR_ROOT_PATH}"
    
    # 检查关键文件是否存在
    gmr_init = os.path.join(GMR_ROOT_PATH, "general_motion_retargeting", "__init__.py")
    if not os.path.exists(gmr_init):
        return False, f"Invalid GMR path: {gmr_init} not found"
    
    # 添加到Python路径
    if GMR_ROOT_PATH not in sys.path:
        sys.path.insert(0, GMR_ROOT_PATH)
    
    return True, "Success"


def get_gmr_root():
    """获取GMR根目录路径"""
    return GMR_ROOT_PATH


def validate_gmr_path():
    """
    验证GMR路径是否有效
    返回 (is_valid, message)
    """
    if not GMR_ROOT_PATH:
        return False, "GMR_ROOT_PATH is empty. Please edit motion_editor/src/gui/config.py and set your GMR path."
    
    if not os.path.exists(GMR_ROOT_PATH):
        return False, f"Path does not exist: {GMR_ROOT_PATH}"
    
    # 检查关键目录
    required_dirs = [
        "general_motion_retargeting",
        "assets",
    ]
    
    for dir_name in required_dirs:
        dir_path = os.path.join(GMR_ROOT_PATH, dir_name)
        if not os.path.exists(dir_path):
            return False, f"Missing required directory: {dir_name}"
    
    return True, "Valid GMR installation"
