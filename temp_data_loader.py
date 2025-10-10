# 临时修复的数据加载器
# temp_data_loader.py

import pandas as pd
from simple_db_config import load_master_data_from_sqlite

def load_master_data():
    """加载主数据，优先使用SQLite"""
    try:
        # 尝试从SQLite加载
        df = load_master_data_from_sqlite()
        if not df.empty:
            return df
            
        print("SQLite加载失败，尝试从文件加载...")
        
        # 回退到文件加载
        import config
        from app.data_loader import load_csv_data
        
        try:
            df = load_csv_data(config.MASTER_DATA_PATH)
            return df
        except Exception as e:
            print(f"文件加载也失败: {e}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"数据加载失败: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = load_master_data()
    print(f"加载结果: {len(df)} 条记录")
    if not df.empty:
        print("列名:", df.columns.tolist())
        print(df.head())