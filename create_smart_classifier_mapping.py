#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于实际数据库的智能分类映射优化
根据现有的548个制造业分类，重新构建关键词映射
"""

import sys
import os
import sqlite3
import json
from typing import Dict, List, Any
import logging

# 添加项目路径到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_existing_categories():
    """分析现有数据库中的分类数据"""
    print("🔍 分析现有分类数据...")
    
    try:
        conn = sqlite3.connect('master_data.db')
        cursor = conn.cursor()
        
        # 获取所有分类
        cursor.execute('''
            SELECT id, category_code, category_name, level, parent_code, parent_name
            FROM material_categories 
            ORDER BY level, category_code
        ''')
        
        categories = cursor.fetchall()
        print(f"总共找到 {len(categories)} 个分类")
        
        # 按层级分组
        level_groups = {1: [], 2: [], 3: []}
        for category in categories:
            level = category[3]
            if level in level_groups:
                level_groups[level].append({
                    'id': category[0],
                    'code': category[1],
                    'name': category[2],
                    'level': category[3],
                    'parent_code': category[4],
                    'parent_name': category[5]
                })
        
        print("\\n各层级分类统计:")
        for level, cats in level_groups.items():
            print(f"  Level {level}: {len(cats)} 个")
            
        conn.close()
        return level_groups
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return {}

def build_smart_keyword_mappings(categories_by_level):
    """基于实际分类构建智能关键词映射"""
    print("\\n🧠 构建智能关键词映射...")
    
    keyword_mappings = {}
    
    # 遍历所有分类，为每个分类生成关键词
    for level, categories in categories_by_level.items():
        for category in categories:
            name = category['name']
            keywords = generate_keywords_for_category(name)
            
            if keywords:
                keyword_mappings[name] = keywords
                
    print(f"生成了 {len(keyword_mappings)} 个分类的关键词映射")
    return keyword_mappings

def generate_keywords_for_category(category_name: str) -> List[str]:
    """为单个分类生成关键词"""
    keywords = []
    name_lower = category_name.lower()
    
    # 基础关键词：分类名称本身的分词
    base_keywords = [category_name]
    
    # 化工相关分类的关键词
    if any(word in name_lower for word in ['化工', '催化剂', '助剂', '溶剂', '添加剂']):
        keywords.extend(['化工', '化学', '催化剂', '助剂', '溶剂', '添加剂', '化学品'])
        if '催化剂' in name_lower:
            keywords.extend(['catalyst', '催化', '载体', 'al2o3', 'sio2'])
        if '助剂' in name_lower:
            keywords.extend(['添加剂', '稳定剂', '增塑剂', '改性剂'])
        if '溶剂' in name_lower:
            keywords.extend(['溶液', '有机溶剂', '无机溶剂', '甲醇', '乙醇'])
    
    # 包装物相关
    if any(word in name_lower for word in ['包装', '容器', '袋', '箱', '桶']):
        keywords.extend(['包装', '容器', '袋子', '纸箱', '包装袋', '包装箱', '桶'])
    
    # 化验用品相关
    if any(word in name_lower for word in ['化验', '试验', '实验', '检测']):
        keywords.extend(['化验', '试验', '实验', '检测', '测试', '分析', '仪器'])
    
    # 劳保用品相关  
    if any(word in name_lower for word in ['劳保', '防护', '安全']):
        keywords.extend(['劳保', '防护', '安全', '防护用品', '劳保用品', '安全用品'])
    
    # 消防设施相关
    if any(word in name_lower for word in ['消防', '灭火', '报警']):
        keywords.extend(['消防', '灭火', '火灾', '报警', '消防器材', '灭火器'])
    
    # 办公用品相关
    if any(word in name_lower for word in ['办公', '文具', '纸张', '笔']):
        keywords.extend(['办公', '文具', '办公用品', '文具用品', '纸张', '笔'])
    
    # 电气设备相关
    if any(word in name_lower for word in ['电气', '电力', '电子', '仪表', '自控']):
        keywords.extend(['电气', '电力', '电子', '仪表', '自控', '电气设备', '电子设备'])
    
    # 机械设备相关
    if any(word in name_lower for word in ['机械', '设备', '泵', '阀', '管件']):
        keywords.extend(['机械', '设备', '泵', '阀门', '管件', '机械设备', '工业设备'])
    
    # 建筑材料相关
    if any(word in name_lower for word in ['建筑', '钢材', '水泥', '砂石']):
        keywords.extend(['建筑', '建材', '钢材', '水泥', '砂石', '建筑材料'])
    
    # 工具相关
    if any(word in name_lower for word in ['工具', '刀具', '量具', '夹具']):
        keywords.extend(['工具', '刀具', '量具', '夹具', '手工工具', '测量工具'])
    
    # 运输设备相关
    if any(word in name_lower for word in ['运输', '车辆', '叉车']):
        keywords.extend(['运输', '车辆', '叉车', '运输设备', '搬运设备'])
    
    # 通用设备相关
    if any(word in name_lower for word in ['通用', '设备', '备件']):
        keywords.extend(['通用', '设备', '备件', '通用设备', '机械备件'])
    
    # 合并并去重
    all_keywords = base_keywords + keywords
    return list(set(all_keywords))

def create_enhanced_classifier_config(keyword_mappings, categories_by_level):
    """创建增强的分类器配置"""
    print("\\n⚙️ 创建增强配置...")
    
    config = {
        'version': '2.0',
        'generated_time': '2025-09-28',
        'description': '基于实际548个制造业分类的智能推荐配置',
        'statistics': {
            'total_categories': sum(len(cats) for cats in categories_by_level.values()),
            'level_distribution': {f'level_{k}': len(v) for k, v in categories_by_level.items()},
            'keyword_mappings_count': len(keyword_mappings)
        },
        'keyword_mappings': keyword_mappings,
        'categories_by_level': categories_by_level,
        'spec_patterns': {
            # 改进的规格模式
            'chemical_purity': r'(\\d+(?:\\.\\d+)?)\\s*%',
            'diameter': r'[φΦ直径]\\s*(\\d+(?:\\.\\d+)?)\\s*mm',  
            'dimensions': r'(\\d+(?:\\.\\d+)?)\\s*[×xX]\\s*(\\d+(?:\\.\\d+)?)',
            'voltage': r'(\\d+(?:\\.\\d+)?)\\s*[VvKk电压伏特]',
            'power': r'(\\d+(?:\\.\\d+)?)\\s*[WwKk功率瓦特千瓦]',
            'capacity': r'(\\d+(?:\\.\\d+)?)\\s*[LlMm容量升毫升立方]',
            'weight': r'(\\d+(?:\\.\\d+)?)\\s*[KkGg千克公斤克吨]',
            'chemical_formula': r'([A-Z][a-z]?[0-9]*)+',
            'model_number': r'[A-Z0-9\\-]{3,}',
            'temperature': r'(\\d+(?:\\.\\d+)?)\\s*[°℃摄氏度]'
        },
        'confidence_weights': {
            'exact_name_match': 0.95,
            'keyword_match': 0.7,
            'spec_pattern_match': 0.5,  
            'manufacturer_match': 0.6,
            'parent_category_match': 0.4
        }
    }
    
    # 保存配置
    with open('enhanced_classifier_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("✅ 增强配置已保存到 enhanced_classifier_config.json")
    return config

def create_improved_classifier_patch():
    """创建改进的分类器补丁代码"""
    print("\\n🔧 创建分类器改进补丁...")
    
    patch_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分类器增强补丁
应用基于实际数据库的改进算法
"""

