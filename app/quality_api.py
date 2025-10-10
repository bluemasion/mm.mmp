# -*- coding: utf-8 -*-
"""
质量评估API端点
为MMP系统提供质量评估服务接口
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any, List
import logging
import traceback
from datetime import datetime

from app.base_quality_assessment import (
    BaseQualityAssessment, QualityIntegratedClassifier
)
from app.unified_classifier import UnifiedMaterialClassifier

logger = logging.getLogger(__name__)

# 创建Blueprint
quality_bp = Blueprint('quality', __name__, url_prefix='/api/quality')

# 全局质量评估器实例
quality_assessor = None
integrated_classifier = None

def init_quality_assessment(app):
    """初始化质量评估系统"""
    global quality_assessor, integrated_classifier
    
    try:
        config_db_path = app.config.get('DATABASE_PATH', 'business_data.db')
        
        # 初始化质量评估器
        quality_assessor = BaseQualityAssessment(config_db_path)
        
        # 初始化统一分类器
        unified_classifier = UnifiedMaterialClassifier({
            'db_path': config_db_path
        })
        
        # 创建集成分类器
        integrated_classifier = QualityIntegratedClassifier(
            unified_classifier, quality_assessor
        )
        
        logger.info("质量评估系统初始化成功")
        
    except Exception as e:
        logger.error(f"质量评估系统初始化失败: {e}")
        raise

@quality_bp.route('/assess', methods=['POST'])
def assess_single_material():
    """
    评估单个物料的质量
    
    请求体：
    {
        "material_data": {
            "material_code": "M001",
            "material_name": "不锈钢球阀",
            "specification": "DN100 PN16",
            "manufacturer": "上海阀门厂",
            "material_type": "阀门",
            "unit": "个"
        }
    }
    """
    
    try:
        if not quality_assessor:
            return jsonify({
                'success': False,
                'error': '质量评估系统未初始化'
            }), 500
        
        data = request.get_json()
        
        if not data or 'material_data' not in data:
            return jsonify({
                'success': False,
                'error': '缺少material_data字段'
            }), 400
        
        material_data = data['material_data']
        
        # 执行质量评估
        quality_result = quality_assessor.assess_material_quality(material_data)
        
        return jsonify({
            'success': True,
            'data': {
                'overall_score': quality_result.overall_score,
                'quality_grade': quality_result.quality_grade,
                'dimension_scores': quality_result.dimension_scores,
                'quality_issues': quality_result.quality_issues,
                'improvement_suggestions': quality_result.improvement_suggestions
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"单个物料质量评估失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'质量评估失败: {str(e)}'
        }), 500

@quality_bp.route('/batch-assess', methods=['POST'])
def assess_batch_materials():
    """
    批量评估物料质量
    
    请求体：
    {
        "materials": [
            {
                "material_code": "M001",
                "material_name": "不锈钢球阀",
                "specification": "DN100 PN16",
                "manufacturer": "上海阀门厂"
            }
        ]
    }
    """
    
    try:
        if not quality_assessor:
            return jsonify({
                'success': False,
                'error': '质量评估系统未初始化'
            }), 500
        
        data = request.get_json()
        
        if not data or 'materials' not in data:
            return jsonify({
                'success': False,
                'error': '缺少materials字段'
            }), 400
        
        materials = data['materials']
        
        if not isinstance(materials, list) or len(materials) == 0:
            return jsonify({
                'success': False,
                'error': 'materials必须是非空数组'
            }), 400
        
        # 执行批量质量评估
        batch_result = quality_assessor.assess_batch_materials(materials)
        
        return jsonify({
            'success': True,
            'data': batch_result,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"批量质量评估失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'批量质量评估失败: {str(e)}'
        }), 500

@quality_bp.route('/classify-with-quality', methods=['POST'])
def classify_with_quality_assessment():
    """
    执行分类并进行质量评估
    
    请求体：
    {
        "material_name": "不锈钢球阀",
        "specification": "DN100 PN16",
        "manufacturer": "上海阀门厂",
        "material_type": "阀门",
        "unit": "个"
    }
    """
    
    try:
        if not integrated_classifier:
            return jsonify({
                'success': False,
                'error': '集成分类器未初始化'
            }), 500
        
        data = request.get_json()
        
        if not data or 'material_name' not in data:
            return jsonify({
                'success': False,
                'error': '缺少material_name字段'
            }), 400
        
        # 创建分类请求对象
        from app.unified_classifier import ClassificationRequest
        
        classification_request = ClassificationRequest(
            material_name=data['material_name'],
            specification=data.get('specification', ''),
            manufacturer=data.get('manufacturer', ''),
            material_type=data.get('material_type', ''),
            unit=data.get('unit', '')
        )
        
        # 执行集成分类和质量评估
        result = integrated_classifier.classify_with_quality(classification_request)
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"集成分类质量评估失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'集成分类质量评估失败: {str(e)}'
        }), 500

@quality_bp.route('/dimensions', methods=['GET'])
def get_quality_dimensions():
    """获取质量评估维度信息"""
    
    try:
        if not quality_assessor:
            return jsonify({
                'success': False,
                'error': '质量评估系统未初始化'
            }), 500
        
        dimensions_info = {}
        
        for dim_key, dimension in quality_assessor.quality_dimensions.items():
            dimensions_info[dim_key] = {
                'name': dimension.name,
                'weight': dimension.weight,
                'description': dimension.description,
                'scoring_rules': dimension.scoring_rules
            }
        
        return jsonify({
            'success': True,
            'data': {
                'quality_dimensions': dimensions_info,
                'quality_grades': quality_assessor.quality_grades,
                'total_weight': sum(dim.weight for dim in quality_assessor.quality_dimensions.values())
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"获取质量维度信息失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'获取质量维度信息失败: {str(e)}'
        }), 500

@quality_bp.route('/report', methods=['POST'])
def generate_quality_report():
    """
    生成质量报告
    
    请求体：
    {
        "source": "database|materials",
        "materials": [...],  // 当source为materials时必填
        "filters": {
            "category": "阀门",
            "manufacturer": "上海阀门厂",
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            }
        }
    }
    """
    
    try:
        if not quality_assessor:
            return jsonify({
                'success': False,
                'error': '质量评估系统未初始化'
            }), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少请求数据'
            }), 400
        
        source = data.get('source', 'materials')
        
        if source == 'materials':
            # 使用提供的物料数据
            materials = data.get('materials', [])
            if not materials:
                return jsonify({
                    'success': False,
                    'error': '当source为materials时，必须提供materials数据'
                }), 400
            
        elif source == 'database':
            # 从数据库获取物料数据（简化实现）
            import sqlite3
            import pandas as pd
            
            conn = sqlite3.connect(quality_assessor.config_db_path)
            
            # 构建查询
            query = "SELECT * FROM material_categories"
            filters = data.get('filters', {})
            conditions = []
            params = []
            
            if filters.get('category'):
                conditions.append("category = ?")
                params.append(filters['category'])
            
            if filters.get('manufacturer'):
                conditions.append("manufacturer = ?")
                params.append(filters['manufacturer'])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " LIMIT 1000"  # 限制查询数量
            
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            
            materials = df.to_dict('records')
            
        else:
            return jsonify({
                'success': False,
                'error': 'source参数必须是database或materials'
            }), 400
        
        # 执行批量质量评估
        batch_result = quality_assessor.assess_batch_materials(materials)
        
        return jsonify({
            'success': True,
            'data': {
                'report_type': 'quality_assessment',
                'source': source,
                'batch_results': batch_result,
                'report_generated_at': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"生成质量报告失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'生成质量报告失败: {str(e)}'
        }), 500

@quality_bp.route('/statistics', methods=['GET'])
def get_quality_statistics():
    """获取质量统计信息"""
    
    try:
        # 这里可以从数据库获取历史质量统计
        # 暂时返回示例统计数据
        
        statistics = {
            'overall_quality_trend': {
                'current_month': {'average_score': 78.5, 'grade_A_rate': 0.25},
                'previous_month': {'average_score': 76.2, 'grade_A_rate': 0.22},
                'improvement': {'score_change': 2.3, 'grade_change': 0.03}
            },
            'dimension_performance': {
                'completeness': 82.1,
                'accuracy': 75.3,
                'consistency': 79.8,
                'richness': 68.4,
                'reliability': 81.2
            },
            'common_issues': [
                {'issue': '缺少必填字段', 'frequency': 156, 'percentage': 23.5},
                {'issue': '规格参数信息不完整', 'frequency': 142, 'percentage': 21.4},
                {'issue': '制造商信息过于简略', 'frequency': 98, 'percentage': 14.8}
            ],
            'quality_distribution': {
                'A': 167,  # 优秀
                'B': 289,  # 良好  
                'C': 198,  # 一般
                'D': 89    # 差
            }
        }
        
        return jsonify({
            'success': True,
            'data': statistics,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"获取质量统计失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'获取质量统计失败: {str(e)}'
        }), 500

@quality_bp.route('/status', methods=['GET'])
def get_quality_service_status():
    """获取质量评估服务状态"""
    
    try:
        status_info = {
            'quality_assessor_status': 'active' if quality_assessor else 'inactive',
            'integrated_classifier_status': 'active' if integrated_classifier else 'inactive',
            'supported_dimensions': list(quality_assessor.quality_dimensions.keys()) if quality_assessor else [],
            'quality_grades': list(quality_assessor.quality_grades.keys()) if quality_assessor else [],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': status_info
        }), 200
        
    except Exception as e:
        logger.error(f"获取质量服务状态失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'获取质量服务状态失败: {str(e)}'
        }), 500

# 错误处理
@quality_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@quality_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': '请求方法不被允许'
    }), 405

@quality_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '内部服务器错误'
    }), 500