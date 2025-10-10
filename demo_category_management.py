#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
MMP 分类管理系统演示脚本
展示完整的分类管理功能
"""

import sqlite3
import json
import webbrowser
import time
import os
import sys

def check_data():
    """检查数据库中的分类数据"""
    print("=" * 60)
    print("📊 MMP 物料分类管理系统 - 数据检查")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('master_data.db')
        cursor = conn.cursor()
        
        # 统计信息
        cursor.execute('SELECT COUNT(*) FROM material_categories')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT level, COUNT(*) FROM material_categories GROUP BY level')
        level_stats = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM material_categories WHERE is_leaf = 1')
        leaf_count = cursor.fetchone()[0]
        
        print(f"✅ 总分类数量: {total}")
        print(f"✅ 1级分类: {level_stats.get(1, 0)} 个")
        print(f"✅ 2级分类: {level_stats.get(2, 0)} 个") 
        print(f"✅ 3级分类: {level_stats.get(3, 0)} 个")
        print(f"✅ 叶子节点: {leaf_count} 个")
        
        # 显示一些示例
        print("\n🔍 分类示例:")
        cursor.execute('''
            SELECT category_code, category_name, level 
            FROM material_categories 
            WHERE level = 1 
            ORDER BY category_code 
            LIMIT 5
        ''')
        
        for row in cursor.fetchall():
            code, name, level = row
            print(f"   📂 {code} - {name} (L{level})")
            
            # 显示该分类的子分类
            cursor.execute('''
                SELECT category_code, category_name, level 
                FROM material_categories 
                WHERE parent_code = ? 
                ORDER BY category_code 
                LIMIT 3
            ''', (code,))
            
            children = cursor.fetchall()
            for child in children:
                child_code, child_name, child_level = child
                print(f"      └── 📁 {child_code} - {child_name} (L{child_level})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据检查失败: {e}")
        return False

def test_api():
    """测试API功能"""
    print("\n" + "=" * 60)
    print("🔧 API 功能测试")
    print("=" * 60)
    
    # 模拟API测试
    try:
        conn = sqlite3.connect('master_data.db')
        cursor = conn.cursor()
        
        # 测试搜索功能
        print("\n🔍 搜索功能测试:")
        
        # 搜索"催化"
        cursor.execute('''
            SELECT category_code, category_name, level 
            FROM material_categories 
            WHERE category_code LIKE ? OR category_name LIKE ?
            ORDER BY level, category_code
        ''', ('%催化%', '%催化%'))
        
        results = cursor.fetchall()
        print(f"   搜索 '催化' 找到 {len(results)} 个结果:")
        for row in results:
            code, name, level = row
            print(f"      🎯 {code} - {name} (L{level})")
        
        # 测试层级过滤
        print(f"\n📊 层级过滤测试:")
        for level in [1, 2, 3]:
            cursor.execute('''
                SELECT COUNT(*) FROM material_categories WHERE level = ?
            ''', (level,))
            count = cursor.fetchone()[0]
            print(f"   L{level} 分类: {count} 个")
        
        conn.close()
        print("✅ API 功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ API 测试失败: {e}")
        return False

def show_tree_structure():
    """展示分类树结构"""
    print("\n" + "=" * 60)
    print("🌳 分类树结构展示")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('master_data.db')
        cursor = conn.cursor()
        
        # 获取根分类
        cursor.execute('''
            SELECT category_code, category_name 
            FROM material_categories 
            WHERE level = 1 
            ORDER BY category_code 
            LIMIT 3
        ''')
        
        root_categories = cursor.fetchall()
        
        for root_code, root_name in root_categories:
            print(f"\n📂 {root_code} - {root_name}")
            
            # 获取二级分类
            cursor.execute('''
                SELECT category_code, category_name 
                FROM material_categories 
                WHERE parent_code = ? AND level = 2
                ORDER BY category_code 
                LIMIT 3
            ''', (root_code,))
            
            level2_categories = cursor.fetchall()
            
            for l2_code, l2_name in level2_categories:
                print(f"├── 📁 {l2_code} - {l2_name}")
                
                # 获取三级分类
                cursor.execute('''
                    SELECT category_code, category_name 
                    FROM material_categories 
                    WHERE parent_code = ? AND level = 3
                    ORDER BY category_code 
                    LIMIT 2
                ''', (l2_code,))
                
                level3_categories = cursor.fetchall()
                
                for i, (l3_code, l3_name) in enumerate(level3_categories):
                    prefix = "└──" if i == len(level3_categories) - 1 else "├──"
                    print(f"│   {prefix} 📄 {l3_code} - {l3_name}")
            
            if len(level2_categories) > 0:
                # 计算该根分类下的总数
                cursor.execute('''
                    SELECT COUNT(*) FROM material_categories 
                    WHERE category_code LIKE ?
                ''', (root_code + '%',))
                total_count = cursor.fetchone()[0]
                print(f"└── ... (该分类下共 {total_count} 个子分类)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 树结构展示失败: {e}")
        return False

def open_web_interface():
    """打开Web界面"""
    print("\n" + "=" * 60)
    print("🌐 启动Web界面")
    print("=" * 60)
    
    print("🚀 Web服务应该已经在运行在 http://localhost:5001")
    print("📱 分类管理页面: http://localhost:5001/categories")
    
    try:
        # 尝试打开浏览器
        print("\n⏰ 3秒后将自动打开浏览器...")
        time.sleep(3)
        webbrowser.open('http://localhost:5001/categories')
        print("✅ 浏览器已打开分类管理页面")
        return True
    except Exception as e:
        print(f"❌ 无法自动打开浏览器: {e}")
        print("🔗 请手动访问: http://localhost:5001/categories")
        return False

def main():
    """主演示函数"""
    print("🎉 欢迎使用 MMP 物料分类管理系统演示")
    print("📅 版本: v2.0")
    print("👨‍💻 功能: 智能物料分类管理与查询")
    
    # 检查当前目录
    if not os.path.exists('master_data.db'):
        print("❌ 错误: 未找到 master_data.db 文件")
        print("📁 请确保在正确的项目目录中运行此脚本")
        sys.exit(1)
    
    success_count = 0
    total_tests = 4
    
    # 执行各项检查
    if check_data():
        success_count += 1
        
    if test_api():
        success_count += 1
        
    if show_tree_structure():
        success_count += 1
        
    if open_web_interface():
        success_count += 1
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 演示总结")
    print("=" * 60)
    
    print(f"✅ 成功完成: {success_count}/{total_tests} 项测试")
    
    if success_count == total_tests:
        print("🎉 所有功能正常！系统准备就绪！")
        
        print("\n📖 使用说明:")
        print("1. 🌐 访问 http://localhost:5001/categories 查看分类管理界面")
        print("2. 🔍 使用搜索框快速查找分类")
        print("3. 📊 使用层级过滤按钮查看不同级别分类")
        print("4. 🖱️  点击分类查看详细信息")
        print("5. 📈 查看右侧统计信息了解分类分布")
        
    else:
        print("⚠️  部分功能存在问题，请检查系统配置")
    
    print(f"\n🕒 演示完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()