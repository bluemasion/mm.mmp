#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料分类数据导入脚本
从CSV文件导入物料分类数据到数据库
"""
import os
import sqlite3
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MaterialCategoryImporter:
    """物料分类导入器"""
    
    def __init__(self, db_path: str = 'master_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除旧表（如果需要重新导入）
            cursor.execute('DROP TABLE IF EXISTS material_categories_new')
            
            # 创建新的物料分类表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS material_categories_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_code TEXT UNIQUE NOT NULL,          -- 物料分类编码
                    category_name TEXT NOT NULL,                 -- 物料分类名称  
                    material_template TEXT,                      -- 物料模板
                    parent_code TEXT,                           -- 上级分类编码
                    parent_name TEXT,                           -- 上级分类名称
                    level INTEGER NOT NULL DEFAULT 1,           -- 层级（1,2,3）
                    description TEXT,                           -- 物料分类说明
                    remarks TEXT,                               -- 备注
                    is_leaf BOOLEAN DEFAULT 0,                  -- 是否叶子节点
                    sort_order INTEGER DEFAULT 0,               -- 排序
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category_code ON material_categories_new(category_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_parent_code ON material_categories_new(parent_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_level ON material_categories_new(level)')
            
            conn.commit()
            conn.close()
            logger.info("数据库表结构初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def parse_category_level(self, category_code: str) -> int:
        """
        根据编码规则解析分类层级
        
        规则分析:
        - A3, A4, A5, A6, A7, AA, AB, AJ, AK, AL, AM, AN, AP, AQ, AR, AS, AT, AU (1级)
        - A301, A401, AA01, AB01 等 (2级) 
        - A30101, A40101, AA0101, AB0101 等 (3级)
        """
        if not category_code:
            return 1
            
        # 去除空格
        code = category_code.strip()
        
        # 第1级: A + 字母 或 A + 数字 (长度2-3)
        if len(code) <= 3 and (code.startswith('A') and len(code) >= 2):
            return 1
        
        # 第2级: 第1级 + 2位数字 (长度4-5) 
        if len(code) <= 5 and code[2:].isdigit():
            return 2
            
        # 第3级: 第2级 + 2位数字 (长度6+)
        if len(code) >= 6:
            return 3
            
        return 1
    
    def get_parent_code(self, category_code: str, level: int) -> Optional[str]:
        """获取父级编码"""
        if level <= 1:
            return None
            
        if level == 2:
            # 2级分类的父级是1级，去掉后面的数字
            if len(category_code) >= 4:
                return category_code[:len(category_code)-2]
        elif level == 3:
            # 3级分类的父级是2级，去掉后面2位数字
            if len(category_code) >= 6:
                return category_code[:-2]
                
        return None
    
    def import_from_csv(self, csv_file_path: str) -> Dict[str, Any]:
        """从CSV文件导入数据"""
        try:
            logger.info(f"开始从CSV文件导入数据: {csv_file_path}")
            
            # 读取CSV文件
            df = pd.read_csv(csv_file_path, encoding='utf-8')
            logger.info(f"CSV文件读取成功，共{len(df)}条记录")
            
            # 清理列名（去除空格）
            df.columns = df.columns.str.strip()
            logger.info(f"CSV列名: {list(df.columns)}")
            
            # 清理数据
            df = df.fillna('')
            
            # 检查必要的列
            required_columns = ['物料分类编码', '物料分类名称']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"CSV文件缺少必要列: {col}")
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    category_code = str(row['物料分类编码']).strip()
                    category_name = str(row['物料分类名称']).strip()
                    
                    if not category_code or not category_name:
                        logger.warning(f"第{index+2}行数据不完整，跳过")
                        error_count += 1
                        continue
                    
                    # 解析层级
                    level = self.parse_category_level(category_code)
                    
                    # 获取父级编码
                    parent_code = self.get_parent_code(category_code, level)
                    
                    # 准备数据
                    data = {
                        'category_code': category_code,
                        'category_name': category_name,
                        'material_template': str(row.get('物料模板', '')).strip(),
                        'parent_code': parent_code,
                        'parent_name': str(row.get('上级分类名称', '')).strip(),
                        'level': level,
                        'description': str(row.get('物料分类说明', '')).strip(),
                        'remarks': str(row.get('备注', '')).strip(),
                        'sort_order': index
                    }
                    
                    # 插入数据
                    cursor.execute('''
                        INSERT OR REPLACE INTO material_categories_new 
                        (category_code, category_name, material_template, parent_code, 
                         parent_name, level, description, remarks, sort_order)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data['category_code'], data['category_name'], data['material_template'],
                        data['parent_code'], data['parent_name'], data['level'],
                        data['description'], data['remarks'], data['sort_order']
                    ))
                    
                    success_count += 1
                    
                    if success_count % 50 == 0:
                        logger.info(f"已导入 {success_count} 条记录...")
                
                except Exception as e:
                    logger.error(f"第{index+2}行数据导入失败: {e}")
                    error_count += 1
            
            # 更新叶子节点标识
            self._update_leaf_nodes(cursor)
            
            conn.commit()
            conn.close()
            
            logger.info(f"数据导入完成: 成功{success_count}条, 失败{error_count}条")
            
            return {
                'success': True,
                'total': len(df),
                'success_count': success_count,
                'error_count': error_count,
                'message': f'成功导入{success_count}条记录'
            }
            
        except Exception as e:
            logger.error(f"数据导入失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'导入失败: {e}'
            }
    
    def _update_leaf_nodes(self, cursor):
        """更新叶子节点标识"""
        try:
            # 查找所有没有子节点的分类，标记为叶子节点
            cursor.execute('''
                UPDATE material_categories_new 
                SET is_leaf = 1 
                WHERE category_code NOT IN (
                    SELECT DISTINCT parent_code 
                    FROM material_categories_new 
                    WHERE parent_code IS NOT NULL AND parent_code != ''
                )
            ''')
            
            # 有子节点的不是叶子节点
            cursor.execute('''
                UPDATE material_categories_new 
                SET is_leaf = 0 
                WHERE category_code IN (
                    SELECT DISTINCT parent_code 
                    FROM material_categories_new 
                    WHERE parent_code IS NOT NULL AND parent_code != ''
                )
            ''')
            
            logger.info("叶子节点标识更新完成")
            
        except Exception as e:
            logger.error(f"更新叶子节点失败: {e}")
    
    def migrate_to_main_table(self):
        """迁移到主表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 备份原表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS material_categories_backup AS 
                SELECT * FROM material_categories WHERE 1=0
            ''')
            
            cursor.execute('''
                INSERT INTO material_categories_backup 
                SELECT * FROM material_categories
            ''')
            
            # 删除原表
            cursor.execute('DROP TABLE IF EXISTS material_categories')
            
            # 重命名新表
            cursor.execute('ALTER TABLE material_categories_new RENAME TO material_categories')
            
            conn.commit()
            conn.close()
            
            logger.info("数据迁移到主表完成")
            
        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取导入统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 总数统计
            cursor.execute('SELECT COUNT(*) FROM material_categories_new')
            total_count = cursor.fetchone()[0]
            
            # 按层级统计
            cursor.execute('''
                SELECT level, COUNT(*) as count 
                FROM material_categories_new 
                GROUP BY level 
                ORDER BY level
            ''')
            level_stats = dict(cursor.fetchall())
            
            # 叶子节点统计
            cursor.execute('SELECT COUNT(*) FROM material_categories_new WHERE is_leaf = 1')
            leaf_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_count': total_count,
                'level_stats': level_stats,
                'leaf_count': leaf_count
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

def main():
    """主函数"""
    # CSV文件路径
    csv_file = '/Users/mason/Desktop/code /物料分类.csv'
    
    if not os.path.exists(csv_file):
        logger.error(f"CSV文件不存在: {csv_file}")
        return
    
    try:
        # 创建导入器
        importer = MaterialCategoryImporter()
        
        # 导入数据
        result = importer.import_from_csv(csv_file)
        
        if result['success']:
            # 获取统计信息
            stats = importer.get_statistics()
            logger.info(f"导入统计: {stats}")
            
            # 迁移到主表
            importer.migrate_to_main_table()
            
            print(f"""
🎉 物料分类数据导入成功！

📊 导入统计:
- 总记录数: {result['success_count']}
- 失败记录数: {result['error_count']}
- 1级分类: {stats.get('level_stats', {}).get(1, 0)} 个
- 2级分类: {stats.get('level_stats', {}).get(2, 0)} 个  
- 3级分类: {stats.get('level_stats', {}).get(3, 0)} 个
- 叶子节点: {stats.get('leaf_count', 0)} 个

✅ 数据已成功导入到 master_data.db 数据库
            """)
        else:
            logger.error(f"导入失败: {result['message']}")
            
    except Exception as e:
        logger.error(f"执行失败: {e}")

if __name__ == '__main__':
    main()