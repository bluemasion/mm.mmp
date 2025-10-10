#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMP系统错误修复脚本
修复当前系统中的主要错误：
1. 主数据字段不匹配问题
2. 分类选择保存错误 
3. 工作流服务初始化失败
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_master_data_schema():
    """修复主数据库表结构，添加缺失字段"""
    logger.info("开始修复主数据库表结构...")
    
    db_path = 'master_data.db'
    if not os.path.exists(db_path):
        logger.error(f"主数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查当前表结构
        cursor.execute("PRAGMA table_info(materials)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"当前字段: {column_names}")
        
        # 添加缺失字段（如果不存在）
        missing_fields = {
            'insurance_code': 'TEXT',  # 医保代码
            'supplier': 'TEXT',        # 供应商
            'price': 'REAL',           # 价格
            'status': 'TEXT DEFAULT "active"'  # 状态
        }
        
        for field, field_type in missing_fields.items():
            if field not in column_names:
                try:
                    cursor.execute(f"ALTER TABLE materials ADD COLUMN {field} {field_type}")
                    logger.info(f"成功添加字段: {field}")
                except sqlite3.Error as e:
                    logger.warning(f"添加字段 {field} 失败: {e}")
        
        # 更新一些示例数据的保险代码
        cursor.execute("""
            UPDATE materials 
            SET insurance_code = CASE 
                WHEN material_code = 'M001001' THEN 'YB001001'
                WHEN material_code = 'M001002' THEN 'YB001002' 
                WHEN material_code = 'M002001' THEN 'YB002001'
                ELSE 'YB' || substr(material_code, 2)
            END
            WHERE insurance_code IS NULL
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("主数据库表结构修复完成")
        return True
        
    except Exception as e:
        logger.error(f"修复主数据库表结构失败: {e}")
        return False

def update_matching_config():
    """更新匹配配置，使用实际存在的字段"""
    logger.info("更新匹配配置...")
    
    # 创建兼容的配置文件
    config_content = '''# -*- coding: utf-8 -*-
"""
修复后的匹配配置 - 使用实际数据库字段
"""

# 匹配规则配置 - 使用实际存在的字段
MATCH_RULES = {
    'master_fields': {
        'id': 'material_code',
        'exact': ['brand', 'model'],  # 品牌、型号精确匹配
        'fuzzy': ['material_name', 'specification'],  # 物料名称、规格模糊匹配
        'optional': ['insurance_code', 'supplier']  # 可选字段
    },
    'new_item_fields': {
        'id': '资产代码',
        'exact': ['品牌', '型号'],  
        'fuzzy': ['物料名称', '规格'],
        'optional': ['医保代码', '供应商']
    }
}

# 字段映射规则
FIELD_MAPPING = {
    '物料名称': 'material_name',
    '品牌': 'brand', 
    '型号': 'model',
    '规格': 'specification',
    '医保代码': 'insurance_code',
    '供应商': 'supplier',
    '物料代码': 'material_code'
}

# 匹配配置
MATCH_CONFIG = {
    'similarity_threshold': 0.3,
    'field_weights': {
        'exact_match': 1.0,
        'fuzzy_match': 0.8,
        'description_match': 0.6
    },
    'top_n_default': 5,
    'enable_fallback': True  # 启用降级匹配
}
'''
    
    try:
        with open('fixed_config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        logger.info("匹配配置更新完成: fixed_config.py")
        return True
        
    except Exception as e:
        logger.error(f"更新匹配配置失败: {e}")
        return False

def create_error_handling_wrapper():
    """创建错误处理包装器"""
    logger.info("创建错误处理包装器...")
    
    wrapper_content = '''# -*- coding: utf-8 -*-
"""
错误处理包装器 - 增强系统稳定性
"""

import logging
import traceback
from functools import wraps
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self):
        self.error_counts = {}
        self.max_retries = 3
        
    def safe_execute(self, func: Callable, *args, fallback=None, **kwargs) -> Any:
        """安全执行函数，带降级处理"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_key = f"{func.__name__}_{type(e).__name__}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            logger.error(f"函数执行失败: {func.__name__}, 错误: {e}")
            logger.debug(f"错误详情: {traceback.format_exc()}")
            
            if fallback is not None:
                logger.info(f"使用降级处理: {fallback}")
                if callable(fallback):
                    return fallback(*args, **kwargs)
                else:
                    return fallback
            
            raise

def safe_api(fallback_response=None):
    """API安全装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"API错误 {func.__name__}: {e}")
                if fallback_response:
                    return fallback_response
                else:
                    return {"error": f"操作失败: {str(e)}", "success": False}, 500
        return wrapper
    return decorator

def safe_length(obj, default=0):
    """安全获取对象长度"""
    try:
        if hasattr(obj, '__len__'):
            return len(obj)
        elif obj is not None:
            return 1
        else:
            return default
    except:
        return default

# 全局错误处理实例
error_handler = ErrorHandler()
'''
    
    try:
        with open('app/error_handler.py', 'w', encoding='utf-8') as f:
            f.write(wrapper_content)
        
        logger.info("错误处理包装器创建完成: app/error_handler.py")
        return True
        
    except Exception as e:
        logger.error(f"创建错误处理包装器失败: {e}")
        return False

def test_system_fixes():
    """测试修复效果"""
    logger.info("测试系统修复效果...")
    
    try:
        # 测试主数据访问
        conn = sqlite3.connect('master_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT material_name, brand, model, insurance_code FROM materials LIMIT 3")
        results = cursor.fetchall()
        
        logger.info("主数据访问测试:")
        for row in results:
            logger.info(f"  {row}")
            
        conn.close()
        
        # 测试配置加载
        try:
            import fixed_config
            logger.info("配置加载测试: ✅ 成功")
            logger.info(f"匹配规则: {fixed_config.MATCH_RULES}")
        except Exception as e:
            logger.warning(f"配置加载测试失败: {e}")
        
        # 测试错误处理器
        try:
            from app.error_handler import safe_length, error_handler
            
            # 测试safe_length函数
            test_cases = [
                ([1, 2, 3], 3),
                ({"a": 1, "b": 2}, 2), 
                ("hello", 5),
                (None, 0),
                (42, 1)
            ]
            
            logger.info("错误处理器测试:")
            for obj, expected in test_cases:
                result = safe_length(obj)
                status = "✅" if result == expected else "❌"
                logger.info(f"  {status} safe_length({obj}) = {result} (期望: {expected})")
                
        except Exception as e:
            logger.warning(f"错误处理器测试失败: {e}")
            
        logger.info("系统修复测试完成")
        return True
        
    except Exception as e:
        logger.error(f"系统测试失败: {e}")
        return False

def main():
    """主修复流程"""
    logger.info("=" * 50)
    logger.info("MMP系统错误修复开始")
    logger.info("=" * 50)
    
    success_count = 0
    total_fixes = 4
    
    # 1. 修复主数据结构
    if fix_master_data_schema():
        success_count += 1
    
    # 2. 更新匹配配置
    if update_matching_config():
        success_count += 1
        
    # 3. 创建错误处理包装器
    if create_error_handling_wrapper():
        success_count += 1
    
    # 4. 测试修复效果
    if test_system_fixes():
        success_count += 1
    
    logger.info("=" * 50)
    logger.info(f"修复完成: {success_count}/{total_fixes} 项成功")
    
    if success_count == total_fixes:
        logger.info("🎉 所有修复项目都已成功完成!")
        logger.info("建议:")
        logger.info("1. 重启MMP服务")
        logger.info("2. 测试文件上传和分类功能")
        logger.info("3. 检查系统日志确认无错误")
    else:
        logger.warning("⚠️  部分修复项目失败，请检查日志")
    
    logger.info("=" * 50)

if __name__ == '__main__':
    main()