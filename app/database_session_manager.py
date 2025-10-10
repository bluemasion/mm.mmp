#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库会话管理器
使用SQLite存储所有会话数据和应用状态
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseSessionManager:
    """基于数据库的会话管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 会话表 - 存储会话基本信息
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_agent TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    metadata TEXT  -- JSON格式的额外信息
                )
            ''')
            
            # 会话数据表 - 存储具体的键值对数据
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    data_key TEXT,
                    data_value TEXT,  -- JSON格式存储
                    data_type TEXT,   -- 数据类型标记
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    UNIQUE(session_id, data_key)
                )
            ''')
            
            # 提取结果表 - 存储参数提取的结果
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extraction_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    material_index INTEGER,
                    original_name TEXT,
                    extracted_name TEXT,
                    original_spec TEXT,
                    extracted_spec TEXT,
                    brand TEXT,
                    manufacturer TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # 分类推荐表 - 存储智能分类推荐结果
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classification_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    material_id INTEGER,
                    category_id TEXT,
                    category_name TEXT,
                    confidence REAL,
                    match_reasons TEXT,  -- JSON格式存储匹配原因
                    is_selected INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (material_id) REFERENCES extraction_results(id)
                )
            ''')
            
            # 分类选择表 - 存储用户的分类选择
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS category_selections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    material_id INTEGER,
                    selected_category_id TEXT,
                    selected_category_name TEXT,
                    selection_source TEXT,  -- 'recommendation', 'manual', 'auto'
                    confidence REAL,
                    user_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (material_id) REFERENCES extraction_results(id)
                )
            ''')
            
            # 工作流状态表 - 跟踪每个会话的工作流进度
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_status (
                    session_id TEXT PRIMARY KEY,
                    current_step TEXT,  -- 'upload', 'extract', 'categorize', 'form_gen', 'match', 'decision'
                    step_data TEXT,     -- JSON格式存储当前步骤的状态数据
                    total_materials INTEGER DEFAULT 0,
                    processed_materials INTEGER DEFAULT 0,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # 创建索引优化查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active, last_accessed)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_data_lookup ON session_data(session_id, data_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_extraction_session ON extraction_results(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_recommendations_session ON classification_recommendations(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_selections_session ON category_selections(session_id)')
            
            conn.commit()
            logger.info("数据库表结构初始化完成")
            
        except Exception as e:
            logger.error(f"数据库表初始化失败: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def create_session(self, session_id: str = None, user_agent: str = None, ip_address: str = None) -> str:
        """创建新会话"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            expires_at = datetime.now() + timedelta(hours=24)
            
            cursor.execute('''
                INSERT OR REPLACE INTO sessions 
                (session_id, user_agent, ip_address, expires_at, metadata) 
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, user_agent, ip_address, expires_at, '{}'))
            
            conn.commit()
            logger.info(f"创建会话: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT session_id, user_agent, ip_address, created_at, last_accessed, 
                       expires_at, is_active, metadata
                FROM sessions 
                WHERE session_id = ? AND is_active = 1 AND expires_at > ?
            ''', (session_id, datetime.now()))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # 更新最后访问时间
            cursor.execute('''
                UPDATE sessions 
                SET last_accessed = CURRENT_TIMESTAMP 
                WHERE session_id = ?
            ''', (session_id,))
            conn.commit()
            
            return {
                'session_id': row[0],
                'user_agent': row[1],
                'ip_address': row[2],
                'created_at': row[3],
                'last_accessed': row[4],
                'expires_at': row[5],
                'is_active': bool(row[6]),
                'metadata': json.loads(row[7] or '{}')
            }
            
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
        finally:
            conn.close()
    
    def store_data(self, session_id: str, key: str, data: Any) -> bool:
        """存储会话数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 确保会话存在
            if not self.get_session(session_id):
                self.create_session(session_id)
            
            data_json = json.dumps(data, ensure_ascii=False, default=str)
            data_type = type(data).__name__
            
            cursor.execute('''
                INSERT OR REPLACE INTO session_data 
                (session_id, data_key, data_value, data_type, updated_at) 
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (session_id, key, data_json, data_type))
            
            conn.commit()
            logger.debug(f"存储会话数据: {session_id}[{key}] = {type(data).__name__}")
            return True
            
        except Exception as e:
            logger.error(f"存储会话数据失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_data(self, session_id: str, key: str, default=None) -> Any:
        """获取会话数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT data_value, data_type 
                FROM session_data 
                WHERE session_id = ? AND data_key = ?
            ''', (session_id, key))
            
            row = cursor.fetchone()
            if not row:
                return default
            
            data_value, data_type = row
            return json.loads(data_value)
            
        except Exception as e:
            logger.error(f"获取会话数据失败: {e}")
            return default
        finally:
            conn.close()
    
    def delete_data(self, session_id: str, key: str = None) -> bool:
        """删除会话数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if key:
                cursor.execute('DELETE FROM session_data WHERE session_id = ? AND data_key = ?', (session_id, key))
            else:
                cursor.execute('DELETE FROM session_data WHERE session_id = ?', (session_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"删除会话数据失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            
            # 获取过期的会话ID
            cursor.execute('SELECT session_id FROM sessions WHERE expires_at <= ?', (now,))
            expired_sessions = [row[0] for row in cursor.fetchall()]
            
            if expired_sessions:
                # 删除相关数据
                placeholders = ','.join(['?' for _ in expired_sessions])
                cursor.execute(f'DELETE FROM session_data WHERE session_id IN ({placeholders})', expired_sessions)
                cursor.execute(f'DELETE FROM extraction_results WHERE session_id IN ({placeholders})', expired_sessions)
                cursor.execute(f'DELETE FROM classification_recommendations WHERE session_id IN ({placeholders})', expired_sessions)
                cursor.execute(f'DELETE FROM category_selections WHERE session_id IN ({placeholders})', expired_sessions)
                cursor.execute(f'DELETE FROM workflow_status WHERE session_id IN ({placeholders})', expired_sessions)
                cursor.execute(f'DELETE FROM sessions WHERE session_id IN ({placeholders})', expired_sessions)
                
                conn.commit()
                logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
            
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_workflow_status(self, session_id: str) -> Dict:
        """获取工作流状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT current_step, step_data, total_materials, processed_materials, completed_at
                FROM workflow_status 
                WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return {
                    'current_step': 'upload',
                    'step_data': {},
                    'total_materials': 0,
                    'processed_materials': 0,
                    'completed_at': None
                }
            
            return {
                'current_step': row[0],
                'step_data': json.loads(row[1] or '{}'),
                'total_materials': row[2],
                'processed_materials': row[3],
                'completed_at': row[4]
            }
            
        except Exception as e:
            logger.error(f"获取工作流状态失败: {e}")
            return {}
        finally:
            conn.close()
    
    def update_workflow_status(self, session_id: str, current_step: str, step_data: Dict = None, 
                             total_materials: int = None, processed_materials: int = None) -> bool:
        """更新工作流状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            step_data_json = json.dumps(step_data or {}, ensure_ascii=False, default=str)
            
            cursor.execute('''
                INSERT OR REPLACE INTO workflow_status 
                (session_id, current_step, step_data, total_materials, processed_materials, updated_at) 
                VALUES (?, ?, ?, 
                        COALESCE(?, (SELECT total_materials FROM workflow_status WHERE session_id = ?), 0),
                        COALESCE(?, (SELECT processed_materials FROM workflow_status WHERE session_id = ?), 0),
                        CURRENT_TIMESTAMP)
            ''', (session_id, current_step, step_data_json, total_materials, session_id, processed_materials, session_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新工作流状态失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def store_recommendation(self, session_id: str, material_features: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> bool:
        """
        存储分类推荐结果
        
        Args:
            session_id: 会话ID
            material_features: 物料特征
            recommendations: 推荐结果列表
            
        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 存储到推荐表
            cursor.execute('''
                INSERT INTO classification_recommendations 
                (session_id, material_features, recommendations)
                VALUES (?, ?, ?)
            ''', (
                session_id,
                json.dumps(material_features, ensure_ascii=False),
                json.dumps(recommendations, ensure_ascii=False)
            ))
            
            conn.commit()
            logger.info(f"推荐结果已存储: session_id={session_id}, count={len(recommendations)}")
            return True
            
        except Exception as e:
            logger.error(f"存储推荐结果失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_all_session_data(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话的所有相关数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            包含所有会话数据的字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            result = {}
            
            # 获取基本会话信息
            cursor.execute('''
                SELECT session_id, user_agent, ip_address, created_at, last_accessed, expires_at
                FROM sessions 
                WHERE session_id = ? AND is_active = 1
            ''', (session_id,))
            
            session_row = cursor.fetchone()
            if session_row:
                result['session_info'] = {
                    'session_id': session_row[0],
                    'user_agent': session_row[1],
                    'ip_address': session_row[2],
                    'created_at': session_row[3],
                    'last_accessed': session_row[4],
                    'expires_at': session_row[5]
                }
            
            # 获取会话数据
            cursor.execute('''
                SELECT data_key, data_value 
                FROM session_data 
                WHERE session_id = ?
                ORDER BY created_at
            ''', (session_id,))
            
            session_data = {}
            for row in cursor.fetchall():
                try:
                    session_data[row[0]] = json.loads(row[1])
                except:
                    session_data[row[0]] = row[1]
            
            result['session_data'] = session_data
            
            # 获取提取结果
            cursor.execute('''
                SELECT original_name, extracted_name, original_spec, extracted_spec, brand, confidence
                FROM extraction_results 
                WHERE session_id = ?
                ORDER BY material_index
            ''', (session_id,))
            
            extraction_results = []
            for row in cursor.fetchall():
                extraction_results.append({
                    'original_name': row[0],
                    'extracted_name': row[1],
                    'original_spec': row[2],
                    'extracted_spec': row[3],
                    'brand': row[4],
                    'confidence': row[5]
                })
            
            result['extraction_results'] = extraction_results
            
            # 获取分类推荐
            cursor.execute('''
                SELECT category_id, category_name, confidence, match_reasons, material_features, recommendations
                FROM classification_recommendations 
                WHERE session_id = ?
                ORDER BY created_at
            ''', (session_id,))
            
            recommendations = []
            for row in cursor.fetchall():
                rec = {
                    'category_id': row[0],
                    'category_name': row[1],
                    'confidence': row[2]
                }
                try:
                    if row[3]: rec['match_reasons'] = json.loads(row[3])
                    if row[4]: rec['material_features'] = json.loads(row[4])
                    if row[5]: rec['recommendations'] = json.loads(row[5])
                except:
                    pass
                recommendations.append(rec)
            
            result['recommendations'] = recommendations
            
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"获取所有会话数据失败: {e}")
            return {}
    
    def get_session_info(self, session_id: str) -> dict:
        """获取会话基本信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取会话基本信息
            cursor.execute('''
                SELECT session_id, created_at, last_accessed 
                FROM sessions 
                WHERE session_id = ?
            ''', (session_id,))
            
            session_row = cursor.fetchone()
            if not session_row:
                return {}
            
            # 统计会话数据
            cursor.execute('''
                SELECT COUNT(*) FROM session_data WHERE session_id = ?
            ''', (session_id,))
            data_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM classification_recommendations WHERE session_id = ?
            ''', (session_id,))
            recommendation_count = cursor.fetchone()[0]
            
            session_info = {
                'session_id': session_row[0],
                'created_at': session_row[1],
                'last_accessed': session_row[2],
                'data_count': data_count,
                'recommendation_count': recommendation_count
            }
            
            conn.close()
            return session_info
            
        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            return {}