#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试增强分类器修复情况
"""

import sys
import os

# 添加项目根目录到路径
project_root = '/Users/mason/Desktop/code /mmp'
sys.path.insert(0, project_root)

# 测试智能分类器
def test_enhanced_classifier():
    print("=== 测试增强智能分类器修复情况 ===")
    
    try:
        # 导入业务数据管理器
        from app.business_data_manager import BusinessDataManager
        business_manager = BusinessDataManager(os.path.join(project_root, 'business_data.db'))
        
        # 导入智能分类器
        from app.intelligent_classifier import IntelligentClassifier
        classifier = IntelligentClassifier(business_manager)
        
        print("✅ 智能分类器实例化成功")
        
        # 测试增强分类匹配方法
        test_material = {
            'name': '包装袋',
            'spec': '30kg装',
            'manufacturer': '某包装公司'
        }
        
        print("测试物料:", test_material)
        
        # 测试增强分类匹配
        enhanced_results = classifier.enhanced_category_matching(test_material)
        print("✅ enhanced_category_matching方法调用成功")
        print("增强匹配结果数量:", len(enhanced_results))
        
        if enhanced_results:
            for i, result in enumerate(enhanced_results[:3], 1):
                print("  {}. {} (置信度: {:.2f})".format(i, result['category_name'], result['confidence']))
                print("     理由:", result['reason'])
        
        # 测试完整推荐流程
        print("\n--- 测试完整推荐流程 ---")
        full_results = classifier.recommend_categories(test_material)
        print("✅ 完整推荐流程成功")
        print("完整推荐结果数量:", len(full_results))
        
        if full_results:
            for i, result in enumerate(full_results[:3], 1):
                print("  {}. {} (置信度: {:.2f})".format(i, result['category_name'], result['confidence']))
                print("     来源:", result['source'])
        
        print("\n🎉 增强分类器修复验证成功！")
        return True
        
    except AttributeError as e:
        print("❌ 方法调用错误:", e)
        return False
    except Exception as e:
        print("❌ 测试失败:", e)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enhanced_classifier()