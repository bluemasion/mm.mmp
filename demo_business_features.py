#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示业务数据管理功能
测试字段映射、文件存储和数据迁移功能
"""

import os
import sys
sys.path.append('.')

from app.business_data_manager import BusinessDataManager
import pandas as pd
import json
import uuid
from datetime import datetime

def demo_business_data_features():
    """演示业务数据管理功能"""
    
    print("=" * 80)
    print("  MMP业务数据管理功能演示")
    print("=" * 80)
    
    # 初始化业务数据管理器
    project_root = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_root, 'business_data.db')
    
    business_manager = BusinessDataManager(db_path)
    print(f"✅ 业务数据管理器初始化完成: {db_path}")
    
    # === 1. 字段映射演示 ===
    print("\n" + "="*60)
    print("1. 字段映射功能演示")
    print("="*60)
    
    # 获取现有字段映射
    mappings = business_manager.get_field_mappings('standard_medical_mapping')
    print(f"📋 当前字段映射数量: {len(mappings)}")
    
    print("🔄 字段映射列表:")
    for mapping in mappings:
        print(f"  {mapping['source_field']:12} -> {mapping['target_field']:12} ({mapping['field_type']})")
    
    # 获取映射字典
    mapping_dict = business_manager.get_field_mapping_dict('standard_medical_mapping')
    print(f"\n🗂️  映射字典: {mapping_dict}")
    
    # === 2. 模拟文件上传和存储 ===
    print("\n" + "="*60)
    print("2. 文件数据存储演示")
    print("="*60)
    
    # 创建模拟数据
    sample_data = {
        '资产代码': ['A001', 'A002', 'A003', 'A004', 'A005'],
        '资产名称': ['医用口罩', '一次性手套', '体温计', '血压计', '听诊器'],
        '规格型号': ['N95型', '乳胶L码', '电子式', '臂式', '双头式'],
        '品牌': ['3M', '安思尔', '欧姆龙', '鱼跃', '利得曼'],
        '医保码': ['YB001', 'YB002', 'YB003', 'YB004', 'YB005'],
        '生产厂家名称': ['3M公司', '安思尔公司', '欧姆龙公司', '鱼跃科技', '利得曼公司']
    }
    
    df = pd.DataFrame(sample_data)
    print("📄 模拟上传数据:")
    print(df.to_string(index=False))
    
    # 应用字段映射
    mapped_df = df.copy()
    if mapping_dict:
        rename_dict = {}
        for col in mapped_df.columns:
            if col in mapping_dict:
                rename_dict[col] = mapping_dict[col]
        
        if rename_dict:
            mapped_df = mapped_df.rename(columns=rename_dict)
            print(f"\n🔄 应用字段映射: {rename_dict}")
            
    print("\n📋 映射后数据:")
    print(mapped_df.to_string(index=False))
    
    # 存储到数据库
    file_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    success = business_manager.store_uploaded_file(
        file_id=file_id,
        original_filename='demo_data.xlsx',
        stored_filename=f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_demo_data.xlsx',
        file_size=1024,
        file_type='xlsx',
        session_id=session_id,
        df=mapped_df
    )
    
    if success:
        print(f"\n✅ 文件数据存储成功: file_id = {file_id}")
        
        # 获取文件信息
        file_info = business_manager.get_uploaded_file_info(file_id)
        print(f"📊 文件信息: {file_info['row_count']} 行, {file_info['column_count']} 列")
        
        # 获取文件数据
        file_data = business_manager.get_file_data(file_id, limit=3)
        print(f"📖 前3行数据预览:")
        for i, row in enumerate(file_data):
            row_without_index = {k: v for k, v in row.items() if k != '_row_index'}
            print(f"  行{i+1}: {row_without_index}")
    else:
        print("❌ 文件数据存储失败")
    
    # === 3. 处理结果存储演示 ===
    print("\n" + "="*60)
    print("3. 处理结果存储演示")
    print("="*60)
    
    # 模拟分类处理结果
    for i, (_, row) in enumerate(mapped_df.iterrows()):
        input_data = row.to_dict()
        result_data = {
            'classification': '医疗器械',
            'category': f'CAT{str(i+1).zfill(3)}',
            'confidence': 0.85 + i * 0.02,
            'matched_rules': ['规格匹配', '品牌匹配']
        }
        
        result_id = business_manager.store_processing_result(
            session_id=session_id,
            file_id=file_id,
            result_type='classification',
            row_index=i,
            input_data=input_data,
            result_data=result_data,
            confidence=result_data['confidence'],
            processing_time=0.15 + i * 0.02
        )
        
    print(f"✅ 存储了 {len(mapped_df)} 个分类结果")
    
    # 获取处理结果
    results = business_manager.get_processing_results(session_id, 'classification')
    print(f"📊 获取处理结果: {len(results)} 条")
    
    if results:
        print("🎯 处理结果示例:")
        for result in results[:2]:
            print(f"  行{result['row_index']}: {result['result_data']['classification']} -> {result['result_data']['category']} (置信度: {result['confidence']})")
    
    # === 4. 系统配置演示 ===
    print("\n" + "="*60)
    print("4. 系统配置管理演示")
    print("="*60)
    
    # 设置一些测试配置
    test_configs = [
        ('demo_threshold', 0.75, 'number', '演示阈值配置'),
        ('demo_enabled', True, 'boolean', '演示开关配置'),
        ('demo_settings', {'max_items': 100, 'timeout': 30}, 'json', '演示JSON配置')
    ]
    
    for key, value, config_type, desc in test_configs:
        business_manager.set_config(key, value, config_type, desc)
        retrieved_value = business_manager.get_config(key)
        print(f"⚙️  {key}: {value} -> {retrieved_value} ({config_type})")
    
    # === 5. 统计信息演示 ===
    print("\n" + "="*60)
    print("5. 系统统计信息")
    print("="*60)
    
    stats = business_manager.get_statistics()
    print("📈 系统统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # === 6. 字段映射解决方案演示 ===
    print("\n" + "="*80)
    print("🎯 字段映射问题解决方案演示")
    print("="*80)
    
    print("❌ 原始问题:")
    print("   - 配置文件定义: '医保代码'")
    print("   - 实际上传文件: '医保码'")
    print("   - 导致字段不匹配错误")
    
    print("\n✅ 解决方案:")
    print("   - 数据库存储字段映射规则")
    print("   - 自动将 '医保码' 映射为 '医保代码'")
    print("   - 支持多种映射配置方案")
    print("   - 可动态添加新的字段映射")
    
    print("\n🔄 映射转换示例:")
    original_fields = ['资产代码', '资产名称', '规格型号', '品牌', '医保码', '生产厂家名称']
    mapped_fields = [mapping_dict.get(field, field) for field in original_fields]
    
    for orig, mapped in zip(original_fields, mapped_fields):
        if orig != mapped:
            print(f"   {orig} -> {mapped}")
        else:
            print(f"   {orig} (无需映射)")
    
    print("\n" + "="*80)
    print("✅ 业务数据管理功能演示完成!")
    print("="*80)
    
    return {
        'file_id': file_id,
        'session_id': session_id,
        'mappings_count': len(mappings),
        'results_count': len(results),
        'statistics': stats
    }

if __name__ == "__main__":
    try:
        demo_results = demo_business_data_features()
        print(f"\n📋 演示结果汇总:")
        print(f"  - 文件ID: {demo_results['file_id']}")
        print(f"  - 会话ID: {demo_results['session_id']}")
        print(f"  - 字段映射: {demo_results['mappings_count']} 个")
        print(f"  - 处理结果: {demo_results['results_count']} 条")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()