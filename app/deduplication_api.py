# -*- coding: utf-8 -*-
"""
去重功能API端点
为MMP系统提供RESTful去重服务接口
"""

from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, List
import logging
import traceback
from datetime import datetime

from app.integrated_deduplication_manager import (
    IntegratedDeduplicationManager, DeduplicationRequest
)

logger = logging.getLogger(__name__)

# 创建Blueprint
deduplication_bp = Blueprint('deduplication', __name__, url_prefix='/api/deduplication')

# 全局去重管理器实例
dedup_manager = None

def init_deduplication_manager(app):
    """初始化去重管理器"""
    global dedup_manager
    
    try:
        mmp_db_path = app.config.get('DATABASE_PATH', 'business_data.db')
        dedup_db_path = app.config.get('DEDUP_DATABASE_PATH', 'material_deduplication.db')
        
        dedup_manager = IntegratedDeduplicationManager(
            mmp_db_path=mmp_db_path,
            dedup_db_path=dedup_db_path
        )
        
        logger.info("去重管理器初始化成功")
        
    except Exception as e:
        logger.error(f"去重管理器初始化失败: {e}")
        raise

@deduplication_bp.route('/analyze', methods=['POST'])
def analyze_duplicates():
    """
    分析物料重复情况
    
    请求体：
    {
        "materials": [
            {
                "material_code": "M001",
                "material_name": "不锈钢球阀",
                "specification": "DN100 PN16",
                "manufacturer": "上海阀门厂",
                "unit": "个"
            }
        ],
        "source_systems": ["ERP", "PLM"],
        "confidence_threshold": 0.75,
        "auto_merge_threshold": 0.85
    }
    """
    
    try:
        if not dedup_manager:
            return jsonify({
                'success': False,
                'error': '去重管理器未初始化'
            }), 500
        
        data = request.get_json()
        
        # 验证请求数据
        if not data or 'materials' not in data:
            return jsonify({
                'success': False,
                'error': '缺少materials字段'
            }), 400
        
        materials = data['materials']
        source_systems = data.get('source_systems', ['unknown'] * len(materials))
        confidence_threshold = data.get('confidence_threshold', 0.75)
        auto_merge_threshold = data.get('auto_merge_threshold', 0.85)
        
        # 验证materials数据
        if not isinstance(materials, list) or len(materials) == 0:
            return jsonify({
                'success': False,
                'error': 'materials必须是非空数组'
            }), 400
        
        # 创建去重请求
        dedup_request = DeduplicationRequest(
            materials=materials,
            source_systems=source_systems,
            confidence_threshold=confidence_threshold,
            auto_merge_threshold=auto_merge_threshold
        )
        
        # 执行去重分析
        result = dedup_manager.analyze_material_duplicates(dedup_request)
        
        # 格式化返回结果
        response_data = {
            'success': True,
            'data': {
                'duplicate_groups': [
                    {
                        'group_id': f'DUP_GROUP_{i:03d}',
                        'master_material': {
                            'code': group.master_material.material_code,
                            'name': group.master_material.material_name,
                            'source': group.master_material.source_system
                        },
                        'duplicate_materials': [
                            {
                                'code': dup.material_code,
                                'name': dup.material_name,
                                'source': dup.source_system
                            } for dup in group.duplicate_materials
                        ],
                        'similarity_score': group.similarity_score,
                        'confidence_level': group.confidence_level,
                        'recommended_action': group.recommended_action
                    } for i, group in enumerate(result.duplicate_groups)
                ],
                'statistics': result.statistics,
                'processing_summary': result.processing_summary
            },
            'recommendations': result.recommendations,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"去重分析失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'去重分析失败: {str(e)}'
        }), 500

@deduplication_bp.route('/merge', methods=['POST'])
def execute_merge():
    """
    执行自动合并
    
    请求体：
    {
        "group_ids": ["DUP_GROUP_001", "DUP_GROUP_002"]
    }
    """
    
    try:
        if not dedup_manager:
            return jsonify({
                'success': False,
                'error': '去重管理器未初始化'
            }), 500
        
        data = request.get_json()
        
        if not data or 'group_ids' not in data:
            return jsonify({
                'success': False,
                'error': '缺少group_ids字段'
            }), 400
        
        group_ids = data['group_ids']
        
        if not isinstance(group_ids, list) or len(group_ids) == 0:
            return jsonify({
                'success': False,
                'error': 'group_ids必须是非空数组'
            }), 400
        
        # 执行自动合并
        merge_result = dedup_manager.execute_auto_merge(group_ids)
        
        return jsonify({
            'success': True,
            'data': merge_result,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"自动合并失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'自动合并失败: {str(e)}'
        }), 500

@deduplication_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """
    获取去重仪表板数据
    """
    
    try:
        if not dedup_manager:
            return jsonify({
                'success': False,
                'error': '去重管理器未初始化'
            }), 500
        
        dashboard_data = dedup_manager.get_deduplication_dashboard()
        
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"获取仪表板数据失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'获取仪表板数据失败: {str(e)}'
        }), 500

