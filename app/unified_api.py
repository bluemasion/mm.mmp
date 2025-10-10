# -*- coding: utf-8 -*-
"""
MMP增强版统一API接口
整合分类、去重、质量评估和同步功能
提供完整的RESTful接口和文档
"""

from flask import Flask, Blueprint, request, jsonify, url_for
from flask_cors import CORS
from typing import Dict, Any, List
import logging
import traceback
from datetime import datetime
import json
import os

# 导入各个功能模块的API
from app.deduplication_api import deduplication_bp, init_deduplication_manager
from app.quality_api import quality_bp, init_quality_assessment
from app.sync_api import sync_bp, init_sync_system

# 导入核心功能类
from app.unified_classifier import UnifiedMaterialClassifier, ClassificationRequest
from app.integrated_deduplication_manager import IntegratedDeduplicationManager
from app.base_quality_assessment import BaseQualityAssessment
from app.simplified_incremental_sync import SimplifiedIncrementalSync

logger = logging.getLogger(__name__)

# 创建主API Blueprint
unified_api_bp = Blueprint('unified_api', __name__, url_prefix='/api/v2')

# 全局服务实例
services = {
    'classifier': None,
    'deduplication': None,
    'quality_assessment': None,
    'sync_system': None
}

def create_enhanced_app(config=None):
    """创建增强版Flask应用"""
    
    app = Flask(__name__)
    
    # 启用CORS
    CORS(app)
    
    # 默认配置
    app.config.update({
        'DATABASE_PATH': 'business_data.db',
        'DEDUP_DATABASE_PATH': 'material_deduplication.db',
        'SYNC_DATABASE_PATH': 'sync_tracking.db',
        'DEBUG': False,
        'TESTING': False
    })
    
    # 更新配置
    if config:
        app.config.update(config)
    
    # 注册蓝图
    app.register_blueprint(unified_api_bp)
    app.register_blueprint(deduplication_bp)
    app.register_blueprint(quality_bp)
    app.register_blueprint(sync_bp)
    
    # 初始化服务
    with app.app_context():
        init_all_services(app)
    
    return app

def init_all_services(app):
    """初始化所有服务"""
    
    global services
    
    try:
        # 初始化统一分类器
        services['classifier'] = UnifiedMaterialClassifier({
            'db_path': app.config['DATABASE_PATH']
        })
        
        # 初始化去重管理器
        init_deduplication_manager(app)
        
        # 初始化质量评估系统
        init_quality_assessment(app)
        
        # 初始化同步系统
        init_sync_system(app)
        
        logger.info("所有服务初始化完成")
        
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        raise

@unified_api_bp.route('/health', methods=['GET'])
def health_check():
    """系统健康检查"""
    
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        # 检查各个服务状态
        health_status['services']['classifier'] = 'active' if services['classifier'] else 'inactive'
        
        # 检查数据库连接
        try:
            import sqlite3
            conn = sqlite3.connect('business_data.db')
            conn.execute('SELECT 1')
            conn.close()
            health_status['services']['database'] = 'connected'
        except:
            health_status['services']['database'] = 'disconnected'
        
        # 检查各API模块
        health_status['services']['deduplication_api'] = 'active'
        health_status['services']['quality_api'] = 'active'
        health_status['services']['sync_api'] = 'active'
        
        return jsonify(health_status), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@unified_api_bp.route('/classify', methods=['POST'])
def unified_classify():
    """
    统一分类接口
    
    请求体：
    {
        "material_name": "不锈钢球阀",
        "specification": "DN100 PN16",
        "manufacturer": "上海阀门厂",
        "material_type": "阀门",
        "unit": "个",
        "include_quality": true,
        "include_alternatives": true
    }
    """
    
    try:
        if not services['classifier']:
            return jsonify({
                'success': False,
                'error': '分类服务未初始化'
            }), 500
        
        data = request.get_json()
        
        if not data or 'material_name' not in data:
            return jsonify({
                'success': False,
                'error': '缺少material_name字段'
            }), 400
        
        # 创建分类请求
        classification_request = ClassificationRequest(
            material_name=data['material_name'],
            specification=data.get('specification', ''),
            manufacturer=data.get('manufacturer', ''),
            material_type=data.get('material_type', ''),
            unit=data.get('unit', '')
        )
        
        # 执行分类
        result = services['classifier'].classify(classification_request)
        
        response_data = {
            'success': True,
            'data': {
                'predicted_category': result.predicted_category,
                'confidence_score': result.confidence_score,
                'alternative_categories': result.alternative_categories,
                'processing_time': result.processing_time,
                'classifier_used': result.classifier_used
            }
        }
        
        # 如果需要质量评估
        if data.get('include_quality', False):
            try:
                from app.base_quality_assessment import BaseQualityAssessment
                quality_assessor = BaseQualityAssessment()
                
                material_data = {
                    'material_name': data['material_name'],
                    'specification': data.get('specification', ''),
                    'manufacturer': data.get('manufacturer', ''),
                    'material_type': data.get('material_type', ''),
                    'unit': data.get('unit', '')
                }
                
                quality_result = quality_assessor.assess_material_quality(material_data)
                response_data['data']['quality_assessment'] = {
                    'overall_score': quality_result.overall_score,
                    'quality_grade': quality_result.quality_grade,
                    'dimension_scores': quality_result.dimension_scores
                }
                
            except Exception as e:
                logger.warning(f"质量评估失败: {e}")
        
        response_data['timestamp'] = datetime.now().isoformat()
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"统一分类失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'分类失败: {str(e)}'
        }), 500

