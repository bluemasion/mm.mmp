#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
首页分类模板功能集成测试脚本
测试新添加到首页的分类模板功能是否正常工作
"""

import requests
import json
import sys
import time

def test_homepage_access():
    """测试首页是否可以正常访问"""
    print("🔍 测试首页访问...")
    
    try:
        response = requests.get('http://localhost:5001/', timeout=10)
        
        if response.status_code == 200:
            print("✅ 首页访问成功")
            
            # 检查是否包含分类模板相关内容
            content = response.text
            template_keywords = [
                '分类模板',
                'template_selection',
                'fas fa-tags',
                '制造业标准分类'
            ]
            
            for keyword in template_keywords:
                if keyword in content:
                    print(f"✅ 找到关键词: {keyword}")
                else:
                    print(f"⚠️ 缺失关键词: {keyword}")
                    
            return True
        else:
            print(f"❌ 首页访问失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 首页访问异常: {e}")
        return False

def test_template_selection_access():
    """测试分类模板选择页面访问"""
    print("\n🔍 测试分类模板页面访问...")
    
    try:
        response = requests.get('http://localhost:5001/template-selection', timeout=10)
        
        if response.status_code == 200:
            print("✅ 分类模板页面访问成功")
            return True
        else:
            print(f"❌ 分类模板页面访问失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 分类模板页面访问异常: {e}")
        return False

def test_categories_api():
    """测试分类统计API"""
    print("\n🔍 测试分类统计API...")
    
    try:
        response = requests.get('http://localhost:5001/api/categories/stats', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                stats = data.get('statistics', {})
                print("✅ 分类统计API调用成功")
                print(f"   总分类数: {stats.get('total', 'N/A')}")
                print(f"   一级分类: {stats.get('level1', 'N/A')}")
                print(f"   二级分类: {stats.get('level2', 'N/A')}")
                print(f"   三级分类: {stats.get('level3', 'N/A')}")
                return True
            else:
                print(f"❌ API返回失败: {data}")
                return False
        else:
            print(f"❌ 分类统计API访问失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 分类统计API访问异常: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return False

def test_navigation_links():
    """测试导航链接"""
    print("\n🔍 测试功能导航链接...")
    
    test_urls = [
        ('首页', 'http://localhost:5001/'),
        ('数据导入', 'http://localhost:5001/upload'),
        ('分类模板', 'http://localhost:5001/template-selection'),
        ('批量管理', 'http://localhost:5001/batch-management')
    ]
    
    results = {}
    for name, url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}页面访问成功")
                results[name] = True
            else:
                print(f"❌ {name}页面访问失败，状态码: {response.status_code}")
                results[name] = False
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}页面访问异常: {e}")
            results[name] = False
    
    return all(results.values())

def main():
    """主测试函数"""
    print("=" * 60)
    print("          首页分类模板功能集成测试")
    print("=" * 60)
    
    # 等待应用启动
    print("⏳ 等待应用启动...")
    time.sleep(3)
    
    tests = [
        ("首页访问测试", test_homepage_access),
        ("分类模板页面测试", test_template_selection_access),
        ("分类统计API测试", test_categories_api),
        ("导航链接测试", test_navigation_links)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"运行测试: {test_name}")
        print('='*40)
        
        result = test_func()
        results.append((test_name, result))
        
        if result:
            print(f"✅ {test_name} - 通过")
        else:
            print(f"❌ {test_name} - 失败")
    
    # 测试结果汇总
    print(f"\n{'='*60}")
    print("                测试结果汇总")
    print('='*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "通过" if result else "失败"
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 总测试数: {total}")
    print(f"✅ 通过数量: {passed}")
    print(f"❌ 失败数量: {total - passed}")
    print(f"🎯 通过率: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！首页分类模板功能集成成功！")
        return True
    else:
        print("\n⚠️ 部分测试失败，请检查相关功能。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)