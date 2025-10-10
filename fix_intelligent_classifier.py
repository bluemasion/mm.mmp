#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分类器修复和优化脚本
修复数据库字段名问题，优化分类算法准确性
"""

import sys
import os
import sqlite3
import logging
from typing import Dict, List, Any

# 添加项目路径到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_schema():
    """检查数据库模式"""
    print("🔍 检查数据库模式...")
    
    try:
        conn = sqlite3.connect('master_data.db')
        cursor = conn.cursor()
        
        # 检查material_categories表结构
        cursor.execute('PRAGMA table_info(material_categories)')
        columns = cursor.fetchall()
        
        print("material_categories表字段:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # 检查数据样本
        cursor.execute('SELECT * FROM material_categories LIMIT 3')
        rows = cursor.fetchall()
        
        print("\n数据样本:")
        for row in rows:
            print(f"  ID: {row[0]}, Code: {row[1]}, Name: {row[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def analyze_classification_data():
    """分析分类数据"""
    print("\n📊 分析分类数据...")
    
    try:
        conn = sqlite3.connect('master_data.db')
        cursor = conn.cursor()
        
        # 统计各层级分类数量
        cursor.execute('''
            SELECT level, COUNT(*) as count 
            FROM material_categories 
            GROUP BY level 
            ORDER BY level
        ''')
        level_stats = cursor.fetchall()
        
        print("各层级分类统计:")
        for level, count in level_stats:
            print(f"  Level {level}: {count} 个分类")
        
        # 查看各层级的分类示例
        for level in [1, 2, 3]:
            cursor.execute('''
                SELECT category_name, category_code 
                FROM material_categories 
                WHERE level = ? 
                LIMIT 5
            ''', (level,))
            examples = cursor.fetchall()
            
            print(f"\nLevel {level} 分类示例:")
            for name, code in examples:
                print(f"  {code}: {name}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 分类数据分析失败: {e}")
        return False

def fix_classifier_field_names():
    """修复智能分类器中的字段名问题"""
    print("\n🔧 修复智能分类器字段名...")
    
    classifier_file = 'app/intelligent_classifier.py'
    
    try:
        # 读取文件内容
        with open(classifier_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 备份原文件
        backup_file = classifier_file + '.backup'
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 创建备份文件: {backup_file}")
        
        # 修复字段名映射问题
        fixes = [
            # 修复 _get_category_by_id 函数中的字段名
            ("if category.get('category_id') == category_id:", "if category.get('id') == category_id or str(category.get('id')) == str(category_id):"),
            
            # 添加容错的字段名获取
            ("'id': category.get('category_id') or category.get('id'),", "'id': category.get('id') or category.get('category_id'),"),
        ]
        
        modified = False
        for old_text, new_text in fixes:
            if old_text in content and old_text != new_text:
                content = content.replace(old_text, new_text)
                modified = True
                print(f"✅ 修复: {old_text[:50]}...")
        
        if modified:
            # 写回修复后的内容
            with open(classifier_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 智能分类器字段名修复完成")
        else:
            print("ℹ️ 未发现需要修复的字段名问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复智能分类器失败: {e}")
        return False

def enhance_classification_mappings():
    """优化分类映射，基于实际数据库内容"""
    print("\n🎯 优化分类映射...")
    
    try:
        conn = sqlite3.connect('master_data.db')
        cursor = conn.cursor()
        
        # 获取所有分类
        cursor.execute('SELECT category_name, category_code, level FROM material_categories ORDER BY level, category_code')
        categories = cursor.fetchall()
        
        # 分析关键词模式
        keyword_mappings = {}
        
        for name, code, level in categories:
            name_lower = name.lower()
            
            # 基于分类名称生成关键词
            keywords = []
            
            # 化工相关
            if any(word in name_lower for word in ['化工', '化学', '催化', '溶剂', '试剂']):
                keywords.extend(['化工', '化学', '催化剂', '溶剂', '试剂'])
            
            # 机械相关
            if any(word in name_lower for word in ['机械', '设备', '器械', '装置']):
                keywords.extend(['机械', '设备', '器械', '装置'])
            
            # 电子相关  
            if any(word in name_lower for word in ['电子', '电气', '仪器', '仪表']):
                keywords.extend(['电子', '电气', '仪器', '仪表'])
            
            # 建材相关
            if any(word in name_lower for word in ['建材', '钢材', '管材', '板材']):
                keywords.extend(['建材', '钢材', '管材', '板材'])
            
            if keywords:
                keyword_mappings[name] = keywords
        
        print(f"生成了 {len(keyword_mappings)} 个分类的关键词映射")
        
        # 生成优化的分类映射配置
        mapping_config = {
            'keyword_mappings': keyword_mappings,
            'categories_count': len(categories),
            'level_distribution': {}
        }
        
        # 统计层级分布
        for level in [1, 2, 3]:
            count = sum(1 for _, _, l in categories if l == level)
            mapping_config['level_distribution'][f'level_{level}'] = count
        
        # 保存配置到文件
        import json
        with open('classification_mapping_config.json', 'w', encoding='utf-8') as f:
            json.dump(mapping_config, f, ensure_ascii=False, indent=2)
        
        print("✅ 分类映射配置已保存到 classification_mapping_config.json")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 优化分类映射失败: {e}")
        return False

def test_improved_classifier():
    """测试改进后的分类器"""
    print("\n🧪 测试改进后的智能分类器...")
    
    try:
        from app.intelligent_classifier import IntelligentClassifier
        from app.business_data_manager import BusinessDataManager
        
        # 初始化
        business_manager = BusinessDataManager('business_data.db')
        classifier = IntelligentClassifier(business_manager)
        
        # 测试用例
        test_materials = [
            {'name': '催化剂载体', 'spec': 'Al2O3', 'manufacturer': '中石化'},
            {'name': '不锈钢管', 'spec': 'φ20mm', 'manufacturer': '宝钢'},
            {'name': '电子仪器', 'spec': '220V', 'manufacturer': '西门子'},
        ]
        
        success_count = 0
        total_count = len(test_materials)
        
        for i, material in enumerate(test_materials, 1):
            print(f"\n测试 {i}. {material['name']}")
            try:
                recommendations = classifier.recommend_categories(material)
                if recommendations:
                    print(f"   ✅ 推荐成功: {len(recommendations)} 个结果")
                    for j, rec in enumerate(recommendations[:2], 1):
                        confidence = rec.get('confidence', 0) * 100
                        print(f"      {j}. {rec.get('category_name')} ({confidence:.1f}%)")
                    success_count += 1
                else:
                    print("   ⚠️ 无推荐结果")
            except Exception as e:
                print(f"   ❌ 推荐失败: {e}")
        
        success_rate = (success_count / total_count) * 100
        print(f"\n📊 测试结果: {success_count}/{total_count} 成功 ({success_rate:.1f}%)")
        
        return success_rate > 50  # 成功率大于50%视为通过
        
    except Exception as e:
        print(f"❌ 分类器测试失败: {e}")
        return False

def create_enhanced_classifier():
    """创建增强版智能分类器"""
    print("\n🚀 创建增强版智能分类器...")
    
    enhanced_code = '''
# 智能分类器增强方法
def get_enhanced_keyword_mappings():
    """获取增强的关键词映射（基于实际数据库分类）"""
    return {
        # 化工类 - 基于实际数据库分类
        '化工催化剂': ['催化剂', '化工', '催化', 'Al2O3', 'SiO2', '载体'],
        '固定床催化剂': ['固定床', '催化剂', '反应器', '化工'],
        '催化剂载体': ['载体', '催化剂', '多孔', '氧化铝', '硅胶'],
        
        # 助剂类
        '化工助剂': ['助剂', '添加剂', '稳定剂', '增塑剂'],
        '塑料添加剂': ['塑料', '添加剂', '改性剂', '填料'],
        
        # 溶剂类  
        '有机溶剂': ['溶剂', '有机', '甲醇', '乙醇', '丙酮', '甲苯'],
        '无机溶剂': ['无机', '溶剂', '水', '酸', '碱'],
        
        # 通用模式
        '电子': ['电子', '电气', '芯片', '电路', '传感器'],
        '机械': ['机械', '零件', '轴承', '齿轮', '阀门'],
        '建材': ['建材', '钢材', '水泥', '砂石', '管材'],
        '医疗': ['医疗', '器械', '设备', '诊断', '治疗']
    }

def enhanced_spec_pattern_matching(spec_text: str) -> List[tuple]:
    """增强的规格模式匹配"""
    import re
    
    patterns = [
        # 化学物质纯度
        (r'(\d+(?:\.\d+)?)\s*%', 'purity', '化学纯度'),
        
        # 尺寸规格
        (r'[φΦ直径]\s*(\d+(?:\.\d+)?)\s*mm', 'diameter', '直径规格'),
        (r'(\d+(?:\.\d+)?)\s*[×xX]\s*(\d+(?:\.\d+)?)', 'dimensions', '尺寸规格'),
        
        # 电气参数
        (r'(\d+(?:\.\d+)?)\s*[VvKk电压]', 'voltage', '电压规格'),
        (r'(\d+(?:\.\d+)?)\s*[WwKk功率]', 'power', '功率规格'),
        
        # 容量/重量
        (r'(\d+(?:\.\d+)?)\s*[LlMm容量升]', 'capacity', '容量规格'),
        (r'(\d+(?:\.\d+)?)\s*[KkGg千克公斤]', 'weight', '重量规格'),
        
        # 化学成分
        (r'([A-Z][a-z]?[0-9]*)+', 'chemical_formula', '化学分子式'),
    ]
    
    matches = []
    for pattern, category, desc in patterns:
        if re.search(pattern, spec_text, re.IGNORECASE):
            matches.append((category, desc))
    
    return matches
'''
    
    # 保存增强代码
    with open('enhanced_classifier_methods.py', 'w', encoding='utf-8') as f:
        f.write(enhanced_code)
    
    print("✅ 增强版分类器方法已保存到 enhanced_classifier_methods.py")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("          智能分类器修复和优化")
    print("=" * 60)
    
    steps = [
        ("检查数据库模式", check_database_schema),
        ("分析分类数据", analyze_classification_data), 
        ("修复字段名问题", fix_classifier_field_names),
        ("优化分类映射", enhance_classification_mappings),
        ("创建增强方法", create_enhanced_classifier),
        ("测试改进效果", test_improved_classifier)
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
                print(f"⚠️ {step_name} - 部分完成或有警告")
                
        except Exception as e:
            print(f"❌ {step_name} - 失败: {e}")
            results.append((step_name, False))
    
    # 结果汇总
    print(f"\n{'='*60}")
    print("                优化结果汇总")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for step_name, result in results:
        status = "✅ 完成" if result else "⚠️ 需要关注"
        print(f"{status} {step_name}")
    
    print(f"\n📊 总体进度: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed >= total * 0.8:  # 80%以上完成
        print("\n🎉 智能分类器优化基本完成！")
        print("   建议后续进行更多测试和微调。")
    else:
        print("\n⚠️ 还有一些问题需要解决。")
        print("   请检查上述失败的步骤。")

if __name__ == "__main__":
    main()