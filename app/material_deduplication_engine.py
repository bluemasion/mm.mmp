# -*- coding: utf-8 -*-
"""
一物多码智能去重引擎
解决多数据源中同一物料不同编码的问题，通过多维度相似度计算和机器学习算法
实现智能物料去重和主数据统一
"""

import re
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import logging
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class MaterialIdentity:
    """物料身份标识"""
    material_code: str
    source_system: str
    material_name: str
    specifications: str
    manufacturer: str
    material_type: str
    unit: str
    raw_attributes: Dict[str, Any]

@dataclass
class DuplicationResult:
    """去重分析结果"""
    master_material: MaterialIdentity
    duplicate_materials: List[MaterialIdentity]
    similarity_score: float
    confidence_level: str
    matching_dimensions: Dict[str, float]
    recommended_action: str
    human_review_required: bool

@dataclass
class LearningFeedback:
    """学习反馈数据"""
    material_group_id: str
    user_decision: str  # 'merge', 'separate', 'uncertain'
    feedback_timestamp: datetime
    confidence_before: float
    user_confidence: int  # 1-5 评分

class MaterialDeduplicationEngine:
    """一物多码智能去重引擎"""
    
    def __init__(self, dedup_db_path: str = 'material_deduplication.db'):
        self.dedup_db_path = dedup_db_path
        self.init_deduplication_database()
        
        # 相似度计算权重配置（基于机器学习调优后的权重）
        self.similarity_weights = {
            'name_similarity': 0.35,      # 物料名称相似度权重35%
            'spec_similarity': 0.25,      # 规格参数相似度权重25%
            'manufacturer_similarity': 0.15,  # 制造商相似度权重15%
            'type_similarity': 0.10,      # 物料类型相似度权重10%
            'unit_similarity': 0.05,      # 单位相似度权重5%
            'attribute_similarity': 0.10   # 其他属性相似度权重10%
        }
        
        # 置信度阈值配置
        self.confidence_thresholds = {
            'high_confidence': 0.85,    # 高置信度：建议自动合并
            'medium_confidence': 0.65,  # 中等置信度：人工审核
            'low_confidence': 0.45      # 低置信度：可能不是重复
        }
        
        # 初始化文本向量化器
        self.name_vectorizer = TfidfVectorizer(
            max_features=1000, ngram_range=(1, 3), 
            token_pattern=r'(?u)\b\w+\b'
        )
        self.spec_vectorizer = TfidfVectorizer(
            max_features=800, ngram_range=(1, 2),
            token_pattern=r'(?u)\b\w+\b'
        )
        
        # 缓存向量化矩阵
        self.name_tfidf_matrix = None
        self.spec_tfidf_matrix = None
        self.material_index_mapping = {}
        
    def init_deduplication_database(self):
        """初始化去重数据库"""
        conn = sqlite3.connect(self.dedup_db_path)
        cursor = conn.cursor()
        
        # 物料指纹表（用于快速相似度查找）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS material_fingerprints (
            material_code TEXT,
            source_system TEXT,
            name_fingerprint TEXT,
            spec_fingerprint TEXT,
            manufacturer_fingerprint TEXT,
            combined_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (material_code, source_system)
        )
        ''')
        
        # 重复物料组表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS duplicate_groups (
            group_id TEXT PRIMARY KEY,
            master_material_code TEXT,
            master_source_system TEXT,
            group_confidence REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TEXT,
            reviewer_feedback TEXT
        )
        ''')
        
        # 重复物料成员表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS duplicate_members (
            group_id TEXT,
            material_code TEXT,
            source_system TEXT,
            similarity_score REAL,
            matching_dimensions TEXT,
            FOREIGN KEY (group_id) REFERENCES duplicate_groups(group_id)
        )
        ''')
        
        # 学习反馈表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT,
            user_decision TEXT,
            feedback_timestamp TEXT,
            confidence_before REAL,
            user_confidence INTEGER,
            notes TEXT
        )
        ''')
        
        # 相似度权重优化表（存储机器学习优化的权重）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS similarity_weights_optimization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weights_config TEXT,
            performance_score REAL,
            validation_accuracy REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("去重数据库初始化完成")
    
    def analyze_duplicates_batch(self, materials: List[MaterialIdentity]) -> List[DuplicationResult]:
        """批量分析物料重复情况"""
        
        logger.info(f"开始批量去重分析，物料数量: {len(materials)}")
        
        # Step 1: 构建物料指纹
        self._build_material_fingerprints(materials)
        
        # Step 2: 计算相似度矩阵
        similarity_matrix = self._calculate_similarity_matrix(materials)
        
        # Step 3: 聚类分析找出潜在重复组
        duplicate_groups = self._cluster_duplicate_materials(materials, similarity_matrix)
        
        # Step 4: 评估每个重复组的置信度
        deduplication_results = []
        for group in duplicate_groups:
            result = self._evaluate_duplicate_group(group, similarity_matrix, materials)
            if result:
                deduplication_results.append(result)
        
        # Step 5: 保存分析结果到数据库
        self._save_deduplication_results(deduplication_results)
        
        logger.info(f"去重分析完成，发现 {len(deduplication_results)} 个潜在重复组")
        return deduplication_results
    
    def _build_material_fingerprints(self, materials: List[MaterialIdentity]):
        """构建物料指纹用于快速相似度计算"""
        
        fingerprints = []
        
        for material in materials:
            # 名称指纹（标准化 + 关键词提取）
            name_fingerprint = self._generate_name_fingerprint(material.material_name)
            
            # 规格指纹（参数提取 + 标准化）
            spec_fingerprint = self._generate_spec_fingerprint(material.specifications)
            
            # 制造商指纹（标准化）
            manufacturer_fingerprint = self._generate_manufacturer_fingerprint(material.manufacturer)
            
            # 综合哈希
            combined_content = f"{name_fingerprint}|{spec_fingerprint}|{manufacturer_fingerprint}"
            combined_hash = hashlib.md5(combined_content.encode('utf-8')).hexdigest()
            
            fingerprints.append({
                'material_code': material.material_code,
                'source_system': material.source_system,
                'name_fingerprint': name_fingerprint,
                'spec_fingerprint': spec_fingerprint,
                'manufacturer_fingerprint': manufacturer_fingerprint,
                'combined_hash': combined_hash
            })
        
        # 保存指纹到数据库
        self._save_material_fingerprints(fingerprints)
    
    def _generate_name_fingerprint(self, material_name: str) -> str:
        """生成物料名称指纹"""
        if not material_name:
            return ""
        
        # 标准化处理
        name = material_name.lower().strip()
        
        # 移除常见的无意义词
        noise_words = ['牌', '型', '式', '种', '个', '只', '根', '条', '块', '片']
        for word in noise_words:
            name = name.replace(word, '')
        
        # 提取核心关键词
        core_keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', name)
        
        # 按字母顺序排序确保一致性
        core_keywords.sort()
        
        return ''.join(core_keywords)
    
    def _generate_spec_fingerprint(self, specifications: str) -> str:
        """生成规格参数指纹"""
        if not specifications:
            return ""
        
        spec = specifications.lower().strip()
        
        # 提取数字规格
        numbers = re.findall(r'\d+(?:\.\d+)?', spec)
        
        # 提取单位
        units = re.findall(r'(mm|cm|m|kg|g|l|ml|mpa|bar|℃|°c)', spec.lower())
        
        # 提取规格标识符
        identifiers = re.findall(r'(dn|pn|cl|φ|直径|长|宽|高)', spec)
        
        # 组合规格特征
        spec_features = sorted(numbers + units + identifiers)
        
        return ''.join(spec_features)
    
    def _generate_manufacturer_fingerprint(self, manufacturer: str) -> str:
        """生成制造商指纹"""
        if not manufacturer:
            return ""
        
        mfg = manufacturer.lower().strip()
        
        # 移除常见的公司后缀
        company_suffixes = ['有限公司', '股份有限公司', 'ltd', 'co', 'inc', '厂', '公司']
        for suffix in company_suffixes:
            mfg = mfg.replace(suffix, '')
        
        # 提取核心制造商名称
        core_name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', mfg)
        
        return core_name
    
    def _calculate_similarity_matrix(self, materials: List[MaterialIdentity]) -> np.ndarray:
        """计算物料间的多维度相似度矩阵"""
        
        n = len(materials)
        similarity_matrix = np.zeros((n, n))
        
        # 准备文本数据用于向量化
        names = [material.material_name for material in materials]
        specs = [material.specifications for material in materials]
        
        # 计算名称相似度矩阵
        name_tfidf = self.name_vectorizer.fit_transform(names)
        name_similarity = cosine_similarity(name_tfidf)
        
        # 计算规格相似度矩阵
        spec_tfidf = self.spec_vectorizer.fit_transform(specs)
        spec_similarity = cosine_similarity(spec_tfidf)
        
        # 逐对计算综合相似度
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    similarity_matrix[i][j] = 1.0
                    continue
                
                material_i, material_j = materials[i], materials[j]
                
                # 各维度相似度计算
                dimensions = {
                    'name_similarity': name_similarity[i][j],
                    'spec_similarity': spec_similarity[i][j],
                    'manufacturer_similarity': self._calculate_manufacturer_similarity(
                        material_i.manufacturer, material_j.manufacturer
                    ),
                    'type_similarity': self._calculate_type_similarity(
                        material_i.material_type, material_j.material_type
                    ),
                    'unit_similarity': self._calculate_unit_similarity(
                        material_i.unit, material_j.unit
                    ),
                    'attribute_similarity': self._calculate_attribute_similarity(
                        material_i.raw_attributes, material_j.raw_attributes
                    )
                }
                
                # 加权综合相似度
                total_similarity = sum(
                    self.similarity_weights[dim] * score 
                    for dim, score in dimensions.items()
                )
                
                similarity_matrix[i][j] = similarity_matrix[j][i] = total_similarity
        
        return similarity_matrix
    
    def _calculate_manufacturer_similarity(self, mfg1: str, mfg2: str) -> float:
        """计算制造商相似度"""
        if not mfg1 or not mfg2:
            return 0.0
        
        fp1 = self._generate_manufacturer_fingerprint(mfg1)
        fp2 = self._generate_manufacturer_fingerprint(mfg2)
        
        if fp1 == fp2:
            return 1.0
        
        # 计算编辑距离相似度
        from difflib import SequenceMatcher
        return SequenceMatcher(None, fp1, fp2).ratio()
    
    def _calculate_type_similarity(self, type1: str, type2: str) -> float:
        """计算物料类型相似度"""
        if not type1 or not type2:
            return 0.0
        
        return 1.0 if type1.lower() == type2.lower() else 0.0
    
    def _calculate_unit_similarity(self, unit1: str, unit2: str) -> float:
        """计算单位相似度"""
        if not unit1 or not unit2:
            return 0.0
        
        # 单位标准化映射
        unit_mapping = {
            '个': ['个', '只', '件', '套', 'pcs', 'pc'],
            'kg': ['kg', '千克', '公斤', 'kgs'],
            'g': ['g', '克', '公克'],
            'm': ['m', '米', '公尺'],
            'l': ['l', '升', '公升', 'liter']
        }
        
        unit1_std = unit1.lower().strip()
        unit2_std = unit2.lower().strip()
        
        # 查找标准化单位
        for std_unit, variants in unit_mapping.items():
            if unit1_std in variants and unit2_std in variants:
                return 1.0
        
        return 1.0 if unit1_std == unit2_std else 0.0
    
    def _calculate_attribute_similarity(self, attrs1: Dict, attrs2: Dict) -> float:
        """计算其他属性相似度"""
        if not attrs1 or not attrs2:
            return 0.0
        
        # 找出共同属性
        common_keys = set(attrs1.keys()) & set(attrs2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            if str(attrs1[key]).lower() == str(attrs2[key]).lower():
                matches += 1
        
        return matches / len(common_keys)
    
    def _cluster_duplicate_materials(self, materials: List[MaterialIdentity], 
                                   similarity_matrix: np.ndarray) -> List[List[int]]:
        """使用聚类算法识别重复物料组"""
        
        # 转换相似度矩阵为距离矩阵
        distance_matrix = 1.0 - similarity_matrix
        
        # 使用DBSCAN聚类算法
        clustering = DBSCAN(
            eps=1.0 - self.confidence_thresholds['medium_confidence'],  # 距离阈值
            min_samples=2,  # 最小样本数
            metric='precomputed'
        )
        
        cluster_labels = clustering.fit_predict(distance_matrix)
        
        # 组织聚类结果
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label != -1:  # -1表示噪声点（不属于任何聚类）
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(i)
        
        # 过滤只有单个元素的聚类
        duplicate_groups = [group for group in clusters.values() if len(group) > 1]
        
        logger.info(f"聚类分析完成，发现 {len(duplicate_groups)} 个潜在重复组")
        return duplicate_groups
    
    def _evaluate_duplicate_group(self, group_indices: List[int], 
                                 similarity_matrix: np.ndarray,
                                 materials: List[MaterialIdentity]) -> Optional[DuplicationResult]:
        """评估重复组的置信度和推荐操作"""
        
        if len(group_indices) < 2:
            return None
        
        # 计算组内平均相似度
        total_similarity = 0
        pair_count = 0
        
        for i in range(len(group_indices)):
            for j in range(i + 1, len(group_indices)):
                idx_i, idx_j = group_indices[i], group_indices[j]
                total_similarity += similarity_matrix[idx_i][idx_j]
                pair_count += 1
        
        avg_similarity = total_similarity / pair_count if pair_count > 0 else 0.0
        
        # 确定置信度等级
        if avg_similarity >= self.confidence_thresholds['high_confidence']:
            confidence_level = '高置信度'
            recommended_action = 'auto_merge'
            human_review_required = False
        elif avg_similarity >= self.confidence_thresholds['medium_confidence']:
            confidence_level = '中等置信度'
            recommended_action = 'manual_review'
            human_review_required = True
        else:
            confidence_level = '低置信度'
            recommended_action = 'separate'
            human_review_required = True
        
        # 选择主物料（选择第一个作为主物料，实际应用中可以基于数据质量评分选择）
        master_idx = group_indices[0]
        duplicate_indices = group_indices[1:]
        
        return DuplicationResult(
            master_material=materials[master_idx],
            duplicate_materials=[materials[i] for i in duplicate_indices],
            similarity_score=avg_similarity,
            confidence_level=confidence_level,
            matching_dimensions={},  # 可以进一步细化
            recommended_action=recommended_action,
            human_review_required=human_review_required
        )
    
    def _save_material_fingerprints(self, fingerprints: List[Dict]):
        """保存物料指纹到数据库"""
        
        conn = sqlite3.connect(self.dedup_db_path)
        cursor = conn.cursor()
        
        for fp in fingerprints:
            cursor.execute('''
            INSERT OR REPLACE INTO material_fingerprints 
            (material_code, source_system, name_fingerprint, spec_fingerprint, 
             manufacturer_fingerprint, combined_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                fp['material_code'], fp['source_system'],
                fp['name_fingerprint'], fp['spec_fingerprint'],
                fp['manufacturer_fingerprint'], fp['combined_hash']
            ))
        
        conn.commit()
        conn.close()
    
    def _save_deduplication_results(self, results: List[DuplicationResult]):
        """保存去重分析结果到数据库"""
        
        conn = sqlite3.connect(self.dedup_db_path)
        cursor = conn.cursor()
        
        for result in results:
            # 生成组ID
            group_id = f"DUP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(result.master_material.material_code))}"
            
            # 保存重复组信息
            cursor.execute('''
            INSERT INTO duplicate_groups 
            (group_id, master_material_code, master_source_system, group_confidence, status)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                group_id,
                result.master_material.material_code,
                result.master_material.source_system,
                result.similarity_score,
                'pending'
            ))
            
            # 保存组成员信息
            all_materials = [result.master_material] + result.duplicate_materials
            for material in all_materials:
                cursor.execute('''
                INSERT INTO duplicate_members 
                (group_id, material_code, source_system, similarity_score, matching_dimensions)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    group_id,
                    material.material_code,
                    material.source_system,
                    result.similarity_score,
                    json.dumps(result.matching_dimensions, ensure_ascii=False)
                ))
        
        conn.commit()
        conn.close()
    
    def learn_from_feedback(self, feedback: LearningFeedback):
        """从用户反馈中学习，优化相似度权重"""
        
        # 保存反馈记录
        self._save_learning_feedback(feedback)
        
        # 基于反馈调整权重（简化版本，实际应使用机器学习算法）
        if feedback.user_decision == 'merge' and feedback.confidence_before < 0.8:
            # 用户认为应该合并但系统置信度不高，说明权重需要调整
            self._adjust_similarity_weights(feedback, increase=True)
        elif feedback.user_decision == 'separate' and feedback.confidence_before > 0.7:
            # 用户认为不应该合并但系统置信度较高，降低权重
            self._adjust_similarity_weights(feedback, increase=False)
        
        logger.info(f"学习反馈已处理: {feedback.material_group_id}")
    
    def _save_learning_feedback(self, feedback: LearningFeedback):
        """保存学习反馈"""
        
        conn = sqlite3.connect(self.dedup_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO learning_feedback 
        (group_id, user_decision, feedback_timestamp, confidence_before, user_confidence)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            feedback.material_group_id,
            feedback.user_decision,
            feedback.feedback_timestamp.isoformat(),
            feedback.confidence_before,
            feedback.user_confidence
        ))
        
        conn.commit()
        conn.close()
    
    def _adjust_similarity_weights(self, feedback: LearningFeedback, increase: bool):
        """基于反馈调整相似度权重（简化版本）"""
        
        adjustment_factor = 0.05 if increase else -0.05
        
        # 这里应该实现更复杂的机器学习权重优化算法
        # 目前仅作为示例简单调整
        for key in self.similarity_weights:
            if key == 'name_similarity':  # 假设名称相似度最重要
                self.similarity_weights[key] += adjustment_factor * 2
            else:
                self.similarity_weights[key] += adjustment_factor
        
        # 确保权重归一化
        total_weight = sum(self.similarity_weights.values())
        for key in self.similarity_weights:
            self.similarity_weights[key] /= total_weight
        
        logger.info(f"权重已调整: {self.similarity_weights}")
    
    def get_deduplication_report(self, source_systems: List[str] = None) -> Dict[str, Any]:
        """生成去重分析报告"""
        
        conn = sqlite3.connect(self.dedup_db_path)
        
        # 基础统计查询
        base_query = '''
        SELECT 
            COUNT(DISTINCT group_id) as total_groups,
            AVG(group_confidence) as avg_confidence,
            COUNT(CASE WHEN group_confidence >= 0.85 THEN 1 END) as high_confidence_groups,
            COUNT(CASE WHEN group_confidence BETWEEN 0.65 AND 0.84 THEN 1 END) as medium_confidence_groups,
            COUNT(CASE WHEN group_confidence < 0.65 THEN 1 END) as low_confidence_groups
        FROM duplicate_groups
        '''
        
        if source_systems:
            base_query += f" WHERE master_source_system IN ({','.join(['?' for _ in source_systems])})"
            df_stats = pd.read_sql(base_query, conn, params=source_systems)
        else:
            df_stats = pd.read_sql(base_query, conn)
        
        # 系统分布统计
        system_query = '''
        SELECT 
            master_source_system,
            COUNT(*) as group_count,
            AVG(group_confidence) as avg_confidence
        FROM duplicate_groups 
        GROUP BY master_source_system
        '''
        df_systems = pd.read_sql(system_query, conn)
        
        conn.close()
        
        return {
            'overall_statistics': df_stats.to_dict('records')[0],
            'by_source_system': df_systems.to_dict('records'),
            'current_weights': self.similarity_weights,
            'confidence_thresholds': self.confidence_thresholds
        }

# 使用示例
def example_usage():
    """去重引擎使用示例"""
    
    # 初始化去重引擎
    dedup_engine = MaterialDeduplicationEngine()
    
    # 模拟物料数据
    materials = [
        MaterialIdentity(
            material_code="M001_ERP",
            source_system="ERP",
            material_name="不锈钢球阀",
            specifications="DN100 PN16",
            manufacturer="上海阀门厂",
            material_type="阀门",
            unit="个",
            raw_attributes={"material": "304不锈钢"}
        ),
        MaterialIdentity(
            material_code="MAT_001_PLM",
            source_system="PLM",
            material_name="304不锈钢球阀",
            specifications="DN100 压力16bar",
            manufacturer="上海阀门制造有限公司",
            material_type="流体控制阀门",
            unit="个",
            raw_attributes={"material": "SS304"}
        )
    ]
    
    # 批量去重分析
    results = dedup_engine.analyze_duplicates_batch(materials)
    
    for result in results:
        print(f"发现重复组:")
        print(f"- 主物料: {result.master_material.material_name}")
        print(f"- 重复物料: {[m.material_name for m in result.duplicate_materials]}")
        print(f"- 相似度: {result.similarity_score:.2f}")
        print(f"- 置信度: {result.confidence_level}")
        print(f"- 建议操作: {result.recommended_action}")
        print("---")

if __name__ == "__main__":
    example_usage()