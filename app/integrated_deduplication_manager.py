# -*- coding: utf-8 -*-
"""
集成一物多码去重引擎到MMP系统
简化版本，专注于核心去重功能，与现有分类器无缝集成
"""

import logging
import sqlite3
import pandas as pd
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

# 导入去重引擎和统一分类器
from app.material_deduplication_engine import (
    MaterialDeduplicationEngine, MaterialIdentity, DuplicationResult
)
from app.unified_classifier import ClassificationRequest, UnifiedMaterialClassifier

logger = logging.getLogger(__name__)

@dataclass
class DeduplicationRequest:
    """去重请求"""
    materials: List[Dict[str, Any]]
    source_systems: List[str]
    confidence_threshold: float = 0.75
    auto_merge_threshold: float = 0.85

@dataclass
class IntegratedDeduplicationResult:
    """集成去重结果"""
    duplicate_groups: List[DuplicationResult]
    statistics: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    processing_summary: Dict[str, Any]

class IntegratedDeduplicationManager:
    """集成去重管理器"""
    
    def __init__(self, mmp_db_path: str = 'business_data.db',
                 dedup_db_path: str = 'material_deduplication.db'):
        self.mmp_db_path = mmp_db_path
        self.dedup_db_path = dedup_db_path
        
        # 初始化去重引擎
        self.dedup_engine = MaterialDeduplicationEngine(dedup_db_path)
        
        # 初始化统一分类器（用于新物料分类）
        self.unified_classifier = UnifiedMaterialClassifier({
            'db_path': mmp_db_path
        })
        
        # 去重处理配置
        self.config = {
            'batch_size': 1000,
            'similarity_threshold': 0.75,
            'auto_merge_enabled': True,
            'auto_merge_threshold': 0.85,
            'require_manual_review_threshold': 0.65
        }
        
        logger.info("集成去重管理器初始化完成")
    
    def analyze_material_duplicates(self, request: DeduplicationRequest) -> IntegratedDeduplicationResult:
        """分析物料重复情况"""
        
        logger.info(f"开始去重分析，物料数量: {len(request.materials)}")
        
        # Step 1: 转换数据格式
        material_identities = self._convert_to_material_identities(
            request.materials, request.source_systems
        )
        
        # Step 2: 执行去重分析
        duplicate_results = self.dedup_engine.analyze_duplicates_batch(material_identities)
        
        # Step 3: 与现有MMP数据库对比
        enhanced_results = self._enhance_with_mmp_data(duplicate_results)
        
        # Step 4: 生成处理建议
        recommendations = self._generate_processing_recommendations(enhanced_results, request)
        
        # Step 5: 统计分析
        statistics = self._calculate_deduplication_statistics(enhanced_results, material_identities)
        
        # Step 6: 处理摘要
        processing_summary = self._create_processing_summary(enhanced_results, recommendations)
        
        return IntegratedDeduplicationResult(
            duplicate_groups=enhanced_results,
            statistics=statistics,
            recommendations=recommendations,
            processing_summary=processing_summary
        )
    
    def _convert_to_material_identities(self, materials: List[Dict[str, Any]], 
                                      source_systems: List[str]) -> List[MaterialIdentity]:
        """转换为MaterialIdentity格式"""
        
        identities = []
        
        for i, material in enumerate(materials):
            # 确定数据源系统
            source_system = source_systems[i] if i < len(source_systems) else 'unknown'
            
            # 提取标准字段
            identity = MaterialIdentity(
                material_code=material.get('material_code', f'MAT_{i:06d}'),
                source_system=source_system,
                material_name=material.get('material_name', material.get('name', '')),
                specifications=material.get('specification', material.get('spec', '')),
                manufacturer=material.get('manufacturer', material.get('mfg', '')),
                material_type=material.get('material_type', material.get('type', '')),
                unit=material.get('unit', ''),
                raw_attributes=material
            )
            
            identities.append(identity)
        
        return identities
    
    def _enhance_with_mmp_data(self, duplicate_results: List[DuplicationResult]) -> List[DuplicationResult]:
        """与现有MMP数据库数据进行增强对比"""
        
        enhanced_results = []
        
        conn = sqlite3.connect(self.mmp_db_path)
        
        for result in duplicate_results:
            try:
                # 查询MMP数据库中的相似物料
                master_material = result.master_material
                
                # 构建查询SQL
                query = '''
                SELECT material_name, category, specification, manufacturer 
                FROM material_categories 
                WHERE material_name LIKE ? 
                   OR specification LIKE ?
                LIMIT 10
                '''
                
                similar_params = (
                    f'%{master_material.material_name}%',
                    f'%{master_material.specifications}%'
                )
                
                df_similar = pd.read_sql(query, conn, params=similar_params)
                
                # 增强匹配信息
                if not df_similar.empty:
                    result.matching_dimensions['mmp_similar_materials'] = df_similar.to_dict('records')
                    
                    # 检查是否有完全匹配的分类
                    existing_categories = df_similar['category'].unique().tolist()
                    if existing_categories:
                        result.matching_dimensions['existing_categories'] = existing_categories
                        
                        # 如果有明确的分类，提高置信度
                        if len(set(existing_categories)) == 1:  # 所有相似物料都是同一分类
                            result.similarity_score = min(result.similarity_score + 0.1, 1.0)
                            result.recommended_action = 'merge_with_existing'
                
                enhanced_results.append(result)
                
            except Exception as e:
                logger.error(f"增强去重结果失败: {e}")
                enhanced_results.append(result)
        
        conn.close()
        return enhanced_results
    
    def _generate_processing_recommendations(self, results: List[DuplicationResult],
                                           request: DeduplicationRequest) -> List[Dict[str, Any]]:
        """生成处理建议"""
        
        recommendations = []
        
        for i, result in enumerate(results):
            recommendation = {
                'group_id': f'DUP_GROUP_{i:03d}',
                'master_material': {
                    'code': result.master_material.material_code,
                    'name': result.master_material.material_name,
                    'source': result.master_material.source_system
                },
                'duplicate_count': len(result.duplicate_materials),
                'similarity_score': result.similarity_score,
                'confidence_level': result.confidence_level
            }
            
            # 基于置信度和配置生成具体建议
            if result.similarity_score >= request.auto_merge_threshold:
                recommendation['action'] = 'auto_merge'
                recommendation['priority'] = 'high'
                recommendation['description'] = '高置信度重复，建议自动合并'
                
            elif result.similarity_score >= request.confidence_threshold:
                recommendation['action'] = 'manual_review'
                recommendation['priority'] = 'medium'
                recommendation['description'] = '中等置信度重复，需要人工审核'
                
            else:
                recommendation['action'] = 'separate'
                recommendation['priority'] = 'low'
                recommendation['description'] = '低置信度，可能不是重复物料'
            
            # 添加MMP集成建议
            if 'existing_categories' in result.matching_dimensions:
                existing_cats = result.matching_dimensions['existing_categories']
                if len(set(existing_cats)) == 1:
                    recommendation['mmp_integration'] = {
                        'suggested_category': existing_cats[0],
                        'integration_type': 'merge_to_existing'
                    }
                else:
                    recommendation['mmp_integration'] = {
                        'conflicting_categories': existing_cats,
                        'integration_type': 'resolve_conflicts'
                    }
            else:
                # 使用统一分类器为新物料分类
                classification_request = ClassificationRequest(
                    material_name=result.master_material.material_name,
                    specification=result.master_material.specifications,
                    manufacturer=result.master_material.manufacturer,
                    material_type=result.master_material.material_type,
                    unit=result.master_material.unit
                )
                
                try:
                    classification_result = self.unified_classifier.classify(classification_request)
                    recommendation['mmp_integration'] = {
                        'suggested_category': classification_result.predicted_category,
                        'classification_confidence': classification_result.confidence_score,
                        'integration_type': 'new_classification'
                    }
                except Exception as e:
                    logger.error(f"新物料分类失败: {e}")
                    recommendation['mmp_integration'] = {
                        'integration_type': 'manual_classification'
                    }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_deduplication_statistics(self, results: List[DuplicationResult],
                                          all_materials: List[MaterialIdentity]) -> Dict[str, Any]:
        """计算去重统计信息"""
        
        total_materials = len(all_materials)
        total_groups = len(results)
        
        # 统计各置信度级别的数量
        high_confidence = sum(1 for r in results if r.similarity_score >= 0.85)
        medium_confidence = sum(1 for r in results if 0.65 <= r.similarity_score < 0.85)
        low_confidence = sum(1 for r in results if r.similarity_score < 0.65)
        
        # 统计潜在重复物料数量
        duplicate_materials_count = sum(len(r.duplicate_materials) for r in results)
        
        # 按数据源统计
        source_distribution = {}
        for material in all_materials:
            source = material.source_system
            if source not in source_distribution:
                source_distribution[source] = {'total': 0, 'involved_in_duplicates': 0}
            source_distribution[source]['total'] += 1
        
        # 统计涉及重复的物料
        involved_materials = set()
        for result in results:
            involved_materials.add(result.master_material.material_code)
            for dup in result.duplicate_materials:
                involved_materials.add(dup.material_code)
        
        # 更新数据源分布中的重复涉及数量
        for material in all_materials:
            if material.material_code in involved_materials:
                source_distribution[material.source_system]['involved_in_duplicates'] += 1
        
        return {
            'total_materials': total_materials,
            'total_duplicate_groups': total_groups,
            'duplicate_materials_count': duplicate_materials_count,
            'duplication_rate': duplicate_materials_count / total_materials if total_materials > 0 else 0,
            'confidence_distribution': {
                'high': high_confidence,
                'medium': medium_confidence,
                'low': low_confidence
            },
            'source_distribution': source_distribution,
            'potential_savings': {
                'auto_mergeable': high_confidence,
                'requires_review': medium_confidence,
                'estimated_cleanup_materials': duplicate_materials_count
            }
        }
    
    def _create_processing_summary(self, results: List[DuplicationResult],
                                  recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建处理摘要"""
        
        auto_merge_count = sum(1 for r in recommendations if r['action'] == 'auto_merge')
        manual_review_count = sum(1 for r in recommendations if r['action'] == 'manual_review')
        separate_count = sum(1 for r in recommendations if r['action'] == 'separate')
        
        return {
            'processing_actions': {
                'auto_merge': auto_merge_count,
                'manual_review': manual_review_count,
                'separate': separate_count
            },
            'estimated_effort': {
                'automatic_processing': auto_merge_count,
                'manual_intervention_required': manual_review_count,
                'total_groups_to_process': len(results)
            },
            'next_steps': self._generate_next_steps(recommendations),
            'processing_timestamp': datetime.now().isoformat()
        }
    
    def _generate_next_steps(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """生成处理的下一步建议"""
        
        next_steps = []
        
        auto_merge_items = [r for r in recommendations if r['action'] == 'auto_merge']
        manual_review_items = [r for r in recommendations if r['action'] == 'manual_review']
        
        if auto_merge_items:
            next_steps.append(f"执行 {len(auto_merge_items)} 个高置信度重复组的自动合并")
        
        if manual_review_items:
            next_steps.append(f"安排人工审核 {len(manual_review_items)} 个中等置信度重复组")
        
        if auto_merge_items or manual_review_items:
            next_steps.append("更新主数据库，统一物料编码")
            next_steps.append("通知相关系统更新物料引用")
        
        next_steps.append("监控去重效果，收集用户反馈优化算法")
        
        return next_steps
    
    def execute_auto_merge(self, group_ids: List[str]) -> Dict[str, Any]:
        """执行自动合并操作"""
        
        logger.info(f"开始执行自动合并，组数: {len(group_ids)}")
        
        merge_results = []
        errors = []
        
        conn = sqlite3.connect(self.dedup_db_path)
        cursor = conn.cursor()
        
        try:
            for group_id in group_ids:
                try:
                    # 获取重复组信息
                    cursor.execute('''
                    SELECT * FROM duplicate_groups WHERE group_id = ?
                    ''', (group_id,))
                    
                    group_info = cursor.fetchone()
                    if not group_info:
                        errors.append(f"未找到组 {group_id}")
                        continue
                    
                    # 获取组成员
                    cursor.execute('''
                    SELECT material_code, source_system FROM duplicate_members 
                    WHERE group_id = ?
                    ''', (group_id,))
                    
                    members = cursor.fetchall()
                    
                    # 执行合并逻辑（这里简化处理）
                    master_code = group_info[1]  # master_material_code
                    duplicate_codes = [m[0] for m in members if m[0] != master_code]
                    
                    merge_result = {
                        'group_id': group_id,
                        'master_material_code': master_code,
                        'merged_materials': duplicate_codes,
                        'merge_timestamp': datetime.now().isoformat(),
                        'status': 'completed'
                    }
                    
                    merge_results.append(merge_result)
                    
                    # 更新数据库状态
                    cursor.execute('''
                    UPDATE duplicate_groups 
                    SET status = 'merged', reviewed_at = ?
                    WHERE group_id = ?
                    ''', (datetime.now().isoformat(), group_id))
                    
                except Exception as e:
                    error_msg = f"合并组 {group_id} 失败: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            conn.commit()
            
        finally:
            conn.close()
        
        return {
            'successful_merges': len(merge_results),
            'failed_merges': len(errors),
            'merge_details': merge_results,
            'errors': errors,
            'processing_timestamp': datetime.now().isoformat()
        }
    
    def get_deduplication_dashboard(self) -> Dict[str, Any]:
        """获取去重仪表板数据"""
        
        try:
            # 获取去重引擎的统计报告
            dedup_report = self.dedup_engine.get_deduplication_report()
            
            # 获取MMP系统的物料统计
            conn = sqlite3.connect(self.mmp_db_path)
            
            mmp_query = '''
            SELECT 
                COUNT(*) as total_materials,
                COUNT(DISTINCT category) as total_categories,
                COUNT(DISTINCT manufacturer) as total_manufacturers
            FROM material_categories
            '''
            
            df_mmp = pd.read_sql(mmp_query, conn)
            mmp_stats = df_mmp.to_dict('records')[0]
            
            conn.close()
            
            return {
                'deduplication_overview': dedup_report,
                'mmp_system_stats': mmp_stats,
                'integration_status': {
                    'dedup_engine_status': 'active',
                    'unified_classifier_status': 'active',
                    'last_analysis_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"获取仪表板数据失败: {e}")
            return {
                'error': str(e),
                'status': 'error'
            }

# 使用示例
def integration_example():
    """集成去重管理器使用示例"""
    
    # 初始化集成管理器
    manager = IntegratedDeduplicationManager()
    
    # 模拟物料数据
    test_materials = [
        {
            'material_code': 'M001_ERP',
            'material_name': '不锈钢球阀',
            'specification': 'DN100 PN16',
            'manufacturer': '上海阀门厂',
            'unit': '个'
        },
        {
            'material_code': 'MAT001_PLM', 
            'material_name': '304不锈钢球阀',
            'specification': 'DN100 压力16bar',
            'manufacturer': '上海阀门制造有限公司',
            'unit': '个'
        }
    ]
    
    # 创建去重请求
    request = DeduplicationRequest(
        materials=test_materials,
        source_systems=['ERP', 'PLM'],
        confidence_threshold=0.75,
        auto_merge_threshold=0.85
    )
    
    # 执行去重分析
    result = manager.analyze_material_duplicates(request)
    
    print("去重分析完成:")
    print(f"发现重复组: {len(result.duplicate_groups)}")
    print(f"处理建议: {len(result.recommendations)}")
    print(f"去重率: {result.statistics.get('duplication_rate', 0):.2%}")

if __name__ == "__main__":
    integration_example()