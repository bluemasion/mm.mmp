#!/usr/bin/env python3
"""
测试API的简单脚本
"""

import requests
import json

def test_generate_data():
    """测试生成测试数据"""
    try:
        print("测试 generate_test_data API...")
        response = requests.get("http://localhost:5001/generate_test_data")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"API测试失败: {e}")
        return False

def test_category_selection():
    """测试分类选择页面"""
    try:
        print("\n测试 category_selection 页面...")
        response = requests.get("http://localhost:5001/category_selection")
        print(f"状态码: {response.status_code}")
        if response.status_code == 302:
            print("重定向到:", response.headers.get('Location'))
        else:
            print("页面加载成功")
        return response.status_code in [200, 302]
    except Exception as e:
        print(f"页面测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始API测试...")
    
    # 测试生成测试数据
    data_ok = test_generate_data()
    
    # 测试分类选择页面
    page_ok = test_category_selection()
    
    print(f"\n测试结果:")
    print(f"- 数据生成: {'✓' if data_ok else '✗'}")
    print(f"- 页面访问: {'✓' if page_ok else '✗'}")