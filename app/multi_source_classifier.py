# -*- coding: utf-8 -*-
"""
多数据源智能分类系统
整合数据源识别、行业适配器和动态模板生成，实现通用的智能分类框架
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
from pathlib import Path

# 导入各个模块
from data_source_recognizer import DataSourcePatternRecognizer, DataSourceSchema
from manufacturing_adapter import ManufacturingAdapter, ManufacturingFeature
from medical_adapter import MedicalAdapter, MedicalFeature
from dynamic_template_generator import DynamicTemplateGenerator, CategoryTemplate

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    """分类结果定义"""
    material_id: str                    # 物料ID
    source_confidence: float            # 数据源识别置信度
    industry_type: str                  # 识别的行业类型
    template_id: str                    # 使用的模板ID
    predicted_category: Dict[str, str]  # 预测分类
    confidence_score: float             # 分类置信度
    feature_vector: Dict[str, Any]      # 特征向量
    matching_details: Dict[str, Any]    # 匹配详情
    alternative_categories: List[Dict]  # 备选分类
    processing_time: float              # 处理时间

@dataclass
class BatchProcessingResult:
    """批处理结果定义"""
    total_processed: int                # 处理总数
    successful_classifications: int     # 成功分类数
    failed_classifications: int         # 失败分类数
    average_confidence: float           # 平均置信度
    processing_time: float              # 总处理时间
    industry_distribution: Dict[str, int]  # 行业分布
    results: List[ClassificationResult] # 详细结果
    error_summary: Dict[str, Any]       # 错误汇总

class MultiSourceIntelligentClassifier:
    """多数据源智能分类系统"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化多数据源智能分类系统
        
        Args:
            config: 系统配置参数
        """
        self.config = config or self._get_default_config()
        
        # 初始化核心组件
        self.recognizer = DataSourcePatternRecognizer()
        self.manufacturing_adapter = ManufacturingAdapter()
        self.medical_adapter = MedicalAdapter()
        self.template_generator = DynamicTemplateGenerator(
            db_path=self.config.get('template_db_path', 'templates.db')
        )
        
        # 缓存管理
        self.schema_cache = {}
        self.template_cache = {}
        
        logger.info("多数据源智能分类系统初始化完成")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'template_db_path': 'templates.db',
            'min_confidence_threshold': 0.6,
            'enable_auto_template_generation': True,
            'enable_performance_optimization': True,
            'batch_size': 100,
            'parallel_processing': False,
            'fallback_to_generic': True,
            'cache_schemas': True,
            'log_level': 'INFO'
        }
    
    def classify_single_record(self, 
                             data_record: Dict[str, Any],
                             source_metadata: Dict[str, Any] = None) -> ClassificationResult:
        """
        对单条记录进行智能分类
        
        Args:
            data_record: 数据记录
            source_metadata: 可选的源数据元信息
            
        Returns:
            ClassificationResult: 分类结果
        """
        import time
        start_time = time.time()
        
        try:
            # 1. 数据源模式识别
            schema = self._get_or_recognize_schema([data_record], source_metadata)
            
            # 2. 获取或生成分类模板
            template = self._get_or_generate_template(schema, [data_record])
            
            # 3. 行业特征提取
            feature = self._extract_industry_features(data_record, schema.industry_type)
            
            # 4. 执行智能分类
            classification_result = self._perform_classification(
                feature, template, schema
            )
            
            # 5. 构建最终结果
            result = ClassificationResult(
                material_id=data_record.get('id', f"auto_{int(time.time()*1000)}"),
                source_confidence=schema.confidence_score,
                industry_type=schema.industry_type,
                template_id=template.template_id,
                predicted_category=classification_result['predicted_category'],
                confidence_score=classification_result['confidence_score'],
                feature_vector=classification_result['feature_vector'],
                matching_details=classification_result['matching_details'],
                alternative_categories=classification_result['alternative_categories'],
                processing_time=time.time() - start_time
            )
            
            logger.info(f"单记录分类完成 - 行业: {schema.industry_type}, 置信度: {result.confidence_score:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"单记录分类失败: {e}")
            # 返回失败结果
            return ClassificationResult(
                material_id=data_record.get('id', 'unknown'),
                source_confidence=0.0,
                industry_type='unknown',
                template_id='none',
                predicted_category={'level1': '分类失败', 'level2': '处理异常'},
                confidence_score=0.0,
                feature_vector={},
                matching_details={'error': str(e)},
                alternative_categories=[],
                processing_time=time.time() - start_time
            )
    
    def classify_batch_records(self, 
                             data_records: List[Dict[str, Any]],
                             source_metadata: Dict[str, Any] = None) -> BatchProcessingResult:
        """
        批量记录智能分类
        
        Args:
            data_records: 数据记录列表
            source_metadata: 可选的源数据元信息
            
        Returns:
            BatchProcessingResult: 批处理结果
        """
        import time
        start_time = time.time()
        
        logger.info(f"开始批量分类处理，记录数: {len(data_records)}")
        
        try:
            # 1. 数据源模式识别（使用样本）
            sample_size = min(100, len(data_records))
            schema = self._get_or_recognize_schema(
                data_records[:sample_size], source_metadata
            )
            
            # 2. 获取或生成分类模板
            template = self._get_or_generate_template(schema, data_records[:sample_size])
            
            # 3. 批量处理
            results = []
            successful_count = 0
            failed_count = 0
            confidence_scores = []
            industry_distribution = {}
            
            batch_size = self.config.get('batch_size', 100)
            
            for i in range(0, len(data_records), batch_size):
                batch = data_records[i:i + batch_size]
                logger.info(f"处理批次 {i//batch_size + 1}, 记录数: {len(batch)}")
                
                for record in batch:
                    try:
                        # 特征提取
                        feature = self._extract_industry_features(record, schema.industry_type)
                        
                        # 执行分类
                        classification_result = self._perform_classification(
                            feature, template, schema
                        )
                        
                        # 构建结果
                        result = ClassificationResult(
                            material_id=record.get('id', f"auto_{int(time.time()*1000000) + len(results)}"),
                            source_confidence=schema.confidence_score,
                            industry_type=schema.industry_type,
                            template_id=template.template_id,
                            predicted_category=classification_result['predicted_category'],
                            confidence_score=classification_result['confidence_score'],
                            feature_vector=classification_result['feature_vector'],
                            matching_details=classification_result['matching_details'],
                            alternative_categories=classification_result['alternative_categories'],
                            processing_time=0.0  # 批处理时不计算单个处理时间
                        )
                        
                        results.append(result)
                        successful_count += 1
                        confidence_scores.append(result.confidence_score)
                        
                        # 统计行业分布
                        industry = result.industry_type
                        industry_distribution[industry] = industry_distribution.get(industry, 0) + 1
                        
                    except Exception as e:
                        logger.error(f"记录分类失败: {e}")
                        failed_count += 1
            
            # 4. 构建批处理结果
            total_time = time.time() - start_time
            batch_result = BatchProcessingResult(
                total_processed=len(data_records),
                successful_classifications=successful_count,
                failed_classifications=failed_count,
                average_confidence=sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
                processing_time=total_time,
                industry_distribution=industry_distribution,
                results=results,
                error_summary={
                    'error_rate': failed_count / len(data_records),
                    'low_confidence_count': len([s for s in confidence_scores if s < 0.7])
                }
            )
            
            logger.info(f"批量分类完成 - 成功: {successful_count}, 失败: {failed_count}, 平均置信度: {batch_result.average_confidence:.3f}")
            return batch_result
            
        except Exception as e:
            logger.error(f"批量分类处理失败: {e}")
            return BatchProcessingResult(
                total_processed=len(data_records),
                successful_classifications=0,
                failed_classifications=len(data_records),
                average_confidence=0.0,
                processing_time=time.time() - start_time,
                industry_distribution={},
                results=[],
                error_summary={'error': str(e)}
            )
    
    def _get_or_recognize_schema(self, 
                                data_sample: List[Dict[str, Any]],
                                source_metadata: Dict[str, Any] = None) -> DataSourceSchema:
        """获取或识别数据源模式"""
        
        # 生成缓存键
        cache_key = self._generate_cache_key(data_sample, source_metadata)
        
        if self.config.get('cache_schemas', True) and cache_key in self.schema_cache:
            logger.debug("使用缓存的数据源模式")
            return self.schema_cache[cache_key]
        
        # 执行模式识别
        schema = self.recognizer.analyze_data_structure(data_sample, source_metadata)
        
        # 缓存结果
        if self.config.get('cache_schemas', True):
            self.schema_cache[cache_key] = schema
        
        return schema
    
    def _get_or_generate_template(self, 
                                schema: DataSourceSchema,
                                sample_data: List[Dict[str, Any]] = None) -> CategoryTemplate:
        """获取或生成分类模板"""
        
        # 首先尝试加载现有模板
        template_id = f"{schema.industry_type}_{schema.source_id}"
        
        if template_id in self.template_cache:
            logger.debug("使用缓存的分类模板")
            return self.template_cache[template_id]
        
        # 尝试从数据库加载
        template = self.template_generator.load_template(template_id)
        
        if template is None and self.config.get('enable_auto_template_generation', True):
            logger.info(f"为行业 {schema.industry_type} 生成新的分类模板")
            
            # 加载现有分类数据（如果需要）
            existing_categories = self._load_existing_categories(schema.industry_type)
            
            # 生成新模板
            template = self.template_generator.generate_template_from_schema(
                schema, existing_categories, sample_data
            )
        
        if template is None:
            raise ValueError(f"无法获取或生成模板: {template_id}")
        
        # 缓存模板
        self.template_cache[template_id] = template
        
        return template
    
    def _extract_industry_features(self, 
                                 data_record: Dict[str, Any],
                                 industry_type: str) -> Any:
        """提取行业特征"""
        
        if industry_type == 'manufacturing':
            return self.manufacturing_adapter.extract_features(data_record)
        elif industry_type == 'medical':
            return self.medical_adapter.extract_features(data_record)
        else:
            # 通用特征提取
            return self._extract_generic_features(data_record)
    
    def _extract_generic_features(self, data_record: Dict[str, Any]) -> Dict[str, Any]:
        """通用特征提取"""
        return {
            'name': data_record.get('名称', data_record.get('name', '未知')),
            'specification': data_record.get('规格', data_record.get('spec', '')),
            'category': data_record.get('分类', data_record.get('category', '')),
            'manufacturer': data_record.get('厂家', data_record.get('manufacturer', '')),
            'raw_data': data_record
        }
    
    def _perform_classification(self, 
                              feature: Any,
                              template: CategoryTemplate,
                              schema: DataSourceSchema) -> Dict[str, Any]:
        """执行智能分类"""
        
        # 获取标准化特征用于匹配
        if isinstance(feature, ManufacturingFeature):
            normalized_feature = self.manufacturing_adapter.normalize_for_matching(feature)
        elif isinstance(feature, MedicalFeature):
            normalized_feature = self.medical_adapter.normalize_for_matching(feature)
        else:
            normalized_feature = feature
        
        # 执行规则匹配
        matching_results = self._apply_template_rules(
            normalized_feature, template, schema
        )
        
        # 计算最终分类
        final_classification = self._calculate_final_classification(
            matching_results, template
        )
        
        return final_classification
    
    def _apply_template_rules(self, 
                            feature: Dict[str, Any],
                            template: CategoryTemplate,
                            schema: DataSourceSchema) -> List[Dict[str, Any]]:
        """应用模板规则进行匹配"""
        
        matching_results = []
        
        # 按优先级排序规则
        sorted_rules = sorted(
            template.matching_rules, 
            key=lambda x: x.get('priority', 0), 
            reverse=True
        )
        
        for rule in sorted_rules:
            if not rule.get('enabled', True):
                continue
            
            try:
                result = self._apply_single_rule(feature, rule, template, schema)
                if result and result['score'] > 0:
                    matching_results.append(result)
            except Exception as e:
                logger.warning(f"规则应用失败: {rule.get('rule_type', 'unknown')} - {e}")
        
        return matching_results
    
    def _apply_single_rule(self, 
                          feature: Dict[str, Any],
                          rule: Dict[str, Any],
                          template: CategoryTemplate,
                          schema: DataSourceSchema) -> Optional[Dict[str, Any]]:
        """应用单个规则"""
        
        rule_type = rule['rule_type']
        
        if rule_type == 'keyword':
            return self._apply_keyword_rule(feature, rule)
        elif rule_type == 'pattern':
            return self._apply_pattern_rule(feature, rule)
        elif rule_type == 'similarity':
            return self._apply_similarity_rule(feature, rule)
        elif rule_type == 'composite':
            return self._apply_composite_rule(feature, rule)
        else:
            logger.warning(f"未知规则类型: {rule_type}")
            return None
    
    def _apply_keyword_rule(self, 
                          feature: Dict[str, Any], 
                          rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """应用关键词匹配规则"""
        
        conditions = rule['conditions']
        keywords = conditions.get('keywords', [])
        field_targets = conditions.get('field_targets', ['name'])
        match_threshold = conditions.get('match_threshold', 0.7)
        
        # 提取目标字段文本
        target_text = ""
        if 'name_keywords' in feature:
            target_text += " ".join(feature['name_keywords'])
        
        # 添加其他相关字段
        for field in field_targets:
            if field in feature and feature[field]:
                if isinstance(feature[field], list):
                    target_text += " " + " ".join(str(x) for x in feature[field])
                else:
                    target_text += " " + str(feature[field])
        
        target_text = target_text.lower()
        
        # 计算匹配分数
        matched_keywords = 0
        for keyword in keywords:
            if keyword.lower() in target_text:
                matched_keywords += 1
        
        match_score = matched_keywords / len(keywords) if keywords else 0
        
        if match_score >= match_threshold:
            actions = rule.get('actions', {})
            assign_category = actions.get('assign_category', {})
            
            return {
                'rule_type': 'keyword',
                'score': match_score,
                'weight': rule.get('weight', 0.3),
                'matched_keywords': matched_keywords,
                'total_keywords': len(keywords),
                'assigned_category': assign_category,
                'confidence_boost': assign_category.get('confidence_boost', 0.0)
            }
        
        return None
    
    def _apply_pattern_rule(self, 
                          feature: Dict[str, Any], 
                          rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """应用模式匹配规则"""
        
        import re
        
        conditions = rule['conditions']
        patterns = conditions.get('patterns', [])
        field_targets = conditions.get('field_targets', ['specification'])
        
        # 提取目标字段文本
        target_text = ""
        for field in field_targets:
            if field in feature and feature[field]:
                target_text += " " + str(feature[field])
        
        # 应用模式匹配
        matched_patterns = 0
        extracted_params = {}
        
        for pattern in patterns:
            matches = re.findall(pattern, target_text, re.IGNORECASE)
            if matches:
                matched_patterns += 1
                # 尝试提取参数
                if 'actions' in rule and 'extract_parameters' in rule['actions']:
                    param_patterns = rule['actions']['extract_parameters']
                    for param_name, param_pattern in param_patterns.items():
                        param_matches = re.findall(param_pattern, target_text, re.IGNORECASE)
                        if param_matches:
                            extracted_params[param_name] = param_matches[0] if isinstance(param_matches[0], str) else param_matches[0][0]
        
        match_score = matched_patterns / len(patterns) if patterns else 0
        
        if match_score > 0:
            actions = rule.get('actions', {})
            return {
                'rule_type': 'pattern',
                'score': match_score,
                'weight': rule.get('weight', 0.3),
                'matched_patterns': matched_patterns,
                'total_patterns': len(patterns),
                'extracted_parameters': extracted_params,
                'confidence_boost': actions.get('confidence_boost', 0.0)
            }
        
        return None
    
    def _apply_similarity_rule(self, 
                             feature: Dict[str, Any], 
                             rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """应用相似度匹配规则"""
        
        conditions = rule['conditions']
        min_similarity = conditions.get('min_similarity', 0.6)
        similarity_method = conditions.get('similarity_method', 'tfidf_cosine')
        
        # 这里简化实现，实际应该调用相应的相似度算法
        # 假设我们有一个相似度计算函数
        similarity_score = self._calculate_similarity(feature, similarity_method)
        
        if similarity_score >= min_similarity:
            return {
                'rule_type': 'similarity',
                'score': similarity_score,
                'weight': rule.get('weight', 0.25),
                'similarity_method': similarity_method,
                'similarity_score': similarity_score
            }
        
        return None
    
    def _apply_composite_rule(self, 
                            feature: Dict[str, Any], 
                            rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """应用复合匹配规则"""
        
        conditions = rule['conditions']
        field_combination = conditions.get('field_combination', [])
        combination_weight = conditions.get('combination_weight', 0.5)
        
        # 检查字段组合是否存在
        available_fields = [field for field in field_combination if field in feature and feature[field]]
        
        if len(available_fields) / len(field_combination) >= combination_weight:
            actions = rule.get('actions', {})
            composite_matching = actions.get('composite_matching', {})
            
            return {
                'rule_type': 'composite',
                'score': len(available_fields) / len(field_combination),
                'weight': rule.get('weight', 0.35),
                'available_fields': available_fields,
                'total_fields': len(field_combination),
                'confidence_multiplier': composite_matching.get('confidence_multiplier', 1.0)
            }
        
        return None
    
    def _calculate_similarity(self, feature: Dict[str, Any], method: str) -> float:
        """计算相似度（简化实现）"""
        # 这里应该实现真实的相似度计算逻辑
        # 暂时返回一个模拟值
        import random
        return random.uniform(0.5, 0.9)
    
    def _calculate_final_classification(self, 
                                      matching_results: List[Dict[str, Any]],
                                      template: CategoryTemplate) -> Dict[str, Any]:
        """计算最终分类结果"""
        
        if not matching_results:
            return {
                'predicted_category': {'level1': '未分类', 'level2': '无匹配规则'},
                'confidence_score': 0.0,
                'feature_vector': {},
                'matching_details': {'message': '没有匹配的规则'},
                'alternative_categories': []
            }
        
        # 计算加权分数
        total_score = 0
        total_weight = 0
        confidence_boosts = 0
        category_votes = {}
        
        for result in matching_results:
            score = result['score']
            weight = result['weight']
            weighted_score = score * weight
            
            total_score += weighted_score
            total_weight += weight
            confidence_boosts += result.get('confidence_boost', 0)
            
            # 收集分类投票
            if 'assigned_category' in result:
                category = result['assigned_category']
                category_key = f"{category.get('level1', '')}|{category.get('level2', '')}"
                
                if category_key not in category_votes:
                    category_votes[category_key] = {
                        'category': category,
                        'votes': 0,
                        'weighted_score': 0
                    }
                
                category_votes[category_key]['votes'] += 1
                category_votes[category_key]['weighted_score'] += weighted_score
        
        # 计算最终置信度
        base_confidence = total_score / total_weight if total_weight > 0 else 0
        final_confidence = min(1.0, base_confidence + confidence_boosts)
        
        # 选择最佳分类
        if category_votes:
            best_category_key = max(
                category_votes.keys(), 
                key=lambda k: category_votes[k]['weighted_score']
            )
            best_category = category_votes[best_category_key]['category']
        else:
            best_category = {'level1': '未分类', 'level2': '规则无分类'}
        
        # 生成备选分类
        alternative_categories = []
        sorted_categories = sorted(
            category_votes.items(),
            key=lambda x: x[1]['weighted_score'],
            reverse=True
        )[1:4]  # 取前3个备选
        
        for cat_key, cat_info in sorted_categories:
            alternative_categories.append({
                'category': cat_info['category'],
                'score': cat_info['weighted_score'],
                'votes': cat_info['votes']
            })
        
        return {
            'predicted_category': best_category,
            'confidence_score': final_confidence,
            'feature_vector': {
                'total_rules_matched': len(matching_results),
                'total_score': total_score,
                'total_weight': total_weight,
                'confidence_boosts': confidence_boosts
            },
            'matching_details': {
                'rules_applied': matching_results,
                'category_votes': category_votes
            },
            'alternative_categories': alternative_categories
        }
    
    def _generate_cache_key(self, 
                          data_sample: List[Dict[str, Any]], 
                          source_metadata: Dict[str, Any] = None) -> str:
        """生成缓存键"""
        
        # 基于数据结构特征生成缓存键
        fields = set()
        for record in data_sample[:5]:  # 只使用前5条记录生成键
            fields.update(record.keys())
        
        fields_str = "|".join(sorted(fields))
        metadata_str = json.dumps(source_metadata or {}, sort_keys=True)
        
        import hashlib
        cache_key = hashlib.md5(f"{fields_str}#{metadata_str}".encode()).hexdigest()
        
        return cache_key
    
    def _load_existing_categories(self, industry_type: str) -> List[Dict[str, Any]]:
        """加载现有分类数据"""
        
        # 这里应该从实际数据库加载现有分类
        # 暂时返回一些示例数据
        if industry_type == 'manufacturing':
            return [
                {"category_level1": "管道阀门", "category_level2": "控制阀门", "category_level3": "球阀"},
                {"category_level1": "管道阀门", "category_level2": "控制阀门", "category_level3": "蝶阀"},
                {"category_level1": "管道连接件", "category_level2": "管道配件", "category_level3": "弯头"},
            ]
        elif industry_type == 'medical':
            return [
                {"category_level1": "医疗器械", "category_level2": "基础医疗器械", "category_level3": "注射器械"},
                {"category_level1": "医疗器械", "category_level2": "诊断设备", "category_level3": "监护设备"},
                {"category_level1": "药品", "category_level2": "处方药", "category_level3": "注射剂"},
            ]
        
        return []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        
        return {
            'cached_schemas': len(self.schema_cache),
            'cached_templates': len(self.template_cache),
            'supported_industries': ['manufacturing', 'medical', 'generic'],
            'configuration': self.config,
            'component_status': {
                'recognizer': 'active',
                'manufacturing_adapter': 'active',
                'medical_adapter': 'active',
                'template_generator': 'active'
            }
        }
    
    def clear_caches(self):
        """清空缓存"""
        self.schema_cache.clear()
        self.template_cache.clear()
        logger.info("系统缓存已清空")


# 测试和演示代码
if __name__ == "__main__":
    # 创建多数据源智能分类系统
    classifier = MultiSourceIntelligentClassifier({
        'enable_auto_template_generation': True,
        'min_confidence_threshold': 0.6,
        'template_db_path': 'test_multi_source.db'
    })
    
    # 测试制造业数据
    manufacturing_data = [
        {
            "id": "MFG_001",
            "物料名称": "不锈钢疏水器",
            "规格型号": "DN25 PN16",
            "制造商": "上海阀门厂",
            "材质": "304不锈钢",
            "执行标准": "GB/T 12246"
        },
        {
            "id": "MFG_002", 
            "物料名称": "球阀",
            "规格型号": "DN50 CL150",
            "制造商": "天津泵业",
            "材质": "WCB"
        }
    ]
    
    # 测试医疗数据
    medical_data = [
        {
            "id": "MED_001",
            "产品名称": "一次性注射器",
            "规格": "5ml",
            "生产企业": "威高集团",
            "分类": "II类医疗器械",
            "注册证号": "国械注准20153660334"
        },
        {
            "id": "MED_002",
            "药品名称": "阿莫西林胶囊", 
            "规格": "0.25g",
            "生产企业": "华北制药",
            "分类": "处方药"
        }
    ]
    
    print("=== 多数据源智能分类系统测试 ===")
    
    # 测试单记录分类
    print("\n--- 制造业单记录分类 ---")
    mfg_result = classifier.classify_single_record(manufacturing_data[0])
    print(f"物料ID: {mfg_result.material_id}")
    print(f"识别行业: {mfg_result.industry_type}")
    print(f"分类结果: {mfg_result.predicted_category}")
    print(f"置信度: {mfg_result.confidence_score:.3f}")
    print(f"处理时间: {mfg_result.processing_time:.3f}秒")
    
    print("\n--- 医疗行业单记录分类 ---")
    med_result = classifier.classify_single_record(medical_data[0])
    print(f"产品ID: {med_result.material_id}")
    print(f"识别行业: {med_result.industry_type}")
    print(f"分类结果: {med_result.predicted_category}")
    print(f"置信度: {med_result.confidence_score:.3f}")
    print(f"处理时间: {med_result.processing_time:.3f}秒")
    
    # 测试批量分类
    print("\n--- 制造业批量分类 ---")
    mfg_batch_result = classifier.classify_batch_records(manufacturing_data)
    print(f"总处理数: {mfg_batch_result.total_processed}")
    print(f"成功分类: {mfg_batch_result.successful_classifications}")
    print(f"平均置信度: {mfg_batch_result.average_confidence:.3f}")
    print(f"行业分布: {mfg_batch_result.industry_distribution}")
    print(f"总处理时间: {mfg_batch_result.processing_time:.3f}秒")
    
    # 获取系统统计
    print("\n--- 系统统计信息 ---")
    stats = classifier.get_system_stats()
    print(f"缓存模式数: {stats['cached_schemas']}")
    print(f"缓存模板数: {stats['cached_templates']}")
    print(f"支持行业: {stats['supported_industries']}")
    print(f"组件状态: {stats['component_status']}")
    
    # 清理测试数据库
    import os
    if os.path.exists("test_multi_source.db"):
        os.remove("test_multi_source.db")
        print("\n测试数据库已清理")