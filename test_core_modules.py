#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强功能核心模块
"""

import sys
import os
import json

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_unified_classifier():
    """测试统一分类器"""
    try:
        print("🔍 测试统一分类器模块...")
        from app.unified_classifier import UnifiedMaterialClassifier, ClassificationRequest
        
        # 创建分类器实例
        classifier = UnifiedMaterialClassifier()
        print("✅ 统一分类器创建成功")
        
        # 测试分类功能
        test_material = {
            'name': '304不锈钢疏水器',
            'specification': 'DN25',
            'unit': '个'
        }
        
        request = ClassificationRequest(
            material_name=test_material['name'],
            specification=test_material.get('specification', ''),
            unit=test_material.get('unit', ''),
            manufacturer=''
        )
        
        result = classifier.classify(request)
        print(f"📊 分类结果: {result.category} (置信度: {result.confidence:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ 统一分类器测试失败: {e}")
        return False

def test_deduplication_engine():
    """测试去重引擎"""
    try:
        print("\n🔍 测试去重引擎模块...")
        from app.material_deduplication_engine import MaterialDeduplicationEngine
        
        # 创建去重引擎
        engine = MaterialDeduplicationEngine()
        print("✅ 去重引擎创建成功")
        
        # 测试去重分析
        test_materials = [
            {'name': '304不锈钢疏水器', 'spec': 'DN25', 'unit': '个'},
            {'name': '不锈钢疏水阀', 'spec': 'DN25', 'unit': '个'},
        ]
        
        result = engine.analyze_duplicates(test_materials)
        print(f"📊 去重分析完成，发现 {len(result.duplicate_groups)} 个潜在重复组")
        
        return True
        
    except Exception as e:
        print(f"❌ 去重引擎测试失败: {e}")
        return False

def test_quality_assessment():
    """测试质量评估"""
    try:
        print("\n🔍 测试质量评估模块...")
        from app.base_quality_assessment import BaseQualityAssessment, MaterialInfo
        
        # 创建质量评估系统
        assessor = BaseQualityAssessment()
        print("✅ 质量评估系统创建成功")
        
        # 测试质量评估
        test_material = MaterialInfo(
            name='304不锈钢疏水器',
            specification='DN25',
            unit='个',
            manufacturer='某钢铁公司',
            description='高品质疏水器，适用于蒸汽系统'
        )
        
        result = assessor.assess_material_quality(test_material)
        print(f"📊 质量评估完成，总分: {result.overall_score:.1f}/100，等级: {result.quality_grade}")
        
        return True
        
    except Exception as e:
        print(f"❌ 质量评估测试失败: {e}")
        return False

def test_incremental_sync():
    """测试增量同步"""
    try:
        print("\n🔍 测试增量同步模块...")
        from app.simplified_incremental_sync import SimplifiedIncrementalSync, SyncConfig
        
        # 创建同步系统
        sync_system = SimplifiedIncrementalSync()
        print("✅ 增量同步系统创建成功")
        
        # 测试同步配置
        config = SyncConfig(
            source_name='TEST_ERP',
            sync_strategy='hybrid',
            conflict_resolution='source_priority',
            batch_size=100
        )
        
        # 模拟数据同步
        test_records = [
            {'id': 'M001', 'name': '测试物料', 'last_modified': '2025-10-08'}
        ]
        
        result = sync_system.sync_data(config, test_records)
        print(f"📊 同步完成，处理记录: {result.total_records}，新记录: {result.new_records}")
        
        return True
        
    except Exception as e:
        print(f"❌ 增量同步测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("  MMP增强功能核心模块测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试各个核心模块
    test_results.append(("统一分类器", test_unified_classifier()))
    test_results.append(("去重引擎", test_deduplication_engine()))
    test_results.append(("质量评估", test_quality_assessment()))
    test_results.append(("增量同步", test_incremental_sync()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("  核心功能测试结果")
    print("=" * 60)
    
    success_count = 0
    for module_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{module_name:15}: {status}")
        if success:
            success_count += 1
    
    total_tests = len(test_results)
    success_rate = (success_count / total_tests) * 100
    
    print(f"\n📊 测试统计:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功数量: {success_count}")
    print(f"   成功率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 所有核心模块测试通过！")
        print("💡 建议: 可以继续进行API集成测试")
    elif success_rate >= 75:
        print("\n✨ 大部分核心模块可用，系统功能基本正常")
        print("💡 建议: 修复失败的模块后进行完整测试")
    else:
        print("\n⚠️  多个核心模块存在问题，需要检查代码")
        print("💡 建议: 优先修复基础功能模块")
    
    return success_rate

if __name__ == '__main__':
    main()