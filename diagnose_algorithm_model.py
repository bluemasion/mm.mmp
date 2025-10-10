#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
算法模型诊断工具
诊断SmartClassifier为什么返回0条匹配结果
"""

import sys
import os
import json
import sqlite3
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database_data():
    """检查数据库中的数据"""
    print("=" * 60)
    print("📊 数据库数据检查")
    print("=" * 60)
    
    try:
        # 检查主数据库
        if os.path.exists('master_data.db'):
            conn = sqlite3.connect('master_data.db')
            cursor = conn.cursor()
            
            # 检查表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"✅ 主数据库表数量: {len(tables)}")
            for table in tables:
                print(f"   - {table[0]}")
            
            # 检查物料分类数据
            try:
                cursor.execute("SELECT COUNT(*) FROM material_categories")
                category_count = cursor.fetchone()[0]
                print(f"✅ 物料分类数量: {category_count}")
                
                if category_count > 0:
                    cursor.execute("SELECT name, parent_id, level FROM material_categories LIMIT 5")
                    categories = cursor.fetchall()
                    print("   样本分类:")
                    for cat in categories:
                        print(f"   - {cat[0]} (父ID: {cat[1]}, 级别: {cat[2]})")
                        
            except sqlite3.OperationalError as e:
                print(f"❌ 物料分类表错误: {e}")
            
            conn.close()
        else:
            print("❌ master_data.db 不存在")
            
        # 检查业务数据库
        if os.path.exists('business_data.db'):
            conn = sqlite3.connect('business_data.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"✅ 业务数据库表数量: {len(tables)}")
            
            conn.close()
        else:
            print("❌ business_data.db 不存在")
            
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")


def check_algorithm_components():
    """检查算法组件"""
    print("\n" + "=" * 60)
    print("🧠 算法组件检查")
    print("=" * 60)
    
    try:
        # 导入核心模块
        from main import SmartClassifier, AdvancedMaterialMatcher
        print("✅ 核心算法模块导入成功")
        
        # 初始化SmartClassifier
        classifier = SmartClassifier()
        print("✅ SmartClassifier 初始化成功")
        
        # 检查分类器数据
        if hasattr(classifier, 'material_categories') and classifier.material_categories:
            print(f"✅ 分类器载入分类数量: {len(classifier.material_categories)}")
            
            # 显示部分分类数据
            categories_sample = list(classifier.material_categories.items())[:5]
            print("   样本分类数据:")
            for key, value in categories_sample:
                print(f"   - {key}: {value}")
        else:
            print("❌ 分类器未载入分类数据")
            
        # 检查关键词映射
        if hasattr(classifier, 'keyword_mapping') and classifier.keyword_mapping:
            print(f"✅ 关键词映射数量: {len(classifier.keyword_mapping)}")
        else:
            print("❌ 关键词映射为空")
            
        return classifier
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 算法组件检查失败: {e}")
        return None


def test_classification_process(classifier):
    """测试分类过程"""
    print("\n" + "=" * 60)
    print("🔬 分类过程测试")
    print("=" * 60)
    
    if not classifier:
        print("❌ 分类器不可用，跳过测试")
        return
        
    # 测试物料
    test_materials = [
        "304不锈钢疏水器",
        "碳钢螺塞", 
        "法兰盘",
        "阀门",
        "管道"
    ]
    
    for material in test_materials:
        print(f"\n🧪 测试物料: {material}")
        
        try:
            # 调用分类方法
            if hasattr(classifier, 'classify_material'):
                result = classifier.classify_material(material)
                print(f"   结果: {result}")
            else:
                print("   ❌ 分类器没有 classify_material 方法")
                
        except Exception as e:
            print(f"   ❌ 分类失败: {e}")


def check_api_endpoint():
    """检查API端点响应"""
    print("\n" + "=" * 60)
    print("🌐 API端点检查")
    print("=" * 60)
    
    try:
        import requests
        
        # 测试批量匹配API
        test_data = {
            "materials": [["M001", "304不锈钢疏水器", "疏水器", "管道配件", "DN25", "", "个"]],
            "template": "universal-manufacturing"
        }
        
        url = "http://127.0.0.1:5001/api/batch_material_matching"
        
        print(f"📡 测试API: {url}")
        print(f"📋 测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, json=test_data, timeout=10)
        
        print(f"✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应内容:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 检查匹配结果
            if 'matches' in result and result['matches']:
                print(f"✅ 找到匹配: {len(result['matches'])} 条")
            else:
                print("❌ 没有找到匹配结果")
                
        else:
            print(f"❌ API响应错误: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {e}")
    except Exception as e:
        print(f"❌ API测试失败: {e}")


def check_template_configuration():
    """检查模板配置"""
    print("\n" + "=" * 60)
    print("📋 模板配置检查")
    print("=" * 60)
    
    try:
        # 检查配置文件
        config_files = ['config.py', 'enhanced_config.py']
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"✅ 找到配置文件: {config_file}")
                
                # 读取配置内容
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 检查分类模板相关配置
                if 'universal-manufacturing' in content:
                    print(f"   ✅ 包含制造业模板配置")
                else:
                    print(f"   ⚠️  未找到制造业模板配置")
                    
            else:
                print(f"❌ 配置文件不存在: {config_file}")
        
        # 检查是否有专门的模板文件
        template_files = ['templates.json', 'classification_templates.json']
        for template_file in template_files:
            if os.path.exists(template_file):
                print(f"✅ 找到模板文件: {template_file}")
                with open(template_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                    print(f"   模板数量: {len(templates)}")
            else:
                print(f"ℹ️  模板文件不存在: {template_file}")
                
    except Exception as e:
        print(f"❌ 模板配置检查失败: {e}")


def main():
    """主诊断流程"""
    print("🔍 MMP算法模型诊断工具")
    print("诊断SmartClassifier返回0条匹配的原因")
    print("=" * 60)
    
    # 1. 检查数据库数据
    check_database_data()
    
    # 2. 检查算法组件
    classifier = check_algorithm_components()
    
    # 3. 测试分类过程
    test_classification_process(classifier)
    
    # 4. 检查API端点
    check_api_endpoint()
    
    # 5. 检查模板配置
    check_template_configuration()
    
    print("\n" + "=" * 60)
    print("🏁 诊断完成")
    print("=" * 60)
    print("请查看上述输出，定位0匹配问题的根本原因")


if __name__ == "__main__":
    main()