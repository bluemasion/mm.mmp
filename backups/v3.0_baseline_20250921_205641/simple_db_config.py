# SQLite数据库简单配置文件
# simple_db_config.py

import sqlite3
import pandas as pd
import os

# SQLite数据库配置
SQLITE_DB_PATH = 'mmp_database.db'

# 数据加载配置
SIMPLE_DATA_CONFIG = {
    'source_type': 'database',
    'database_type': 'sqlite',
    'database_path': SQLITE_DB_PATH,
    'table_name': 'materials'
}

def load_master_data_from_sqlite():
    """从SQLite数据库加载主数据"""
    try:
        if not os.path.exists(SQLITE_DB_PATH):
            print(f"数据库文件 {SQLITE_DB_PATH} 不存在")
            return pd.DataFrame()
            
        conn = sqlite3.connect(SQLITE_DB_PATH)
        
        # 加载物料数据
        query = """
        SELECT 
            id,
            name as "产品名称",
            specification as "产品规格", 
            manufacturer as "生产厂家",
            category as "分类",
            price as "价格",
            unit as "单位",
            description as "描述"
        FROM materials
        WHERE is_active = 1
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"成功从SQLite数据库加载 {len(df)} 条主数据记录")
        return df
        
    except Exception as e:
        print(f"从SQLite加载数据失败: {e}")
        return pd.DataFrame()

def test_sqlite_connection():
    """测试SQLite连接"""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        # 获取表信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("数据库表:", [table[0] for table in tables])
        
        # 检查materials表记录数
        cursor.execute("SELECT COUNT(*) FROM materials")
        count = cursor.fetchone()[0]
        print(f"materials表记录数: {count}")
        
        # 获取示例数据
        cursor.execute("SELECT * FROM materials LIMIT 3")
        samples = cursor.fetchall()
        print("示例数据:")
        for i, sample in enumerate(samples, 1):
            print(f"  {i}: {sample}")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"SQLite连接测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=== SQLite数据库测试 ===")
    if test_sqlite_connection():
        print("\n=== 加载主数据测试 ===")
        df = load_master_data_from_sqlite()
        if not df.empty:
            print("数据列:", df.columns.tolist())
            print("数据形状:", df.shape)
            print("前3行数据:")
            print(df.head(3))
        else:
            print("数据加载失败或为空")
    else:
        print("数据库连接失败")