# app/training_data_manager.py
"""
训练数据管理器
管理训练数据、训练结果和分类模型的数据库存储
"""
import sqlite3
import json
import pickle
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import os

logger = logging.getLogger(__name__)

class TrainingDataManager:
    """训练数据和模型管理器"""
    
    def __init__(self, db_path: str = 'training_data.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化训练数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 训练数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material_code TEXT,
                    material_name TEXT NOT NULL,
                    brand TEXT,
                    specification TEXT,
                    category TEXT,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. 训练结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    training_session_id TEXT UNIQUE NOT NULL,
                    total_samples INTEGER,
                    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    model_accuracy REAL,
                    model_metrics TEXT,  -- JSON格式存储各种指标
                    keyword_rules TEXT,  -- JSON格式存储关键词规则
                    manufacturer_rules TEXT,  -- JSON格式存储制造商规则
                    specification_rules TEXT,  -- JSON格式存储规格规则
                    enhanced_keywords TEXT,  -- JSON格式存储增强关键词
                    notes TEXT
                )
            ''')
            
            # 3. 分类模型表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classification_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    model_type TEXT,  -- tfidf, neural_network, etc.
                    model_data BLOB,  -- 序列化的模型数据
                    feature_names TEXT,  -- JSON格式的特征名称
                    model_parameters TEXT,  -- JSON格式的模型参数
                    training_session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (training_session_id) REFERENCES training_results(training_session_id)
                )
            ''')
            
            # 4. 分类规则缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classification_rules_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_type TEXT NOT NULL,  -- keyword, manufacturer, specification
                    rule_key TEXT NOT NULL,
                    rule_value TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    training_session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_training_samples_name ON training_samples(material_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_training_samples_brand ON training_samples(brand)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_training_samples_category ON training_samples(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_classification_rules_type ON classification_rules_cache(rule_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_classification_rules_active ON classification_rules_cache(is_active)')
            
            conn.commit()
            logger.info("训练数据库初始化完成")
    
    def import_training_data_from_files(self, file_paths: List[str]) -> str:
        """从CSV/Excel文件导入训练数据"""
        training_session_id = f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        total_imported = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for file_path in file_paths:
                try:
                    if not os.path.exists(file_path):
                        logger.warning(f"文件不存在: {file_path}")
                        continue
                    
                    # 读取文件数据
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    else:
                        df = pd.read_excel(file_path)
                    
                    # 标准化列名映射
                    column_mapping = self._get_column_mapping(df.columns.tolist())
                    
                    for _, row in df.iterrows():
                        try:
                            material_code = row.get(column_mapping.get('material_code', ''), '')
                            material_name = row.get(column_mapping.get('material_name', ''), '')
                            brand = row.get(column_mapping.get('brand', ''), '')
                            specification = row.get(column_mapping.get('specification', ''), '')
                            category = row.get(column_mapping.get('category', ''), '')
                            
                            if material_name:  # 至少需要物料名称
                                cursor.execute('''
                                    INSERT INTO training_samples 
                                    (material_code, material_name, brand, specification, category, source_file)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (material_code, material_name, brand, specification, category, file_path))
                                total_imported += 1
                        
                        except Exception as e:
                            logger.warning(f"导入行数据失败: {e}")
                            continue
                    
                    logger.info(f"从 {file_path} 导入了 {len(df)} 条记录")
                
                except Exception as e:
                    logger.error(f"导入文件 {file_path} 失败: {e}")
                    continue
            
            conn.commit()
        
        logger.info(f"训练数据导入完成，会话ID: {training_session_id}, 总计: {total_imported} 条")
        return training_session_id
    
    def _get_column_mapping(self, columns: List[str]) -> Dict[str, str]:
        """获取列名映射"""
        mapping = {}
        
        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['编号', 'code', 'id', '代码']):
                mapping['material_code'] = col
            elif any(keyword in col_lower for keyword in ['名称', 'name', '物料名']):
                mapping['material_name'] = col
            elif any(keyword in col_lower for keyword in ['品牌', 'brand', '厂家', '生产商', 'manufacturer']):
                mapping['brand'] = col
            elif any(keyword in col_lower for keyword in ['规格', 'spec', '型号', 'specification']):
                mapping['specification'] = col
            elif any(keyword in col_lower for keyword in ['分类', 'category', '类别']):
                mapping['category'] = col
        
        return mapping
    
    def save_training_results(self, session_id: str, results: Dict[str, Any]) -> bool:
        """保存训练结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO training_results 
                    (training_session_id, total_samples, model_accuracy, model_metrics,
                     keyword_rules, manufacturer_rules, specification_rules, enhanced_keywords, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    results.get('total_samples', 0),
                    results.get('model_accuracy', 0.0),
                    json.dumps(results.get('model_metrics', {})),
                    json.dumps(results.get('keyword_rules', {})),
                    json.dumps(results.get('manufacturer_rules', {})),
                    json.dumps(results.get('specification_rules', {})),
                    json.dumps(results.get('enhanced_keywords', {})),
                    results.get('notes', '')
                ))
                
                conn.commit()
                logger.info(f"训练结果已保存，会话ID: {session_id}")
                return True
        
        except Exception as e:
            logger.error(f"保存训练结果失败: {e}")
            return False
    
    def save_classification_model(self, model_name: str, model_version: str, 
                                model_type: str, model_obj: Any, 
                                feature_names: List[str], parameters: Dict,
                                training_session_id: str) -> bool:
        """保存分类模型"""
        try:
            # 序列化模型
            model_data = pickle.dumps(model_obj)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 先将其他相同名称的模型设为非活跃
                cursor.execute('''
                    UPDATE classification_models 
                    SET is_active = FALSE 
                    WHERE model_name = ?
                ''', (model_name,))
                
                # 插入新模型
                cursor.execute('''
                    INSERT INTO classification_models
                    (model_name, model_version, model_type, model_data, 
                     feature_names, model_parameters, training_session_id, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, TRUE)
                ''', (
                    model_name,
                    model_version,
                    model_type,
                    model_data,
                    json.dumps(feature_names),
                    json.dumps(parameters),
                    training_session_id
                ))
                
                conn.commit()
                logger.info(f"分类模型已保存: {model_name} v{model_version}")
                return True
        
        except Exception as e:
            logger.error(f"保存分类模型失败: {e}")
            return False
    
    def load_active_classification_model(self, model_name: str) -> Optional[Tuple[Any, List[str], Dict]]:
        """加载活跃的分类模型"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT model_data, feature_names, model_parameters
                    FROM classification_models
                    WHERE model_name = ? AND is_active = TRUE
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (model_name,))
                
                row = cursor.fetchone()
                if row:
                    model_obj = pickle.loads(row[0])
                    feature_names = json.loads(row[1])
                    parameters = json.loads(row[2])
                    return model_obj, feature_names, parameters
                
                return None
        
        except Exception as e:
            logger.error(f"加载分类模型失败: {e}")
            return None
    
    def get_latest_training_results(self) -> Optional[Dict[str, Any]]:
        """获取最新的训练结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT training_session_id, total_samples, model_accuracy, model_metrics,
                           keyword_rules, manufacturer_rules, specification_rules, 
                           enhanced_keywords, training_date
                    FROM training_results
                    ORDER BY training_date DESC
                    LIMIT 1
                ''')
                
                row = cursor.fetchone()
                if row:
                    return {
                        'training_session_id': row[0],
                        'total_samples': row[1],
                        'model_accuracy': row[2],
                        'model_metrics': json.loads(row[3]) if row[3] else {},
                        'keyword_rules': json.loads(row[4]) if row[4] else {},
                        'manufacturer_rules': json.loads(row[5]) if row[5] else {},
                        'specification_rules': json.loads(row[6]) if row[6] else {},
                        'enhanced_keywords': json.loads(row[7]) if row[7] else {},
                        'training_date': row[8]
                    }
                
                return None
        
        except Exception as e:
            logger.error(f"获取训练结果失败: {e}")
            return None
    
    def cache_classification_rules(self, rules: Dict[str, Any], training_session_id: str):
        """缓存分类规则以提高查询性能"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 清除旧的缓存
                cursor.execute('DELETE FROM classification_rules_cache WHERE training_session_id = ?', 
                             (training_session_id,))
                
                # 缓存关键词规则
                if 'keyword_rules' in rules:
                    for category, rule_data in rules['keyword_rules'].items():
                        for keyword in rule_data.get('keywords', []):
                            cursor.execute('''
                                INSERT INTO classification_rules_cache
                                (rule_type, rule_key, rule_value, confidence, training_session_id)
                                VALUES (?, ?, ?, ?, ?)
                            ''', ('keyword', keyword, category, rule_data.get('confidence_base', 0.5), training_session_id))
                
                # 缓存制造商规则
                if 'manufacturer_rules' in rules:
                    for manufacturer, category in rules['manufacturer_rules'].items():
                        cursor.execute('''
                            INSERT INTO classification_rules_cache
                            (rule_type, rule_key, rule_value, confidence, training_session_id)
                            VALUES (?, ?, ?, ?, ?)
                        ''', ('manufacturer', manufacturer, category, 0.75, training_session_id))
                
                # 缓存规格规则
                if 'specification_rules' in rules:
                    for category, spec_keywords in rules['specification_rules'].items():
                        for keyword in spec_keywords:
                            cursor.execute('''
                                INSERT INTO classification_rules_cache
                                (rule_type, rule_key, rule_value, confidence, training_session_id)
                                VALUES (?, ?, ?, ?, ?)
                            ''', ('specification', keyword, category, 0.6, training_session_id))
                
                conn.commit()
                logger.info(f"分类规则缓存完成，会话ID: {training_session_id}")
        
        except Exception as e:
            logger.error(f"缓存分类规则失败: {e}")
    
    def get_classification_rules(self, rule_type: str = None) -> Dict[str, Any]:
        """获取分类规则"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if rule_type:
                    cursor.execute('''
                        SELECT rule_key, rule_value, confidence
                        FROM classification_rules_cache
                        WHERE rule_type = ? AND is_active = TRUE
                    ''', (rule_type,))
                else:
                    cursor.execute('''
                        SELECT rule_type, rule_key, rule_value, confidence
                        FROM classification_rules_cache
                        WHERE is_active = TRUE
                    ''')
                
                rules = {}
                for row in cursor.fetchall():
                    if rule_type:
                        rule_key, rule_value, confidence = row
                        if rule_value not in rules:
                            rules[rule_value] = []
                        rules[rule_value].append({'keyword': rule_key, 'confidence': confidence})
                    else:
                        rule_type_val, rule_key, rule_value, confidence = row
                        if rule_type_val not in rules:
                            rules[rule_type_val] = {}
                        if rule_value not in rules[rule_type_val]:
                            rules[rule_type_val][rule_value] = []
                        rules[rule_type_val][rule_value].append({'keyword': rule_key, 'confidence': confidence})
                
                return rules
        
        except Exception as e:
            logger.error(f"获取分类规则失败: {e}")
            return {}
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """获取训练统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 训练样本统计
                cursor.execute('SELECT COUNT(*) FROM training_samples')
                total_samples = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT category) FROM training_samples WHERE category IS NOT NULL')
                categories_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT brand) FROM training_samples WHERE brand IS NOT NULL')
                brands_count = cursor.fetchone()[0]
                
                # 训练结果统计
                cursor.execute('SELECT COUNT(*) FROM training_results')
                training_sessions = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM classification_models WHERE is_active = TRUE')
                active_models = cursor.fetchone()[0]
                
                return {
                    'total_training_samples': total_samples,
                    'categories_count': categories_count,
                    'brands_count': brands_count,
                    'training_sessions': training_sessions,
                    'active_models': active_models
                }
        
        except Exception as e:
            logger.error(f"获取训练统计失败: {e}")
            return {}