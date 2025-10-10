# app/advanced_matcher.py
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import logging
from typing import Dict, List, Tuple, Optional, Any

class AdvancedMaterialMatcher:
    """增强版物料匹配器，支持属性级匹配和配置化规则"""
    
    def __init__(self, df_master: pd.DataFrame, rules: Dict, match_config: Dict = None):
        """
        初始化匹配器
        
        Args:
            df_master: 主数据DataFrame
            rules: 匹配规则配置
            match_config: 高级匹配配置
        """
        if df_master.empty:
            raise ValueError("主数据 DataFrame 不能为空")
            
        self.rules = rules
        self.master_fields = rules['master_fields']
        self.new_item_fields = rules['new_item_fields']
        
        # 默认匹配配置
        self.match_config = match_config or {
            'similarity_threshold': 0.3,
            'field_weights': {
                'exact_match': 1.0,
                'fuzzy_match': 0.8,
                'description_match': 0.6
            },
            'description_template': '{name} {spec}',
            'top_n_default': 5
        }
        
        # 预处理主数据
        self.df_master = self._preprocess_master_data(df_master.copy())
        
        # 初始化向量化器
        self.vectorizers = {}
        self.tfidf_matrices = {}
        
        # 为每个模糊匹配字段创建向量化器
        for field in self.master_fields['fuzzy']:
            if field in self.df_master.columns:
                self._initialize_field_vectorizer(field)
        
        # 创建描述字段的向量化器
        self._create_description_field()
        
        logging.info("AdvancedMaterialMatcher 初始化完成")

    def _preprocess_master_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """预处理主数据"""
        # 检查必需字段
        all_fields = self.master_fields['exact'] + self.master_fields['fuzzy']
        for field in all_fields:
            if field not in df.columns:
                raise ValueError(f"主数据中缺少字段: {field}")
            df[field] = df[field].fillna('').astype(str)
        
        # 添加ID字段（如果没有）
        if 'id' not in df.columns:
            df['id'] = range(len(df))
        
        return df

    def _initialize_field_vectorizer(self, field: str):
        """为指定字段初始化向量化器"""
        try:
            vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words=None,  # 中文不使用英文停用词
                lowercase=True,
                token_pattern=r'(?u)\b\w+\b'
            )
            
            field_texts = self.df_master[field].astype(str).tolist()
            tfidf_matrix = vectorizer.fit_transform(field_texts)
            
            self.vectorizers[field] = vectorizer
            self.tfidf_matrices[field] = tfidf_matrix
            
            logging.info(f"字段 {field} 向量化完成，特征数: {len(vectorizer.vocabulary_)}")
            
        except Exception as e:
            logging.warning(f"字段 {field} 向量化失败: {e}")

    def _create_description_field(self):
        """创建描述字段用于整体匹配"""
        template = self.match_config.get('description_template', '{name} {spec}')
        
        # 构建描述文本
        descriptions = []
        for _, row in self.df_master.iterrows():
            desc_parts = []
            for field in self.master_fields['fuzzy']:
                if field in row and pd.notna(row[field]):
                    desc_parts.append(str(row[field]))
            descriptions.append(' '.join(desc_parts))
        
        self.df_master['_description'] = descriptions
        
        # 为描述字段创建向量化器
        if descriptions and any(desc.strip() for desc in descriptions):
            self._initialize_field_vectorizer('_description')

    def find_matches_advanced(self, new_item: Dict[str, Any], 
                            category_id: str = None,
                            top_n: int = None) -> pd.DataFrame:
        """
        高级匹配算法，支持属性级匹配
        
        Args:
            new_item: 新物料数据
            category_id: 分类ID（可选）
            top_n: 返回结果数量
            
        Returns:
            匹配结果DataFrame，包含相似度得分
        """
        if top_n is None:
            top_n = self.match_config.get('top_n_default', 5)
        
        # 1. 精确匹配过滤
        candidates = self._apply_exact_filters(new_item)
        
        if candidates.empty:
            logging.info("精确匹配过滤后无候选项")
            return pd.DataFrame()
        
        # 2. 属性级模糊匹配
        similarity_scores = self._calculate_attribute_similarities(new_item, candidates)
        
        # 3. 组合相似度得分
        final_scores = self._combine_similarity_scores(similarity_scores)
        
        # 4. 应用阈值过滤
        threshold = self.match_config.get('similarity_threshold', 0.3)
        valid_indices = [i for i, score in enumerate(final_scores) if score >= threshold]
        
        if not valid_indices:
            logging.info(f"应用阈值 {threshold} 后无匹配结果")
            return pd.DataFrame()
        
        # 5. 构建结果
        results = candidates.iloc[valid_indices].copy()
        results['similarity'] = [final_scores[i] for i in valid_indices]
        results['match_details'] = [
            self._create_match_details(similarity_scores, i) 
            for i in valid_indices
        ]
        
        # 6. 排序并返回Top-N
        results = results.sort_values('similarity', ascending=False).head(top_n)
        
        logging.info(f"返回 {len(results)} 个匹配结果")
        return results

    def _apply_exact_filters(self, new_item: Dict[str, Any]) -> pd.DataFrame:
        """应用精确匹配过滤器"""
        candidates = self.df_master.copy()
        
        for i, master_field in enumerate(self.master_fields['exact']):
            new_field = self.new_item_fields['exact'][i]
            
            if new_field in new_item:
                new_value = str(new_item[new_field]).strip()
                if new_value:  # 只有非空值才进行过滤
                    candidates = candidates[
                        candidates[master_field].astype(str).str.strip() == new_value
                    ]
        
        logging.info(f"精确匹配过滤后剩余 {len(candidates)} 个候选项")
        return candidates

    def _calculate_attribute_similarities(self, new_item: Dict[str, Any], 
                                        candidates: pd.DataFrame) -> Dict[str, np.ndarray]:
        """计算各属性的相似度"""
        similarity_scores = {}
        
        # 对每个模糊匹配字段计算相似度
        for i, master_field in enumerate(self.master_fields['fuzzy']):
            new_field = self.new_item_fields['fuzzy'][i]
            
            if new_field in new_item and master_field in self.vectorizers:
                new_text = str(new_item[new_field])
                similarities = self._calculate_field_similarity(
                    new_text, master_field, candidates.index
                )
                similarity_scores[master_field] = similarities
        
        # 计算整体描述相似度
        if '_description' in self.vectorizers:
            new_desc_parts = []
            for field in self.new_item_fields['fuzzy']:
                if field in new_item:
                    new_desc_parts.append(str(new_item[field]))
            
            new_description = ' '.join(new_desc_parts)
            desc_similarities = self._calculate_field_similarity(
                new_description, '_description', candidates.index
            )
            similarity_scores['_description'] = desc_similarities
        
        return similarity_scores

    def _calculate_field_similarity(self, new_text: str, field: str, 
                                  candidate_indices: pd.Index) -> np.ndarray:
        """计算单个字段的相似度"""
        if field not in self.vectorizers:
            return np.zeros(len(candidate_indices))
        
        try:
            # 向量化新文本
            new_vector = self.vectorizers[field].transform([new_text])
            
            # 获取候选项的向量
            candidate_vectors = self.tfidf_matrices[field][candidate_indices]
            
            # 计算余弦相似度
            similarities = cosine_similarity(new_vector, candidate_vectors)
            return similarities.flatten()
            
        except Exception as e:
            logging.warning(f"计算字段 {field} 相似度失败: {e}")
            return np.zeros(len(candidate_indices))

    def _combine_similarity_scores(self, similarity_scores: Dict[str, np.ndarray]) -> List[float]:
        """组合各属性的相似度得分"""
        if not similarity_scores:
            return []
        
        # 获取权重配置
        field_weights = self.match_config.get('field_weights', {})
        
        # 初始化组合得分
        num_candidates = len(list(similarity_scores.values())[0])
        combined_scores = np.zeros(num_candidates)
        total_weight = 0
        
        # 加权组合各字段得分
        for field, scores in similarity_scores.items():
            if field == '_description':
                weight = field_weights.get('description_match', 0.6)
            elif field in self.master_fields['fuzzy']:
                weight = field_weights.get('fuzzy_match', 0.8)
            else:
                weight = 0.5  # 默认权重
            
            combined_scores += scores * weight
            total_weight += weight
        
        # 归一化
        if total_weight > 0:
            combined_scores /= total_weight
        
        return combined_scores.tolist()

    def _create_match_details(self, similarity_scores: Dict[str, np.ndarray], 
                            index: int) -> Dict[str, float]:
        """创建匹配详情"""
        details = {}
        for field, scores in similarity_scores.items():
            if index < len(scores):
                details[f"{field}_similarity"] = round(float(scores[index]), 4)
        return details

    def find_matches(self, new_item_series, top_n: int = 3) -> pd.DataFrame:
        """
        兼容原有API的匹配方法
        
        Args:
            new_item_series: 新物料数据（Series或Dict）
            top_n: 返回结果数量
            
        Returns:
            匹配结果DataFrame
        """
        # 转换为字典格式
        if hasattr(new_item_series, 'to_dict'):
            new_item = new_item_series.to_dict()
        else:
            new_item = dict(new_item_series)
        
        # 使用高级匹配方法
        return self.find_matches_advanced(new_item, top_n=top_n)

    def batch_find_matches(self, new_items_df: pd.DataFrame, 
                          top_n: int = 3) -> List[pd.DataFrame]:
        """
        批量匹配
        
        Args:
            new_items_df: 新物料数据DataFrame
            top_n: 每个物料返回的匹配结果数量
            
        Returns:
            匹配结果列表
        """
        results = []
        
        for index, row in new_items_df.iterrows():
            item_matches = self.find_matches_advanced(row.to_dict(), top_n=top_n)
            results.append(item_matches)
            
            if (index + 1) % 100 == 0:
                logging.info(f"已处理 {index + 1} 个物料")
        
        logging.info(f"批量匹配完成，共处理 {len(results)} 个物料")
        return results

    def get_match_statistics(self) -> Dict[str, Any]:
        """获取匹配统计信息"""
        stats = {
            'master_data_count': len(self.df_master),
            'exact_fields': self.master_fields['exact'],
            'fuzzy_fields': self.master_fields['fuzzy'],
            'vectorized_fields': list(self.vectorizers.keys()),
            'similarity_threshold': self.match_config.get('similarity_threshold'),
            'field_weights': self.match_config.get('field_weights')
        }
        
        # 添加向量化统计
        for field, vectorizer in self.vectorizers.items():
            stats[f'{field}_features'] = len(vectorizer.vocabulary_)
        
        return stats

# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    test_master = pd.DataFrame({
        '商品操作码': ['M001', 'M002', 'M003'],
        '产品名称': ['阿莫西林胶囊', '头孢拉定胶囊', '阿莫西林克拉维酸钾片'],
        '产品规格': ['0.25g*24粒', '0.25g*12粒', '0.5g*14片'],
        '生产厂家': ['华北制药', '石药集团', '华北制药'],
        '医保代码': ['A001', 'A002', 'A003']
    })
    
    test_rules = {
        'master_fields': {
            'id': '商品操作码',
            'exact': ['生产厂家', '医保代码'],
            'fuzzy': ['产品名称', '产品规格']
        },
        'new_item_fields': {
            'id': '资产代码',
            'exact': ['生产厂家名称', '医保码'],
            'fuzzy': ['资产名称', '规格型号']
        }
    }
    
    # 创建匹配器
    matcher = AdvancedMaterialMatcher(test_master, test_rules)
    
    # 测试匹配
    test_item = {
        '资产名称': '阿莫西林胶囊',
        '规格型号': '0.25g*24粒',
        '生产厂家名称': '华北制药',
        '医保码': 'A001'
    }
    
    results = matcher.find_matches_advanced(test_item)
    print("匹配结果:")
    print(results[['产品名称', '产品规格', 'similarity', 'match_details']])
    
    print("\n匹配统计:")
    print(matcher.get_match_statistics())
