# -*- coding: utf-8 -*-
"""
混合增量更新引擎
结合时间戳和哈希值的双重策略，确保数据同步的准确性和效率
"""

import hashlib
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    """变更类型枚举"""
    INSERT = "INSERT"
    UPDATE = "UPDATE" 
    DELETE = "DELETE"
    CONFLICT = "CONFLICT"

@dataclass
class ChangeRecord:
    """变更记录数据结构"""
    record_id: str
    change_type: ChangeType
    source_system: str
    timestamp: datetime
    content_hash: str
    data_payload: Dict[str, Any]
    conflict_score: float = 0.0
    resolved: bool = False

@dataclass
class SyncCheckpoint:
    """同步检查点"""
    source_id: str
    last_sync_timestamp: datetime
    last_content_hash: str
    processed_count: int
    error_count: int

class HybridIncrementalSyncEngine:
    """混合增量同步引擎 - 时间戳+哈希双重策略"""
    
    def __init__(self, sync_db_path: str = 'sync_tracking.db'):
        self.sync_db_path = sync_db_path
        self.init_sync_database()
        
    def init_sync_database(self):
        """初始化同步跟踪数据库"""
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        # 创建同步检查点表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_checkpoints (
            source_id TEXT PRIMARY KEY,
            last_sync_timestamp TEXT,
            last_content_hash TEXT,
            processed_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建变更记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS change_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT,
            change_type TEXT,
            source_system TEXT,
            timestamp TEXT,
            content_hash TEXT,
            data_payload TEXT,
            conflict_score REAL DEFAULT 0.0,
            resolved INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(record_id, source_system, content_hash)
        )
        ''')
        
        # 创建哈希索引表（用于快速查找重复内容）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_hashes (
            content_hash TEXT PRIMARY KEY,
            record_count INTEGER DEFAULT 1,
            first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("同步跟踪数据库初始化完成")
    
    def detect_changes_hybrid(self, source_config: Dict, data_source) -> List[ChangeRecord]:
        """
        混合策略检测变更
        优先使用时间戳，辅助使用哈希值验证
        """
        source_id = source_config['source_id']
        last_checkpoint = self.get_last_checkpoint(source_id)
        
        # Step 1: 基于时间戳获取候选变更
        timestamp_changes = self._detect_by_timestamp(
            data_source, last_checkpoint, source_config
        )
        
        # Step 2: 使用哈希值验证真实变更
        verified_changes = self._verify_by_hash(timestamp_changes, source_id)
        
        # Step 3: 检测删除记录（通过哈希对比）
        deletion_changes = self._detect_deletions(data_source, source_id)
        
        all_changes = verified_changes + deletion_changes
        
        # Step 4: 保存变更记录
        self._save_change_records(all_changes)
        
        logger.info(f"检测到 {len(all_changes)} 条变更，来源: {source_id}")
        return all_changes
    
    def _detect_by_timestamp(self, data_source, checkpoint: SyncCheckpoint, 
                           source_config: Dict) -> List[Dict]:
        """基于时间戳检测变更"""
        
        timestamp_field = source_config.get('timestamp_field', 'updated_at')
        last_sync = checkpoint.last_sync_timestamp if checkpoint else datetime.min
        
        # 构建查询条件
        if hasattr(data_source, 'query'):
            # 数据库数据源
            query = f"""
            SELECT * FROM {source_config['table_name']} 
            WHERE {timestamp_field} > '{last_sync.isoformat()}'
            ORDER BY {timestamp_field} ASC
            """
            df = pd.read_sql(query, data_source.connection)
        else:
            # 文件数据源
            df = data_source
            if timestamp_field in df.columns:
                df = df[pd.to_datetime(df[timestamp_field]) > last_sync]
        
        return df.to_dict('records')
    
    def _verify_by_hash(self, candidate_changes: List[Dict], source_id: str) -> List[ChangeRecord]:
        """使用哈希值验证真实变更"""
        
        verified_changes = []
        
        for record in candidate_changes:
            # 计算记录内容哈希
            content_hash = self._calculate_record_hash(record)
            record_id = str(record.get('id', record.get('material_code', '')))
            
            # 检查是否为真实变更
            if self._is_real_change(record_id, content_hash, source_id):
                change_type = self._determine_change_type(record_id, source_id)
                
                change_record = ChangeRecord(
                    record_id=record_id,
                    change_type=change_type,
                    source_system=source_id,
                    timestamp=pd.to_datetime(record.get('updated_at', datetime.now())),
                    content_hash=content_hash,
                    data_payload=record
                )
                verified_changes.append(change_record)
        
        return verified_changes
    
    def _calculate_record_hash(self, record: Dict) -> str:
        """计算记录内容哈希值"""
        
        # 排除时间戳字段，只对业务字段计算哈希
        business_fields = {k: v for k, v in record.items() 
                          if k not in ['updated_at', 'created_at', 'last_modified']}
        
        # 排序字段确保哈希一致性
        sorted_content = json.dumps(business_fields, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(sorted_content.encode('utf-8')).hexdigest()
    
    def _is_real_change(self, record_id: str, content_hash: str, source_id: str) -> bool:
        """判断是否为真实变更"""
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        # 查询最近的记录哈希
        cursor.execute('''
        SELECT content_hash FROM change_records 
        WHERE record_id = ? AND source_system = ? 
        ORDER BY timestamp DESC LIMIT 1
        ''', (record_id, source_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            return True  # 新记录
        
        return result[0] != content_hash  # 哈希不同则为变更
    
    def _determine_change_type(self, record_id: str, source_id: str) -> ChangeType:
        """确定变更类型"""
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT COUNT(*) FROM change_records 
        WHERE record_id = ? AND source_system = ?
        ''', (record_id, source_id))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return ChangeType.INSERT if count == 0 else ChangeType.UPDATE
    
    def get_last_checkpoint(self, source_id: str) -> Optional[SyncCheckpoint]:
        """获取最后同步检查点"""
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM sync_checkpoints WHERE source_id = ?
        ''', (source_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return SyncCheckpoint(
                source_id=result[0],
                last_sync_timestamp=pd.to_datetime(result[1]),
                last_content_hash=result[2],
                processed_count=result[3],
                error_count=result[4]
            )
        return None
    
    def update_checkpoint(self, source_id: str, new_timestamp: datetime, 
                         processed_count: int, error_count: int = 0):
        """更新同步检查点"""
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO sync_checkpoints 
        (source_id, last_sync_timestamp, processed_count, error_count)
        VALUES (?, ?, ?, ?)
        ''', (source_id, new_timestamp.isoformat(), processed_count, error_count))
        
        conn.commit()
        conn.close()
        
        logger.info(f"更新检查点: {source_id}, 时间: {new_timestamp}")
    
    def _save_change_records(self, changes: List[ChangeRecord]):
        """保存变更记录"""
        
        if not changes:
            return
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        for change in changes:
            cursor.execute('''
            INSERT OR IGNORE INTO change_records 
            (record_id, change_type, source_system, timestamp, content_hash, data_payload)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                change.record_id,
                change.change_type.value,
                change.source_system,
                change.timestamp.isoformat(),
                change.content_hash,
                json.dumps(change.data_payload, ensure_ascii=False)
            ))
        
        conn.commit()
        conn.close()
    
    def get_sync_statistics(self, source_id: str = None) -> Dict[str, Any]:
        """获取同步统计信息"""
        
        conn = sqlite3.connect(self.sync_db_path)
        
        if source_id:
            query = '''
            SELECT 
                change_type,
                COUNT(*) as count,
                AVG(conflict_score) as avg_conflict_score
            FROM change_records 
            WHERE source_system = ?
            GROUP BY change_type
            '''
            df = pd.read_sql(query, conn, params=(source_id,))
        else:
            query = '''
            SELECT 
                source_system,
                change_type,
                COUNT(*) as count,
                AVG(conflict_score) as avg_conflict_score
            FROM change_records 
            GROUP BY source_system, change_type
            '''
            df = pd.read_sql(query, conn)
        
        conn.close()
        return df.to_dict('records')

# 使用示例
def example_usage():
    """使用示例"""
    
    # 初始化混合同步引擎
    sync_engine = HybridIncrementalSyncEngine()
    
    # 配置数据源
    source_config = {
        'source_id': 'erp_materials',
        'table_name': 'material_master',
        'timestamp_field': 'last_modified',
        'primary_key': 'material_code'
    }
    
    # 检测变更（模拟数据源）
    changes = sync_engine.detect_changes_hybrid(source_config, mock_data_source)
    
    print(f"检测到 {len(changes)} 条变更")
    for change in changes:
        print(f"- {change.change_type.value}: {change.record_id}")
    
    # 获取统计信息
    stats = sync_engine.get_sync_statistics('erp_materials')
    print("同步统计:", stats)

if __name__ == "__main__":
    example_usage()