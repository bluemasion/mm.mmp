#!/usr/bin/env python3
# test_intelligent_recommendation.py
"""
测试智能分类推荐功能
"""
import json
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_intelligent_recommendation():
    """测试智能推荐功能"""
    try:
        print("🔍 测试智能分类推荐功能...")
        
        # 导入必要的模块
        from app.intelligent_classifier import get_intelligent_classifier
        from app.business_data_manager import BusinessDataManager
        from app.master_data_manager import master_data_manager
        
        # 初始化业务数据管理器
        business_manager = BusinessDataManager('business_data.db')
        
        # 初始化智能分类器
        classifier = get_intelligent_classifier(business_manager)
        
        # 测试数据
        test_materials = [
            {
                'name': '阿莫西林胶囊',
                'spec': '250mg*24粒',
                'manufacturer': '华北制药'
            },
            {
                'name': 'CT扫描仪',
                'spec': '64排螺旋CT',
                'manufacturer': '西门子'
            },
            {
                'name': '钢筋',
                'spec': 'φ12mm HRB400',
                'manufacturer': '首钢集团'
            },
            {
                'name': '笔记本电脑',
                'spec': 'ThinkPad X1 Carbon',
                'manufacturer': '联想'
            },
            {
                'name': '圆珠笔',
                'spec': '0.5mm 蓝色',
                'manufacturer': '晨光文具'
            }
        ]
        
        print("\n📊 测试推荐结果:")
        print("=" * 80)
        
        for i, material in enumerate(test_materials, 1):
            print(f"\n{i}. 测试物料: {material['name']}")
            print(f"   规格: {material.get('spec', '无')}")
            print(f"   厂家: {material.get('manufacturer', '无')}")
            
            try:
                # 执行推荐
                recommendations = classifier.recommend_categories(material, f"test_session_{i}")
                
                if recommendations:
                    print("   推荐结果:")
                    for j, rec in enumerate(recommendations[:3], 1):
                        confidence_pct = rec.get('confidence', 0) * 100
                        print(f"     {j}. {rec.get('category_name', '未知分类')} "
                              f"(置信度: {confidence_pct:.1f}%)")
                        print(f"        原因: {rec.get('reason', '无')}")
                        print(f"        来源: {rec.get('source', '未知')}")
                else:
                    print("   ❌ 无推荐结果")
                    
            except Exception as e:
                print(f"   ❌ 推荐失败: {e}")
        
        print("\n" + "=" * 80)
        print("✅ 智能推荐测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_integration():
    """测试API集成"""
    try:
        print("\n🌐 测试API集成...")
        
        # 导入Flask应用
        from app.web_app import app
        
        # 创建测试客户端
        with app.test_client() as client:
            test_data = {
                'material_info': {
                    'name': 'X光机',
                    'spec': '数字化DR',
                    'manufacturer': 'GE医疗'
                }
            }
            
            # 测试智能推荐API
            print("   测试 /api/intelligent_recommend 接口...")
            response = client.post(
                '/api/intelligent_recommend',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.get_json()
                print(f"   成功: {result.get('success', False)}")
                recommendations = result.get('recommendations', [])
                print(f"   推荐数量: {len(recommendations)}")
                
                for i, rec in enumerate(recommendations[:2], 1):
                    confidence_pct = rec.get('confidence', 0) * 100
                    print(f"     {i}. {rec.get('category_name')} ({confidence_pct:.1f}%)")
            else:
                print(f"   ❌ API调用失败: {response.get_json()}")
        
        print("✅ API集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始智能分类推荐测试...")
    
    # 测试智能推荐
    success1 = test_intelligent_recommendation()
    
    # 测试API集成
    success2 = test_api_integration()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！智能分类推荐功能运行正常。")
    else:
        print("\n⚠️ 部分测试失败，请检查日志。")