@deduplication_bp.route('/batch-analyze', methods=['POST'])
def batch_analyze():
    """
    批量分析多个数据源的重复情况
    
    请求体：
    {
        "data_sources": [
            {
                "source_name": "ERP系统",
                "materials": [...],
                "batch_size": 1000
            },
            {
                "source_name": "PLM系统", 
                "materials": [...],
                "batch_size": 1000
            }
        ],
        "global_settings": {
            "confidence_threshold": 0.75,
            "auto_merge_threshold": 0.85,
            "cross_source_analysis": true
        }
    }
    """
    
    try:
        if not dedup_manager:
            return jsonify({
                'success': False,
                'error': '去重管理器未初始化'
            }), 500
        
        data = request.get_json()
        
        if not data or 'data_sources' not in data:
            return jsonify({
                'success': False,
                'error': '缺少data_sources字段'
            }), 400
        
        data_sources = data['data_sources']
        global_settings = data.get('global_settings', {})
        
        # 汇总所有物料
        all_materials = []
        all_source_systems = []
        
        for source in data_sources:
            source_name = source.get('source_name', 'unknown')
            materials = source.get('materials', [])
            
            all_materials.extend(materials)
            all_source_systems.extend([source_name] * len(materials))
        
        # 创建统一的去重请求
        dedup_request = DeduplicationRequest(
            materials=all_materials,
            source_systems=all_source_systems,
            confidence_threshold=global_settings.get('confidence_threshold', 0.75),
            auto_merge_threshold=global_settings.get('auto_merge_threshold', 0.85)
        )
        
        # 执行批量分析
        result = dedup_manager.analyze_material_duplicates(dedup_request)
        
        # 按数据源组织结果
        source_specific_results = {}
        cross_source_duplicates = []
        
        for i, group in enumerate(result.duplicate_groups):
            group_sources = set()
            group_sources.add(group.master_material.source_system)
            
            for dup in group.duplicate_materials:
                group_sources.add(dup.source_system)
            
            group_data = {
                'group_id': f'BATCH_DUP_GROUP_{i:03d}',
                'master_material': group.master_material,
                'duplicate_materials': group.duplicate_materials,
                'similarity_score': group.similarity_score,
                'involved_sources': list(group_sources)
            }
            
            if len(group_sources) > 1:
                cross_source_duplicates.append(group_data)
            else:
                source = list(group_sources)[0]
                if source not in source_specific_results:
                    source_specific_results[source] = []
                source_specific_results[source].append(group_data)
        
        return jsonify({
            'success': True,
            'data': {
                'overall_statistics': result.statistics,
                'source_specific_results': source_specific_results,
                'cross_source_duplicates': cross_source_duplicates,
                'processing_summary': result.processing_summary
            },
            'recommendations': result.recommendations,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"批量分析失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'批量分析失败: {str(e)}'
        }), 500

@deduplication_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    提交用户反馈用于算法优化
    
    请求体：
    {
        "group_id": "DUP_GROUP_001",
        "user_decision": "merge|separate|uncertain",
        "feedback_notes": "用户的具体反馈",
        "material_pairs": [
            {
                "material_1": "M001",
                "material_2": "M002", 
                "user_similarity": 0.9,
                "should_merge": true
            }
        ]
    }
    """
    
    try:
        if not dedup_manager:
            return jsonify({
                'success': False,
                'error': '去重管理器未初始化'
            }), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少请求数据'
            }), 400
        
        # 提取反馈数据
        group_id = data.get('group_id')
        user_decision = data.get('user_decision')
        feedback_notes = data.get('feedback_notes', '')
        material_pairs = data.get('material_pairs', [])
        
        # 调用去重引擎的反馈接口
        feedback_result = dedup_manager.dedup_engine.submit_user_feedback(
            group_id=group_id,
            user_decision=user_decision,
            feedback_notes=feedback_notes
        )
        
        # 处理物料对反馈
        for pair in material_pairs:
            dedup_manager.dedup_engine.update_similarity_feedback(
                material_1_code=pair.get('material_1'),
                material_2_code=pair.get('material_2'),
                user_similarity=pair.get('user_similarity'),
                should_merge=pair.get('should_merge')
            )
        
        return jsonify({
            'success': True,
            'data': {
                'feedback_processed': True,
                'feedback_id': feedback_result.get('feedback_id'),
                'pairs_updated': len(material_pairs)
            },
            'message': '反馈已提交，将用于算法优化',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"提交反馈失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'提交反馈失败: {str(e)}'
        }), 500

@deduplication_bp.route('/status', methods=['GET'])
def get_status():
    """获取去重服务状态"""
    
    try:
        status_info = {
            'service_status': 'active' if dedup_manager else 'inactive',
            'timestamp': datetime.now().isoformat()
        }
        
        if dedup_manager:
            # 获取更详细的状态信息
            dashboard_data = dedup_manager.get_deduplication_dashboard()
            status_info.update({
                'dedup_engine_status': dashboard_data.get('integration_status', {}).get('dedup_engine_status'),
                'unified_classifier_status': dashboard_data.get('integration_status', {}).get('unified_classifier_status'),
                'last_analysis_time': dashboard_data.get('integration_status', {}).get('last_analysis_time')
            })
        
        return jsonify({
            'success': True,
            'data': status_info
        }), 200
        
    except Exception as e:
        logger.error(f"获取服务状态失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'获取服务状态失败: {str(e)}'
        }), 500

# 错误处理
@deduplication_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@deduplication_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': '请求方法不被允许'
    }), 405

@deduplication_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '内部服务器错误'
    }), 500