# database_example.py
"""
数据库对接功能使用示例
演示如何配置和使用MMP系统的数据库功能
"""

import logging
from app.workflow_service import MaterialWorkflowService
from app.database_connector import DatabaseConnector
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO)

def example_mysql_config():
    """MySQL数据库配置示例"""
    return {
        'type': 'mysql',
        'host': 'localhost',
        'port': 3306,
        'database': 'material_system',
        'username': 'material_user',
        'password': 'your_password',
        'driver': 'pymysql',
        'params': {
            'charset': 'utf8mb4',
            'autocommit': True
        },
        'pool_size': 10,
        'max_overflow': 20,
        'echo': False
    }

def example_postgresql_config():
    """PostgreSQL数据库配置示例"""
    return {
        'type': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'database': 'material_system',
        'username': 'material_user',
        'password': 'your_password',
        'driver': 'psycopg2',
        'params': {
            'sslmode': 'prefer'
        }
    }

def example_mongodb_config():
    """MongoDB数据库配置示例"""
    return {
        'type': 'mongodb',
        'host': 'localhost',
        'port': 27017,
        'database': 'material_system',
        'username': 'material_user',
        'password': 'your_password'
    }

def demo_database_connection():
    """演示数据库连接功能"""
    print("=== 数据库连接演示 ===")
    
    # 使用MySQL配置
    mysql_config = example_mysql_config()
    
    try:
        with DatabaseConnector(mysql_config) as db:
            print("✓ 数据库连接成功")
            
            # 测试连接
            if db.test_connection():
                print("✓ 连接测试通过")
            
            # 获取表信息
            try:
                table_info = db.get_table_info('materials')
                print(f"✓ 表结构信息: {len(table_info['columns'])} 个字段")
            except Exception as e:
                print(f"⚠ 获取表信息失败: {e}")
            
            # 执行简单查询
            try:
                df = db.execute_query("SELECT COUNT(*) as total FROM materials")
                print(f"✓ 查询成功，材料总数: {df.iloc[0]['total']}")
            except Exception as e:
                print(f"⚠ 查询失败: {e}")
                
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")

def demo_workflow_with_database():
    """演示工作流服务使用数据库"""
    print("\n=== 工作流数据库集成演示 ===")
    
    # 配置数据库数据源
    service_config = {
        'data_source': {
            'master_data': {
                'source_type': 'database',
                'connection': example_mysql_config(),
                'query': {
                    'type': 'table',
                    'table_name': 'material_master',
                    'conditions': {
                        'status': 'active'
                    }
                },
                'filters': {
                    'columns': ['id', 'product_name', 'specification', 'manufacturer', 'medical_code'],
                    'drop_duplicates': True,
                    'limit': 1000
                }
            }
        },
        'match_rules': {
            'master_fields': {
                'id': 'id',
                'exact': ['manufacturer', 'medical_code'],
                'fuzzy': ['product_name', 'specification']
            },
            'new_item_fields': {
                'id': 'asset_code',
                'exact': ['manufacturer_name', 'medical_insurance_code'],
                'fuzzy': ['asset_name', 'spec_model']
            }
        }
    }
    
    try:
        # 初始化工作流服务
        service = MaterialWorkflowService(service_config)
        print("✓ 工作流服务初始化成功")
        
        # 获取服务统计
        stats = service.get_service_stats()
        print(f"✓ 主数据加载: {stats['master_data_count']} 条记录")
        
        # 处理单条数据
        test_item = {
            'asset_name': '阿莫西林胶囊',
            'spec_model': '0.25g*24粒',
            'manufacturer_name': '华北制药',
            'medical_insurance_code': 'A001'
        }
        
        result = service.process_single_item(test_item)
        print(f"✓ 单条处理完成，找到 {len(result['matches'])} 个匹配")
        
    except Exception as e:
        print(f"✗ 工作流演示失败: {e}")

def demo_batch_processing_from_database():
    """演示从数据库批量处理"""
    print("\n=== 数据库批量处理演示 ===")
    
    # 批量处理配置
    batch_config = {
        'connection': example_mysql_config(),
        'query': {
            'type': 'custom_query',
            'query': """
                SELECT 
                    asset_code,
                    asset_name,
                    spec_model,
                    manufacturer_name,
                    medical_insurance_code
                FROM pending_materials 
                WHERE status = 'pending' 
                AND created_at >= '2024-01-01'
                ORDER BY created_at DESC
                LIMIT 100
            """
        }
    }
    
    service_config = {
        'data_source': {
            'master_data': {
                'source_type': 'database',
                'connection': example_mysql_config(),
                'query': {
                    'type': 'table',
                    'table_name': 'material_master'
                }
            }
        }
    }
    
    try:
        service = MaterialWorkflowService(service_config)
        
        # 批量处理
        results = service.process_batch_from_database(batch_config)
        print(f"✓ 批量处理完成: {len(results)} 条记录")
        
        # 保存结果到数据库
        save_config = {
            'type': 'database',
            'connection': example_mysql_config(),
            'save': {
                'table_name': 'matching_results',
                'if_exists': 'append'
            }
        }
        
        success = service.save_results(results, save_config)
        if success:
            print("✓ 结果保存到数据库成功")
        else:
            print("✗ 结果保存失败")
            
    except Exception as e:
        print(f"✗ 批量处理演示失败: {e}")

