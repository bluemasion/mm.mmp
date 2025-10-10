# app/master_data_manager.py
"""
主数据管理器
将常用的主数据部分存储到数据库中，优化查询性能和数据访问
"""
import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
from app.database_session_manager import DatabaseSessionManager

logger = logging.getLogger(__name__)

class MasterDataManager:
    """主数据管理器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化主数据管理器
        
        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            # 默认使用项目根目录下的主数据库
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, 'master_data.db')
        
        self.db_path = db_path
        self.init_master_data_tables()
        logger.info(f"主数据管理器初始化完成: {db_path}")
    
    def init_master_data_tables(self):
        """初始化主数据表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 物料分类表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS material_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id TEXT UNIQUE NOT NULL,
                    category_name TEXT NOT NULL,
                    parent_id TEXT,
                    level INTEGER DEFAULT 1,
                    description TEXT,
                    features TEXT,  -- JSON格式存储分类特征
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 物料主数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material_code TEXT UNIQUE NOT NULL,
                    material_name TEXT NOT NULL,
                    category_id TEXT,
                    brand TEXT,
                    model TEXT,
                    specification TEXT,
                    unit TEXT,
                    attributes TEXT,  -- JSON格式存储其他属性
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES material_categories(category_id)
                )
            ''')
            
            # 供应商表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_code TEXT UNIQUE NOT NULL,
                    supplier_name TEXT NOT NULL,
                    contact_person TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 分类特征模板表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS category_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    feature_type TEXT,  -- text, number, select, boolean
                    options TEXT,  -- JSON格式，用于select类型
                    is_required BOOLEAN DEFAULT 0,
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES material_categories(category_id)
                )
            ''')
            
            # 数据缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    cache_data TEXT NOT NULL,  -- JSON数据
                    expire_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("主数据表结构初始化完成")
            
        except Exception as e:
            logger.error(f"初始化主数据表失败: {e}")
            raise
    
    def store_material_categories(self, categories: List[Dict[str, Any]]):
        """
        存储物料分类数据
        
        Args:
            categories: 分类数据列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for category in categories:
                cursor.execute('''
                    INSERT OR REPLACE INTO material_categories 
                    (category_id, category_name, parent_id, level, description, features, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    category.get('category_id'),
                    category.get('category_name'),
                    category.get('parent_id'),
                    category.get('level', 1),
                    category.get('description', ''),
                    json.dumps(category.get('features', {}), ensure_ascii=False),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"已存储 {len(categories)} 个物料分类")
            
        except Exception as e:
            logger.error(f"存储物料分类失败: {e}")
            raise
    
    def get_material_categories(self, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取物料分类数据
        
        Args:
            parent_id: 父分类ID，None表示获取所有分类
            
        Returns:
            分类数据列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if parent_id:
                cursor.execute('''
                    SELECT id, category_name, parent_code, level, description, remarks
                    FROM material_categories 
                    WHERE parent_code = ?
                    ORDER BY category_name
                ''', (parent_id,))
            else:
                cursor.execute('''
                    SELECT id, category_name, parent_code, level, description, remarks
                    FROM material_categories 
                    ORDER BY level, category_name
                ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            categories = []
            for row in rows:
                category = {
                    'id': row[0],
                    'category_id': row[0],  # 兼容旧字段名
                    'category_name': row[1],
                    'name': row[1],  # 兼容其他字段名
                    'parent_id': row[2],
                    'parent_code': row[2],
                    'level': row[3],
                    'description': row[4],
                    'remarks': row[5],
                    'features': {}  # 暂时为空，实际数据库中没有这个字段
                }
                categories.append(category)
            
            logger.info(f"获取到 {len(categories)} 个物料分类")
            return categories
            
        except Exception as e:
            logger.error(f"获取物料分类失败: {e}")
            return []
    
    def store_materials(self, materials: List[Dict[str, Any]]):
        """
        存储物料主数据
        
        Args:
            materials: 物料数据列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for material in materials:
                cursor.execute('''
                    INSERT OR REPLACE INTO materials 
                    (material_code, material_name, category_id, brand, model, specification, unit, attributes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    material.get('material_code'),
                    material.get('material_name'),
                    material.get('category_id'),
                    material.get('brand', ''),
                    material.get('model', ''),
                    material.get('specification', ''),
                    material.get('unit', ''),
                    json.dumps(material.get('attributes', {}), ensure_ascii=False),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"已存储 {len(materials)} 个物料主数据")
            
        except Exception as e:
            logger.error(f"存储物料主数据失败: {e}")
            raise
    
    def search_materials(self, keyword: str, category_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索物料
        
        Args:
            keyword: 搜索关键词
            category_id: 分类ID过滤
            limit: 结果数量限制
            
        Returns:
            匹配的物料列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            base_query = '''
                SELECT material_code, material_name, category_id, brand, model, specification, unit, attributes
                FROM materials 
                WHERE (material_name LIKE ? OR material_code LIKE ? OR brand LIKE ? OR model LIKE ?)
            '''
            
            params = [f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%']
            
            if category_id:
                base_query += ' AND category_id = ?'
                params.append(category_id)
            
            base_query += ' ORDER BY material_name LIMIT ?'
            params.append(limit)
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            conn.close()
            
            materials = []
            for row in rows:
                material = {
                    'material_code': row[0],
                    'material_name': row[1],
                    'category_id': row[2],
                    'brand': row[3],
                    'model': row[4],
                    'specification': row[5],
                    'unit': row[6],
                    'attributes': json.loads(row[7]) if row[7] else {}
                }
                materials.append(material)
            
            logger.info(f"搜索到 {len(materials)} 个匹配物料")
            return materials
            
        except Exception as e:
            logger.error(f"搜索物料失败: {e}")
            return []
    
    def store_category_features(self, category_id: str, features: List[Dict[str, Any]]):
        """
        存储分类特征模板
        
        Args:
            category_id: 分类ID
            features: 特征列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 先删除已有的特征
            cursor.execute('DELETE FROM category_features WHERE category_id = ?', (category_id,))
            
            # 插入新特征
            for i, feature in enumerate(features):
                cursor.execute('''
                    INSERT INTO category_features 
                    (category_id, feature_name, feature_type, options, is_required, display_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    category_id,
                    feature.get('name'),
                    feature.get('type', 'text'),
                    json.dumps(feature.get('options', []), ensure_ascii=False),
                    feature.get('required', False),
                    i + 1
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"已存储分类 {category_id} 的 {len(features)} 个特征")
            
        except Exception as e:
            logger.error(f"存储分类特征失败: {e}")
            raise
    
    def get_category_features(self, category_id: str) -> List[Dict[str, Any]]:
        """
        获取分类特征模板
        
        Args:
            category_id: 分类ID
            
        Returns:
            特征列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT feature_name, feature_type, options, is_required, display_order
                FROM category_features 
                WHERE category_id = ?
                ORDER BY display_order
            ''', (category_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            features = []
            for row in rows:
                feature = {
                    'name': row[0],
                    'type': row[1],
                    'options': json.loads(row[2]) if row[2] else [],
                    'required': bool(row[3]),
                    'display_order': row[4]
                }
                features.append(feature)
            
            logger.info(f"获取到分类 {category_id} 的 {len(features)} 个特征")
            return features
            
        except Exception as e:
            logger.error(f"获取分类特征失败: {e}")
            return []
    
    def set_cache(self, key: str, data: Any, expire_hours: int = 24):
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            data: 数据
            expire_hours: 过期时间（小时）
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expire_time = datetime.now() + timedelta(hours=expire_hours)
            
            cursor.execute('''
                INSERT OR REPLACE INTO data_cache (cache_key, cache_data, expire_time)
                VALUES (?, ?, ?)
            ''', (key, json.dumps(data, ensure_ascii=False), expire_time.isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"缓存数据已设置: {key}")
            
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
    
    def get_cache(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果过期或不存在返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cache_data, expire_time FROM data_cache 
                WHERE cache_key = ? AND (expire_time IS NULL OR expire_time > ?)
            ''', (key, datetime.now().isoformat()))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                data = json.loads(row[0])
                logger.info(f"缓存命中: {key}")
                return data
            else:
                logger.info(f"缓存未命中: {key}")
                return None
                
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    def cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM data_cache 
                WHERE expire_time IS NOT NULL AND expire_time <= ?
            ''', (datetime.now().isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 个过期缓存")
            
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")

# 全局实例
master_data_manager = MasterDataManager()