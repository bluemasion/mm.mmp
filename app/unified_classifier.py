# -*- coding: utf-8 -*-
"""
统一物料分类器 - 整合现有分类器并提供统一接口
整合 SmartClassifier, AdvancedMatcher, IntelligentClassifier
"""

import logging
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import sqlite3

# 导入现有分类器
try:
    from app.smart_classifier import SmartClassifier, MaterialFeature
    from app.advanced_matcher import AdvancedMaterialMatcher
    from app.intelligent_classifier import IntelligentClassifier
except ImportError as e:
    logging.warning(f"导入现有分类器失败: {e}")

logger = logging.getLogger(__name__)

@dataclass
class ClassificationRequest:
    """分类请求数据结构"""
    material_name: str
    specification: str = ""
    manufacturer: str = ""
    material_type: str = ""
    unit: str = ""
    source_system: str = ""
    raw_attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.raw_attributes is None:
            self.raw_attributes = {}

@dataclass
class ClassificationResult:
    """分类结果数据结构"""
    request_id: str
    predicted_category: str
    confidence_score: float
    classification_path: List[str]
    alternative_categories: List[Dict[str, Any]]
    matching_evidence: Dict[str, Any]
    processing_time: float
    classifier_used: str
    quality_score: float = 0.0
    
@dataclass
class BatchClassificationResult:
    """批量分类结果"""
    total_processed: int
    successful_count: int
    failed_count: int
    average_confidence: float
    processing_time: float
    results: List[ClassificationResult]
    error_summary: List[Dict[str, str]]

class BaseClassifier(ABC):
    """分类器基础接口"""
    
    @abstractmethod
    def classify(self, request: ClassificationRequest) -> ClassificationResult:
        """单个分类接口"""
        pass
    
    @abstractmethod
    def classify_batch(self, requests: List[ClassificationRequest]) -> BatchClassificationResult:
        """批量分类接口"""
        pass
    
    @abstractmethod
    def get_classifier_info(self) -> Dict[str, Any]:
        """获取分类器信息"""
        pass

class SmartClassifierAdapter(BaseClassifier):
    """SmartClassifier适配器"""
    
    def __init__(self, db_path: str):
        try:
            self.classifier = SmartClassifier(db_path)
            self.available = True
        except Exception as e:
            logger.error(f"SmartClassifier初始化失败: {e}")
            self.available = False
    
    def classify(self, request: ClassificationRequest) -> ClassificationResult:
        """适配SmartClassifier的分类接口"""
        if not self.available:
            raise RuntimeError("SmartClassifier不可用")
        
        start_time = time.time()
        
        # 转换为SmartClassifier的数据格式
        material_feature = MaterialFeature(
            name=request.material_name,
            spec=request.specification,
            unit=request.unit,
            material=request.raw_attributes.get('material', '')
        )
        
        try:
            # 调用SmartClassifier
            raw_results = self.classifier.classify_material(material_feature)
            processing_time = time.time() - start_time
            
            if not raw_results:
                return ClassificationResult(
                    request_id=f"smart_{int(time.time())}",
                    predicted_category="未分类",
                    confidence_score=0.0,
                    classification_path=["未分类"],
                    alternative_categories=[],
                    matching_evidence={},
                    processing_time=processing_time,
                    classifier_used="SmartClassifier"
                )
            
            # 转换结果格式
            best_result = raw_results[0]
            alternatives = raw_results[1:5] if len(raw_results) > 1 else []
            
            return ClassificationResult(
                request_id=f"smart_{int(time.time())}",
                predicted_category=best_result['category'],
                confidence_score=best_result['confidence'] / 100.0,
                classification_path=[best_result['category']],
                alternative_categories=alternatives,
                matching_evidence={
                    'matching_samples': best_result.get('matching_samples', []),
                    'attributes': best_result.get('attributes', [])
                },
                processing_time=processing_time,
                classifier_used="SmartClassifier"
            )
            
        except Exception as e:
            logger.error(f"SmartClassifier分类失败: {e}")
            return ClassificationResult(
                request_id=f"smart_error_{int(time.time())}",
                predicted_category="分类失败",
                confidence_score=0.0,
                classification_path=["分类失败"],
                alternative_categories=[],
                matching_evidence={'error': str(e)},
                processing_time=time.time() - start_time,
                classifier_used="SmartClassifier"
            )
    
    def classify_batch(self, requests: List[ClassificationRequest]) -> BatchClassificationResult:
        """批量分类实现"""
        start_time = time.time()
        results = []
        errors = []
        
        for i, request in enumerate(requests):
            try:
                result = self.classify(request)
                results.append(result)
            except Exception as e:
                errors.append({
                    'index': i,
                    'material_name': request.material_name,
                    'error': str(e)
                })
        
        successful_count = len(results)
        failed_count = len(errors)
        
        avg_confidence = sum(r.confidence_score for r in results) / successful_count if successful_count > 0 else 0.0
        
        return BatchClassificationResult(
            total_processed=len(requests),
            successful_count=successful_count,
            failed_count=failed_count,
            average_confidence=avg_confidence,
            processing_time=time.time() - start_time,
            results=results,
            error_summary=errors
        )
    
    def get_classifier_info(self) -> Dict[str, Any]:
        return {
            'name': 'SmartClassifier',
            'version': '1.0',
            'description': '基于关键词和规则的智能分类器',
            'available': self.available
        }

