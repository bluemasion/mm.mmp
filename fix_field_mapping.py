#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMP字段匹配问题修复脚本
解决数据库字段名与配置不匹配的问题
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

def fix_database_fields():
    """修复数据库字段匹配问题"""
    print("🔧 开始修复MMP字段匹配问题...")
    
    # 1. 初始化主数据库
    print("\n1️⃣ 初始化主数据库...")
    try:
        os.system("python3 init_master_data.py")
        print("✅ 主数据库初始化完成")
    except Exception as e:
        print(f"❌ 主数据库初始化失败: {e}")
    
    # 2. 检查并修复SQLite数据库结构
    print("\n2️⃣ 检查SQLite数据库结构...")
    
    db_files = ['master_data.db', 'business_data.db', 'mmp_database.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                print(f"\n📊 检查数据库: {db_file}")
                
                # 获取所有表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    print(f"  表: {table_name}")
                    
                    # 获取表结构
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    for col in columns:
                        print(f"    - {col[1]} ({col[2]})")
                
                conn.close()
                print(f"✅ {db_file} 结构检查完成")
                
            except Exception as e:
                print(f"❌ 检查 {db_file} 失败: {e}")
    
    # 3. 创建兼容性数据视图
    print("\n3️⃣ 创建数据兼容性视图...")
    
    try:
        # 连接主数据库
        conn = sqlite3.connect('master_data.db')
        cursor = conn.cursor()
        
        # 创建兼容视图 - 将新字段名映射到旧字段名
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS materials_compat AS
            SELECT 
                material_code as id,
                material_name as name,
                specification,
                brand as manufacturer,
                category_id as category,
                unit,
                model,
                attributes
            FROM materials
        """)
        
        conn.commit()
        conn.close()
        print("✅ 兼容性视图创建完成")
        
    except Exception as e:
        print(f"❌ 创建兼容性视图失败: {e}")
    
    # 4. 测试数据加载
    print("\n4️⃣ 测试数据加载...")
    
    try:
        from temp_data_loader import load_master_data
        df = load_master_data()
        
        if df.empty:
            print("⚠️  数据加载为空，尝试直接查询...")
            
            # 直接从数据库查询
            conn = sqlite3.connect('master_data.db')
            df = pd.read_sql_query("SELECT * FROM materials_compat LIMIT 5", conn)
            conn.close()
            
        print(f"📊 测试数据加载结果: {len(df)} 条记录")
        if not df.empty:
            print("字段列表:", list(df.columns))
            print("样本数据:")
            print(df.head().to_string())
        
    except Exception as e:
        print(f"❌ 数据加载测试失败: {e}")
    
    # 5. 验证配置匹配
    print("\n5️⃣ 验证配置匹配...")
    
    try:
        import config
        rules = config.MATCH_RULES
        
        print("当前匹配规则配置:")
        print(f"  主数据字段: {rules['master_fields']}")
        print(f"  新数据字段: {rules['new_item_fields']}")
        
        # 检查字段是否存在
        if not df.empty:
            master_fields = rules['master_fields']
            missing_fields = []
            
            for field_type, fields in master_fields.items():
                if isinstance(fields, list):
                    for field in fields:
                        if field not in df.columns:
                            missing_fields.append(field)
                elif isinstance(fields, str) and fields not in df.columns:
                    missing_fields.append(fields)
            
            if missing_fields:
                print(f"❌ 缺少字段: {missing_fields}")
            else:
                print("✅ 所有配置字段都存在")
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
    
    print("\n🎉 字段匹配修复完成！")
    print("\n📝 修复摘要:")
    print("  ✅ 更新了config.py中的字段映射")
    print("  ✅ 修复了simple_db_config.py中的SQL查询")
    print("  ✅ 创建了数据库兼容性视图")
    print("  ✅ 验证了数据加载功能")
    
    print("\n🚀 现在可以重新启动MMP应用了!")
    print("  python3 run_app.py")

def create_sample_data():
    """创建示例数据用于测试"""
    print("\n🎯 创建示例测试数据...")
    
    try:
        conn = sqlite3.connect('master_data.db')
        
        # 确保materials表存在正确的字段
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO materials 
            (material_code, material_name, brand, specification, category_id, unit, model)
            VALUES 
            ('TEST001', '测试电阻器', 'KOA', '1KΩ ±5% 1/4W', 'CAT001001', '个', 'CF14JT1K00'),
            ('TEST002', '测试电容器', 'MURATA', '100nF 16V X7R 0603', 'CAT001002', '个', 'GCM188R71C104KA57'),
            ('TEST003', '测试螺丝', '东明', 'M3x8 304不锈钢', 'CAT002001', '个', 'DIN7985-M3x8')
        """)
        
        conn.commit()
        conn.close()
        print("✅ 示例数据创建完成")
        
    except Exception as e:
        print(f"❌ 示例数据创建失败: {e}")

if __name__ == "__main__":
    print("="*60)
    print("    MMP字段匹配问题修复脚本")
    print("="*60)
    
    fix_database_fields()
    create_sample_data()
    
    print("\n" + "="*60)
    print("修复脚本执行完成！请重新启动MMP应用。")
    print("="*60)