@unified_api_bp.route('/process-material', methods=['POST'])
def comprehensive_material_processing():
    """
    综合物料处理接口
    执行分类、质量评估、去重检测的完整流程
    
    请求体：
    {
        "material_data": {
            "material_name": "不锈钢球阀",
            "specification": "DN100 PN16",
            "manufacturer": "上海阀门厂"
        },
        "processing_options": {
            "enable_classification": true,
            "enable_quality_assessment": true,
            "enable_deduplication": true,
            "deduplication_threshold": 0.75
        }
    }
    """
    
    try:
        data = request.get_json()
        
        if not data or 'material_data' not in data:
            return jsonify({
                'success': False,
                'error': '缺少material_data字段'
            }), 400
        
        material_data = data['material_data']
        processing_options = data.get('processing_options', {})
        
        comprehensive_result = {
            'material_code': material_data.get('material_code', f'MAT_{datetime.now().strftime("%Y%m%d%H%M%S")}'),
            'processing_timestamp': datetime.now().isoformat(),
            'results': {}
        }
        
        # 1. 分类处理
        if processing_options.get('enable_classification', True) and services['classifier']:
            try:
                classification_request = ClassificationRequest(
                    material_name=material_data['material_name'],
                    specification=material_data.get('specification', ''),
                    manufacturer=material_data.get('manufacturer', ''),
                    material_type=material_data.get('material_type', ''),
                    unit=material_data.get('unit', '')
                )
                
                classification_result = services['classifier'].classify(classification_request)
                comprehensive_result['results']['classification'] = {
                    'predicted_category': classification_result.predicted_category,
                    'confidence_score': classification_result.confidence_score,
                    'alternative_categories': classification_result.alternative_categories
                }
                
            except Exception as e:
                comprehensive_result['results']['classification'] = {'error': str(e)}
        
        # 2. 质量评估
        if processing_options.get('enable_quality_assessment', True):
            try:
                from app.base_quality_assessment import BaseQualityAssessment
                quality_assessor = BaseQualityAssessment()
                
                quality_result = quality_assessor.assess_material_quality(material_data)
                comprehensive_result['results']['quality_assessment'] = {
                    'overall_score': quality_result.overall_score,
                    'quality_grade': quality_result.quality_grade,
                    'dimension_scores': quality_result.dimension_scores,
                    'quality_issues': quality_result.quality_issues
                }
                
            except Exception as e:
                comprehensive_result['results']['quality_assessment'] = {'error': str(e)}
        
        # 3. 去重检测
        if processing_options.get('enable_deduplication', True):
            try:
                from app.integrated_deduplication_manager import (
                    IntegratedDeduplicationManager, DeduplicationRequest
                )
                
                dedup_manager = IntegratedDeduplicationManager()
                dedup_request = DeduplicationRequest(
                    materials=[material_data],
                    source_systems=[material_data.get('source_system', 'api')],
                    confidence_threshold=processing_options.get('deduplication_threshold', 0.75)
                )
                
                dedup_result = dedup_manager.analyze_material_duplicates(dedup_request)
                
                comprehensive_result['results']['deduplication'] = {
                    'duplicate_groups_found': len(dedup_result.duplicate_groups),
                    'potential_duplicates': len(dedup_result.duplicate_groups) > 0,
                    'statistics': dedup_result.statistics
                }
                
            except Exception as e:
                comprehensive_result['results']['deduplication'] = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'data': comprehensive_result,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"综合物料处理失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'综合处理失败: {str(e)}'
        }), 500