def demo_multi_database_setup():
    """演示多数据库配置"""
    print("\n=== 多数据库配置演示 ===")
    
    # 多数据库配置
    service_config = {
        'data_source': {
            'master_data': {
                'source_type': 'database',
                'connection': example_postgresql_config(),  # 主数据来自PostgreSQL
                'query': {
                    'type': 'table',
                    'table_name': 'material_master'
                }
            }
        }
    }
    
    # 新数据来源（MySQL）
    new_data_config = {
        'source_type': 'database',
        'connection': example_mysql_config(),
        'query': {
            'type': 'table',
            'table_name': 'business_materials',
            'conditions': {'status': 'pending'}
        }
    }
    
    # 结果保存（MongoDB）
    result_save_config = {
        'type': 'database',
        'connection': example_mongodb_config(),
        'save': {
            'table_name': 'matching_results'  # MongoDB中是collection
        }
    }
    
    try:
        service = MaterialWorkflowService(service_config)
        print("✓ 多数据库服务初始化成功")
        
        # 从MySQL加载新数据并处理
        results = service.process_batch(new_data_config)
        print(f"✓ 处理完成: {len(results)} 条记录")
        
        # 保存到MongoDB
        success = service.save_results(results, result_save_config)
        if success:
            print("✓ 结果保存到MongoDB成功")
            
    except Exception as e:
        print(f"✗ 多数据库演示失败: {e}")

def create_sample_tables():
    """创建示例表结构（仅用于演示）"""
    print("\n=== 示例表结构 ===")
    
    mysql_config = example_mysql_config()
    
    # 主数据表
    master_table_sql = """
    CREATE TABLE IF NOT EXISTS material_master (
        id VARCHAR(50) PRIMARY KEY,
        product_name VARCHAR(255) NOT NULL,
        specification VARCHAR(255),
        manufacturer VARCHAR(255),
        medical_code VARCHAR(100),
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_manufacturer (manufacturer),
        INDEX idx_medical_code (medical_code),
        INDEX idx_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # 待处理数据表
    pending_table_sql = """
    CREATE TABLE IF NOT EXISTS pending_materials (
        asset_code VARCHAR(50) PRIMARY KEY,
        asset_name VARCHAR(255) NOT NULL,
        spec_model VARCHAR(255),
        manufacturer_name VARCHAR(255),
        medical_insurance_code VARCHAR(100),
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_status (status),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # 匹配结果表
    results_table_sql = """
    CREATE TABLE IF NOT EXISTS matching_results (
        id INT AUTO_INCREMENT PRIMARY KEY,
        input_asset_code VARCHAR(50),
        input_asset_name VARCHAR(255),
        recommended_category VARCHAR(100),
        best_match_id VARCHAR(50),
        best_match_similarity DECIMAL(5,4),
        match_count INT DEFAULT 0,
        processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processing_status VARCHAR(20) DEFAULT 'success',
        error_message TEXT,
        INDEX idx_asset_code (input_asset_code),
        INDEX idx_similarity (best_match_similarity),
        INDEX idx_timestamp (processing_timestamp)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    print("主数据表结构:")
    print(master_table_sql)
    print("\n待处理数据表结构:")
    print(pending_table_sql)
    print("\n匹配结果表结构:")
    print(results_table_sql)

def main():
    """主函数，运行所有演示"""
    print("MMP系统数据库对接功能演示")
    print("=" * 50)
    
    # 显示表结构
    create_sample_tables()
    
    # 注释掉需要真实数据库连接的演示
    print("\n注意：以下演示需要配置真实的数据库连接")
    print("请根据实际环境修改数据库配置信息")
    
    # demo_database_connection()
    # demo_workflow_with_database()
    # demo_batch_processing_from_database()
    # demo_multi_database_setup()
    
    print("\n配置说明:")
    print("1. 安装数据库驱动: pip install pymysql psycopg2-binary pymongo")
    print("2. 配置数据库连接信息")
    print("3. 创建相应的数据表")
    print("4. 运行相应的演示函数")

if __name__ == "__main__":
    main()
