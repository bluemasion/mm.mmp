#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务数据管理器
管理系统中的所有业务数据：上传文件、字段映射、匹配规则、分类结果等
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import os
import pandas as pd

logger = logging.getLogger(__name__)

class BusinessDataManager:
    """业务数据管理器 - 管理所有过程数据和配置数据"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """初始化所有业务数据表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 1. 字段映射配置表 - 解决"医保代码"等字段不匹配问题
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS field_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mapping_name VARCHAR(100) NOT NULL,  -- 映射配置名称
                    source_field VARCHAR(100) NOT NULL,  -- 源字段名（实际上传文件中的字段）
                    target_field VARCHAR(100) NOT NULL,  -- 目标字段名（系统标准字段）
                    field_type VARCHAR(50) NOT NULL,     -- 字段类型：exact, fuzzy, id
                    data_type VARCHAR(50) DEFAULT 'string', -- 数据类型
                    validation_rule TEXT,                 -- 验证规则
                    description TEXT,                     -- 字段描述
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. 上传文件记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id VARCHAR(50) UNIQUE NOT NULL,  -- 文件唯一标识
                    original_filename VARCHAR(255) NOT NULL,
                    stored_filename VARCHAR(255) NOT NULL,
                    file_size INTEGER,
                    file_type VARCHAR(50),
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id VARCHAR(50),
                    row_count INTEGER DEFAULT 0,
                    column_count INTEGER DEFAULT 0,
                    columns_json TEXT,  -- 存储列信息的JSON
                    status VARCHAR(50) DEFAULT 'uploaded', -- uploaded, processing, completed, error
                    error_message TEXT,
                    processed_at TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT 0
                )
            """)
            
            # 3. 上传文件数据内容表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id VARCHAR(50) NOT NULL,
                    row_index INTEGER NOT NULL,
                    data_json TEXT NOT NULL,  -- 行数据的JSON格式
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id)
                )
            """)
            
            # 4. 匹配规则配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matching_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name VARCHAR(100) NOT NULL,
                    rule_type VARCHAR(50) NOT NULL,  -- exact, fuzzy, custom
                    master_field VARCHAR(100),       -- 主数据字段
                    target_field VARCHAR(100),       -- 目标字段
                    weight DECIMAL(3,2) DEFAULT 1.0, -- 权重
                    threshold DECIMAL(3,2) DEFAULT 0.8, -- 匹配阈值
                    rule_config TEXT,                -- 规则配置JSON
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 5. 分类规则表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classification_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name VARCHAR(100) NOT NULL,
                    category_id VARCHAR(50),
                    conditions_json TEXT NOT NULL,   -- 分类条件JSON
                    priority INTEGER DEFAULT 0,     -- 优先级
                    confidence DECIMAL(3,2) DEFAULT 1.0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 6. 处理结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id VARCHAR(50) NOT NULL,
                    file_id VARCHAR(50) NOT NULL,
                    result_type VARCHAR(50) NOT NULL, -- matching, classification, extraction
                    row_index INTEGER,
                    input_data_json TEXT,
                    result_data_json TEXT,
                    confidence DECIMAL(3,2),
                    processing_time DECIMAL(10,3),
                    status VARCHAR(50) DEFAULT 'completed', -- completed, failed, pending
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id)
                )
            """)
            
            # 7. 数据质量评估表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id VARCHAR(50) NOT NULL,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value DECIMAL(10,4),
                    metric_details TEXT,
                    threshold_value DECIMAL(10,4),
                    status VARCHAR(50), -- pass, warning, fail
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id)
                )
            """)
            
            # 8. 系统配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key VARCHAR(100) UNIQUE NOT NULL,
                    config_value TEXT,
                    config_type VARCHAR(50) DEFAULT 'string', -- string, number, json, boolean
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_field_mappings_source ON field_mappings(source_field)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_field_mappings_target ON field_mappings(target_field)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_uploaded_files_session ON uploaded_files(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_data_file_id ON file_data(file_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_results_session ON processing_results(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_results_file ON processing_results(file_id)")
            
            conn.commit()
            logger.info("业务数据表初始化完成")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"初始化业务数据表失败: {e}")
            raise
        finally:
            conn.close()
    
    # === 字段映射管理 ===
    
    def create_field_mapping(self, mapping_name: str, source_field: str, target_field: str, 
                           field_type: str, data_type: str = 'string', 
                           validation_rule: str = None, description: str = None) -> int:
        """创建字段映射"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO field_mappings 
                (mapping_name, source_field, target_field, field_type, data_type, validation_rule, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (mapping_name, source_field, target_field, field_type, data_type, validation_rule, description))
            
            mapping_id = cursor.lastrowid
            conn.commit()
            logger.info(f"字段映射创建成功: {source_field} -> {target_field}")
            return mapping_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"创建字段映射失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_field_mappings(self, mapping_name: str = None) -> List[Dict]:
        """获取字段映射配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if mapping_name:
                cursor.execute("""
                    SELECT * FROM field_mappings 
                    WHERE mapping_name = ? AND is_active = 1
                    ORDER BY field_type, source_field
                """, (mapping_name,))
            else:
                cursor.execute("""
                    SELECT * FROM field_mappings 
                    WHERE is_active = 1
                    ORDER BY mapping_name, field_type, source_field
                """)
            
            columns = [desc[0] for desc in cursor.description]
            mappings = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            logger.info(f"获取到 {len(mappings)} 个字段映射")
            return mappings
            
        except Exception as e:
            logger.error(f"获取字段映射失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_field_mapping_dict(self, mapping_name: str) -> Dict[str, str]:
        """获取字段映射字典 - 用于数据转换"""
        mappings = self.get_field_mappings(mapping_name)
        mapping_dict = {}
        
        for mapping in mappings:
            mapping_dict[mapping['source_field']] = mapping['target_field']
        
        return mapping_dict
    
    # === 文件管理 ===
    
    def store_uploaded_file(self, file_id: str, original_filename: str, stored_filename: str,
                          file_size: int, file_type: str, session_id: str, 
                          df: pd.DataFrame = None) -> bool:
        """存储上传文件信息和数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 存储文件元信息
            columns_info = []
            row_count = 0
            column_count = 0
            
            if df is not None:
                row_count = len(df)
                column_count = len(df.columns)
                columns_info = [
                    {
                        'name': col,
                        'dtype': str(df[col].dtype),
                        'null_count': int(df[col].isnull().sum()),
                        'unique_count': int(df[col].nunique())
                    }
                    for col in df.columns
                ]
            
            cursor.execute("""
                INSERT INTO uploaded_files 
                (file_id, original_filename, stored_filename, file_size, file_type, 
                 session_id, row_count, column_count, columns_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (file_id, original_filename, stored_filename, file_size, file_type,
                  session_id, row_count, column_count, json.dumps(columns_info, ensure_ascii=False)))
            
            # 存储文件数据
            if df is not None:
                for idx, row in df.iterrows():
                    row_data = row.to_dict()
                    # 处理NaN值
                    for key, value in row_data.items():
                        if pd.isna(value):
                            row_data[key] = None
                    
                    cursor.execute("""
                        INSERT INTO file_data (file_id, row_index, data_json)
                        VALUES (?, ?, ?)
                    """, (file_id, idx, json.dumps(row_data, ensure_ascii=False)))
            
            conn.commit()
            logger.info(f"文件数据存储成功: {original_filename} ({row_count} 行)")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"存储文件数据失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_uploaded_file_info(self, file_id: str) -> Optional[Dict]:
        """获取上传文件信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM uploaded_files WHERE file_id = ? AND is_deleted = 0
            """, (file_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                file_info = dict(zip(columns, row))
                
                # 解析列信息
                if file_info['columns_json']:
                    file_info['columns'] = json.loads(file_info['columns_json'])
                
                return file_info
            return None
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None
        finally:
            conn.close()
    
    def get_file_data(self, file_id: str, limit: int = None, offset: int = 0) -> List[Dict]:
        """获取文件数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT row_index, data_json FROM file_data 
                WHERE file_id = ? 
                ORDER BY row_index
            """
            params = [file_id]
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            data = []
            for row_index, data_json in cursor.fetchall():
                row_data = json.loads(data_json)
                row_data['_row_index'] = row_index
                data.append(row_data)
            
            return data
            
        except Exception as e:
            logger.error(f"获取文件数据失败: {e}")
            return []
        finally:
            conn.close()
    
    # === 处理结果管理 ===
    
    def store_processing_result(self, session_id: str, file_id: str, result_type: str,
                              row_index: int, input_data: Dict, result_data: Dict,
                              confidence: float = None, processing_time: float = None) -> int:
        """存储处理结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO processing_results 
                (session_id, file_id, result_type, row_index, input_data_json, 
                 result_data_json, confidence, processing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, file_id, result_type, row_index,
                  json.dumps(input_data, ensure_ascii=False),
                  json.dumps(result_data, ensure_ascii=False),
                  confidence, processing_time))
            
            result_id = cursor.lastrowid
            conn.commit()
            return result_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"存储处理结果失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_processing_results(self, session_id: str, result_type: str = None,
                             file_id: str = None) -> List[Dict]:
        """获取处理结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM processing_results WHERE session_id = ?"
            params = [session_id]
            
            if result_type:
                query += " AND result_type = ?"
                params.append(result_type)
            
            if file_id:
                query += " AND file_id = ?"
                params.append(file_id)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                # 解析JSON数据
                if result['input_data_json']:
                    result['input_data'] = json.loads(result['input_data_json'])
                if result['result_data_json']:
                    result['result_data'] = json.loads(result['result_data_json'])
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"获取处理结果失败: {e}")
            return []
        finally:
            conn.close()
    
    # === 配置管理 ===
    
    def set_config(self, key: str, value: Any, config_type: str = 'string', 
                  description: str = None) -> bool:
        """设置系统配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 将值转换为字符串存储
            if config_type == 'json':
                value_str = json.dumps(value, ensure_ascii=False)
            else:
                value_str = str(value)
            
            cursor.execute("""
                INSERT OR REPLACE INTO system_config 
                (config_key, config_value, config_type, description, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value_str, config_type, description))
            
            conn.commit()
            logger.info(f"配置设置成功: {key}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"设置配置失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取系统配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT config_value, config_type FROM system_config 
                WHERE config_key = ? AND is_active = 1
            """, (key,))
            
            row = cursor.fetchone()
            if row:
                value_str, config_type = row
                
                # 根据类型转换值
                if config_type == 'json':
                    return json.loads(value_str)
                elif config_type == 'boolean':
                    return value_str.lower() in ('true', '1', 'yes')
                elif config_type == 'number':
                    try:
                        return float(value_str) if '.' in value_str else int(value_str)
                    except ValueError:
                        return default
                else:
                    return value_str
            
            return default
            
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            return default
        finally:
            conn.close()
    
    # === 数据统计 ===
    
    def get_statistics(self) -> Dict:
        """获取系统统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # 文件统计
            cursor.execute("SELECT COUNT(*) FROM uploaded_files WHERE is_deleted = 0")
            stats['total_files'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(row_count) FROM uploaded_files WHERE is_deleted = 0")
            stats['total_rows'] = cursor.fetchone()[0] or 0
            
            # 字段映射统计
            cursor.execute("SELECT COUNT(*) FROM field_mappings WHERE is_active = 1")
            stats['field_mappings'] = cursor.fetchone()[0]
            
            # 处理结果统计
            cursor.execute("SELECT result_type, COUNT(*) FROM processing_results GROUP BY result_type")
            stats['processing_results'] = dict(cursor.fetchall())
            
            # 最近24小时活动
            cursor.execute("""
                SELECT COUNT(*) FROM uploaded_files 
                WHERE upload_time > datetime('now', '-24 hours')
            """)
            stats['recent_uploads'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
        finally:
            conn.close()
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """清理旧数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 标记删除旧文件
            cursor.execute("""
                UPDATE uploaded_files 
                SET is_deleted = 1 
                WHERE upload_time < datetime('now', '-{} days')
            """.format(days))
            
            deleted_files = cursor.rowcount
            
            # 删除旧的处理结果
            cursor.execute("""
                DELETE FROM processing_results 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            
            deleted_results = cursor.rowcount
            
            conn.commit()
            logger.info(f"数据清理完成: {deleted_files} 个文件, {deleted_results} 个结果")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"数据清理失败: {e}")
            return False
        finally:
            conn.close()