class IntelligentClassifierAdapter(BaseClassifier):
    """IntelligentClassifier适配器"""
    
    def __init__(self, business_manager):
        try:
            self.classifier = IntelligentClassifier(business_manager)
            self.available = True
        except Exception as e:
            logger.error(f"IntelligentClassifier初始化失败: {e}")
            self.available = False
    
    def classify(self, request: ClassificationRequest) -> ClassificationResult:
        """适配IntelligentClassifier的分类接口"""
        if not self.available:
            raise RuntimeError("IntelligentClassifier不可用")
        
        start_time = time.time()
        
        try:
            # 调用IntelligentClassifier
            raw_results = self.classifier.get_material_recommendations({
                'name': request.material_name,
                'spec': request.specification,
                'manufacturer': request.manufacturer,
                'unit': request.unit
            })
            
            processing_time = time.time() - start_time
            
            if not raw_results or not raw_results.get('recommendations'):
                return ClassificationResult(
                    request_id=f"intel_{int(time.time())}",
                    predicted_category="未分类",
                    confidence_score=0.0,
                    classification_path=["未分类"],
                    alternative_categories=[],
                    matching_evidence={},
                    processing_time=processing_time,
                    classifier_used="IntelligentClassifier"
                )
            
            # 转换结果格式
            recommendations = raw_results['recommendations']
            best_result = recommendations[0] if recommendations else {}
            
            return ClassificationResult(
                request_id=f"intel_{int(time.time())}",
                predicted_category=best_result.get('category', '未分类'),
                confidence_score=best_result.get('confidence', 0.0) / 100.0,
                classification_path=[best_result.get('category', '未分类')],
                alternative_categories=recommendations[1:5],
                matching_evidence={
                    'reasoning': raw_results.get('reasoning', {}),
                    'feature_analysis': raw_results.get('feature_analysis', {})
                },
                processing_time=processing_time,
                classifier_used="IntelligentClassifier"
            )
            
        except Exception as e:
            logger.error(f"IntelligentClassifier分类失败: {e}")
            return ClassificationResult(
                request_id=f"intel_error_{int(time.time())}",
                predicted_category="分类失败",
                confidence_score=0.0,
                classification_path=["分类失败"],
                alternative_categories=[],
                matching_evidence={'error': str(e)},
                processing_time=time.time() - start_time,
                classifier_used="IntelligentClassifier"
            )
    
    def classify_batch(self, requests: List[ClassificationRequest]) -> BatchClassificationResult:
        """批量分类实现"""
        start_time = time.time()
        results = []
        errors = []
        
        for i, request in enumerate(requests):
            try:
                result = self.classify(request)
                results.append(result)
            except Exception as e:
                errors.append({
                    'index': i,
                    'material_name': request.material_name,
                    'error': str(e)
                })
        
        successful_count = len(results)
        failed_count = len(errors)
        
        avg_confidence = sum(r.confidence_score for r in results) / successful_count if successful_count > 0 else 0.0
        
        return BatchClassificationResult(
            total_processed=len(requests),
            successful_count=successful_count,
            failed_count=failed_count,
            average_confidence=avg_confidence,
            processing_time=time.time() - start_time,
            results=results,
            error_summary=errors
        )
    
    def get_classifier_info(self) -> Dict[str, Any]:
        return {
            'name': 'IntelligentClassifier',
            'version': '1.0',
            'description': '基于TF-IDF和机器学习的智能分类器',
            'available': self.available
        }

