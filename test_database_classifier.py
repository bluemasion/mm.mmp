#!/usr/bin/env python3
# test_database_classifier.py
"""测试基于数据库的智能分类器"""
from app.intelligent_classifier import IntelligentClassifier
from app.business_data_manager import BusinessDataManager

print("🔄 初始化基于数据库的智能分类器...")
business_manager = BusinessDataManager('business_data.db')
classifier = IntelligentClassifier(business_manager)

print("📊 分类器状态检查:")
print(f"  训练结果: {'✅ 已加载' if classifier.training_results else '❌ 未加载'}")
print(f"  缓存规则: {'✅ 已加载' if classifier.cached_rules else '❌ 未加载'}")
print(f"  TF-IDF模型: {'✅ 已加载' if classifier.tfidf_model else '❌ 未加载'}")
print()

# 测试不同类型的物料
test_materials = [
    {
        'name': '(Depuy)等离子刀头电极系统',
        'spec': 'P90电极,227204', 
        'manufacturer': '强生（中国）医疗器材有限公司'
    },
    {
        'name': '传感器控制模块',
        'spec': '12V 5A 电子控制器', 
        'manufacturer': '北京电子科技公司'
    },
    {
        'name': '不锈钢螺栓',
        'spec': 'M8×50mm 304不锈钢', 
        'manufacturer': '机械配件厂'
    }
]

for i, test_material in enumerate(test_materials, 1):
    print(f"🧪 测试物料 {i}: {test_material['name']}")
    print(f"   制造商: {test_material['manufacturer']}")
    print()
    
    recommendations = classifier.recommend_categories(test_material)
    print(f"✨ 推荐结果数量: {len(recommendations)}")
    
    if recommendations:
        for j, rec in enumerate(recommendations[:3], 1):
            print(f"  {j}. 分类: {rec['category_name']}")
            print(f"     置信度: {rec['confidence']:.3f}")
            print(f"     推荐原因: {rec['reason']}")
            print(f"     数据来源: {rec['source']}")
            print()
    else:
        print("  ❌ 未找到合适的分类推荐")
        print()
    
    print("-" * 60)
    print()

print("🎯 数据库化智能分类系统测试完成！")