# -*- coding: utf-8 -*-
"""
简化增量同步系统
支持时间戳和哈希的混合策略，处理多数据源同步
暂时简化冲突解决机制，专注于核心同步功能
"""

import logging
import sqlite3
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import json
import time
from enum import Enum

logger = logging.getLogger(__name__)

class SyncStatus(Enum):
    """同步状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CONFLICT = "conflict"

class ConflictResolution(Enum):
    """冲突解决策略枚举"""
    LATEST_WINS = "latest_wins"
    SOURCE_PRIORITY = "source_priority"
    MANUAL_REVIEW = "manual_review"
    MERGE_FIELDS = "merge_fields"

@dataclass
class SyncRecord:
    """同步记录"""
    record_id: str
    source_system: str
    material_code: str
    content_hash: str
    last_modified: datetime
    sync_timestamp: datetime
    sync_status: SyncStatus
    version: int
    raw_data: Dict[str, Any]

@dataclass
class SyncConflict:
    """同步冲突"""
    material_code: str
    conflicting_sources: List[str]
    conflict_type: str
    local_record: SyncRecord
    remote_records: List[SyncRecord]
    resolution_strategy: ConflictResolution
    resolved: bool = False

@dataclass 
class SyncResult:
    """同步结果"""
    total_records: int
    new_records: int
    updated_records: int
    conflicts: int
    errors: int
    processing_time: float
    sync_timestamp: datetime

class SimplifiedIncrementalSync:
    """简化增量同步系统"""
    
    def __init__(self, main_db_path: str = 'business_data.db',
                 sync_db_path: str = 'sync_tracking.db'):
        self.main_db_path = main_db_path
        self.sync_db_path = sync_db_path
        
        # 数据源优先级配置（数字越小优先级越高）
        self.source_priority = {
            'ERP': 1,
            'PLM': 2,
            'PDM': 3,
            'MRP': 4,
            'WMS': 5,
            'manual': 10,
            'unknown': 99
        }
        
        # 同步配置
        self.sync_config = {
            'batch_size': 1000,
            'max_conflicts_per_batch': 100,
            'conflict_resolution_strategy': ConflictResolution.LATEST_WINS,
            'enable_auto_resolution': True,
            'sync_interval_minutes': 30,
            'retention_days': 90
        }
        
        # 初始化同步数据库
        self._init_sync_database()
        
        logger.info("简化增量同步系统初始化完成")
    
    def _init_sync_database(self):
        """初始化同步跟踪数据库"""
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        try:
            # 同步记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_records (
                record_id TEXT PRIMARY KEY,
                source_system TEXT NOT NULL,
                material_code TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                last_modified TIMESTAMP NOT NULL,
                sync_timestamp TIMESTAMP NOT NULL,
                sync_status TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_system, material_code)
            )''')
            
            # 同步冲突表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_conflicts (
                conflict_id TEXT PRIMARY KEY,
                material_code TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                conflicting_sources TEXT NOT NULL,
                resolution_strategy TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                resolver TEXT,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                conflict_data TEXT
            )''')
            
            # 同步历史表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_history (
                sync_id TEXT PRIMARY KEY,
                source_system TEXT NOT NULL,
                sync_type TEXT NOT NULL,
                total_records INTEGER,
                new_records INTEGER,
                updated_records INTEGER,
                conflicts INTEGER,
                errors INTEGER,
                processing_time REAL,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT NOT NULL,
                error_details TEXT
            )''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_records_material ON sync_records(material_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_records_source ON sync_records(source_system)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_records_timestamp ON sync_records(sync_timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conflicts_material ON sync_conflicts(material_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_source ON sync_history(source_system)')
            
            conn.commit()
            
        finally:
            conn.close()
    
    def sync_from_source(self, source_system: str, 
                        source_data: List[Dict[str, Any]],
                        sync_type: str = 'incremental') -> SyncResult:
        """从指定数据源同步数据"""
        
        start_time = time.time()
        logger.info(f"开始从 {source_system} 同步 {len(source_data)} 条记录")
        
        # 生成同步ID
        sync_id = f"SYNC_{source_system}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # 初始化统计计数
            stats = {
                'total_records': len(source_data),
                'new_records': 0,
                'updated_records': 0,
                'conflicts': 0,
                'errors': 0
            }
            
            conflicts = []
            
            # 获取现有同步记录
            existing_records = self._get_existing_sync_records(source_system)
            existing_lookup = {rec.material_code: rec for rec in existing_records}
            
            # 批量处理数据
            for batch_start in range(0, len(source_data), self.sync_config['batch_size']):
                batch_end = min(batch_start + self.sync_config['batch_size'], len(source_data))
                batch_data = source_data[batch_start:batch_end]
                
                batch_result = self._process_sync_batch(
                    source_system, batch_data, existing_lookup, sync_id
                )
                
                # 累积统计
                stats['new_records'] += batch_result['new_records']
                stats['updated_records'] += batch_result['updated_records']
                stats['conflicts'] += batch_result['conflicts']
                stats['errors'] += batch_result['errors']
                conflicts.extend(batch_result['conflicts_list'])
            
            processing_time = time.time() - start_time
            
            # 记录同步历史
            self._record_sync_history(
                sync_id, source_system, sync_type, stats, 
                processing_time, 'completed'
            )
            
            # 处理冲突（如果启用自动解决）
            if self.sync_config['enable_auto_resolution'] and conflicts:
                self._auto_resolve_conflicts(conflicts)
            
            logger.info(f"同步完成: {stats}")
            
            return SyncResult(
                total_records=stats['total_records'],
                new_records=stats['new_records'],
                updated_records=stats['updated_records'],
                conflicts=stats['conflicts'],
                errors=stats['errors'],
                processing_time=processing_time,
                sync_timestamp=datetime.now()
            )
            
        except Exception as e:
            # 记录失败的同步历史
            processing_time = time.time() - start_time
            self._record_sync_history(
                sync_id, source_system, sync_type, stats,
                processing_time, 'failed', str(e)
            )
            
            logger.error(f"同步失败: {e}")
            raise
    
    def _get_existing_sync_records(self, source_system: str) -> List[SyncRecord]:
        """获取现有的同步记录"""
        
        conn = sqlite3.connect(self.sync_db_path)
        
        try:
            query = '''
            SELECT record_id, source_system, material_code, content_hash,
                   last_modified, sync_timestamp, sync_status, version, raw_data
            FROM sync_records
            WHERE source_system = ?
            '''
            
            df = pd.read_sql(query, conn, params=[source_system])
            
            records = []
            for _, row in df.iterrows():
                records.append(SyncRecord(
                    record_id=row['record_id'],
                    source_system=row['source_system'],
                    material_code=row['material_code'],
                    content_hash=row['content_hash'],
                    last_modified=pd.to_datetime(row['last_modified']),
                    sync_timestamp=pd.to_datetime(row['sync_timestamp']),
                    sync_status=SyncStatus(row['sync_status']),
                    version=row['version'],
                    raw_data=json.loads(row['raw_data']) if row['raw_data'] else {}
                ))
            
            return records
            
        finally:
            conn.close()
    
    def _process_sync_batch(self, source_system: str, batch_data: List[Dict[str, Any]],
                           existing_lookup: Dict[str, SyncRecord], 
                           sync_id: str) -> Dict[str, Any]:
        """处理同步批次"""
        
        batch_stats = {
            'new_records': 0,
            'updated_records': 0,
            'conflicts': 0,
            'errors': 0,
            'conflicts_list': []
        }
        
        new_records = []
        updated_records = []
        
        for material_data in batch_data:
            try:
                material_code = material_data.get('material_code', '')
                if not material_code:
                    batch_stats['errors'] += 1
                    continue
                
                # 计算内容哈希
                content_hash = self._calculate_content_hash(material_data)
                
                # 获取最后修改时间
                last_modified = self._extract_last_modified(material_data)
                
                # 创建同步记录
                sync_record = SyncRecord(
                    record_id=f"{source_system}_{material_code}_{int(time.time())}",
                    source_system=source_system,
                    material_code=material_code,
                    content_hash=content_hash,
                    last_modified=last_modified,
                    sync_timestamp=datetime.now(),
                    sync_status=SyncStatus.PENDING,
                    version=1,
                    raw_data=material_data
                )
                
                # 检查是否已存在记录
                existing_record = existing_lookup.get(material_code)
                
                if existing_record is None:
                    # 新记录
                    new_records.append(sync_record)
                    batch_stats['new_records'] += 1
                    
                elif existing_record.content_hash != content_hash:
                    # 内容有变化，需要更新
                    
                    # 检查是否有冲突（比较时间戳）
                    if self._has_temporal_conflict(existing_record, sync_record):
                        # 创建冲突记录
                        conflict = self._create_conflict_record(
                            material_code, existing_record, sync_record
                        )
                        batch_stats['conflicts_list'].append(conflict)
                        batch_stats['conflicts'] += 1
                        
                    else:
                        # 正常更新
                        sync_record.version = existing_record.version + 1
                        updated_records.append(sync_record)
                        batch_stats['updated_records'] += 1
                
                # 如果哈希相同，则跳过（无需更新）
                
            except Exception as e:
                logger.error(f"处理物料 {material_data.get('material_code', 'unknown')} 失败: {e}")
                batch_stats['errors'] += 1
        
        # 批量保存记录
        self._save_sync_records(new_records + updated_records)
        
        return batch_stats
    
    def _calculate_content_hash(self, material_data: Dict[str, Any]) -> str:
        """计算内容哈希值"""
        
        # 选择用于哈希计算的关键字段
        hash_fields = [
            'material_name', 'specification', 'manufacturer',
            'material_type', 'unit', 'category'
        ]
        
        # 构建哈希源字符串
        hash_source = {}
        for field in hash_fields:
            value = material_data.get(field, '')
            if value:
                # 标准化字符串（去除空白、转小写）
                hash_source[field] = str(value).strip().lower()
        
        # 生成哈希
        source_json = json.dumps(hash_source, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(source_json.encode('utf-8')).hexdigest()
    
    def _extract_last_modified(self, material_data: Dict[str, Any]) -> datetime:
        """提取最后修改时间"""
        
        # 尝试多个可能的时间字段
        time_fields = ['last_modified', 'update_time', 'modified_at', 'updated_at']
        
        for field in time_fields:
            if field in material_data:
                try:
                    time_value = material_data[field]
                    if isinstance(time_value, str):
                        # 尝试解析时间字符串
                        return pd.to_datetime(time_value)
                    elif isinstance(time_value, datetime):
                        return time_value
                except:
                    continue
        
        # 如果没有找到有效时间戳，使用当前时间
        return datetime.now()
    
    def _has_temporal_conflict(self, existing_record: SyncRecord, 
                             new_record: SyncRecord) -> bool:
        """检查是否存在时间冲突"""
        
        # 如果新记录的修改时间早于已存在记录，可能存在冲突
        time_diff = (new_record.last_modified - existing_record.last_modified).total_seconds()
        
        # 如果时间差在冲突窗口内（比如5分钟），认为可能是冲突
        conflict_window_seconds = 300  # 5分钟
        
        return abs(time_diff) <= conflict_window_seconds
    
    def _create_conflict_record(self, material_code: str, 
                              existing_record: SyncRecord,
                              new_record: SyncRecord) -> SyncConflict:
        """创建冲突记录"""
        
        conflict = SyncConflict(
            material_code=material_code,
            conflicting_sources=[existing_record.source_system, new_record.source_system],
            conflict_type='timestamp_hash_mismatch',
            local_record=existing_record,
            remote_records=[new_record],
            resolution_strategy=self.sync_config['conflict_resolution_strategy']
        )
        
        # 保存冲突到数据库
        self._save_conflict_record(conflict)
        
        return conflict
    
    def _save_sync_records(self, records: List[SyncRecord]):
        """保存同步记录到数据库"""
        
        if not records:
            return
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        try:
            # 准备批量插入数据
            insert_data = []
            for record in records:
                insert_data.append((
                    record.record_id,
                    record.source_system,
                    record.material_code,
                    record.content_hash,
                    record.last_modified.isoformat(),
                    record.sync_timestamp.isoformat(),
                    record.sync_status.value,
                    record.version,
                    json.dumps(record.raw_data, ensure_ascii=False)
                ))
            
            # 使用INSERT OR REPLACE进行批量更新
            cursor.executemany('''
            INSERT OR REPLACE INTO sync_records (
                record_id, source_system, material_code, content_hash,
                last_modified, sync_timestamp, sync_status, version, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', insert_data)
            
            conn.commit()
            
        finally:
            conn.close()
    
    def _save_conflict_record(self, conflict: SyncConflict):
        """保存冲突记录到数据库"""
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        try:
            conflict_id = f"CONF_{conflict.material_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            conflict_data = {
                'local_record': asdict(conflict.local_record),
                'remote_records': [asdict(rec) for rec in conflict.remote_records]
            }
            
            cursor.execute('''
            INSERT INTO sync_conflicts (
                conflict_id, material_code, conflict_type, conflicting_sources,
                resolution_strategy, resolved, conflict_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                conflict_id,
                conflict.material_code,
                conflict.conflict_type,
                json.dumps(conflict.conflicting_sources),
                conflict.resolution_strategy.value,
                conflict.resolved,
                json.dumps(conflict_data, default=str, ensure_ascii=False)
            ))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def _auto_resolve_conflicts(self, conflicts: List[SyncConflict]):
        """自动解决冲突"""
        
        logger.info(f"开始自动解决 {len(conflicts)} 个冲突")
        
        for conflict in conflicts:
            try:
                resolution_strategy = conflict.resolution_strategy
                
                if resolution_strategy == ConflictResolution.LATEST_WINS:
                    self._resolve_latest_wins(conflict)
                    
                elif resolution_strategy == ConflictResolution.SOURCE_PRIORITY:
                    self._resolve_source_priority(conflict)
                    
                else:
                    # 其他策略暂时标记为需要人工解决
                    logger.info(f"冲突 {conflict.material_code} 需要人工解决")
                    
            except Exception as e:
                logger.error(f"自动解决冲突 {conflict.material_code} 失败: {e}")
    
    def _resolve_latest_wins(self, conflict: SyncConflict):
        """按最新时间戳获胜的策略解决冲突"""
        
        # 找出最新的记录
        all_records = [conflict.local_record] + conflict.remote_records
        latest_record = max(all_records, key=lambda x: x.last_modified)
        
        # 更新主数据库
        self._apply_record_to_main_db(latest_record)
        
        # 标记冲突已解决
        self._mark_conflict_resolved(conflict, 'auto_latest_wins')
        
        logger.info(f"冲突 {conflict.material_code} 已按最新时间戳解决")
    
    def _resolve_source_priority(self, conflict: SyncConflict):
        """按数据源优先级解决冲突"""
        
        # 找出优先级最高的记录
        all_records = [conflict.local_record] + conflict.remote_records
        
        highest_priority_record = min(
            all_records,
            key=lambda x: self.source_priority.get(x.source_system, 99)
        )
        
        # 更新主数据库
        self._apply_record_to_main_db(highest_priority_record)
        
        # 标记冲突已解决
        self._mark_conflict_resolved(conflict, 'auto_source_priority')
        
        logger.info(f"冲突 {conflict.material_code} 已按数据源优先级解决")
    
    def _apply_record_to_main_db(self, record: SyncRecord):
        """将记录应用到主数据库"""
        
        conn = sqlite3.connect(self.main_db_path)
        cursor = conn.cursor()
        
        try:
            # 检查主数据库中的表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # 假设使用material_categories表作为主表
            if 'material_categories' in tables:
                
                raw_data = record.raw_data
                
                # 构建更新/插入语句
                cursor.execute('''
                INSERT OR REPLACE INTO material_categories (
                    material_name, category, specification, manufacturer,
                    material_type, unit, last_updated, source_system
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    raw_data.get('material_name', ''),
                    raw_data.get('category', raw_data.get('material_type', '')),
                    raw_data.get('specification', ''),
                    raw_data.get('manufacturer', ''),
                    raw_data.get('material_type', ''),
                    raw_data.get('unit', ''),
                    record.last_modified.isoformat(),
                    record.source_system
                ))
                
                conn.commit()
                
        finally:
            conn.close()
    
    def _mark_conflict_resolved(self, conflict: SyncConflict, resolver: str):
        """标记冲突已解决"""
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE sync_conflicts 
            SET resolved = TRUE, resolver = ?, resolved_at = ?
            WHERE material_code = ? AND resolved = FALSE
            ''', (resolver, datetime.now().isoformat(), conflict.material_code))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def _record_sync_history(self, sync_id: str, source_system: str, sync_type: str,
                           stats: Dict[str, Any], processing_time: float, 
                           status: str, error_details: str = None):
        """记录同步历史"""
        
        conn = sqlite3.connect(self.sync_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO sync_history (
                sync_id, source_system, sync_type, total_records,
                new_records, updated_records, conflicts, errors,
                processing_time, started_at, completed_at, status, error_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sync_id, source_system, sync_type, stats['total_records'],
                stats['new_records'], stats['updated_records'], 
                stats['conflicts'], stats['errors'],
                processing_time, 
                (datetime.now() - timedelta(seconds=processing_time)).isoformat(),
                datetime.now().isoformat(),
                status, error_details
            ))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态报告"""
        
        conn = sqlite3.connect(self.sync_db_path)
        
        try:
            # 获取各数据源的同步统计
            source_stats_query = '''
            SELECT source_system,
                   COUNT(*) as total_records,
                   MAX(sync_timestamp) as last_sync_time,
                   COUNT(CASE WHEN sync_status = 'success' THEN 1 END) as success_count,
                   COUNT(CASE WHEN sync_status = 'failed' THEN 1 END) as failed_count
            FROM sync_records
            GROUP BY source_system
            '''
            
            df_sources = pd.read_sql(source_stats_query, conn)
            
            # 获取未解决的冲突
            conflicts_query = '''
            SELECT material_code, conflicting_sources, conflict_type, created_at
            FROM sync_conflicts
            WHERE resolved = FALSE
            ORDER BY created_at DESC
            LIMIT 10
            '''
            
            df_conflicts = pd.read_sql(conflicts_query, conn)
            
            # 获取最近的同步历史
            recent_syncs_query = '''
            SELECT sync_id, source_system, total_records, 
                   new_records, updated_records, conflicts, errors,
                   status, completed_at
            FROM sync_history
            ORDER BY completed_at DESC
            LIMIT 5
            '''
            
            df_recent = pd.read_sql(recent_syncs_query, conn)
            
            return {
                'source_statistics': df_sources.to_dict('records'),
                'unresolved_conflicts': df_conflicts.to_dict('records'),
                'recent_syncs': df_recent.to_dict('records'),
                'total_records': df_sources['total_records'].sum() if not df_sources.empty else 0,
                'total_conflicts': len(df_conflicts),
                'sync_config': self.sync_config,
                'report_timestamp': datetime.now().isoformat()
            }
            
        finally:
            conn.close()
    
    def get_conflicts_for_review(self) -> List[Dict[str, Any]]:
        """获取需要人工审核的冲突"""
        
        conn = sqlite3.connect(self.sync_db_path)
        
        try:
            query = '''
            SELECT conflict_id, material_code, conflict_type, 
                   conflicting_sources, conflict_data, created_at
            FROM sync_conflicts
            WHERE resolved = FALSE
            ORDER BY created_at DESC
            '''
            
            df = pd.read_sql(query, conn)
            conflicts_list = []
            
            for _, row in df.iterrows():
                conflict_data = json.loads(row['conflict_data'])
                
                conflicts_list.append({
                    'conflict_id': row['conflict_id'],
                    'material_code': row['material_code'],
                    'conflict_type': row['conflict_type'],
                    'conflicting_sources': json.loads(row['conflicting_sources']),
                    'local_record': conflict_data.get('local_record'),
                    'remote_records': conflict_data.get('remote_records'),
                    'created_at': row['created_at']
                })
            
            return conflicts_list
            
        finally:
            conn.close()

# 使用示例
def sync_example():
    """增量同步系统使用示例"""
    
    # 初始化同步系统
    sync_system = SimplifiedIncrementalSync()
    
    # 模拟ERP数据
    erp_data = [
        {
            'material_code': 'ERP_M001',
            'material_name': '不锈钢球阀',
            'specification': 'DN100 PN16',
            'manufacturer': '上海阀门厂',
            'unit': '个',
            'last_modified': '2024-01-15T10:30:00'
        },
        {
            'material_code': 'ERP_M002',
            'material_name': '钢制法兰',
            'specification': 'DN150 PN25',
            'manufacturer': '北京钢铁公司',
            'unit': '个',
            'last_modified': '2024-01-15T11:00:00'
        }
    ]
    
    # 执行同步
    result = sync_system.sync_from_source('ERP', erp_data)
    
    print("同步结果:")
    print(f"总记录: {result.total_records}")
    print(f"新记录: {result.new_records}")
    print(f"更新记录: {result.updated_records}")
    print(f"冲突数: {result.conflicts}")
    print(f"处理时间: {result.processing_time:.2f}秒")

if __name__ == "__main__":
    sync_example()