class UnifiedMaterialClassifier:
    """统一物料分类器 - 整合所有分类器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # 初始化各个分类器适配器
        self.classifiers = {}
        self._initialize_classifiers()
        
        # 分类器优先级和融合策略
        self.classifier_priority = ['IntelligentClassifier', 'SmartClassifier']
        self.fusion_strategy = self.config.get('fusion_strategy', 'weighted_voting')
        
        logger.info(f"统一分类器初始化完成，可用分类器: {list(self.classifiers.keys())}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            'db_path': 'business_data.db',
            'fusion_strategy': 'weighted_voting',
            'confidence_threshold': 0.6,
            'use_ensemble': True,
            'fallback_enabled': True
        }
    
    def _initialize_classifiers(self):
        """初始化所有分类器适配器"""
        
        # 初始化SmartClassifier
        try:
            smart_adapter = SmartClassifierAdapter(self.config['db_path'])
            if smart_adapter.available:
                self.classifiers['SmartClassifier'] = smart_adapter
        except Exception as e:
            logger.warning(f"SmartClassifier初始化失败: {e}")
        
        # 初始化IntelligentClassifier
        try:
            # 这里需要business_manager实例，暂时跳过
            # intel_adapter = IntelligentClassifierAdapter(business_manager)
            # if intel_adapter.available:
            #     self.classifiers['IntelligentClassifier'] = intel_adapter
            pass
        except Exception as e:
            logger.warning(f"IntelligentClassifier初始化失败: {e}")
    
    def classify(self, request: ClassificationRequest) -> ClassificationResult:
        """统一分类接口"""
        
        if self.config.get('use_ensemble', True) and len(self.classifiers) > 1:
            # 使用集成方法
            return self._classify_with_ensemble(request)
        else:
            # 使用单个分类器
            return self._classify_with_priority(request)
    
    def _classify_with_priority(self, request: ClassificationRequest) -> ClassificationResult:
        """按优先级使用分类器"""
        
        last_error = None
        
        for classifier_name in self.classifier_priority:
            if classifier_name in self.classifiers:
                try:
                    result = self.classifiers[classifier_name].classify(request)
                    
                    # 检查置信度阈值
                    if result.confidence_score >= self.config['confidence_threshold']:
                        return result
                    
                    # 如果置信度不够，尝试下一个分类器
                    logger.info(f"{classifier_name} 置信度不足 ({result.confidence_score:.2f}), 尝试下一个分类器")
                    
                except Exception as e:
                    last_error = e
                    logger.error(f"{classifier_name} 分类失败: {e}")
                    continue
        
        # 所有分类器都失败，返回错误结果
        return ClassificationResult(
            request_id=f"unified_error_{int(time.time())}",
            predicted_category="分类失败",
            confidence_score=0.0,
            classification_path=["分类失败"],
            alternative_categories=[],
            matching_evidence={'error': str(last_error) if last_error else '无可用分类器'},
            processing_time=0.0,
            classifier_used="Unified"
        )
    
    def _classify_with_ensemble(self, request: ClassificationRequest) -> ClassificationResult:
        """使用集成方法进行分类"""
        
        start_time = time.time()
        classifier_results = []
        
        # 收集所有分类器的结果
        for classifier_name, classifier in self.classifiers.items():
            try:
                result = classifier.classify(request)
                classifier_results.append(result)
            except Exception as e:
                logger.error(f"{classifier_name} 集成分类失败: {e}")
        
        if not classifier_results:
            return ClassificationResult(
                request_id=f"ensemble_error_{int(time.time())}",
                predicted_category="集成失败",
                confidence_score=0.0,
                classification_path=["集成失败"],
                alternative_categories=[],
                matching_evidence={'error': '所有分类器都失败'},
                processing_time=time.time() - start_time,
                classifier_used="Ensemble"
            )
        
        # 应用融合策略
        if self.fusion_strategy == 'weighted_voting':
            final_result = self._weighted_voting_fusion(classifier_results)
        elif self.fusion_strategy == 'highest_confidence':
            final_result = max(classifier_results, key=lambda r: r.confidence_score)
        else:
            # 默认使用第一个结果
            final_result = classifier_results[0]
        
        # 更新集成信息
        final_result.classifier_used = "Ensemble"
        final_result.processing_time = time.time() - start_time
        final_result.matching_evidence['ensemble_details'] = {
            'num_classifiers': len(classifier_results),
            'individual_results': [
                {
                    'classifier': r.classifier_used,
                    'category': r.predicted_category,
                    'confidence': r.confidence_score
                }
                for r in classifier_results
            ]
        }
        
        return final_result
    
    def _weighted_voting_fusion(self, results: List[ClassificationResult]) -> ClassificationResult:
        """加权投票融合策略"""
        
        # 分类器权重配置
        classifier_weights = {
            'IntelligentClassifier': 0.6,
            'SmartClassifier': 0.4,
            'AdvancedMatcher': 0.3
        }
        
        # 计算加权投票
        category_scores = {}
        
        for result in results:
            weight = classifier_weights.get(result.classifier_used, 0.2)
            weighted_score = result.confidence_score * weight
            
            if result.predicted_category in category_scores:
                category_scores[result.predicted_category] += weighted_score
            else:
                category_scores[result.predicted_category] = weighted_score
        
        # 选择得分最高的分类
        if category_scores:
            best_category = max(category_scores.keys(), key=lambda k: category_scores[k])
            best_score = category_scores[best_category]
            
            # 找到对应的原始结果
            for result in results:
                if result.predicted_category == best_category:
                    result.confidence_score = min(best_score, 1.0)  # 确保不超过1.0
                    return result
        
        # 如果没有找到，返回置信度最高的结果
        return max(results, key=lambda r: r.confidence_score)
    
    def classify_batch(self, requests: List[ClassificationRequest]) -> BatchClassificationResult:
        """批量分类接口"""
        start_time = time.time()
        results = []
        errors = []
        
        for i, request in enumerate(requests):
            try:
                result = self.classify(request)
                results.append(result)
            except Exception as e:
                errors.append({
                    'index': i,
                    'material_name': request.material_name,
                    'error': str(e)
                })
                logger.error(f"批量分类第{i}项失败: {e}")
        
        successful_count = len(results)
        failed_count = len(errors)
        
        avg_confidence = sum(r.confidence_score for r in results) / successful_count if successful_count > 0 else 0.0
        
        return BatchClassificationResult(
            total_processed=len(requests),
            successful_count=successful_count,
            failed_count=failed_count,
            average_confidence=avg_confidence,
            processing_time=time.time() - start_time,
            results=results,
            error_summary=errors
        )
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        classifier_info = []
        
        for name, classifier in self.classifiers.items():
            info = classifier.get_classifier_info()
            classifier_info.append(info)
        
        return {
            'unified_classifier_version': '1.0',
            'available_classifiers': len(self.classifiers),
            'classifier_details': classifier_info,
            'fusion_strategy': self.fusion_strategy,
            'configuration': self.config
        }

# 使用示例
def create_unified_classifier_example():
    """创建统一分类器示例"""
    
    # 初始化统一分类器
    unified_classifier = UnifiedMaterialClassifier({
        'db_path': 'business_data.db',
        'fusion_strategy': 'weighted_voting',
        'confidence_threshold': 0.6,
        'use_ensemble': True
    })
    
    # 创建分类请求
    request = ClassificationRequest(
        material_name="不锈钢球阀",
        specification="DN100 PN16",
        manufacturer="上海阀门厂",
        material_type="阀门",
        unit="个"
    )
    
    # 执行分类
    result = unified_classifier.classify(request)
    
    print(f"分类结果: {result.predicted_category}")
    print(f"置信度: {result.confidence_score:.2f}")
    print(f"使用的分类器: {result.classifier_used}")
    
    return unified_classifier

if __name__ == "__main__":
    create_unified_classifier_example()