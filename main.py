# -*- coding: utf-8 -*-
# main.py
import logging
import pandas as pd
import os
from app.workflow_service import MaterialWorkflowService
from app import config

# 尝试导入增强配置
try:
    from enhanced_config import DATA_LOADING_CONFIGS, DATA_SAVING_CONFIGS, DATABASE_CONNECTIONS
    ENHANCED_CONFIG_AVAILABLE = True
except ImportError:
    ENHANCED_CONFIG_AVAILABLE = False
    logging.warning("增强配置不可用，使用基础配置")

logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

def run_batch_job():
    """执行批量匹配任务（文件模式，保持向后兼容）"""
    logging.info("开始执行批量匹配任务（文件模式）")
    
    # 1. 初始化服务
    service = MaterialWorkflowService()
    
    # 2. 执行批量处理
    results = service.process_batch(config.NEW_DATA_PATH)
    
    # 3. 保存结果
    if results:
        # 使用增强的保存功能
        save_config = {
            'type': 'file',
            'path': config.OUTPUT_RESULT_PATH,
            'format': 'csv',
            'encoding': 'utf-8-sig'
        }
        
        success = service.save_results(results, save_config)
        if success:
            logging.info(f"批量处理结果已保存到 {config.OUTPUT_RESULT_PATH}")
        else:
            logging.error("结果保存失败")
    else:
        logging.warning("没有处理结果")

def run_database_batch_job():
    """执行数据库批量匹配任务"""
    if not ENHANCED_CONFIG_AVAILABLE:
        logging.error("数据库功能需要增强配置，请检查enhanced_config.py")
        return
    
    logging.info("开始执行批量匹配任务（数据库模式）")
    
    try:
        # 1. 配置数据库服务
        service_config = {
            'data_source': {
                'master_data': DATA_LOADING_CONFIGS['master_data'],
                'use_database': True
            },
            'processing': {
                'use_advanced_preprocessor': True,
                'use_advanced_matcher': True,
                'batch_size': 1000
            }
        }
        
        # 2. 初始化服务
        service = MaterialWorkflowService(service_config)
        logging.info("数据库工作流服务初始化成功")
        
        # 3. 从数据库批量处理
        new_data_config = DATA_LOADING_CONFIGS['new_data']
        results = service.process_batch(new_data_config)
        
        # 4. 保存结果到数据库
        if results:
            db_save_config = DATA_SAVING_CONFIGS['database_results']
            success = service.save_results(results, db_save_config)
            
            if success:
                logging.info(f"成功处理并保存 {len(results)} 条记录到数据库")
                
                # 同时保存到文件作为备份
                file_save_config = DATA_SAVING_CONFIGS['file_results']
                service.save_results(results, file_save_config)
                logging.info("结果文件备份已创建")
            else:
                logging.error("数据库保存失败")
        else:
            logging.warning("没有处理结果")
    
    except Exception as e:
        logging.error(f"数据库批量任务执行失败: {e}")

def run_mixed_mode_job():
    """执行混合模式任务（主数据来自数据库，新数据来自文件）"""
    if not ENHANCED_CONFIG_AVAILABLE:
        logging.error("混合模式需要增强配置")
        return
    
    logging.info("开始执行混合模式匹配任务")
    
    try:
        # 1. 配置混合模式服务（主数据来自数据库）
        service_config = {
            'data_source': {
                'master_data': DATA_LOADING_CONFIGS['master_data'],  # 数据库
                'use_database': True
            },
            'processing': {
                'use_advanced_preprocessor': True,
                'use_advanced_matcher': True
            }
        }
        
        # 2. 初始化服务
        service = MaterialWorkflowService(service_config)
        
        # 3. 处理文件数据
        file_config = DATA_LOADING_CONFIGS['file_data']
        results = service.process_batch(file_config)
        
        # 4. 保存结果
        if results:
            # 保存到Excel文件
            excel_save_config = DATA_SAVING_CONFIGS['excel_results']
            success = service.save_results(results, excel_save_config)
            
            if success:
                logging.info(f"混合模式处理完成，结果已保存到Excel文件")
        
    except Exception as e:
        logging.error(f"混合模式任务执行失败: {e}")

def run_api_mode_job():
    """演示API数据源模式"""
    if not ENHANCED_CONFIG_AVAILABLE:
        logging.error("API模式需要增强配置")
        return
    
    logging.info("开始执行API数据源匹配任务")
    
    try:
        # 1. 配置API模式服务
        service_config = {
            'data_source': {
                'master_data': DATA_LOADING_CONFIGS['master_data']
            }
        }
        
        service = MaterialWorkflowService(service_config)
        
        # 2. 从API获取数据并处理
        api_config = DATA_LOADING_CONFIGS['api_data']
        results = service.process_batch(api_config)
        
        # 3. 保存结果
        if results:
            save_config = DATA_SAVING_CONFIGS['file_results']
            service.save_results(results, save_config)
            logging.info("API数据处理完成")
            
    except Exception as e:
        logging.error(f"API模式任务执行失败: {e}")

def check_environment():
    """检查运行环境"""
    logging.info("检查运行环境...")
    
    # 检查数据文件
    if os.path.exists(config.MASTER_DATA_PATH):
        logging.info(f"✓ 主数据文件存在: {config.MASTER_DATA_PATH}")
    else:
        logging.warning(f"⚠ 主数据文件不存在: {config.MASTER_DATA_PATH}")
    
    if os.path.exists(config.NEW_DATA_PATH):
        logging.info(f"✓ 新数据文件存在: {config.NEW_DATA_PATH}")
    else:
        logging.warning(f"⚠ 新数据文件不存在: {config.NEW_DATA_PATH}")
    
    # 检查增强功能
    if ENHANCED_CONFIG_AVAILABLE:
        logging.info("✓ 增强配置可用")
        
        # 检查数据库配置
        try:
            from app.database_connector import DatabaseConnector
            logging.info("✓ 数据库连接器可用")
        except ImportError:
            logging.warning("⚠ 数据库连接器不可用，请安装相关依赖")
        
        try:
            from app.advanced_preprocessor import AdvancedPreprocessor
            logging.info("✓ 高级预处理器可用")
        except ImportError:
            logging.warning("⚠ 高级预处理器不可用")
        
        try:
            from app.advanced_matcher import AdvancedMaterialMatcher
            logging.info("✓ 高级匹配器可用")
        except ImportError:
            logging.warning("⚠ 高级匹配器不可用")
    else:
        logging.warning("⚠ 增强配置不可用，仅支持基础功能")

def main():
    """主函数，支持多种运行模式"""
    import sys
    
    # 检查环境
    check_environment()
    
    # 根据命令行参数选择运行模式
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = 'file'  # 默认文件模式
    
    logging.info(f"选择运行模式: {mode}")
    
    try:
        if mode == 'file':
            run_batch_job()
        elif mode == 'database':
            run_database_batch_job()
        elif mode == 'mixed':
            run_mixed_mode_job()
        elif mode == 'api':
            run_api_mode_job()
        else:
            logging.error(f"不支持的运行模式: {mode}")
            print("支持的运行模式:")
            print("  file     - 文件模式（默认）")
            print("  database - 数据库模式")
            print("  mixed    - 混合模式")
            print("  api      - API数据源模式")
            print("\n使用方法: python main.py [mode]")
            
    except KeyboardInterrupt:
        logging.info("用户中断程序执行")
    except Exception as e:
        logging.error(f"程序执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()