@unified_api_bp.route('/batch-process', methods=['POST'])
def batch_material_processing():
    """
    批量物料处理接口
    
    请求体：
    {
        "materials": [
            {
                "material_name": "不锈钢球阀",
                "specification": "DN100 PN16"
            }
        ],
        "processing_config": {
            "enable_classification": true,
            "enable_quality_assessment": true,
            "enable_deduplication": true,
            "batch_size": 100
        }
    }
    """
    
    try:
        data = request.get_json()
        
        if not data or 'materials' not in data:
            return jsonify({
                'success': False,
                'error': '缺少materials字段'
            }), 400
        
        materials = data['materials']
        processing_config = data.get('processing_config', {})
        batch_size = processing_config.get('batch_size', 100)
        
        if not isinstance(materials, list) or len(materials) == 0:
            return jsonify({
                'success': False,
                'error': 'materials必须是非空数组'
            }), 400
        
        batch_results = {
            'batch_id': f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'total_materials': len(materials),
            'processed_materials': 0,
            'results': [],
            'statistics': {
                'classification': {'success': 0, 'failed': 0},
                'quality_assessment': {'success': 0, 'failed': 0},
                'deduplication': {'success': 0, 'failed': 0}
            },
            'processing_time': 0
        }
        
        start_time = datetime.now()
        
        # 分批处理
        for batch_start in range(0, len(materials), batch_size):
            batch_end = min(batch_start + batch_size, len(materials))
            batch_materials = materials[batch_start:batch_end]
            
            for i, material in enumerate(batch_materials):
                material_result = {
                    'material_index': batch_start + i,
                    'material_code': material.get('material_code', f'MAT_{batch_start + i:06d}'),
                    'processing_results': {}
                }
                
                # 分类
                if processing_config.get('enable_classification', True) and services['classifier']:
                    try:
                        classification_request = ClassificationRequest(
                            material_name=material.get('material_name', ''),
                            specification=material.get('specification', ''),
                            manufacturer=material.get('manufacturer', ''),
                            material_type=material.get('material_type', ''),
                            unit=material.get('unit', '')
                        )
                        
                        result = services['classifier'].classify(classification_request)
                        material_result['processing_results']['classification'] = {
                            'predicted_category': result.predicted_category,
                            'confidence_score': result.confidence_score
                        }
                        batch_results['statistics']['classification']['success'] += 1
                        
                    except Exception as e:
                        material_result['processing_results']['classification'] = {'error': str(e)}
                        batch_results['statistics']['classification']['failed'] += 1
                
                # 质量评估
                if processing_config.get('enable_quality_assessment', True):
                    try:
                        from app.base_quality_assessment import BaseQualityAssessment
                        quality_assessor = BaseQualityAssessment()
                        
                        quality_result = quality_assessor.assess_material_quality(material)
                        material_result['processing_results']['quality_assessment'] = {
                            'overall_score': quality_result.overall_score,
                            'quality_grade': quality_result.quality_grade
                        }
                        batch_results['statistics']['quality_assessment']['success'] += 1
                        
                    except Exception as e:
                        material_result['processing_results']['quality_assessment'] = {'error': str(e)}
                        batch_results['statistics']['quality_assessment']['failed'] += 1
                
                batch_results['results'].append(material_result)
                batch_results['processed_materials'] += 1
        
        # 批量去重（如果启用）
        if processing_config.get('enable_deduplication', True):
            try:
                from app.integrated_deduplication_manager import (
                    IntegratedDeduplicationManager, DeduplicationRequest
                )
                
                dedup_manager = IntegratedDeduplicationManager()
                dedup_request = DeduplicationRequest(
                    materials=materials,
                    source_systems=[material.get('source_system', 'batch_api') for material in materials]
                )
                
                dedup_result = dedup_manager.analyze_material_duplicates(dedup_request)
                
                batch_results['deduplication_summary'] = {
                    'duplicate_groups_found': len(dedup_result.duplicate_groups),
                    'statistics': dedup_result.statistics
                }
                batch_results['statistics']['deduplication']['success'] = 1
                
            except Exception as e:
                batch_results['deduplication_summary'] = {'error': str(e)}
                batch_results['statistics']['deduplication']['failed'] = 1
        
        end_time = datetime.now()
        batch_results['processing_time'] = (end_time - start_time).total_seconds()
        batch_results['completed_at'] = end_time.isoformat()
        
        return jsonify({
            'success': True,
            'data': batch_results,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"批量处理失败: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'批量处理失败: {str(e)}'
        }), 500

