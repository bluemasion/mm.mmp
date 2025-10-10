#!/usr/bin/env python3
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
