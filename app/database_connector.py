# app/database_connector.py
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager
import traceback

try:
    import sqlalchemy
    from sqlalchemy import create_engine, text, MetaData, Table
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logging.warning("SQLAlchemy未安装，数据库功能将不可用")

try:
    import pymongo
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    logging.warning("PyMongo未安装，MongoDB功能将不可用")

class DatabaseConnector:
    """统一数据库连接器，支持多种数据库类型"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据库连接器
        
        Args:
            config: 数据库配置字典
        """
        self.config = config
        self.db_type = config.get('type', '').lower()
        self.connection = None
        self.engine = None
        self.session_factory = None
        
        # 验证配置
        self._validate_config()
        
        # 初始化连接
        self._initialize_connection()

    def _validate_config(self):
        """验证数据库配置"""
        required_fields = ['type', 'host', 'database']
        
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"数据库配置缺少必需字段: {field}")
        
        if self.db_type not in ['mysql', 'postgresql', 'sqlite', 'oracle', 'mongodb']:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")

    def _initialize_connection(self):
        """初始化数据库连接"""
        try:
            if self.db_type == 'mongodb':
                self._initialize_mongodb()
            else:
                self._initialize_sql_database()
            
            logging.info(f"成功连接到 {self.db_type} 数据库: {self.config['database']}")
            
        except Exception as e:
            logging.error(f"数据库连接失败: {e}")
            raise

    def _initialize_sql_database(self):
        """初始化SQL数据库连接"""
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("需要安装SQLAlchemy才能使用SQL数据库功能")
        
        # 构建连接字符串
        connection_string = self._build_connection_string()
        
        # 创建引擎
        engine_config = {
            'echo': self.config.get('echo', False),
            'pool_size': self.config.get('pool_size', 10),
            'max_overflow': self.config.get('max_overflow', 20),
            'pool_timeout': self.config.get('pool_timeout', 30),
            'pool_recycle': self.config.get('pool_recycle', 3600)
        }
        
        self.engine = create_engine(connection_string, **engine_config)
        
        # 创建会话工厂
        self.session_factory = sessionmaker(bind=self.engine)
        
        # 测试连接
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def _initialize_mongodb(self):
        """初始化MongoDB连接"""
        if not PYMONGO_AVAILABLE:
            raise ImportError("需要安装PyMongo才能使用MongoDB功能")
        
        # 构建MongoDB连接字符串
        host = self.config['host']
        port = self.config.get('port', 27017)
        username = self.config.get('username')
        password = self.config.get('password')
        
        if username and password:
            connection_string = f"mongodb://{username}:{password}@{host}:{port}/{self.config['database']}"
        else:
            connection_string = f"mongodb://{host}:{port}"
        
        # 创建MongoDB客户端
        self.connection = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=self.config.get('timeout', 5000)
        )
        
        # 测试连接
        self.connection.admin.command('ping')

    def _build_connection_string(self) -> str:
        """构建SQL数据库连接字符串"""
        host = self.config['host']
        port = self.config.get('port')
        database = self.config['database']
        username = self.config.get('username')
        password = self.config.get('password')
        
        # 根据数据库类型设置默认端口
        if not port:
            port_mapping = {
                'mysql': 3306,
                'postgresql': 5432,
                'oracle': 1521
            }
            port = port_mapping.get(self.db_type, 5432)
        
        # 构建连接字符串
        if self.db_type == 'mysql':
            driver = self.config.get('driver', 'pymysql')
            connection_string = f"mysql+{driver}://"
        elif self.db_type == 'postgresql':
            driver = self.config.get('driver', 'psycopg2')
            connection_string = f"postgresql+{driver}://"
        elif self.db_type == 'sqlite':
            return f"sqlite:///{database}"
        elif self.db_type == 'oracle':
            driver = self.config.get('driver', 'cx_oracle')
            connection_string = f"oracle+{driver}://"
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")
        
        # 添加认证信息
        if username and password:
            connection_string += f"{username}:{password}@"
        elif username:
            connection_string += f"{username}@"
        
        # 添加主机和数据库
        if self.db_type != 'sqlite':
            connection_string += f"{host}:{port}/{database}"
        
        # 添加额外参数
        params = self.config.get('params', {})
        if params:
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            connection_string += f"?{param_string}"
        
        return connection_string

    @contextmanager
    def get_session(self):
        """获取数据库会话（上下文管理器）"""
        if self.db_type == 'mongodb':
            yield self.connection[self.config['database']]
        else:
            session = self.session_factory()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

    def execute_query(self, query: str, params: Dict = None) -> pd.DataFrame:
        """
        执行SQL查询并返回DataFrame
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果DataFrame
        """
        if self.db_type == 'mongodb':
            raise ValueError("MongoDB不支持SQL查询，请使用find_documents方法")
        
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql(query, conn, params=params or {})
                logging.info(f"查询成功，返回 {len(result)} 条记录")
                return result
                
        except Exception as e:
            logging.error(f"查询执行失败: {e}")
            raise

    def execute_query_chunked(self, query: str, chunk_size: int = 10000, 
                            params: Dict = None) -> pd.DataFrame:
        """
        分块执行大查询
        
        Args:
            query: SQL查询语句
            chunk_size: 每块大小
            params: 查询参数
            
        Returns:
            完整结果DataFrame
        """
        if self.db_type == 'mongodb':
            raise ValueError("MongoDB不支持SQL查询")
        
        try:
            chunks = []
            with self.engine.connect() as conn:
                for chunk in pd.read_sql(query, conn, params=params or {}, chunksize=chunk_size):
                    chunks.append(chunk)
                    logging.info(f"已读取 {len(chunk)} 条记录")
                
                if chunks:
                    result = pd.concat(chunks, ignore_index=True)
                    logging.info(f"分块查询完成，总计 {len(result)} 条记录")
                    return result
                else:
                    return pd.DataFrame()
                    
        except Exception as e:
            logging.error(f"分块查询失败: {e}")
            raise

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            表结构信息字典
        """
        if self.db_type == 'mongodb':
            return self._get_collection_info(table_name)
        else:
            return self._get_sql_table_info(table_name)

    def _get_sql_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取SQL表结构信息"""
        try:
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=self.engine)
            
            columns = []
            for column in table.columns:
                columns.append({
                    'name': column.name,
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'primary_key': column.primary_key,
                    'default': str(column.default) if column.default else None
                })
            
            return {
                'table_name': table_name,
                'columns': columns,
                'primary_keys': [col.name for col in table.primary_key.columns],
                'indexes': [idx.name for idx in table.indexes]
            }
            
        except Exception as e:
            logging.error(f"获取表 {table_name} 信息失败: {e}")
            raise

    def _get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """获取MongoDB集合信息"""
        try:
            with self.get_session() as db:
                collection = db[collection_name]
                
                # 获取样本文档来推断结构
                sample_doc = collection.find_one()
                
                if sample_doc:
                    fields = list(sample_doc.keys())
                else:
                    fields = []
                
                return {
                    'collection_name': collection_name,
                    'fields': fields,
                    'document_count': collection.count_documents({}),
                    'indexes': list(collection.list_indexes())
                }
                
        except Exception as e:
            logging.error(f"获取集合 {collection_name} 信息失败: {e}")
            raise

    def find_documents(self, collection_name: str, filter_dict: Dict = None, 
                      limit: int = None) -> pd.DataFrame:
        """
        MongoDB文档查询
        
        Args:
            collection_name: 集合名
            filter_dict: 过滤条件
            limit: 限制数量
            
        Returns:
            查询结果DataFrame
        """
        if self.db_type != 'mongodb':
            raise ValueError("此方法仅适用于MongoDB")
        
        try:
            with self.get_session() as db:
                collection = db[collection_name]
                cursor = collection.find(filter_dict or {})
                
                if limit:
                    cursor = cursor.limit(limit)
                
                documents = list(cursor)
                
                if documents:
                    result = pd.DataFrame(documents)
                    # 转换ObjectId为字符串
                    if '_id' in result.columns:
                        result['_id'] = result['_id'].astype(str)
                    
                    logging.info(f"MongoDB查询成功，返回 {len(result)} 条记录")
                    return result
                else:
                    return pd.DataFrame()
                    
        except Exception as e:
            logging.error(f"MongoDB查询失败: {e}")
            raise

    def insert_dataframe(self, df: pd.DataFrame, table_name: str, 
                        if_exists: str = 'append') -> int:
        """
        将DataFrame插入数据库
        
        Args:
            df: 要插入的DataFrame
            table_name: 目标表名
            if_exists: 如果表存在的处理方式 ('fail', 'replace', 'append')
            
        Returns:
            插入的记录数
        """
        if df.empty:
            logging.warning("DataFrame为空，跳过插入")
            return 0
        
        try:
            if self.db_type == 'mongodb':
                return self._insert_to_mongodb(df, table_name)
            else:
                return self._insert_to_sql(df, table_name, if_exists)
                
        except Exception as e:
            logging.error(f"数据插入失败: {e}")
            raise

    def _insert_to_sql(self, df: pd.DataFrame, table_name: str, if_exists: str) -> int:
        """插入数据到SQL数据库"""
        with self.engine.connect() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            logging.info(f"成功插入 {len(df)} 条记录到表 {table_name}")
            return len(df)

    def _insert_to_mongodb(self, df: pd.DataFrame, collection_name: str) -> int:
        """插入数据到MongoDB"""
        with self.get_session() as db:
            collection = db[collection_name]
            documents = df.to_dict('records')
            result = collection.insert_many(documents)
            logging.info(f"成功插入 {len(result.inserted_ids)} 条记录到集合 {collection_name}")
            return len(result.inserted_ids)

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            if self.db_type == 'mongodb':
                self.connection.admin.command('ping')
            else:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            
            logging.info("数据库连接测试成功")
            return True
            
        except Exception as e:
            logging.error(f"数据库连接测试失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        try:
            if self.db_type == 'mongodb' and self.connection:
                self.connection.close()
            elif self.engine:
                self.engine.dispose()
            
            logging.info("数据库连接已关闭")
            
        except Exception as e:
            logging.error(f"关闭数据库连接时出错: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class DatabaseDataLoader:
    """数据库数据加载器"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        初始化数据库数据加载器
        
        Args:
            db_config: 数据库配置
        """
        self.db_config = db_config
        self.connector = None

    def load_master_data(self, query_config: Dict[str, Any]) -> pd.DataFrame:
        """
        加载主数据
        
        Args:
            query_config: 查询配置
            
        Returns:
            主数据DataFrame
        """
        try:
            with DatabaseConnector(self.db_config) as connector:
                if query_config.get('type') == 'table':
                    # 直接从表加载
                    table_name = query_config['table_name']
                    conditions = query_config.get('conditions', {})
                    
                    if connector.db_type == 'mongodb':
                        df = connector.find_documents(table_name, conditions)
                    else:
                        # 构建SQL查询
                        query = f"SELECT * FROM {table_name}"
                        if conditions:
                            where_clauses = [f"{k} = :{k}" for k in conditions.keys()]
                            query += f" WHERE {' AND '.join(where_clauses)}"
                        
                        df = connector.execute_query(query, conditions)
                
                elif query_config.get('type') == 'custom_query':
                    # 自定义查询
                    query = query_config['query']
                    params = query_config.get('params', {})
                    df = connector.execute_query(query, params)
                
                else:
                    raise ValueError("查询配置类型无效")
                
                logging.info(f"成功加载主数据，共 {len(df)} 条记录")
                return df
                
        except Exception as e:
            logging.error(f"加载主数据失败: {e}")
            raise

    def load_new_data(self, query_config: Dict[str, Any]) -> pd.DataFrame:
        """
        加载新数据
        
        Args:
            query_config: 查询配置
            
        Returns:
            新数据DataFrame
        """
        # 与load_master_data逻辑相同，但可以有不同的配置
        return self.load_master_data(query_config)

    def save_results(self, results_df: pd.DataFrame, 
                    save_config: Dict[str, Any]) -> bool:
        """
        保存匹配结果到数据库
        
        Args:
            results_df: 结果DataFrame
            save_config: 保存配置
            
        Returns:
            是否保存成功
        """
        try:
            with DatabaseConnector(self.db_config) as connector:
                table_name = save_config['table_name']
                if_exists = save_config.get('if_exists', 'append')
                
                count = connector.insert_dataframe(results_df, table_name, if_exists)
                logging.info(f"成功保存 {count} 条结果记录")
                return True
                
        except Exception as e:
            logging.error(f"保存结果失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    # MySQL配置示例
    mysql_config = {
        'type': 'mysql',
        'host': 'localhost',
        'port': 3306,
        'database': 'material_db',
        'username': 'user',
        'password': 'password',
        'driver': 'pymysql',
        'params': {
            'charset': 'utf8mb4'
        }
    }
    
    # PostgreSQL配置示例
    postgresql_config = {
        'type': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'database': 'material_db',
        'username': 'user',
        'password': 'password'
    }
    
    # MongoDB配置示例
    mongodb_config = {
        'type': 'mongodb',
        'host': 'localhost',
        'port': 27017,
        'database': 'material_db',
        'username': 'user',
        'password': 'password'
    }
    
    # 使用示例
    try:
        with DatabaseConnector(mysql_config) as db:
            # 测试连接
            if db.test_connection():
                print("数据库连接成功")
                
                # 执行查询
                df = db.execute_query("SELECT * FROM materials LIMIT 10")
                print(f"查询结果: {len(df)} 条记录")
                
                # 获取表信息
                table_info = db.get_table_info("materials")
                print(f"表结构: {table_info}")
                
    except Exception as e:
        print(f"数据库操作失败: {e}")
        traceback.print_exc()
