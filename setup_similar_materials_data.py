#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置近似物料数据脚本
从管道配件数据中分出2000条作为近似匹配基础数据，剩余数据保存为测试文件
"""

import pandas as pd
import sqlite3
import json
import logging
from datetime import datetime
import os

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimilarMaterialsDataManager:
    """近似物料数据管理器"""
    
    def __init__(self, db_path: str = 'business_data.db'):
        """初始化"""
        self.db_path = db_path
        self.similar_materials_table = 'similar_materials'
        
    def init_similar_materials_table(self):
        """初始化近似物料数据表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建近似物料数据表
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.similar_materials_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material_code TEXT NOT NULL,
                    material_name TEXT NOT NULL,
                    material_long_desc TEXT,
                    material_category TEXT,
                    specification TEXT,
                    model TEXT,
                    unit TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(material_code)
                )
            ''')
            
            # 创建索引
            cursor.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_similar_material_name 
                ON {self.similar_materials_table}(material_name)
            ''')
            
            cursor.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_similar_material_category 
                ON {self.similar_materials_table}(material_category)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"初始化表 {self.similar_materials_table} 成功")
            
        except Exception as e:
            logger.error(f"初始化表失败: {e}")
            raise
    
    def import_similar_materials(self, df: pd.DataFrame, limit: int = 2000):
        """导入近似物料数据"""
        try:
            # 清空现有数据
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM {self.similar_materials_table}')
            
            # 取前limit条数据
            data_to_import = df.head(limit)
            
            success_count = 0
            error_count = 0
            
            for index, row in data_to_import.iterrows():
                try:
                    material_code = str(row['物料编码']).strip()
                    material_name = str(row['物料名称']).strip() 
                    material_long_desc = str(row['物料长描述']).strip()
                    material_category = str(row['物料分类']).strip()
                    specification = str(row.get('规格', '')).strip()
                    model = str(row.get('型号', '')).strip()
                    unit = str(row.get('主计量单位', '')).strip()
                    
                    # 插入数据
                    cursor.execute(f'''
                        INSERT OR REPLACE INTO {self.similar_materials_table}
                        (material_code, material_name, material_long_desc, 
                         material_category, specification, model, unit)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        material_code, material_name, material_long_desc,
                        material_category, specification, model, unit
                    ))
                    
                    success_count += 1
                    
                    if success_count % 100 == 0:
                        logger.info(f"已导入 {success_count} 条近似物料数据...")
                        
                except Exception as e:
                    logger.error(f"第{index+1}行数据导入失败: {e}")
                    error_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"近似物料数据导入完成: 成功{success_count}条, 失败{error_count}条")
            
            return {
                'success': True,
                'total': len(data_to_import),
                'success_count': success_count,
                'error_count': error_count
            }
            
        except Exception as e:
            logger.error(f"导入近似物料数据失败: {e}")
            raise
    
    def export_remaining_data(self, df: pd.DataFrame, skip_count: int = 2000, 
                             output_file: str = 'test_materials_data.csv'):
        """导出剩余数据为测试文件"""
        try:
            # 跳过前skip_count条数据，保存剩余数据
            remaining_data = df.iloc[skip_count:].copy()
            
            # 保存为CSV文件
            remaining_data.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"剩余数据已保存到 {output_file}: {len(remaining_data)} 条记录")
            
            return {
                'success': True,
                'output_file': output_file,
                'record_count': len(remaining_data)
            }
            
        except Exception as e:
            logger.error(f"导出剩余数据失败: {e}")
            raise
    
    def get_similar_materials_count(self):
        """获取近似物料数据数量"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f'SELECT COUNT(*) FROM {self.similar_materials_table}')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"获取近似物料数据数量失败: {e}")
            return 0
    
    def search_similar_materials(self, keyword: str = None, category: str = None, limit: int = 10):
        """搜索近似物料数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = f'SELECT * FROM {self.similar_materials_table} WHERE 1=1'
            params = []
            
            if keyword:
                query += ' AND (material_name LIKE ? OR material_long_desc LIKE ?)'
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            
            if category:
                query += ' AND material_category = ?'
                params.append(category)
            
            query += f' LIMIT {limit}'
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"搜索近似物料数据失败: {e}")
            return []

def main():
    """主函数"""
    logger.info("开始设置近似物料数据...")
    
    # 1. 读取原始数据
    input_file = '管道配件数据.csv'
    if not os.path.exists(input_file):
        logger.error(f"输入文件不存在: {input_file}")
        return
    
    try:
        # 跳过前6行header，读取数据
        df = pd.read_csv(input_file, skiprows=6)
        logger.info(f"成功读取数据文件: {len(df)} 条记录")
        
        # 2. 初始化数据管理器
        manager = SimilarMaterialsDataManager()
        
        # 3. 初始化数据库表
        manager.init_similar_materials_table()
        
        # 4. 导入前2000条数据到数据库
        import_result = manager.import_similar_materials(df, limit=2000)
        logger.info(f"数据库导入结果: {import_result}")
        
        # 5. 导出剩余数据为CSV文件
        export_result = manager.export_remaining_data(df, skip_count=2000)
        logger.info(f"CSV导出结果: {export_result}")
        
        # 6. 验证结果
        db_count = manager.get_similar_materials_count()
        logger.info(f"数据库中近似物料数据量: {db_count}")
        
        # 7. 测试搜索功能
        test_results = manager.search_similar_materials(keyword='疏水器', limit=3)
        logger.info(f"测试搜索结果 (疏水器): {len(test_results)} 条")
        for result in test_results:
            logger.info(f"  - {result['material_code']}: {result['material_name']}")
        
        logger.info("近似物料数据设置完成！")
        
    except Exception as e:
        logger.error(f"设置近似物料数据失败: {e}")
        raise

if __name__ == '__main__':
    main()