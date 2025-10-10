# app/data_loader.py
import pandas as pd
import logging
from typing import Dict, Any, Optional, Union
import os

# 尝试导入数据库连接器
try:
    from app.database_connector import DatabaseConnector, DatabaseDataLoader
    DATABASE_SUPPORT = True
except ImportError:
    DATABASE_SUPPORT = False
    logging.warning("数据库连接器不可用，仅支持文件数据源")

def load_csv_data(file_path):
    """从CSV文件加载数据（保持向后兼容）"""
    try:
        df = pd.read_csv(file_path)
        logging.info(f"成功从 {file_path} 加载了 {len(df)} 条数据。")
        return df
    except FileNotFoundError:
        logging.error(f"错误：找不到文件 {file_path}。")
        return pd.DataFrame()

def load_data_from_config(data_config: Dict[str, Any]) -> pd.DataFrame:
    """
    根据配置加载数据，支持多种数据源
    
    Args:
        data_config: 数据配置字典
        
    Returns:
        加载的DataFrame
    """
    source_type = data_config.get('source_type', 'file').lower()
    
    if source_type == 'file':
        return load_file_data(data_config)
    elif source_type == 'database':
        return load_database_data(data_config)
    elif source_type == 'api':
        return load_api_data(data_config)
    else:
        raise ValueError(f"不支持的数据源类型: {source_type}")

def load_file_data(file_config: Dict[str, Any]) -> pd.DataFrame:
    """
    从文件加载数据
    
    Args:
        file_config: 文件配置
        
    Returns:
        DataFrame
    """
    file_path = file_config.get('path')
    if not file_path:
        raise ValueError("文件配置缺少path参数")
    
    if not os.path.exists(file_path):
        logging.error(f"文件不存在: {file_path}")
        return pd.DataFrame()
    
    file_type = file_config.get('type', '').lower()
    encoding = file_config.get('encoding', 'utf-8')
    
    try:
        if file_type == 'csv' or file_path.endswith('.csv'):
            separator = file_config.get('separator', ',')
            df = pd.read_csv(file_path, encoding=encoding, sep=separator)
            
        elif file_type == 'excel' or file_path.endswith(('.xlsx', '.xls')):
            sheet_name = file_config.get('sheet_name', 0)
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
        elif file_type == 'json' or file_path.endswith('.json'):
            df = pd.read_json(file_path, encoding=encoding)
            
        elif file_type == 'parquet' or file_path.endswith('.parquet'):
            df = pd.read_parquet(file_path)
            
        else:
            # 默认尝试CSV格式
            df = pd.read_csv(file_path, encoding=encoding)
        
        # 应用数据过滤
        df = apply_data_filters(df, file_config.get('filters', {}))
        
        logging.info(f"成功从文件 {file_path} 加载了 {len(df)} 条数据")
        return df
        
    except Exception as e:
        logging.error(f"文件加载失败 {file_path}: {e}")
        return pd.DataFrame()

def load_database_data(db_config: Dict[str, Any]) -> pd.DataFrame:
    """
    从数据库加载数据
    
    Args:
        db_config: 数据库配置
        
    Returns:
        DataFrame
    """
    if not DATABASE_SUPPORT:
        raise ImportError("数据库功能不可用，请安装相关依赖包")
    
    connection_config = db_config.get('connection', {})
    query_config = db_config.get('query', {})
    
    if not connection_config:
        raise ValueError("数据库配置缺少connection参数")
    
    try:
        loader = DatabaseDataLoader(connection_config)
        df = loader.load_master_data(query_config)
        
        # 应用数据过滤
        df = apply_data_filters(df, db_config.get('filters', {}))
        
        logging.info(f"成功从数据库加载了 {len(df)} 条数据")
        return df
        
    except Exception as e:
        logging.error(f"数据库加载失败: {e}")
        return pd.DataFrame()

def load_api_data(api_config: Dict[str, Any]) -> pd.DataFrame:
    """
    从API加载数据
    
    Args:
        api_config: API配置
        
    Returns:
        DataFrame
    """
    try:
        import requests
        
        url = api_config.get('url')
        method = api_config.get('method', 'GET').upper()
        headers = api_config.get('headers', {})
        params = api_config.get('params', {})
        data = api_config.get('data', {})
        timeout = api_config.get('timeout', 30)
        
        if not url:
            raise ValueError("API配置缺少url参数")
        
        # 发送HTTP请求
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        response.raise_for_status()
        
        # 解析响应数据
        response_data = response.json()
        
        # 提取数据部分
        data_key = api_config.get('data_key', 'data')
        if data_key and data_key in response_data:
            records = response_data[data_key]
        else:
            records = response_data
        
        # 转换为DataFrame
        if isinstance(records, list):
            df = pd.DataFrame(records)
        else:
            df = pd.DataFrame([records])
        
        # 应用数据过滤
        df = apply_data_filters(df, api_config.get('filters', {}))
        
        logging.info(f"成功从API {url} 加载了 {len(df)} 条数据")
        return df
        
    except ImportError:
        logging.error("需要安装requests库才能使用API数据源")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"API数据加载失败: {e}")
        return pd.DataFrame()

