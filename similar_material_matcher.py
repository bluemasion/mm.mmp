#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
近似物料匹配器
实现基于阈值的近似物料数据匹配功能
"""

import sqlite3
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import jieba

logger = logging.getLogger(__name__)

class SimilarMaterialMatcher:
    """近似物料匹配器"""
    
    def __init__(self, db_path: str = 'business_data.db'):
        """初始化"""
        self.db_path = db_path
        self.similar_materials_table = 'similar_materials'
        self.vectorizer = None
        self.material_vectors = None
        self.materials_data = None
        self._load_materials_data()
    
    def _load_materials_data(self):
        """加载近似物料数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = f'''
                SELECT material_code, material_name, material_long_desc, 
                       material_category, specification, model, unit
                FROM {self.similar_materials_table}
                ORDER BY material_code
            '''
            
            self.materials_data = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(self.materials_data) == 0:
                logger.warning("近似物料数据为空")
                return
            
            # 准备文本数据用于向量化
            self._prepare_text_features()
            logger.info(f"已加载 {len(self.materials_data)} 条近似物料数据")
            
        except Exception as e:
            logger.error(f"加载近似物料数据失败: {e}")
            self.materials_data = pd.DataFrame()
    
    def _prepare_text_features(self):
        """准备文本特征用于相似度计算"""
        if self.materials_data.empty:
            return
        
        # 组合文本特征: 物料名称 + 规格 + 长描述
        text_features = []
        for _, row in self.materials_data.iterrows():
            combined_text = f"{row['material_name']} {row['specification']} {row['material_long_desc']}"
            # 使用jieba分词
            words = jieba.cut(combined_text)
            processed_text = ' '.join(words)
            text_features.append(processed_text)
        
        # TF-IDF向量化
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words=None  # 对中文，我们不设置停用词
        )
        
        self.material_vectors = self.vectorizer.fit_transform(text_features)
        logger.info("文本特征向量化完成")
    
    def find_similar_materials(
        self, 
        input_material: Dict[str, str],
        threshold: float = 0.3,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查找近似物料
        
        Args:
            input_material: 输入物料信息 {'name': '', 'spec': '', 'desc': ''}
            threshold: 相似度阈值 (0-1)
            max_results: 最大返回结果数
            
        Returns:
            相似物料列表，按相似度降序排列
        """
        if self.materials_data.empty or self.vectorizer is None:
            logger.warning("近似物料数据未准备就绪")
            return []
        
        try:
            # 组合输入文本
            input_text = f"{input_material.get('name', '')} {input_material.get('spec', '')} {input_material.get('desc', '')}"
            
            # 分词处理
            words = jieba.cut(input_text)
            processed_input = ' '.join(words)
            
            # 向量化输入文本
            input_vector = self.vectorizer.transform([processed_input])
            
            # 计算相似度
            similarities = cosine_similarity(input_vector, self.material_vectors)[0]
            
            # 获取超过阈值的结果
            similar_indices = np.where(similarities >= threshold)[0]
            
            # 按相似度排序
            sorted_indices = similar_indices[np.argsort(similarities[similar_indices])[::-1]]
            
            # 构造结果
            results = []
            for i, idx in enumerate(sorted_indices[:max_results]):
                material_row = self.materials_data.iloc[idx]
                similarity_score = float(similarities[idx])
                
                result = {
                    'material_code': material_row['material_code'],
                    'material_name': material_row['material_name'],
                    'material_long_desc': material_row['material_long_desc'],
                    'material_category': material_row['material_category'],
                    'specification': material_row['specification'],
                    'model': material_row['model'],
                    'unit': material_row['unit'],
                    'similarity_score': similarity_score,
                    'confidence_percentage': int(similarity_score * 100),
                    'rank': i + 1
                }
                results.append(result)
            
            logger.info(f"找到 {len(results)} 个相似物料 (阈值: {threshold})")
            return results
            
        except Exception as e:
            logger.error(f"查找相似物料失败: {e}")
            return []
    
    def get_material_categories_stats(self) -> Dict[str, int]:
        """获取物料分类统计"""
        if self.materials_data.empty:
            return {}
        
        return self.materials_data['material_category'].value_counts().to_dict()
    
    def search_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """按分类搜索物料"""
        if self.materials_data.empty:
            return []
        
        try:
            filtered_data = self.materials_data[
                self.materials_data['material_category'] == category
            ].head(limit)
            
            results = []
            for _, row in filtered_data.iterrows():
                result = {
                    'material_code': row['material_code'],
                    'material_name': row['material_name'],
                    'material_long_desc': row['material_long_desc'],
                    'material_category': row['material_category'],
                    'specification': row['specification'],
                    'model': row['model'],
                    'unit': row['unit']
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"按分类搜索失败: {e}")
            return []
    
    def validate_threshold(self, threshold: float) -> bool:
        """验证阈值有效性"""
        return 0.0 <= threshold <= 1.0
    
    def get_recommended_threshold(self, sample_size: int = 100) -> Dict[str, float]:
        """获取推荐阈值"""
        if self.materials_data.empty or sample_size <= 0:
            return {'low': 0.2, 'medium': 0.4, 'high': 0.6}
        
        try:
            # 随机采样进行阈值分析
            sample_data = self.materials_data.sample(min(sample_size, len(self.materials_data)))
            
            similarities = []
            for i in range(min(10, len(sample_data))):  # 取少量样本测试
                material_dict = {
                    'name': sample_data.iloc[i]['material_name'],
                    'spec': sample_data.iloc[i]['specification'],
                    'desc': sample_data.iloc[i]['material_long_desc']
                }
                
                # 使用很低的阈值获取所有相似度
                results = self.find_similar_materials(material_dict, threshold=0.0, max_results=20)
                for result in results:
                    if result['similarity_score'] > 0:
                        similarities.append(result['similarity_score'])
            
            if not similarities:
                return {'low': 0.2, 'medium': 0.4, 'high': 0.6}
            
            # 计算推荐阈值
            similarities = np.array(similarities)
            
            return {
                'low': float(np.percentile(similarities, 25)),
                'medium': float(np.percentile(similarities, 50)), 
                'high': float(np.percentile(similarities, 75))
            }
            
        except Exception as e:
            logger.error(f"计算推荐阈值失败: {e}")
            return {'low': 0.2, 'medium': 0.4, 'high': 0.6}

# 测试和示例
if __name__ == "__main__":
    # 测试近似物料匹配器
    import logging
    logging.basicConfig(level=logging.INFO)
    
    matcher = SimilarMaterialMatcher()
    
    # 测试用例1: 疏水器
    test_material_1 = {
        'name': '疏水器',
        'spec': 'DN25 PN1.6',
        'desc': '碳钢疏水器DN25'
    }
    
    print("=== 测试用例1: 疏水器匹配 ===")
    results1 = matcher.find_similar_materials(test_material_1, threshold=0.2, max_results=5)
    for result in results1:
        print(f"相似度: {result['confidence_percentage']}% - {result['material_name']} ({result['material_code']})")
    
    # 测试用例2: 法兰
    test_material_2 = {
        'name': '法兰',
        'spec': 'DN100 PN1.6',
        'desc': '带颈对焊法兰'
    }
    
    print("\n=== 测试用例2: 法兰匹配 ===")
    results2 = matcher.find_similar_materials(test_material_2, threshold=0.3, max_results=5)
    for result in results2:
        print(f"相似度: {result['confidence_percentage']}% - {result['material_name']} ({result['material_code']})")
    
    # 获取推荐阈值
    print("\n=== 推荐阈值 ===")
    thresholds = matcher.get_recommended_threshold()
    print(f"推荐阈值: {thresholds}")
    
    # 分类统计
    print("\n=== 分类统计 (前10) ===")
    categories = matcher.get_material_categories_stats()
    for category, count in list(categories.items())[:10]:
        print(f"{category}: {count} 个物料")