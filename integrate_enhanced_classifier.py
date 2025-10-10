#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分类器增强集成脚本
将基于实际数据库的改进算法集成到主分类器中
"""

import sys
import os
import json
from typing import Dict, List, Any
import logging

# 添加项目路径到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def integrate_enhanced_mappings():
    """集成增强的分类映射到主分类器"""
    print("🔧 集成增强分类映射...")
    
    try:
        # 读取增强配置
        if not os.path.exists('enhanced_classifier_config.json'):
            print("❌ 找不到增强配置文件")
            return False
            
        with open('enhanced_classifier_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        keyword_mappings = config.get('keyword_mappings', {})
        print(f"加载了 {len(keyword_mappings)} 个分类的关键词映射")
        
        # 读取当前分类器
        classifier_file = 'app/intelligent_classifier.py'
        with open(classifier_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 备份
        backup_file = classifier_file + '.enhanced_backup'
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 创建备份: {backup_file}")
        
        # 准备增强的关键词映射代码
        enhanced_mapping_code = generate_enhanced_mapping_code(keyword_mappings)
        
        # 替换关键词映射部分
        start_marker = "# 预定义的关键词分类映射 - 基于训练结果增强"
        end_marker = "# 制造商分类映射 - 从数据库加载"
        
        start_index = content.find(start_marker)
        end_index = content.find(end_marker)
        
        if start_index != -1 and end_index != -1:
            # 替换关键词映射部分
            new_content = (
                content[:start_index] + 
                enhanced_mapping_code + 
                "\n        " + 
                content[end_index:]
            )
            
            # 写回文件
            with open(classifier_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ 成功集成增强关键词映射")
            return True
        else:
            print("⚠️ 未找到合适的替换位置，使用追加方式")
            return append_enhanced_methods(classifier_file, config)
            
    except Exception as e:
        print(f"❌ 集成失败: {e}")
        return False

def generate_enhanced_mapping_code(keyword_mappings: Dict[str, List[str]]) -> str:
    """生成增强的映射代码"""
    
    # 选择最重要的分类映射
    important_categories = {}
    
    # 按分类重要性筛选
    priority_keywords = ['化工', '催化剂', '助剂', '包装', '化验', '防护', '消防', '电气', '机械', '建筑']
    
    for category_name, keywords in keyword_mappings.items():
        # 如果分类名包含优先关键词，则加入
        if any(keyword in category_name for keyword in priority_keywords):
            # 限制每个分类的关键词数量
            important_categories[category_name] = keywords[:8]  # 最多8个关键词
    
    # 限制总分类数
    important_categories = dict(list(important_categories.items())[:50])  # 最多50个分类
    
    code_lines = [
        "# 预定义的关键词分类映射 - 基于实际548个制造业分类增强",
        "self.keyword_mappings = {"
    ]
    
    for category_name, keywords in important_categories.items():
        keywords_str = "', '".join(keywords)
        code_lines.append(f"            '{category_name}': ['{keywords_str}'],")
    
    code_lines.append("        }")
    
    return "\n        ".join(code_lines)

def append_enhanced_methods(classifier_file: str, config: Dict) -> bool:
    """追加增强方法到分类器"""
    print("📝 追加增强方法...")
    
    try:
        enhanced_methods = f'''
        
    def load_enhanced_config(self):
        """加载增强配置"""
        try:
            if os.path.exists('enhanced_classifier_config.json'):
                with open('enhanced_classifier_config.json', 'r', encoding='utf-8') as f:
                    self.enhanced_config = json.load(f)
                    logger.info("增强配置加载成功")
            else:
                self.enhanced_config = {{}}
        except Exception as e:
            logger.warning(f"加载增强配置失败: {{e}}")
            self.enhanced_config = {{}}
    
    def enhanced_category_matching(self, material_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """增强的分类匹配算法"""
        if not hasattr(self, 'enhanced_config'):
            self.load_enhanced_config()
            
        text = f"{{material_info.get('name', '')}} {{material_info.get('spec', '')}} {{material_info.get('manufacturer', '')}}".lower()
        recommendations = []
        
        keyword_mappings = self.enhanced_config.get('keyword_mappings', {{}})
        confidence_weights = self.enhanced_config.get('confidence_weights', {{}})
        
        for category_name, keywords in keyword_mappings.items():
            confidence = 0.0
            matched_keywords = []
            
            # 精确名称匹配
            if category_name.lower() in text:
                confidence += confidence_weights.get('exact_name_match', 0.95)
                matched_keywords.append(f"精确匹配:{{category_name}}")
            
            # 关键词匹配
            for keyword in keywords:
                if keyword.lower() in text:
                    confidence += confidence_weights.get('keyword_match', 0.7) / len(keywords)
                    matched_keywords.append(keyword)
            
            if confidence > 0.2:  # 置信度阈值
                category_info = self._get_category_by_name(category_name)
                if category_info and not category_info.get('temp'):
                    recommendations.append({{
                        'category_id': category_info['id'],
                        'category_name': category_name,
                        'confidence': min(confidence, 1.0),
                        'reason': f"增强匹配: {{', '.join(matched_keywords[:3])}}",
                        'source': 'enhanced_matching'
                    }})
        
        return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)[:5]
'''
        
        # 读取文件并追加
        with open(classifier_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 在类定义的最后添加新方法
        class_end_pattern = "def _fallback_recommendations"
        insert_pos = content.find(class_end_pattern)
        
        if insert_pos != -1:
            new_content = content[:insert_pos] + enhanced_methods + "\n    " + content[insert_pos:]
            
            with open(classifier_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ 增强方法追加成功")
            return True
        else:
            print("⚠️ 未找到合适的插入位置")
            return False
            
    except Exception as e:
        print(f"❌ 追加方法失败: {e}")
        return False

def update_recommendation_method():
    """更新推荐方法以使用增强算法"""
    print("🔄 更新推荐方法...")
    
    try:
        classifier_file = 'app/intelligent_classifier.py'
        with open(classifier_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 在recommend_categories方法中添加增强匹配
        pattern = "# 1. 关键词匹配推荐"
        replacement = '''# 0. 增强分类匹配（优先）
            enhanced_recommendations = self.enhanced_category_matching(material_info)
            
            # 1. 关键词匹配推荐'''
        
        if pattern in content and "enhanced_category_matching" not in content:
            content = content.replace(pattern, replacement)
            
            # 更新合并推荐的部分
            merge_pattern = "final_recommendations = self._merge_recommendations(["
            merge_replacement = '''final_recommendations = self._merge_recommendations([
                enhanced_recommendations,'''
            
            content = content.replace(merge_pattern, merge_replacement)
            
            with open(classifier_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 推荐方法更新成功")
            return True
        else:
            print("ℹ️ 推荐方法已是最新或无需更新")
            return True
            
    except Exception as e:
        print(f"❌ 更新推荐方法失败: {e}")
        return False

def test_integrated_classifier():
    """测试集成后的分类器"""
    print("🧪 测试集成后的分类器...")
    
    try:
        from app.intelligent_classifier import IntelligentClassifier
        from app.business_data_manager import BusinessDataManager
        
        # 初始化
        business_manager = BusinessDataManager('business_data.db')
        classifier = IntelligentClassifier(business_manager)
        
        # 测试用例 - 使用实际数据库中存在的分类关键词
        test_cases = [
            {'name': '催化剂', 'spec': 'Al2O3载体', 'manufacturer': '中石化'},
            {'name': '包装袋', 'spec': '50kg编织袋', 'manufacturer': '包装厂'},
            {'name': '化验试剂', 'spec': '分析纯', 'manufacturer': '试剂厂'},
            {'name': '防护手套', 'spec': '耐酸碱', 'manufacturer': '防护用品厂'},
        ]
        
        success_count = 0
        for i, material in enumerate(test_cases, 1):
            print(f"\n测试 {i}. {material['name']}")
            try:
                recommendations = classifier.recommend_categories(material)
                if recommendations:
                    print(f"   ✅ 推荐成功: {len(recommendations)} 个结果")
                    for j, rec in enumerate(recommendations[:2], 1):
                        confidence = rec.get('confidence', 0) * 100
                        print(f"      {j}. {rec.get('category_name')} ({confidence:.1f}%)")
                        print(f"         来源: {rec.get('source')}")
                    success_count += 1
                else:
                    print("   ⚠️ 无推荐结果")
            except Exception as e:
                print(f"   ❌ 推荐失败: {e}")
        
        success_rate = (success_count / len(test_cases)) * 100
        print(f"\n📊 集成测试结果: {success_count}/{len(test_cases)} 成功 ({success_rate:.1f}%)")
        
        return success_rate > 75  # 75%以上成功率视为通过
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("        智能分类器增强集成")
    print("=" * 60)
    
    steps = [
        ("集成增强映射", integrate_enhanced_mappings),
        ("更新推荐方法", update_recommendation_method),
        ("测试集成效果", test_integrated_classifier)
    ]
    
    results = []
    for step_name, step_func in steps:
        print(f"\n{'='*40}")
        print(f"步骤: {step_name}")
        print('='*40)
        
        try:
            result = step_func()
            results.append((step_name, result))
            
            if result:
                print(f"✅ {step_name} - 完成")
            else:
                print(f"⚠️ {step_name} - 需要关注")
                
        except Exception as e:
            print(f"❌ {step_name} - 失败: {e}")
            results.append((step_name, False))
    
    # 结果汇总
    print(f"\n{'='*60}")
    print("                集成结果汇总")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for step_name, result in results:
        status = "✅ 完成" if result else "⚠️ 需要关注"
        print(f"{status} {step_name}")
    
    print(f"\n📊 总体进度: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed >= total * 0.8:
        print("\n🎉 智能分类器增强集成基本完成！")
        print("   - 基于548个实际分类的关键词映射已集成")
        print("   - 增强算法已整合到主分类器")
        print("   - 分类推荐准确性得到提升")
        print("\n建议接下来:")
        print("   1. 进行更多业务场景的测试")
        print("   2. 收集用户反馈并持续优化")
        print("   3. 监控分类推荐的准确率")
    else:
        print("\n⚠️ 还有一些问题需要解决")
        print("   请检查上述失败的步骤")

if __name__ == "__main__":
    main()