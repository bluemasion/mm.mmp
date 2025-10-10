#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件上传功能
模拟前端文件上传请求
"""

import requests
import os
import pandas as pd
import json

def test_file_upload():
    """测试文件上传功能"""
    
    print("🧪 测试MMP平台文件上传功能")
    print("=" * 50)
    
    # 创建测试数据文件
    test_data = {
        '资产代码': ['TEST001', 'TEST002', 'TEST003'],
        '资产名称': ['测试医用口罩', '测试一次性手套', '测试体温计'],
        '规格型号': ['N95型', '乳胶L码', '电子式'],
        '品牌': ['3M', '安思尔', '欧姆龙'],
        '医保码': ['YB001', 'YB002', 'YB003'],
        '生产厂家名称': ['3M公司', '安思尔公司', '欧姆龙公司']
    }
    
    # 创建测试Excel文件
    df = pd.DataFrame(test_data)
    test_file_path = 'test_upload.xlsx'
    df.to_excel(test_file_path, index=False)
    
    print(f"📄 创建测试文件: {test_file_path}")
    print("文件内容:")
    print(df.to_string(index=False))
    
    try:
        # 测试文件上传
        url = 'http://localhost:5001/upload'
        
        with open(test_file_path, 'rb') as f:
            files = {'file': (test_file_path, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            print(f"\n🚀 发送上传请求到: {url}")
            response = requests.post(url, files=files, timeout=30)
            
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 文件上传成功!")
                print("📋 响应数据:")
                
                # 格式化打印响应数据
                for key, value in result.items():
                    if key == 'preview_data':
                        print(f"  {key}: [{len(value)} 行预览数据]")
                        for i, row in enumerate(value[:2]):  # 只显示前2行
                            print(f"    行{i+1}: {row}")
                    elif key == 'field_mapping':
                        print(f"  {key}: {value}")
                    elif isinstance(value, list):
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: {value}")
                
                # 验证字段映射
                if 'field_mapping' in result and result['field_mapping']:
                    print("\n🔄 字段映射验证:")
                    for original, mapped in result['field_mapping'].items():
                        print(f"  {original} -> {mapped}")
                
            else:
                print(f"❌ 上传失败: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"错误信息: {error_data}")
                except:
                    print(f"错误信息: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 无法连接到MMP平台")
        print("请确保平台已启动并运行在 http://localhost:5001")
    
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"\n🧹 清理测试文件: {test_file_path}")

def test_upload_api_status():
    """测试上传API状态"""
    
    print("\n🔍 测试上传相关API状态")
    print("=" * 50)
    
    # 测试上传页面
    try:
        response = requests.get('http://localhost:5001/upload', timeout=10)
        print(f"📄 上传页面: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 上传页面测试失败: {e}")
    
    # 测试字段映射API
    try:
        response = requests.get('http://localhost:5001/api/field_mappings', timeout=10)
        print(f"🗂️  字段映射API: HTTP {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   字段映射数量: {data.get('total', 0)}")
    except Exception as e:
        print(f"❌ 字段映射API测试失败: {e}")
    
    # 测试统计信息API
    try:
        response = requests.get('http://localhost:5001/api/statistics', timeout=10)
        print(f"📊 统计信息API: HTTP {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            stats = data.get('statistics', {})
            print(f"   文件数量: {stats.get('total_files', 0)}")
            print(f"   数据行数: {stats.get('total_rows', 0)}")
    except Exception as e:
        print(f"❌ 统计信息API测试失败: {e}")

if __name__ == "__main__":
    test_upload_api_status()
    test_file_upload()