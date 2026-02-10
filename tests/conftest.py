"""
pytest 配置和通用 fixtures
"""
import pytest
import os
import sys
import shutil

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

# 需要保护的配置文件列表（data/ 下的重要文件）
CONFIG_FILES = [
    'data/rules.json',
    'data/categories.json',
    'data/DB.xlsx',  # 账单数据库
]

# 测试生成的临时文件（测试后自动清理）
TEMP_FILES = [
    'bills.process',
]


@pytest.fixture(autouse=True)
def protect_config_files():
    """
    自动保护配置文件
    
    在每个测试前备份配置文件，测试后恢复，防止测试覆盖用户数据
    """
    backup_files = {}
    
    # 备份配置文件
    for config_path in CONFIG_FILES:
        if os.path.exists(config_path):
            backup_path = config_path + '.test_backup'
            shutil.copy2(config_path, backup_path)
            backup_files[config_path] = backup_path
    
    yield  # 运行测试
    
    # 恢复配置文件
    for config_path, backup_path in backup_files.items():
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, config_path)
            os.remove(backup_path)


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """
    自动清理测试生成的临时文件
    
    在测试完成后删除 bills.process 等临时文件
    """
    yield  # 运行测试
    
    # 清理临时文件
    for temp_file in TEMP_FILES:
        if os.path.exists(temp_file):
            os.remove(temp_file)
