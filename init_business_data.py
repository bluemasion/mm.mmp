#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化业务数据库
创建所有业务数据表并填充基础配置数据
"""

import os
import sys
sys.path.append('.')

from app.business_data_manager import BusinessDataManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_business_database():
    """初始化业务数据库"""
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_root, 'business_data.db')
    
    print("=" * 60)
    print("  初始化业务数据库")
    print("=" * 60)
    print(f"数据库路径: {db_path}")
    
    # 创建数据库管理器
    business_manager = BusinessDataManager(db_path)
    
    print("\n✅ 业务数据表创建完成")
    
    # 设置默认字段映射 - 解决"医保代码"等字段不匹配问题
    print("\n📊 设置默认字段映射...")
    
    # 标准医疗器械字段映射
    medical_mappings = [
        # 精确匹配字段
        ('standard_medical_mapping', '医保码', '医保代码', 'exact', 'string', None, '医保编码字段映射'),
        ('standard_medical_mapping', '生产厂家名称', '生产厂家', 'exact', 'string', None, '生产厂家字段映射'),
        ('standard_medical_mapping', '资产代码', '商品操作码', 'id', 'string', None, '主键字段映射'),
        
        # 模糊匹配字段
        ('standard_medical_mapping', '资产名称', '产品名称', 'fuzzy', 'string', None, '产品名称字段映射'),
        ('standard_medical_mapping', '规格型号', '产品规格', 'fuzzy', 'string', None, '规格型号字段映射'),
        ('standard_medical_mapping', '品牌', '品牌名称', 'fuzzy', 'string', None, '品牌字段映射'),
    ]
    
    for mapping in medical_mappings:
        try:
            business_manager.create_field_mapping(*mapping)
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                logger.info(f"字段映射已存在: {mapping[1]} -> {mapping[2]}")
            else:
                logger.error(f"创建字段映射失败: {e}")
    
    # 设置系统配置
    print("\n⚙️  设置系统配置...")
    
    configs = [
        ('default_field_mapping', 'standard_medical_mapping', 'string', '默认字段映射配置'),
        ('max_file_size', '100', 'number', '最大文件大小(MB)'),
        ('supported_file_types', '[".xlsx", ".xls", ".csv"]', 'json', '支持的文件类型'),
        ('default_confidence_threshold', '0.8', 'number', '默认置信度阈值'),
        ('enable_auto_mapping', 'true', 'boolean', '启用自动字段映射'),
        ('data_retention_days', '90', 'number', '数据保留天数'),
        ('batch_size', '1000', 'number', '批处理大小'),
        ('enable_data_validation', 'true', 'boolean', '启用数据验证'),
    ]
    
    for key, value, config_type, description in configs:
        business_manager.set_config(key, value, config_type, description)
    
    # 创建默认匹配规则
    print("\n🎯 设置默认匹配规则...")
    
    # 这里可以添加默认的匹配规则到matching_rules表
    
    # 显示统计信息
    print("\n📈 数据库统计信息:")
    stats = business_manager.get_statistics()
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    # 验证字段映射
    print("\n🔍 验证字段映射...")
    mappings = business_manager.get_field_mappings('standard_medical_mapping')
    print(f"标准医疗器械字段映射数量: {len(mappings)}")
    
    for mapping in mappings:
        print(f"  {mapping['source_field']} -> {mapping['target_field']} ({mapping['field_type']})")
    
    print("\n" + "=" * 60)
    print("✅ 业务数据库初始化完成!")
    print("=" * 60)
    
    return db_path

if __name__ == "__main__":
    try:
        db_path = init_business_database()
        print(f"\n数据库文件: {db_path}")
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)