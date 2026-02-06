#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐条模糊匹配API
提供单条物料的智能分类推荐和近似物料匹配功能
"""

from flask import Blueprint, request, jsonify, render_template
import logging
import json
from typing import Dict, List, Any
from datetime import datetime
import os
import sys
import sqlite3

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from similar_material_matcher import SimilarMaterialMatcher
from app.enhanced_smart_classifier import EnhancedSmartClassifier

logger = logging.getLogger(__name__)

# 创建Blueprint
single_matching_bp = Blueprint('single_matching', __name__)

class SingleFuzzyMatcher:
    """逐条模糊匹配服务"""
    
    def __init__(self):
        """初始化"""
        self.similar_matcher = None
        self.enhanced_classifier = None
        self._initialize_matchers()
    
    def _initialize_matchers(self):
        """初始化匹配器"""
        try:
            # 初始化近似物料匹配器
            self.similar_matcher = SimilarMaterialMatcher('business_data.db')
            logger.info("近似物料匹配器初始化成功")
            
            # 初始化增强智能分类器
            master_db_path = 'master_data.db'  # 使用相对路径
            self.enhanced_classifier = EnhancedSmartClassifier(master_db_path)
            logger.info("增强智能分类器初始化成功")
            
        except Exception as e:
            logger.error(f"匹配器初始化失败: {e}")
            raise
    
    def get_category_mapping(self, original_category: str) -> Dict[str, Any]:
        """
        获取分类映射信息
        
        Args:
            original_category: 原始分类名称
            
        Returns:
            映射信息字典
        """
        try:
            conn = sqlite3.connect('business_data.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT standard_category, standard_id, mapping_confidence, mapping_type
                FROM category_mapping 
                WHERE original_category = ?
            ''', (original_category,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'has_mapping': True,
                    'standard_category': result[0],
                    'standard_id': result[1],
                    'mapping_confidence': result[2],
                    'mapping_type': result[3]
                }
            else:
                return {
                    'has_mapping': False,
                    'standard_category': original_category,
                    'standard_id': None,
                    'mapping_confidence': 1.0,
                    'mapping_type': 'original'
                }
                
        except Exception as e:
            logger.error(f"获取分类映射失败: {e}")
            return {
                'has_mapping': False,
                'standard_category': original_category,
                'standard_id': None,
                'mapping_confidence': 1.0,
                'mapping_type': 'original'
            }
    
    def perform_single_matching(
        self, 
        material_info: Dict[str, str], 
        threshold: float = 0.5, 
        max_results: int = 200
    ) -> Dict[str, Any]:
        """
        执行单条物料匹配
        
        Args:
            material_info: 物料信息 {'name': '', 'spec': '', 'desc': ''}
            threshold: 相似度阈值 (0-1)
            max_results: 最大返回结果数
            
        Returns:
            匹配结果字典
        """
        try:
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'input_material': material_info,
                'threshold': threshold,
                'similar_materials': [],
                'recommended_categories': [],
                'matching_info': {}
            }
            
            # 1. 获取近似物料匹配结果并添加标准分类映射
            if self.similar_matcher:
                similar_materials_raw = self.similar_matcher.find_similar_materials(
                    material_info, 
                    threshold=threshold,
                    max_results=max_results
                )
                
                # 为每个近似物料添加标准分类映射信息
                similar_materials = []
                for material in similar_materials_raw:
                    original_category = material.get('material_category', '')
                    mapping_info = self.get_category_mapping(original_category)
                    
                    # 添加映射信息到物料数据
                    enhanced_material = material.copy()
                    enhanced_material.update({
                        'original_category': original_category,
                        'standard_category': mapping_info['standard_category'],
                        'standard_id': mapping_info['standard_id'],
                        'has_standard_mapping': mapping_info['has_mapping'],
                        'mapping_confidence': mapping_info['mapping_confidence'],
                        'mapping_type': mapping_info['mapping_type']
                    })
                    similar_materials.append(enhanced_material)
                
                result['similar_materials'] = similar_materials
                logger.info(f"找到 {len(similar_materials)} 个近似物料（已添加标准分类映射）")
            
            # 2. 获取智能分类推荐
            if self.enhanced_classifier:
                # 构造MaterialFeature对象
                try:
                    from app.smart_classifier import MaterialFeature
                    material_feature = MaterialFeature(
                        name=material_info.get('name', ''),
                        spec=material_info.get('spec', ''),
                        unit='个',  # 默认单位
                        dn='',
                        pn='',
                        material=''
                    )
                    
                    classification_results = self.enhanced_classifier.classify_material(material_feature)
                    
                    # 转换为统一格式并添加标准分类映射
                    recommended_categories = []
                    for i, cls_result in enumerate(classification_results[:5]):  # 取前5个
                        original_category = cls_result.get('category', '')
                        
                        # 获取分类映射信息
                        mapping_info = self.get_category_mapping(original_category)
                        
                        category = {
                            'rank': i + 1,
                            'category_code': cls_result.get('category', ''),
                            'category_name': original_category,
                            'original_category': original_category,
                            'standard_category': mapping_info['standard_category'],
                            'standard_id': mapping_info['standard_id'],
                            'has_standard_mapping': mapping_info['has_mapping'],
                            'mapping_confidence': mapping_info['mapping_confidence'],
                            'mapping_type': mapping_info['mapping_type'],
                            'confidence': cls_result.get('confidence', 0),
                            'confidence_percentage': int(cls_result.get('confidence', 0)),
                            'matching_details': cls_result.get('details', ''),
                            'material_detected': cls_result.get('material_info', []),
                            'source': 'enhanced_classifier'
                        }
                        recommended_categories.append(category)
                    
                    # 3. 从近似物料中提取分类建议
                    if result['similar_materials']:
                        category_counts = {}
                        for material in result['similar_materials'][:10]:  # 取前10个最相似的物料
                            standard_cat = material.get('standard_category', '')
                            original_cat = material.get('original_category', '')
                            similarity = material.get('similarity_score', 0)
                            
                            if standard_cat and standard_cat not in [cat['standard_category'] for cat in recommended_categories]:
                                if standard_cat not in category_counts:
                                    category_counts[standard_cat] = {
                                        'count': 0,
                                        'total_similarity': 0,
                                        'original_category': original_cat,
                                        'standard_id': material.get('standard_id'),
                                        'mapping_type': material.get('mapping_type', '')
                                    }
                                category_counts[standard_cat]['count'] += 1
                                category_counts[standard_cat]['total_similarity'] += similarity
                        
                        # 将分类建议加入推荐列表
                        for standard_cat, info in category_counts.items():
                            avg_similarity = info['total_similarity'] / info['count']
                            confidence = min(avg_similarity * info['count'] * 0.3, 0.85)  # 基于相似度和出现次数
                            
                            category = {
                                'rank': len(recommended_categories) + 1,
                                'category_code': info['original_category'],
                                'category_name': info['original_category'],
                                'original_category': info['original_category'],
                                'standard_category': standard_cat,
                                'standard_id': info['standard_id'],
                                'has_standard_mapping': True,
                                'mapping_confidence': 1.0,
                                'mapping_type': info['mapping_type'],
                                'confidence': confidence,
                                'confidence_percentage': int(confidence * 100),
                                'matching_details': f'基于{info["count"]}个相似物料，平均相似度{avg_similarity:.3f}',
                                'material_detected': [],
                                'source': 'similar_materials'
                            }
                            recommended_categories.append(category)
                    
                    result['recommended_categories'] = recommended_categories
                    logger.info(f"生成 {len(recommended_categories)} 个推荐分类")
                    
                except Exception as e:
                    logger.error(f"分类推荐失败: {e}")
                    result['recommended_categories'] = []
            
            # 3. 统计信息
            result['matching_info'] = {
                'similar_materials_count': len(result['similar_materials']),
                'recommended_categories_count': len(result['recommended_categories']),
                'threshold_used': threshold,
                'algorithm_info': {
                    'similar_matcher_available': self.similar_matcher is not None,
                    'enhanced_classifier_available': self.enhanced_classifier is not None
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"单条匹配失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# 全局匹配服务实例
matcher_service = None

def get_matcher_service():
    """获取匹配服务实例"""
    global matcher_service
    if matcher_service is None:
        matcher_service = SingleFuzzyMatcher()
    return matcher_service

@single_matching_bp.route('/single-fuzzy-matching')
def single_fuzzy_matching_page():
    """逐条模糊匹配页面"""
    return render_template('single_fuzzy_matching.html')

@single_matching_bp.route('/api/single_fuzzy_matching', methods=['POST'])
def single_fuzzy_matching_api():
    """逐条模糊匹配API"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        # 验证必需字段
        material_info = data.get('material', {})
        if not material_info.get('name') or not material_info.get('spec'):
            return jsonify({
                'success': False,
                'error': '物料名称和规格参数不能为空'
            }), 400
        
        # 获取参数
        threshold = float(data.get('threshold', 0.5))
        max_results = int(data.get('max_results', 200))
        
        # 验证阈值范围
        if threshold < 0 or threshold > 1:
            return jsonify({
                'success': False,
                'error': '阈值必须在0-1之间'
            }), 400
        
        # 执行匹配
        service = get_matcher_service()
        result = service.perform_single_matching(
            material_info=material_info,
            threshold=threshold,
            max_results=max_results
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"逐条匹配API错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500

@single_matching_bp.route('/api/similar_materials/categories', methods=['GET'])
def get_similar_material_categories():
    """获取近似物料的分类列表"""
    try:
        service = get_matcher_service()
        if service.similar_matcher:
            categories = service.similar_matcher.get_material_categories_stats()
            
            # 转换为前端需要的格式
            category_list = []
            for category, count in categories.items():
                category_list.append({
                    'name': category,
                    'count': count
                })
            
            # 按数量排序
            category_list.sort(key=lambda x: x['count'], reverse=True)
            
            return jsonify({
                'success': True,
                'categories': category_list
            })
        else:
            return jsonify({
                'success': False,
                'error': '近似物料匹配器未初始化'
            })
            
    except Exception as e:
        logger.error(f"获取分类列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@single_matching_bp.route('/api/similar_materials/search', methods=['POST'])
def search_similar_materials_by_category():
    """按分类搜索近似物料"""
    try:
        data = request.get_json()
        category = data.get('category', '')
        limit = int(data.get('limit', 50))
        
        service = get_matcher_service()
        if service.similar_matcher:
            materials = service.similar_matcher.search_by_category(category, limit)
            
            return jsonify({
                'success': True,
                'materials': materials,
                'category': category,
                'count': len(materials)
            })
        else:
            return jsonify({
                'success': False,
                'error': '近似物料匹配器未初始化'
            })
            
    except Exception as e:
        logger.error(f"按分类搜索失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@single_matching_bp.route('/api/threshold/recommendations', methods=['GET'])
def get_threshold_recommendations():
    """获取推荐阈值"""
    try:
        service = get_matcher_service()
        if service.similar_matcher:
            recommendations = service.similar_matcher.get_recommended_threshold()
            
            return jsonify({
                'success': True,
                'recommendations': {
                    'low': int(recommendations['low'] * 100),
                    'medium': int(recommendations['medium'] * 100),
                    'high': int(recommendations['high'] * 100)
                },
                'default': int(recommendations['medium'] * 100)
            })
        else:
            return jsonify({
                'success': True,
                'recommendations': {
                    'low': 30,
                    'medium': 55,
                    'high': 75
                },
                'default': 55
            })
            
    except Exception as e:
        logger.error(f"获取推荐阈值失败: {e}")
        return jsonify({
            'success': True,
            'recommendations': {
                'low': 30,
                'medium': 55,
                'high': 75
            },
            'default': 55
        })

# 测试函数
def test_single_matching():
    """测试逐条匹配功能"""
    service = SingleFuzzyMatcher()
    
    # 测试用例
    test_material = {
        'name': '疏水器',
        'spec': 'DN25 PN1.6 CS',
        'desc': '碳钢疏水器，温度150℃'
    }
    
    result = service.perform_single_matching(test_material, threshold=0.3)
    
    print("=== 单条匹配测试结果 ===")
    print(f"成功: {result['success']}")
    print(f"近似物料数量: {len(result.get('similar_materials', []))}")
    print(f"推荐分类数量: {len(result.get('recommended_categories', []))}")
    
    if result.get('similar_materials'):
        print("\n前3个近似物料:")
        for i, material in enumerate(result['similar_materials'][:3]):
            print(f"{i+1}. {material['material_name']} - {material['confidence_percentage']}%")
    
    if result.get('recommended_categories'):
        print("\n前3个推荐分类:")
        for i, category in enumerate(result['recommended_categories'][:3]):
            print(f"{i+1}. {category['category_name']} - {category['confidence_percentage']}%")

if __name__ == '__main__':
    # 测试功能
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_single_matching()