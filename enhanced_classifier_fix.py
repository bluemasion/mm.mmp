#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强智能分类器修复脚本
更新关键词映射，改进医疗器械识别能力
"""

import sys
import os
import re

def update_intelligent_classifier():
    """更新智能分类器的关键词映射"""
    
    classifier_path = 'app/intelligent_classifier.py'
    
    if not os.path.exists(classifier_path):
        print(f"错误: 找不到文件 {classifier_path}")
        return False
    
    # 读取原文件
    with open(classifier_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 新的关键词映射
    new_keyword_mappings = '''        self.keyword_mappings = {
            # 医疗器械类 - 扩展关键词
            '医疗器械': ['设备', '仪器', '机器', '器械', '医疗', '诊断', '治疗', '手术', '监护', '射频', '等离子', '气化', '电极'],
            '诊断设备': ['CT', '核磁', 'MRI', 'X光', 'B超', '心电图', 'ECG', '血压计', '体温计', '诊断', '检测'],
            '治疗设备': ['呼吸机', '透析机', '激光', '理疗', '康复', '手术台', '无影灯', '射频', '等离子', '气化', '治疗'],
            '监护设备': ['监护仪', '心电监护', '血氧', '血压监护', '生命体征', '监护', '监测'],
            '手术器械': ['电极', '手术', '外科', '切割', '缝合', '止血', '手术器械'],
            '康复设备': ['康复', '理疗', '训练', '锻炼', '恢复'],
            
            # 根据品牌和厂家的映射
            'Depuy医疗器械': ['depuy', '强生', 'johnson'],
            
            # 办公用品类
            '办公用品': ['笔', '纸', '文具', '办公', '打印', '复印', '装订', '文件夹'],
            '文具用品': ['钢笔', '圆珠笔', '铅笔', '橡皮', '尺子', '订书机', '胶水'],
            '打印用品': ['打印机', '复印机', '墨盒', '硒鼓', '纸张', '标签纸'],
            
            # 建筑材料类
            '建筑材料': ['钢材', '水泥', '砂石', '砖块', '管材', '板材', '涂料'],
            '钢材': ['钢筋', '钢管', '钢板', '角钢', '工字钢', '槽钢', 'H型钢'],
            '管材': ['钢管', '塑料管', 'PVC管', '不锈钢管', '铜管', '铝管'],
            
            # 电子设备类
            '电子设备': ['电脑', '手机', '平板', '服务器', '路由器', '交换机', '电源'],
            '计算机设备': ['台式机', '笔记本', '服务器', '工作站', '一体机'],
            '网络设备': ['路由器', '交换机', '防火墙', '网关', 'WiFi', '网卡'],
            
            # 化工材料类
            '化工材料': ['化学品', '溶剂', '添加剂', '催化剂', '树脂', '涂料', '胶粘剂'],
            '化学试剂': ['试剂', '溶液', '缓冲液', '标准品', '指示剂']
        }'''
    
    # 查找并替换keyword_mappings
    pattern = r'(        self\.keyword_mappings = \{.*?\n        \})'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # 替换关键词映射
        updated_content = content.replace(match.group(1), new_keyword_mappings)
        
        # 写回文件
        with open(classifier_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✅ 智能分类器关键词映射已更新")
        return True
    else:
        print("❌ 未找到keyword_mappings部分")
        return False

def add_enhanced_classification_logic():
    """添加增强的分类逻辑"""
    
    classifier_path = 'app/intelligent_classifier.py'
    
    with open(classifier_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找_keyword_based_recommendation方法
    method_pattern = r'(def _keyword_based_recommendation\(self, material_info: Dict\[str, Any\]\) -> List\[Dict\[str, Any\]\]:.*?return sorted\(recommendations, key=lambda x: x\[\'confidence\'\], reverse=True\)\[:3\])'
    
    enhanced_method = '''def _keyword_based_recommendation(self, material_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于关键词的推荐 - 增强版"""
        material_name = material_info.get('name', '').lower()
        spec = material_info.get('spec', '').lower()
        manufacturer = material_info.get('manufacturer', '').lower()
        text_to_analyze = f"{material_name} {spec} {manufacturer}".strip()
        
        logger.info(f"分析文本: '{text_to_analyze}'")
        
        recommendations = []
        
        # 特殊处理：医疗器械品牌和关键词优先匹配
        if any(keyword in text_to_analyze for keyword in ['depuy', '强生', 'johnson', '等离子', '射频', '气化', '电极']):
            medical_categories = ['治疗设备', '手术器械', '医疗器械']
            for category in medical_categories:
                category_info = self._get_category_by_name(category)
                if category_info and not category_info.get('temp'):
                    recommendations.append({
                        'category_id': category_info['category_id'],
                        'category_name': category_info['category_name'],
                        'confidence': 0.85,
                        'reason': "医疗器械品牌/关键词匹配",
                        'source': 'medical_keyword_priority'
                    })
                    break
        
        # 常规关键词匹配
        for category, keywords in self.keyword_mappings.items():
            confidence = 0.0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in text_to_analyze:
                    confidence += 0.2  # 每个匹配的关键词增加0.2置信度
                    matched_keywords.append(keyword)
            
            if confidence > 0:
                logger.info(f"分类'{category}'匹配到关键词: {matched_keywords}, 置信度: {confidence}")
                
                # 获取分类的详细信息
                category_info = self._get_category_by_name(category)
                if category_info and not category_info.get('temp'):
                    recommendations.append({
                        'category_id': category_info['category_id'],
                        'category_name': category_info['category_name'],
                        'confidence': min(confidence, 0.95),  # 最高置信度不超过0.95
                        'reason': f"关键词匹配: {', '.join(matched_keywords)}",
                        'source': 'keyword_matching'
                    })
        
        logger.info(f"关键词推荐结果: {len(recommendations)}个")
        return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)[:3]'''
    
    match = re.search(method_pattern, content, re.DOTALL)
    if match:
        updated_content = content.replace(match.group(1), enhanced_method)
        
        with open(classifier_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✅ 增强分类逻辑已添加")
        return True
    else:
        print("❌ 未找到_keyword_based_recommendation方法")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("    智能分类器增强修复")
    print("=" * 60)
    
    print("1️⃣ 更新关键词映射...")
    if update_intelligent_classifier():
        print("✅ 关键词映射更新成功")
    else:
        print("❌ 关键词映射更新失败")
        return
    
    print("\n2️⃣ 添加增强分类逻辑...")
    if add_enhanced_classification_logic():
        print("✅ 增强分类逻辑添加成功")
    else:
        print("❌ 增强分类逻辑添加失败")
        return
    
    print("\n🎉 智能分类器修复完成！")
    print("\n建议重启应用以使更改生效：")
    print("  python3.8 run_app.py")

if __name__ == "__main__":
    main()