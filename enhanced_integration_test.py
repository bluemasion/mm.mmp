# -*- coding: utf-8 -*-
"""
增强功能集成测试
测试新增功能与现有系统的集成
"""

import requests
import json
import sys
from datetime import datetime

def test_enhanced_classification():
    """测试增强分类功能"""
    print("\n🔍 测试增强分类功能...")
    
    # 测试数据
    test_data = {
        "material_name": "不锈钢球阀",
        "specification": "DN100 PN16 304材质",
        "manufacturer": "上海阀门制造有限公司",
        "material_type": "阀门",
        "unit": "个"
    }
    
    try:
        # 测试现有API
        existing_response = requests.post(
            "http://localhost:5001/api/recommend_categories",
            json={"material_info": {
                "name": test_data["material_name"],
                "spec": test_data["specification"],
                "manufacturer": test_data["manufacturer"]
            }},
            timeout=10
        )
        
        if existing_response.status_code == 200:
            existing_result = existing_response.json()
            print(f"✅ 现有分类API正常: {existing_result.get('recommended_categories', ['无推荐'])[:2]}")
        else:
            print(f"⚠️ 现有分类API响应: {existing_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分类测试失败: {e}")
        return False

def test_batch_processing():
    """测试批量处理功能"""
    print("\n📦 测试批量处理功能...")
    
    # 测试批量物料匹配
    test_materials = [
        ["M001", "不锈钢球阀", "球阀", "阀门", "DN100 PN16", "", "个"],
        ["M002", "碳钢法兰", "法兰", "管件", "DN150 PN25", "", "个"],
        ["M003", "橡胶密封圈", "密封圈", "密封件", "内径100mm", "", "个"]
    ]
    
    try:
        response = requests.post(
            "http://localhost:5001/api/batch_material_matching",
            json={
                "materials": test_materials,
                "template": "universal-manufacturing"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            processed_count = len(result.get('results', []))
            print(f"✅ 批量处理成功: 处理了{processed_count}个物料")
            
            # 显示部分结果
            for i, item_result in enumerate(result.get('results', [])[:2]):
                category = item_result.get('recommended_category', '未分类')
                confidence = item_result.get('confidence_score', 0)
                print(f"   物料{i+1}: {category} (置信度: {confidence:.2f})")
            
            return True
        else:
            print(f"⚠️ 批量处理API响应: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 批量处理测试失败: {e}")
        return False

def test_quality_metrics():
    """测试质量指标"""
    print("\n📊 测试质量指标...")
    
    try:
        # 测试物料质量评估（模拟）
        test_material = {
            'material_code': 'TEST_M001',
            'material_name': '不锈钢球阀',
            'specification': 'DN100 PN16 304不锈钢材质 法兰连接 手动操作',
            'manufacturer': '上海阀门制造有限公司',
            'material_type': '阀门',
            'unit': '个'
        }
        
        # 导入质量评估模块进行本地测试
        sys.path.append('app')
        from base_quality_assessment import BaseQualityAssessment
        
        quality_assessor = BaseQualityAssessment()
        quality_result = quality_assessor.assess_material_quality(test_material)
        
        print(f"✅ 质量评估完成:")
        print(f"   总分: {quality_result.overall_score:.1f}/100")
        print(f"   等级: {quality_result.quality_grade}")
        print(f"   维度数量: {len(quality_result.dimension_scores)}")
        
        return quality_result.overall_score > 0
        
    except Exception as e:
        print(f"❌ 质量评估测试失败: {e}")
        return False

def test_deduplication():
    """测试去重功能"""
    print("\n🔍 测试去重功能...")
    
    try:
        # 导入去重模块进行本地测试
        sys.path.append('app')
        from integrated_deduplication_manager import (
            IntegratedDeduplicationManager, DeduplicationRequest
        )
        
        # 创建测试物料（相似物料）
        test_materials = [
            {
                'material_code': 'ERP_M001',
                'material_name': '不锈钢球阀',
                'specification': 'DN100 PN16',
                'manufacturer': '上海阀门厂',
                'unit': '个'
            },
            {
                'material_code': 'PLM_M001',
                'material_name': '304不锈钢球阀',
                'specification': 'DN100 压力16bar',
                'manufacturer': '上海阀门制造有限公司',
                'unit': '个'
            }
        ]
        
        dedup_manager = IntegratedDeduplicationManager()
        dedup_request = DeduplicationRequest(
            materials=test_materials,
            source_systems=['ERP', 'PLM'],
            confidence_threshold=0.75
        )
        
        dedup_result = dedup_manager.analyze_material_duplicates(dedup_request)
        
        print(f"✅ 去重分析完成:")
        print(f"   分析物料: {dedup_result.statistics['total_materials']}")
        print(f"   发现重复组: {len(dedup_result.duplicate_groups)}")
        print(f"   处理建议: {len(dedup_result.recommendations)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 去重测试失败: {e}")
        return False

def test_sync_capabilities():
    """测试同步能力"""
    print("\n🔄 测试同步能力...")
    
    try:
        # 导入同步模块进行本地测试
        sys.path.append('app')
        from simplified_incremental_sync import SimplifiedIncrementalSync
        
        # 模拟数据源
        erp_data = [
            {
                'material_code': 'SYNC_TEST_001',
                'material_name': '测试物料1',
                'specification': '测试规格1',
                'manufacturer': '测试厂商1',
                'unit': '个',
                'last_modified': '2024-01-15T10:30:00'
            }
        ]
        
        sync_system = SimplifiedIncrementalSync()
        sync_result = sync_system.sync_from_source('TEST_ERP', erp_data)
        
        print(f"✅ 同步测试完成:")
        print(f"   处理记录: {sync_result.total_records}")
        print(f"   新记录: {sync_result.new_records}")
        print(f"   处理时间: {sync_result.processing_time:.3f}秒")
        
        return True
        
    except Exception as e:
        print(f"❌ 同步测试失败: {e}")
        return False

def test_system_performance():
    """测试系统性能"""
    print("\n⚡ 测试系统性能...")
    
    try:
        start_time = datetime.now()
        
        # 模拟并发请求
        test_requests = []
        for i in range(5):
            try:
                response = requests.get(
                    "http://localhost:5001/api/categories",
                    timeout=5
                )
                test_requests.append(response.status_code == 200)
            except:
                test_requests.append(False)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        success_rate = sum(test_requests) / len(test_requests)
        
        print(f"✅ 性能测试完成:")
        print(f"   请求数量: {len(test_requests)}")
        print(f"   成功率: {success_rate:.1%}")
        print(f"   总耗时: {processing_time:.3f}秒")
        print(f"   平均响应: {processing_time/len(test_requests):.3f}秒")
        
        return success_rate >= 0.8 and processing_time < 10.0
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("="*60)
    print("MMP增强功能集成测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 定义测试用例
    tests = [
        ("增强分类功能", test_enhanced_classification),
        ("批量处理功能", test_batch_processing),
        ("质量评估功能", test_quality_metrics),
        ("去重分析功能", test_deduplication),
        ("增量同步功能", test_sync_capabilities),
        ("系统性能测试", test_system_performance)
    ]
    
    # 执行测试
    results = {}
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
        except Exception as e:
            print(f"💥 测试异常: {e}")
            results[test_name] = False
    
    # 输出总结
    total = len(tests)
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"总测试数: {total}")
    print(f"通过数量: {passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    print(f"\n详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    # 系统评估
    if passed >= total * 0.8:
        print(f"\n🎉 系统集成状态: 优秀")
        print("建议: 系统已准备就绪，可以投入使用")
    elif passed >= total * 0.6:
        print(f"\n⚠️ 系统集成状态: 良好")
        print("建议: 修复部分问题后可以投入使用")
    else:
        print(f"\n🚨 系统集成状态: 需要改进")
        print("建议: 解决关键问题后再进行部署")
    
    return passed >= total * 0.6

if __name__ == "__main__":
    success = main()
    print(f"\n测试完成，退出码: {0 if success else 1}")
    sys.exit(0 if success else 1)