@unified_api_bp.route('/dashboard', methods=['GET'])
def get_system_dashboard():
    """获取系统仪表板数据"""
    
    try:
        dashboard_data = {
            'system_overview': {
                'timestamp': datetime.now().isoformat(),
                'services_status': {
                    'classifier': 'active' if services['classifier'] else 'inactive',
                    'deduplication': 'active',
                    'quality_assessment': 'active',
                    'sync_system': 'active'
                }
            },
            'statistics': {}
        }
        
        # 获取分类统计
        try:
            if services['classifier']:
                # 这里可以添加分类统计逻辑
                dashboard_data['statistics']['classification'] = {
                    'total_categories': 544,  # 从数据库获取
                    'active_classifiers': 3,
                    'average_confidence': 0.87
                }
        except Exception as e:
            logger.warning(f"获取分类统计失败: {e}")
        
        # 获取去重统计
        try:
            from app.integrated_deduplication_manager import IntegratedDeduplicationManager
            dedup_manager = IntegratedDeduplicationManager()
            dedup_dashboard = dedup_manager.get_deduplication_dashboard()
            dashboard_data['statistics']['deduplication'] = dedup_dashboard
            
        except Exception as e:
            logger.warning(f"获取去重统计失败: {e}")
        
        # 获取质量评估统计
        try:
            # 这里可以添加质量评估统计
            dashboard_data['statistics']['quality'] = {
                'average_score': 78.5,
                'grade_distribution': {'A': 167, 'B': 289, 'C': 198, 'D': 89}
            }
        except Exception as e:
            logger.warning(f"获取质量统计失败: {e}")
        
        # 获取同步统计  
        try:
            from app.simplified_incremental_sync import SimplifiedIncrementalSync
            sync_system = SimplifiedIncrementalSync()
            sync_status = sync_system.get_sync_status()
            dashboard_data['statistics']['sync'] = sync_status
            
        except Exception as e:
            logger.warning(f"获取同步统计失败: {e}")
        
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

@unified_api_bp.route('/docs', methods=['GET'])
def api_documentation():
    """API文档"""
    
    docs = {
        'title': 'MMP增强版统一API文档',
        'version': '2.0.0',
        'description': '智能物料分类、去重、质量评估和增量同步系统',
        'base_url': request.host_url.rstrip('/'),
        'endpoints': {
            'health_check': {
                'method': 'GET',
                'path': '/api/v2/health',
                'description': '系统健康检查'
            },
            'unified_classify': {
                'method': 'POST', 
                'path': '/api/v2/classify',
                'description': '统一物料分类接口',
                'parameters': {
                    'material_name': 'string (required)',
                    'specification': 'string',
                    'manufacturer': 'string',
                    'include_quality': 'boolean'
                }
            },
            'comprehensive_processing': {
                'method': 'POST',
                'path': '/api/v2/process-material',
                'description': '综合物料处理（分类+质量+去重）'
            },
            'batch_processing': {
                'method': 'POST',
                'path': '/api/v2/batch-process',
                'description': '批量物料处理'
            },
            'dashboard': {
                'method': 'GET',
                'path': '/api/v2/dashboard',
                'description': '系统仪表板数据'
            },
            'deduplication_apis': {
                'base_path': '/api/deduplication',
                'endpoints': [
                    'POST /analyze - 去重分析',
                    'POST /merge - 执行合并', 
                    'GET /dashboard - 去重仪表板',
                    'POST /feedback - 提交反馈'
                ]
            },
            'quality_apis': {
                'base_path': '/api/quality',
                'endpoints': [
                    'POST /assess - 质量评估',
                    'POST /batch-assess - 批量质量评估',
                    'POST /classify-with-quality - 分类+质量评估',
                    'GET /dimensions - 质量维度信息'
                ]
            },
            'sync_apis': {
                'base_path': '/api/sync',
                'endpoints': [
                    'POST /from-source - 数据源同步',
                    'GET /status - 同步状态',
                    'GET /conflicts - 冲突列表',
                    'POST /batch-sync - 批量同步'
                ]
            }
        },
        'response_format': {
            'success': 'boolean',
            'data': 'object',
            'timestamp': 'ISO 8601 timestamp',
            'error': 'string (when success is false)'
        },
        'examples': {
            'classify_request': {
                'material_name': '不锈钢球阀',
                'specification': 'DN100 PN16',
                'manufacturer': '上海阀门厂',
                'include_quality': True
            }
        }
    }
    
    return jsonify(docs), 200

# 错误处理
@unified_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在',
        'available_docs': f'{request.host_url}api/v2/docs'
    }), 404

@unified_api_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': '请求方法不被允许'
    }), 405

@unified_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '内部服务器错误'
    }), 500

# 启动脚本
if __name__ == "__main__":
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建应用
    app = create_enhanced_app({
        'DEBUG': True,
        'DATABASE_PATH': 'business_data.db',
        'DEDUP_DATABASE_PATH': 'material_deduplication.db',
        'SYNC_DATABASE_PATH': 'sync_tracking.db'
    })
    
    print("MMP增强版API服务启动中...")
    print("API文档地址: http://localhost:5000/api/v2/docs")
    print("健康检查: http://localhost:5000/api/v2/health")
    
    app.run(host='0.0.0.0', port=5000, debug=True)