def apply_data_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    应用数据过滤器
    
    Args:
        df: 原始DataFrame
        filters: 过滤器配置
        
    Returns:
        过滤后的DataFrame
    """
    if df.empty or not filters:
        return df
    
    filtered_df = df.copy()
    
    try:
        # 列选择
        if 'columns' in filters:
            columns = filters['columns']
            available_columns = [col for col in columns if col in filtered_df.columns]
            if available_columns:
                filtered_df = filtered_df[available_columns]
                logging.info(f"选择了 {len(available_columns)} 列")
        
        # 行过滤
        if 'conditions' in filters:
            conditions = filters['conditions']
            for condition in conditions:
                column = condition.get('column')
                operator = condition.get('operator', '==')
                value = condition.get('value')
                
                if column in filtered_df.columns:
                    if operator == '==':
                        filtered_df = filtered_df[filtered_df[column] == value]
                    elif operator == '!=':
                        filtered_df = filtered_df[filtered_df[column] != value]
                    elif operator == '>':
                        filtered_df = filtered_df[filtered_df[column] > value]
                    elif operator == '<':
                        filtered_df = filtered_df[filtered_df[column] < value]
                    elif operator == '>=':
                        filtered_df = filtered_df[filtered_df[column] >= value]
                    elif operator == '<=':
                        filtered_df = filtered_df[filtered_df[column] <= value]
                    elif operator == 'in':
                        filtered_df = filtered_df[filtered_df[column].isin(value)]
                    elif operator == 'not_in':
                        filtered_df = filtered_df[~filtered_df[column].isin(value)]
                    elif operator == 'contains':
                        filtered_df = filtered_df[filtered_df[column].str.contains(str(value), na=False)]
        
        # 去重
        if filters.get('drop_duplicates', False):
            subset = filters.get('duplicate_subset')
            filtered_df = filtered_df.drop_duplicates(subset=subset)
            logging.info("已去除重复行")
        
        # 排序
        if 'sort_by' in filters:
            sort_config = filters['sort_by']
            if isinstance(sort_config, str):
                filtered_df = filtered_df.sort_values(sort_config)
            elif isinstance(sort_config, dict):
                column = sort_config.get('column')
                ascending = sort_config.get('ascending', True)
                filtered_df = filtered_df.sort_values(column, ascending=ascending)
        
        # 限制行数
        if 'limit' in filters:
            limit = filters['limit']
            filtered_df = filtered_df.head(limit)
            logging.info(f"限制结果为 {limit} 行")
        
        logging.info(f"过滤后剩余 {len(filtered_df)} 条数据")
        return filtered_df
        
    except Exception as e:
        logging.error(f"数据过滤失败: {e}")
        return df

def save_data_to_config(df: pd.DataFrame, save_config: Dict[str, Any]) -> bool:
    """
    根据配置保存数据
    
    Args:
        df: 要保存的DataFrame
        save_config: 保存配置
        
    Returns:
        是否保存成功
    """
    if df.empty:
        logging.warning("DataFrame为空，跳过保存")
        return False
    
    save_type = save_config.get('type', 'file').lower()
    
    try:
        if save_type == 'file':
            return save_to_file(df, save_config)
        elif save_type == 'database':
            return save_to_database(df, save_config)
        else:
            raise ValueError(f"不支持的保存类型: {save_type}")
            
    except Exception as e:
        logging.error(f"数据保存失败: {e}")
        return False

def save_to_file(df: pd.DataFrame, file_config: Dict[str, Any]) -> bool:
    """保存到文件"""
    file_path = file_config.get('path')
    file_format = file_config.get('format', 'csv').lower()
    
    if not file_path:
        raise ValueError("文件保存配置缺少path参数")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    if file_format == 'csv':
        encoding = file_config.get('encoding', 'utf-8-sig')
        separator = file_config.get('separator', ',')
        df.to_csv(file_path, index=False, encoding=encoding, sep=separator)
    elif file_format == 'excel':
        sheet_name = file_config.get('sheet_name', 'Sheet1')
        df.to_excel(file_path, index=False, sheet_name=sheet_name)
    elif file_format == 'json':
        df.to_json(file_path, orient='records', force_ascii=False, indent=2)
    elif file_format == 'parquet':
        df.to_parquet(file_path, index=False)
    else:
        raise ValueError(f"不支持的文件格式: {file_format}")
    
    logging.info(f"成功保存 {len(df)} 条数据到文件 {file_path}")
    return True

def save_to_database(df: pd.DataFrame, db_config: Dict[str, Any]) -> bool:
    """保存到数据库"""
    if not DATABASE_SUPPORT:
        raise ImportError("数据库功能不可用，请安装相关依赖包")
    
    connection_config = db_config.get('connection', {})
    save_config = db_config.get('save', {})
    
    loader = DatabaseDataLoader(connection_config)
    return loader.save_results(df, save_config)