import json
import os
from typing import Dict, List, Any

class EnhancedClassifierPatch:
    """增强分类器补丁"""
    
    def __init__(self, config_file='enhanced_classifier_config.json'):
        self.config = self.load_config(config_file)
        
    def load_config(self, config_file: str) -> Dict:
        """加载增强配置"""
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def enhanced_keyword_matching(self, text: str, categories: List[Dict]) -> List[Dict]:
        """增强的关键词匹配"""
        recommendations = []
        text_lower = text.lower()
        
        keyword_mappings = self.config.get('keyword_mappings', {})
        confidence_weights = self.config.get('confidence_weights', {})
        
        for category_name, keywords in keyword_mappings.items():
            # 寻找匹配的实际分类
            matching_category = None
            for cat in categories:
                if cat.get('category_name') == category_name or cat.get('name') == category_name:
                    matching_category = cat
                    break
            
            if not matching_category:
                continue
                
            confidence = 0.0
            matched_keywords = []
            
            # 精确名称匹配
            if category_name.lower() in text_lower:
                confidence += confidence_weights.get('exact_name_match', 0.95)
                matched_keywords.append(f"精确匹配:{category_name}")
            
            # 关键词匹配
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    confidence += confidence_weights.get('keyword_match', 0.7) / len(keywords)
                    matched_keywords.append(keyword)
            
            if confidence > 0.1:  # 置信度阈值
                recommendations.append({
                    'category_id': matching_category.get('id'),
                    'category_name': category_name,
                    'confidence': min(confidence, 1.0),
                    'reason': f"关键词匹配: {', '.join(matched_keywords[:3])}",
                    'source': 'enhanced_keyword_matching',
                    'matched_keywords': matched_keywords
                })
        
        return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)
    
    def smart_fallback_recommendation(self, text: str, categories: List[Dict]) -> List[Dict]:
        """智能备用推荐"""
        recommendations = []
        text_lower = text.lower()
        
        # 基于一级分类的模糊匹配
        level1_categories = [cat for cat in categories if cat.get('level') == 1]
        
        for category in level1_categories[:5]:  # 只考虑前5个一级分类
            category_name = category.get('category_name', '')
            
            # 简单的字符匹配
            common_chars = set(text_lower) & set(category_name.lower())
            if len(common_chars) >= 2:  # 至少2个共同字符
                recommendations.append({
                    'category_id': category.get('id'),
                    'category_name': category_name,
                    'confidence': len(common_chars) / max(len(text_lower), len(category_name)),
                    'reason': f"模糊匹配: 共同字符 {len(common_chars)} 个",
                    'source': 'smart_fallback'
                })
        
        return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)[:3]

