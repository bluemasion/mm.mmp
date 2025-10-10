# -*- coding: utf-8 -*-
"""
基础质量评估系统
使用固定权重对物料质量进行评分，为后续ML优化做准备
集成到分类流程中，提供质量维度的评估
"""

import logging
import sqlite3
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re
import hashlib
import json

logger = logging.getLogger(__name__)

@dataclass
class QualityDimension:
    """质量评估维度"""
    name: str
    weight: float
    description: str
    scoring_rules: Dict[str, Any]

@dataclass
class QualityScore:
    """质量评分结果"""
    overall_score: float  # 0-100总分
    dimension_scores: Dict[str, float]  # 各维度得分
    quality_grade: str  # A/B/C/D等级
    quality_issues: List[str]  # 质量问题列表
    improvement_suggestions: List[str]  # 改进建议

class BaseQualityAssessment:
    """基础质量评估系统"""
    
    def __init__(self, config_db_path: str = 'business_data.db'):
        self.config_db_path = config_db_path
        
        # 定义质量评估维度（使用固定权重）
        self.quality_dimensions = {
            'completeness': QualityDimension(
                name='完整性',
                weight=0.25,
                description='物料信息的完整程度',
                scoring_rules={
                    'required_fields': ['material_name', 'specification'],
                    'preferred_fields': ['manufacturer', 'material_type', 'unit'],
                    'bonus_fields': ['model', 'brand', 'technical_parameters']
                }
            ),
            'accuracy': QualityDimension(
                name='准确性',
                weight=0.25,
                description='物料信息的准确程度',
                scoring_rules={
                    'name_patterns': [
                        r'^[A-Za-z0-9\u4e00-\u9fa5\s\-_]+$',  # 合法字符
                        r'^(?!.*\b(测试|test|temp|临时)\b).*$'  # 非测试数据
                    ],
                    'spec_patterns': [
                        r'(?i)(DN|φ|Ø)?\d+',  # 尺寸规格
                        r'(?i)(PN|压力|pressure)\s*\d+',  # 压力等级
                        r'(?i)(材质|material|材料)[:：]?\s*\w+'  # 材质信息
                    ]
                }
            ),
            'consistency': QualityDimension(
                name='一致性',
                weight=0.20,
                description='物料信息格式的一致性',
                scoring_rules={
                    'naming_consistency': True,
                    'format_standards': True,
                    'unit_standardization': True
                }
            ),
            'richness': QualityDimension(
                name='丰富度',
                weight=0.15,
                description='物料信息的丰富程度',
                scoring_rules={
                    'detail_level': 'comprehensive',
                    'technical_depth': True,
                    'contextual_info': True
                }
            ),
            'reliability': QualityDimension(
                name='可靠性',
                weight=0.15,
                description='物料信息的可靠程度',
                scoring_rules={
                    'source_credibility': True,
                    'update_frequency': True,
                    'validation_status': True
                }
            )
        }
        
        # 质量等级定义
        self.quality_grades = {
            'A': {'min_score': 90, 'description': '优秀 - 高质量物料信息'},
            'B': {'min_score': 75, 'description': '良好 - 质量较好的物料信息'},
            'C': {'min_score': 60, 'description': '一般 - 基本满足要求的物料信息'},
            'D': {'min_score': 0, 'description': '差 - 质量较差，需要改进'}
        }
        
        logger.info("基础质量评估系统初始化完成")
    
    def assess_material_quality(self, material_data: Dict[str, Any]) -> QualityScore:
        """评估单个物料的质量"""
        
        dimension_scores = {}
        quality_issues = []
        improvement_suggestions = []
        
        # 逐维度评估
        for dim_key, dimension in self.quality_dimensions.items():
            score, issues, suggestions = self._assess_dimension(
                material_data, dimension, dim_key
            )
            dimension_scores[dim_key] = score
            quality_issues.extend(issues)
            improvement_suggestions.extend(suggestions)
        
        # 计算总分
        overall_score = sum(
            dimension_scores[dim_key] * dimension.weight
            for dim_key, dimension in self.quality_dimensions.items()
        )
        
        # 确定质量等级
        quality_grade = self._determine_quality_grade(overall_score)
        
        return QualityScore(
            overall_score=round(overall_score, 2),
            dimension_scores=dimension_scores,
            quality_grade=quality_grade,
            quality_issues=quality_issues,
            improvement_suggestions=improvement_suggestions
        )
    
    def _assess_dimension(self, material_data: Dict[str, Any], 
                         dimension: QualityDimension, dim_key: str) -> Tuple[float, List[str], List[str]]:
        """评估单个维度的质量"""
        
        if dim_key == 'completeness':
            return self._assess_completeness(material_data, dimension)
        elif dim_key == 'accuracy':
            return self._assess_accuracy(material_data, dimension)
        elif dim_key == 'consistency':
            return self._assess_consistency(material_data, dimension)
        elif dim_key == 'richness':
            return self._assess_richness(material_data, dimension)
        elif dim_key == 'reliability':
            return self._assess_reliability(material_data, dimension)
        else:
            return 0.0, [], []
    
    def _assess_completeness(self, material_data: Dict[str, Any], 
                           dimension: QualityDimension) -> Tuple[float, List[str], List[str]]:
        """评估完整性维度"""
        
        rules = dimension.scoring_rules
        required_fields = rules['required_fields']
        preferred_fields = rules['preferred_fields']
        bonus_fields = rules['bonus_fields']
        
        score = 0.0
        issues = []
        suggestions = []
        
        # 必填字段检查 (60分)
        required_filled = 0
        for field in required_fields:
            value = material_data.get(field, '').strip()
            if value:
                required_filled += 1
            else:
                issues.append(f'缺少必填字段: {field}')
                suggestions.append(f'请补充{field}信息')
        
        score += (required_filled / len(required_fields)) * 60
        
        # 推荐字段检查 (25分)
        preferred_filled = 0
        for field in preferred_fields:
            value = material_data.get(field, '').strip()
            if value:
                preferred_filled += 1
            else:
                suggestions.append(f'建议补充{field}信息以提高完整性')
        
        score += (preferred_filled / len(preferred_fields)) * 25
        
        # 附加字段检查 (15分)
        bonus_filled = 0
        for field in bonus_fields:
            value = material_data.get(field, '').strip()
            if value:
                bonus_filled += 1
        
        score += (bonus_filled / len(bonus_fields)) * 15
        
        return score, issues, suggestions
    
    def _assess_accuracy(self, material_data: Dict[str, Any], 
                        dimension: QualityDimension) -> Tuple[float, List[str], List[str]]:
        """评估准确性维度"""
        
        rules = dimension.scoring_rules
        score = 0.0
        issues = []
        suggestions = []
        
        # 物料名称格式检查 (40分)
        material_name = material_data.get('material_name', '')
        if material_name:
            name_valid = True
            for pattern in rules['name_patterns']:
                if not re.search(pattern, material_name):
                    name_valid = False
                    break
            
            if name_valid:
                score += 40
            else:
                issues.append('物料名称格式不规范')
                suggestions.append('请检查物料名称格式，确保使用标准命名规则')
        
        # 规格参数检查 (40分)
        specification = material_data.get('specification', '')
        if specification:
            spec_matches = 0
            for pattern in rules['spec_patterns']:
                if re.search(pattern, specification):
                    spec_matches += 1
            
            if spec_matches > 0:
                score += min(40, spec_matches * 15)  # 每个匹配模式15分
            else:
                issues.append('规格参数信息不完整或格式不规范')
                suggestions.append('建议补充详细的技术规格参数')
        
        # 制造商信息检查 (20分)
        manufacturer = material_data.get('manufacturer', '')
        if manufacturer and len(manufacturer) >= 2:
            score += 20
        elif manufacturer:
            suggestions.append('制造商信息过于简略，建议提供完整厂商名称')
        
        return score, issues, suggestions
    
    def _assess_consistency(self, material_data: Dict[str, Any], 
                          dimension: QualityDimension) -> Tuple[float, List[str], List[str]]:
        """评估一致性维度"""
        
        score = 0.0
        issues = []
        suggestions = []
        
        # 命名一致性检查 (40分)
        material_name = material_data.get('material_name', '').lower()
        specification = material_data.get('specification', '').lower()
        
        # 检查名称和规格的一致性
        if material_name and specification:
            # 简单的一致性检查：名称中的关键词是否在规格中体现
            name_keywords = set(re.findall(r'\b\w{2,}\b', material_name))
            spec_keywords = set(re.findall(r'\b\w{2,}\b', specification))
            
            overlap = len(name_keywords & spec_keywords)
            if overlap > 0:
                score += min(40, overlap * 10)
            else:
                issues.append('物料名称与规格信息缺乏一致性')
                suggestions.append('确保物料名称与规格描述相互呼应')
        
        # 单位标准化检查 (30分)
        unit = material_data.get('unit', '')
        standard_units = ['个', '台', '套', 'm', 'kg', 'L', '米', '千克', '升', 'pcs', 'set', 'pc']
        
        if unit.lower() in [u.lower() for u in standard_units]:
            score += 30
        elif unit:
            suggestions.append(f'单位"{unit}"建议使用标准单位')
        
        # 格式一致性检查 (30分)
        # 检查各字段是否遵循统一的格式规范
        format_score = 30
        
        # 检查是否有异常字符或格式
        for field_name, field_value in material_data.items():
            if isinstance(field_value, str) and field_value:
                # 检查是否有不一致的格式标记
                if '【】' in field_value or '[]' in field_value or '()' in field_value:
                    pass  # 这些是可接受的格式
                elif any(char in field_value for char in ['~', '～', '※', '★', '●']):
                    format_score -= 10
                    issues.append(f'{field_name}字段包含非标准符号')
        
        score += max(0, format_score)
        
        return score, issues, suggestions
    
    def _assess_richness(self, material_data: Dict[str, Any], 
                        dimension: QualityDimension) -> Tuple[float, List[str], List[str]]:
        """评估丰富度维度"""
        
        score = 0.0
        issues = []
        suggestions = []
        
        # 信息详细程度评估 (50分)
        detail_score = 0
        
        # 检查描述性信息的丰富程度
        specification = material_data.get('specification', '')
        if len(specification) > 50:
            detail_score += 20
        elif len(specification) > 20:
            detail_score += 10
        
        # 检查是否有技术参数
        tech_keywords = ['DN', 'PN', '材质', '压力', '温度', '精度', '型号', '规格']
        tech_count = sum(1 for keyword in tech_keywords if keyword in specification)
        detail_score += min(20, tech_count * 3)
        
        # 检查附加信息字段
        additional_fields = ['model', 'brand', 'technical_parameters', 'application', 'notes']
        additional_count = sum(1 for field in additional_fields if material_data.get(field))
        detail_score += min(10, additional_count * 2)
        
        score += detail_score
        
        # 上下文信息评估 (30分)
        context_score = 0
        
        # 检查应用场景信息
        if material_data.get('application'):
            context_score += 15
        
        # 检查分类信息的详细程度
        category_info = material_data.get('category', material_data.get('material_type', ''))
        if category_info and len(category_info) > 5:
            context_score += 15
        
        score += context_score
        
        # 关联性信息评估 (20分)
        relation_score = 0
        
        # 检查是否有相关产品信息
        if material_data.get('related_materials'):
            relation_score += 10
        
        # 检查是否有供应商相关信息
        if material_data.get('supplier_info') or material_data.get('manufacturer'):
            relation_score += 10
        
        score += relation_score
        
        if score < 60:
            suggestions.append('建议补充更详细的技术参数和应用信息')
        if score < 40:
            suggestions.append('信息过于简单，建议丰富物料描述')
        
        return score, issues, suggestions
    
    def _assess_reliability(self, material_data: Dict[str, Any], 
                          dimension: QualityDimension) -> Tuple[float, List[str], List[str]]:
        """评估可靠性维度"""
        
        score = 0.0
        issues = []
        suggestions = []
        
        # 数据源可信度评估 (40分)
        source_system = material_data.get('source_system', '')
        trusted_sources = ['ERP', 'PLM', 'PDM', 'official', '正式系统']
        
        if any(source in source_system for source in trusted_sources):
            score += 40
        elif source_system:
            score += 20
            suggestions.append('数据来源需要进一步验证')
        else:
            issues.append('缺少数据来源信息')
            suggestions.append('请标明数据来源系统')
        
        # 更新时效性评估 (30分)
        last_updated = material_data.get('last_updated', material_data.get('update_time'))
        if last_updated:
            try:
                if isinstance(last_updated, str):
                    update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                else:
                    update_time = last_updated
                
                days_old = (datetime.now() - update_time.replace(tzinfo=None)).days
                
                if days_old <= 30:
                    score += 30
                elif days_old <= 90:
                    score += 20
                elif days_old <= 365:
                    score += 10
                else:
                    suggestions.append('数据更新时间较久，建议重新验证')
            except:
                suggestions.append('更新时间格式不正确')
        
        # 验证状态评估 (30分)
        validation_status = material_data.get('validation_status', material_data.get('status'))
        approved_statuses = ['approved', '已审核', 'validated', 'confirmed', 'active']
        
        if any(status in str(validation_status).lower() for status in approved_statuses):
            score += 30
        elif validation_status:
            score += 15
            suggestions.append('建议完成正式审核流程')
        else:
            issues.append('缺少验证状态信息')
            suggestions.append('请补充审核验证状态')
        
        return score, issues, suggestions
    
    def _determine_quality_grade(self, overall_score: float) -> str:
        """确定质量等级"""
        
        for grade, criteria in self.quality_grades.items():
            if overall_score >= criteria['min_score']:
                return grade
        
        return 'D'  # 默认最低等级
    
    def assess_batch_materials(self, materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量评估物料质量"""
        
        logger.info(f"开始批量质量评估，物料数量: {len(materials)}")
        
        batch_results = []
        grade_distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        total_scores = []
        dimension_averages = {dim: [] for dim in self.quality_dimensions.keys()}
        
        for i, material in enumerate(materials):
            try:
                quality_score = self.assess_material_quality(material)
                
                # 收集统计信息
                batch_results.append({
                    'material_index': i,
                    'material_code': material.get('material_code', f'MAT_{i:06d}'),
                    'quality_score': quality_score
                })
                
                grade_distribution[quality_score.quality_grade] += 1
                total_scores.append(quality_score.overall_score)
                
                for dim, score in quality_score.dimension_scores.items():
                    dimension_averages[dim].append(score)
                
            except Exception as e:
                logger.error(f"评估物料 {i} 失败: {e}")
                batch_results.append({
                    'material_index': i,
                    'material_code': material.get('material_code', f'MAT_{i:06d}'),
                    'error': str(e)
                })
        
        # 计算统计数据
        avg_score = sum(total_scores) / len(total_scores) if total_scores else 0
        avg_dimension_scores = {
            dim: sum(scores) / len(scores) if scores else 0
            for dim, scores in dimension_averages.items()
        }
        
        return {
            'batch_results': batch_results,
            'statistics': {
                'total_materials': len(materials),
                'average_score': round(avg_score, 2),
                'grade_distribution': grade_distribution,
                'dimension_averages': avg_dimension_scores
            },
            'quality_report': self._generate_quality_report(
                batch_results, grade_distribution, avg_score
            ),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_quality_report(self, batch_results: List[Dict], 
                               grade_distribution: Dict[str, int], 
                               avg_score: float) -> Dict[str, Any]:
        """生成质量报告"""
        
        total_materials = len(batch_results)
        high_quality_count = grade_distribution['A'] + grade_distribution['B']
        
        # 识别质量问题
        common_issues = []
        improvement_priorities = []
        
        # 分析常见问题
        all_issues = []
        all_suggestions = []
        
        for result in batch_results:
            quality_score = result.get('quality_score')
            if quality_score:
                all_issues.extend(quality_score.quality_issues)
                all_suggestions.extend(quality_score.improvement_suggestions)
        
        # 统计最频繁的问题
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'overall_assessment': {
                'average_score': avg_score,
                'quality_level': 'high' if avg_score >= 75 else 'medium' if avg_score >= 60 else 'low',
                'high_quality_rate': high_quality_count / total_materials if total_materials > 0 else 0
            },
            'grade_summary': {
                'excellent': grade_distribution['A'],
                'good': grade_distribution['B'], 
                'fair': grade_distribution['C'],
                'poor': grade_distribution['D']
            },
            'common_issues': [{'issue': issue, 'frequency': count} for issue, count in common_issues],
            'improvement_recommendations': self._generate_improvement_recommendations(
                grade_distribution, common_issues, avg_score
            )
        }
    
    def _generate_improvement_recommendations(self, grade_distribution: Dict[str, int],
                                           common_issues: List[Tuple[str, int]], 
                                           avg_score: float) -> List[str]:
        """生成改进建议"""
        
        recommendations = []
        
        # 基于平均分数的建议
        if avg_score < 60:
            recommendations.append("整体数据质量较低，建议建立数据质量管理流程")
            recommendations.append("重点关注数据完整性和准确性改进")
        
        # 基于等级分布的建议
        poor_rate = grade_distribution['D'] / sum(grade_distribution.values())
        if poor_rate > 0.3:
            recommendations.append("超过30%的物料质量等级为D，需要紧急改进")
        
        # 基于常见问题的建议
        for issue, frequency in common_issues[:3]:  # 只看前3个问题
            if '缺少必填字段' in issue:
                recommendations.append("建立数据录入规范，确保必填字段完整性")
            elif '格式不规范' in issue:
                recommendations.append("制定并执行标准化的数据格式规范")
            elif '信息过于简单' in issue:
                recommendations.append("鼓励录入更详细的技术参数和描述信息")
        
        return recommendations

# 与统一分类器集成的质量评估接口
class QualityIntegratedClassifier:
    """集成质量评估的分类器"""
    
    def __init__(self, unified_classifier, quality_assessor):
        self.unified_classifier = unified_classifier
        self.quality_assessor = quality_assessor
        
        logger.info("质量集成分类器初始化完成")
    
    def classify_with_quality(self, classification_request) -> Dict[str, Any]:
        """执行分类并进行质量评估"""
        
        # 执行分类
        classification_result = self.unified_classifier.classify(classification_request)
        
        # 准备质量评估数据
        material_data = {
            'material_name': classification_request.material_name,
            'specification': classification_request.specification,
            'manufacturer': classification_request.manufacturer,
            'material_type': classification_request.material_type,
            'unit': classification_request.unit,
            'source_system': getattr(classification_request, 'source_system', 'unknown'),
            'last_updated': datetime.now().isoformat()
        }
        
        # 执行质量评估
        quality_score = self.quality_assessor.assess_material_quality(material_data)
        
        return {
            'classification': {
                'predicted_category': classification_result.predicted_category,
                'confidence_score': classification_result.confidence_score,
                'alternative_categories': classification_result.alternative_categories,
                'processing_time': classification_result.processing_time
            },
            'quality_assessment': {
                'overall_score': quality_score.overall_score,
                'quality_grade': quality_score.quality_grade,
                'dimension_scores': quality_score.dimension_scores,
                'quality_issues': quality_score.quality_issues,
                'improvement_suggestions': quality_score.improvement_suggestions
            },
            'integrated_score': self._calculate_integrated_score(
                classification_result, quality_score
            )
        }
    
    def _calculate_integrated_score(self, classification_result, quality_score) -> Dict[str, Any]:
        """计算集成分数"""
        
        # 综合分类置信度和质量分数
        classification_weight = 0.6
        quality_weight = 0.4
        
        integrated_score = (
            classification_result.confidence_score * classification_weight +
            (quality_score.overall_score / 100) * quality_weight
        )
        
        return {
            'integrated_confidence': round(integrated_score, 4),
            'classification_confidence': classification_result.confidence_score,
            'quality_score': quality_score.overall_score / 100,
            'recommendation': (
                'high_confidence' if integrated_score >= 0.8 else
                'medium_confidence' if integrated_score >= 0.6 else
                'low_confidence'
            )
        }

# 使用示例
def quality_assessment_example():
    """质量评估系统使用示例"""
    
    # 初始化质量评估器
    assessor = BaseQualityAssessment()
    
    # 测试物料数据
    test_material = {
        'material_code': 'M001',
        'material_name': '不锈钢球阀',
        'specification': 'DN100 PN16 304不锈钢材质 法兰连接',
        'manufacturer': '上海阀门制造有限公司',
        'material_type': '阀门',
        'unit': '个',
        'source_system': 'ERP',
        'last_updated': '2024-01-15T10:00:00'
    }
    
    # 执行质量评估
    quality_result = assessor.assess_material_quality(test_material)
    
    print("质量评估结果:")
    print(f"总分: {quality_result.overall_score}")
    print(f"等级: {quality_result.quality_grade}")
    print(f"维度分数: {quality_result.dimension_scores}")
    print(f"质量问题: {quality_result.quality_issues}")

if __name__ == "__main__":
    quality_assessment_example()