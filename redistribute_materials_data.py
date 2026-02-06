#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新分配近似物料数据脚本
采用分层抽样方式，确保每个分类都有代表性数据
"""

import pandas as pd
import sqlite3
import json
import logging
from datetime import datetime
import os
import numpy as np

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def redistribute_similar_materials_data(input_file: str = '管道配件数据.csv'):
    """重新分配近似物料数据"""
    
    logger.info("开始重新分配近似物料数据...")
    
    try:
        # 1. 读取原始数据
        df = pd.read_csv(input_file, skiprows=6)
        logger.info(f"原始数据: {len(df)} 条记录")
        
        # 2. 分层抽样策略
        # 按分类分组，每个分类按比例抽取数据到数据库
        categories = df['物料分类'].value_counts()
        logger.info(f"共有 {len(categories)} 个分类")
        
        database_data = []
        test_data = []
        
        target_db_size = 2000  # 数据库目标大小
        
        for category, total_count in categories.items():
            category_data = df[df['物料分类'] == category].copy()
            
            # 计算该分类应该分配给数据库的数量
            # 至少1条，最多不超过总数的30%
            db_count = max(1, min(int(total_count * 0.3), int(target_db_size * total_count / len(df))))
            
            # 如果是重要分类（如疏水器），确保更多数据在数据库中
            if category in ['疏水器', '带颈对焊法兰', '金属软管', '过滤器']:
                db_count = max(db_count, min(total_count, int(total_count * 0.5)))
            
            # 随机抽样
            if db_count >= total_count:
                # 全部放入数据库
                db_samples = category_data
                test_samples = pd.DataFrame()
            else:
                db_samples = category_data.sample(n=db_count, random_state=42)
                test_samples = category_data.drop(db_samples.index)
            
            database_data.append(db_samples)
            test_data.append(test_samples)
            
            logger.info(f"{category}: 总数{total_count}, 数据库{len(db_samples)}, 测试{len(test_samples)}")
        
        # 3. 合并数据
        db_df = pd.concat(database_data, ignore_index=True)
        test_df = pd.concat(test_data, ignore_index=True)
        
        # 4. 如果数据库数据超过目标大小，随机减少
        if len(db_df) > target_db_size:
            db_df = db_df.sample(n=target_db_size, random_state=42)
            logger.info(f"数据库数据调整为 {len(db_df)} 条")
        
        # 5. 导入数据库
        import_to_database(db_df)
        
        # 6. 保存测试数据
        test_df.to_csv('test_materials_data_balanced.csv', index=False, encoding='utf-8-sig')
        logger.info(f"测试数据已保存: {len(test_df)} 条记录")
        
        # 7. 验证结果
        verify_redistribution()
        
        logger.info("重新分配完成！")
        
    except Exception as e:
        logger.error(f"重新分配失败: {e}")
        raise

def import_to_database(df: pd.DataFrame):
    """导入数据到数据库"""
    try:
        conn = sqlite3.connect('business_data.db')
        cursor = conn.cursor()
        
        # 清空现有数据
        cursor.execute('DELETE FROM similar_materials')
        
        success_count = 0
        for index, row in df.iterrows():
            try:
                cursor.execute('''
                    INSERT INTO similar_materials
                    (material_code, material_name, material_long_desc, 
                     material_category, specification, model, unit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(row['物料编码']).strip(),
                    str(row['物料名称']).strip(), 
                    str(row['物料长描述']).strip(),
                    str(row['物料分类']).strip(),
                    str(row.get('规格', '')).strip(),
                    str(row.get('型号', '')).strip(),
                    str(row.get('主计量单位', '')).strip()
                ))
                success_count += 1
            except Exception as e:
                logger.error(f"导入第{index}行失败: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"数据库导入完成: {success_count} 条记录")
        
    except Exception as e:
        logger.error(f"数据库导入失败: {e}")
        raise

def verify_redistribution():
    """验证重新分配结果"""
    try:
        # 验证数据库
        conn = sqlite3.connect('business_data.db')
        
        # 数据库分类统计
        db_stats = pd.read_sql_query('''
            SELECT material_category, COUNT(*) as count 
            FROM similar_materials 
            GROUP BY material_category 
            ORDER BY count DESC
        ''', conn)
        
        print("\n=== 数据库分类分布 ===")
        for _, row in db_stats.iterrows():
            print(f"{row['material_category']}: {row['count']} 条")
        
        # 检查重要分类
        important_categories = ['疏水器', '带颈对焊法兰', '金属软管', '过滤器']
        print("\n=== 重要分类检查 ===")
        for category in important_categories:
            count = pd.read_sql_query(f'''
                SELECT COUNT(*) as count FROM similar_materials 
                WHERE material_category = '{category}'
            ''', conn)['count'][0]
            print(f"{category}: {count} 条")
        
        conn.close()
        
        # 验证测试文件
        if os.path.exists('test_materials_data_balanced.csv'):
            test_df = pd.read_csv('test_materials_data_balanced.csv')
            test_stats = test_df['物料分类'].value_counts()
            
            print(f"\n=== 测试数据总量: {len(test_df)} 条 ===")
            print("前10个分类:")
            for category, count in test_stats.head(10).items():
                print(f"{category}: {count} 条")
        
    except Exception as e:
        logger.error(f"验证失败: {e}")

if __name__ == '__main__':
    redistribute_similar_materials_data()