# app/external_classifier.py
"""
外部分类体系对接模块
对接用友数据中台等外部主数据平台，获取标准物料分类模板
"""
import requests
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import os
from app.database_session_manager import DatabaseSessionManager

# 延迟导入避免循环引用
def get_master_data_manager():
    from app.master_data_manager import master_data_manager
    return master_data_manager

logger = logging.getLogger(__name__)

class ExternalClassifier:
    """外部分类体系对接服务"""
    
    def __init__(self, config: Optional[Dict] = None, db_manager: Optional[DatabaseSessionManager] = None):
        """
        初始化外部分类服务
        
        Args:
            config: 配置字典，包含API地址、认证信息等
            db_manager: 数据库会话管理器，用于存储分类推荐结果
        """
        self.config = config or self._get_default_config()
        self.cache = {}
        self.cache_timeout = 3600  # 缓存1小时
        self.db_manager = db_manager
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'api_base_url': 'https://api.yonyou.com/masterdata/v1',
            'api_key': os.getenv('YONYOU_API_KEY', ''),
            'api_secret': os.getenv('YONYOU_API_SECRET', ''),
            'timeout': 30,
            'retry_count': 3,
            'mock_mode': True  # 开发阶段使用模拟数据
        }
    
    def get_material_categories(self) -> Dict[str, Any]:
        """
        获取物料分类体系
        
        Returns:
            物料分类体系数据
        """
        try:
            # 首先尝试从主数据库获取
            master_manager = get_master_data_manager()
            cached_categories = master_manager.get_cache('external_categories')
            
            if cached_categories:
                logger.info(f"从缓存获取分类体系，共{len(cached_categories.get('categories', []))}个分类")
                return cached_categories
            
            if self.config.get('mock_mode', True):
                # 从主数据库获取分类并格式化
                db_categories = master_manager.get_material_categories()
                formatted_data = {
                    'categories': db_categories,
                    'total': len(db_categories),
                    'source': 'master_database'
                }
                
                # 缓存结果
                master_manager.set_cache('external_categories', formatted_data, 6)  # 缓存6小时
                logger.info(f"从主数据库获取分类体系，共{len(db_categories)}个分类")
                return formatted_data
            
            # 实际API调用逻辑
            url = f"{self.config['api_base_url']}/categories"
            headers = self._get_auth_headers()
            
            response = requests.get(url, headers=headers, timeout=self.config['timeout'])
            response.raise_for_status()
            
            categories_data = response.json()
            
            # 缓存API结果
            master_manager.set_cache('external_categories', categories_data, 6)
            logger.info(f"从外部API获取分类体系，共{len(categories_data.get('categories', []))}个分类")
            
            return categories_data
            
        except Exception as e:
            logger.error(f"获取分类体系失败: {e}")
            # 降级到模拟数据
            return self._get_mock_categories()
    
    def get_category_features(self, category_id: str) -> Dict[str, Any]:
        """
        获取指定分类的特征模型
        
        Args:
            category_id: 分类ID
            
        Returns:
            分类特征模型数据
        """
        try:
            # 首先尝试从主数据库获取
            master_manager = get_master_data_manager()
            cache_key = f'features_{category_id}'
            cached_features = master_manager.get_cache(cache_key)
            
            if cached_features:
                logger.info(f"从缓存获取分类{category_id}的特征模型")
                return cached_features
            
            if self.config.get('mock_mode', True):
                # 从主数据库获取特征
                db_features = master_manager.get_category_features(category_id)
                features_data = {
                    'category_id': category_id,
                    'features': db_features,
                    'source': 'master_database'
                }
                
                # 缓存结果
                master_manager.set_cache(cache_key, features_data, 24)  # 缓存24小时
                logger.info(f"从主数据库获取分类{category_id}的特征模型，共{len(db_features)}个特征")
                return features_data
            
            # 实际API调用逻辑
            url = f"{self.config['api_base_url']}/categories/{category_id}/features"
            headers = self._get_auth_headers()
            
            response = requests.get(url, headers=headers, timeout=self.config['timeout'])
            response.raise_for_status()
            
            features_data = response.json()
            
            # 缓存API结果
            master_manager.set_cache(cache_key, features_data, 24)
            logger.info(f"从外部API获取分类{category_id}的特征模型")
            
            return features_data
            
        except Exception as e:
            logger.error(f"获取分类特征模型失败: {e}")
            return self._get_mock_category_features(category_id)
    
    def recommend_categories(self, material_features: Dict[str, Any], session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        基于物料特征推荐分类
        
        Args:
            material_features: 物料特征数据
            session_id: 会话ID，用于存储推荐结果到数据库
            
        Returns:
            推荐分类列表，包含置信度
        """
        try:
            if self.config.get('mock_mode', True):
                recommendations = self._get_mock_recommendations(material_features)
            else:
                # 实际推荐逻辑
                url = f"{self.config['api_base_url']}/classify/recommend"
                headers = self._get_auth_headers()
                
                payload = {
                    'features': material_features,
                    'top_n': 5,
                    'min_confidence': 0.3
                }
                
                response = requests.post(url, json=payload, headers=headers, 
                                       timeout=self.config['timeout'])
                response.raise_for_status()
                
                result = response.json()
                recommendations = result.get('recommendations', [])
                logger.info(f"成功获取分类推荐，共{len(recommendations)}个")
            
            # 如果提供了会话ID和数据库管理器，保存推荐结果
            if session_id and self.db_manager:
                try:
                    self.db_manager.store_recommendation(
                        session_id=session_id,
                        material_features=material_features,
                        recommendations=recommendations
                    )
                    logger.info(f"推荐结果已存储到数据库: session_id={session_id}")
                except Exception as e:
                    logger.error(f"存储推荐结果到数据库失败: {e}")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"分类推荐失败: {e}")
            return self._get_mock_recommendations(material_features)
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取API认证头"""
        timestamp = str(int(datetime.now().timestamp()))
        signature = self._generate_signature(timestamp)
        
        return {
            'Content-Type': 'application/json',
            'X-API-Key': self.config['api_key'],
            'X-Timestamp': timestamp,
            'X-Signature': signature
        }
    
    def _generate_signature(self, timestamp: str) -> str:
        """生成API签名"""
        raw_string = f"{self.config['api_key']}{timestamp}{self.config['api_secret']}"
        return hashlib.md5(raw_string.encode()).hexdigest()
    
    def _get_mock_categories(self) -> Dict[str, Any]:
        """获取模拟分类数据"""
        return {
            'categories': [
                {
                    'id': 'CAT001',
                    'name': '医疗器械',
                    'level': 1,
                    'parent_id': None,
                    'children': [
                        {
                            'id': 'CAT001001',
                            'name': '诊断设备',
                            'level': 2,
                            'parent_id': 'CAT001'
                        },
                        {
                            'id': 'CAT001002', 
                            'name': '治疗设备',
                            'level': 2,
                            'parent_id': 'CAT001'
                        }
                    ]
                },
                {
                    'id': 'CAT002',
                    'name': '办公用品',
                    'level': 1,
                    'parent_id': None,
                    'children': [
                        {
                            'id': 'CAT002001',
                            'name': '文具用品',
                            'level': 2,
                            'parent_id': 'CAT002'
                        },
                        {
                            'id': 'CAT002002',
                            'name': '电子设备',
                            'level': 2,
                            'parent_id': 'CAT002'
                        }
                    ]
                },
                {
                    'id': 'CAT003',
                    'name': '建筑材料',
                    'level': 1,
                    'parent_id': None,
                    'children': [
                        {
                            'id': 'CAT003001',
                            'name': '钢材',
                            'level': 2,
                            'parent_id': 'CAT003'
                        },
                        {
                            'id': 'CAT003002',
                            'name': '水泥',
                            'level': 2,
                            'parent_id': 'CAT003'
                        }
                    ]
                }
            ],
            'total_count': 3,
            'update_time': datetime.now().isoformat()
        }
    
    def _get_mock_category_features(self, category_id: str) -> Dict[str, Any]:
        """获取模拟分类特征模型"""
        features_templates = {
            'CAT001001': {  # 诊断设备
                'features': [
                    {'name': '设备名称', 'type': 'text', 'required': True, 'max_length': 100},
                    {'name': '型号规格', 'type': 'text', 'required': True, 'max_length': 50},
                    {'name': '生产厂家', 'type': 'text', 'required': True, 'max_length': 50},
                    {'name': '医疗器械注册证号', 'type': 'text', 'required': True, 'pattern': r'^[A-Z0-9]+$'},
                    {'name': '适用科室', 'type': 'enum', 'required': True, 
                     'options': ['内科', '外科', '妇科', '儿科', '急诊科']},
                    {'name': '设备等级', 'type': 'enum', 'required': True,
                     'options': ['一类', '二类', '三类']},
                    {'name': '技术参数', 'type': 'textarea', 'required': False}
                ]
            },
            'CAT002001': {  # 文具用品
                'features': [
                    {'name': '商品名称', 'type': 'text', 'required': True, 'max_length': 100},
                    {'name': '品牌', 'type': 'text', 'required': True, 'max_length': 50},
                    {'name': '规格型号', 'type': 'text', 'required': True, 'max_length': 50},
                    {'name': '材质', 'type': 'enum', 'required': False,
                     'options': ['塑料', '金属', '纸质', '木质', '其他']},
                    {'name': '颜色', 'type': 'text', 'required': False},
                    {'name': '包装规格', 'type': 'text', 'required': False}
                ]
            },
            'CAT003001': {  # 钢材
                'features': [
                    {'name': '钢材名称', 'type': 'text', 'required': True, 'max_length': 100},
                    {'name': '钢材牌号', 'type': 'text', 'required': True, 'max_length': 50},
                    {'name': '规格尺寸', 'type': 'text', 'required': True, 'max_length': 100},
                    {'name': '钢材标准', 'type': 'enum', 'required': True,
                     'options': ['GB/T', 'ASTM', 'JIS', 'EN', '其他']},
                    {'name': '表面处理', 'type': 'enum', 'required': False,
                     'options': ['镀锌', '喷漆', '原材', '其他']},
                    {'name': '长度', 'type': 'number', 'required': False, 'unit': 'mm'},
                    {'name': '重量', 'type': 'number', 'required': False, 'unit': 'kg'}
                ]
            }
        }
        
        return features_templates.get(category_id, {
            'features': [
                {'name': '物料名称', 'type': 'text', 'required': True, 'max_length': 100},
                {'name': '规格型号', 'type': 'text', 'required': True, 'max_length': 50},
                {'name': '生产厂家', 'type': 'text', 'required': True, 'max_length': 50}
            ]
        })
    
    def _get_mock_recommendations(self, material_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取模拟推荐结果"""
        # 简单的关键词匹配逻辑
        material_name = material_features.get('name', '').lower()
        
        recommendations = []
        
        if any(keyword in material_name for keyword in ['设备', '仪器', '机器']):
            recommendations.append({
                'category_id': 'CAT001001',
                'category_name': '诊断设备',
                'confidence': 0.85,
                'match_reasons': ['包含设备关键词', '规格型号匹配']
            })
            
        if any(keyword in material_name for keyword in ['笔', '纸', '文具', '办公']):
            recommendations.append({
                'category_id': 'CAT002001',
                'category_name': '文具用品',
                'confidence': 0.92,
                'match_reasons': ['包含文具关键词', '品牌匹配']
            })
            
        if any(keyword in material_name for keyword in ['钢', '铁', '材料', '建筑']):
            recommendations.append({
                'category_id': 'CAT003001',
                'category_name': '钢材',
                'confidence': 0.78,
                'match_reasons': ['包含钢材关键词', '规格匹配']
            })
        
        # 如果没有匹配到，返回默认推荐
        if not recommendations:
            recommendations = [
                {
                    'category_id': 'CAT002001',
                    'category_name': '文具用品',
                    'confidence': 0.45,
                    'match_reasons': ['默认推荐']
                }
            ]
        
        # 按置信度排序
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"为物料'{material_name}'生成了{len(recommendations)}个推荐")
        return recommendations

# 全局实例 - 需要在使用时初始化数据库管理器
def get_external_classifier(db_manager: Optional[DatabaseSessionManager] = None) -> ExternalClassifier:
    """获取外部分类器实例"""
    return ExternalClassifier(db_manager=db_manager)

# 默认实例（兼容现有代码）
external_classifier = ExternalClassifier()