def apply_enhanced_classifier_patch():
    """应用增强分类器补丁"""
    print("应用分类器增强补丁...")
    
    # 这里可以添加动态补丁代码
    # 或者生成新的分类器实现
    
    return True

if __name__ == "__main__":
    patch = EnhancedClassifierPatch()
    apply_enhanced_classifier_patch()
'''
    
    with open('enhanced_classifier_patch.py', 'w', encoding='utf-8') as f:
        f.write(patch_code)
    
    print("✅ 分类器改进补丁已保存到 enhanced_classifier_patch.py")
    return True

def test_enhanced_mappings(keyword_mappings, categories_by_level):
    """测试增强的映射效果"""
    print("\\n🧪 测试增强映射...")
    
    test_cases = [
        "催化剂载体",
        "化工助剂", 
        "包装袋",
        "化验仪器",
        "防护用品",
        "消防器材",
        "办公纸张",
        "电气设备",
        "机械泵",
        "建筑钢材"
    ]
    
    print("测试结果:")
    for test_text in test_cases:
        matched_categories = []
        
        for category_name, keywords in keyword_mappings.items():
            if any(keyword.lower() in test_text.lower() for keyword in keywords):
                matched_categories.append(category_name)
        
        print(f"  '{test_text}' -> 匹配分类: {matched_categories[:3]}")
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("     基于实际数据库的智能分类映射优化")
    print("=" * 60)
    
    # 1. 分析现有分类数据
    categories_by_level = analyze_existing_categories()
    
    if not categories_by_level:
        print("❌ 无法获取分类数据，退出")
        return
    
    # 2. 构建智能关键词映射
    keyword_mappings = build_smart_keyword_mappings(categories_by_level)
    
    # 3. 创建增强配置
    config = create_enhanced_classifier_config(keyword_mappings, categories_by_level)
    
    # 4. 创建改进补丁
    create_improved_classifier_patch()
    
    # 5. 测试映射效果
    test_enhanced_mappings(keyword_mappings, categories_by_level)
    
    print("\\n" + "=" * 60)
    print("✅ 智能分类映射优化完成！")
    print("   - 生成了基于实际548个分类的关键词映射")
    print("   - 创建了增强配置文件")
    print("   - 提供了改进补丁代码")
    print("   建议接下来将这些改进集成到主分类器中。")

if __name__ == "__main__":
    main()