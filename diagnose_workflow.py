#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料工作流页面问题诊断脚本
"""

import requests
import json

def diagnose_workflow_issue():
    """诊断工作流页面问题"""
    print("🔍 诊断物料工作流页面问题...")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5001"
    
    # 1. 检查页面是否可访问
    try:
        response = requests.get(f"{base_url}/material-workflow")
        print(f"📄 页面访问状态: {response.status_code}")
        if response.status_code == 200:
            print("✅ 页面可正常访问")
        else:
            print("❌ 页面访问失败")
            return
    except Exception as e:
        print(f"❌ 页面访问错误: {e}")
        return
    
    # 2. 检查关键API端点
    api_endpoints = [
        "/api/batch_material_matching",
        "/api/status",
        "/api/templates",  # 如果存在的话
    ]
    
    print("\n🔗 检查API端点:")
    for endpoint in api_endpoints:
        try:
            if endpoint == "/api/batch_material_matching":
                # POST请求测试
                test_data = {
                    "materials": [["M001", "测试物料", "测试", "测试分类", "", "", "个"]],
                    "template": "universal-manufacturing"
                }
                response = requests.post(f"{base_url}{endpoint}", 
                                       json=test_data, timeout=5)
            else:
                # GET请求测试
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            print(f"  {endpoint}: {response.status_code}")
            if response.status_code == 200:
                if endpoint == "/api/batch_material_matching":
                    result = response.json()
                    if result.get("success"):
                        print(f"    ✅ 批量匹配API正常工作")
                        print(f"    📊 处理结果: {len(result.get('results', []))} 条")
                    else:
                        print(f"    ⚠️ API响应成功但业务失败: {result.get('error', 'Unknown error')}")
        except requests.exceptions.Timeout:
            print(f"  {endpoint}: ⏰ 超时")
        except requests.exceptions.ConnectionError:
            print(f"  {endpoint}: ❌ 连接失败")  
        except Exception as e:
            print(f"  {endpoint}: ❌ 错误 - {e}")
    
    # 3. 检查JavaScript错误的可能原因
    print(f"\n🧩 可能的问题分析:")
    
    # 检查页面中的关键JavaScript片段
    page_content = response.text
    
    # 检查关键函数是否存在
    js_checks = [
        ("nextStep函数", "function nextStep"),
        ("startMatchingAndProgress函数", "startMatchingAndProgress"),
        ("WorkflowManager类", "class WorkflowManager"),
        ("按钮启用逻辑", "nextStep3.*disabled.*false"),
    ]
    
    for check_name, pattern in js_checks:
        if pattern in page_content:
            print(f"  ✅ {check_name}: 存在")
        else:
            print(f"  ❌ {check_name}: 缺失")
    
    # 4. 提供解决方案建议
    print(f"\n💡 问题解决建议:")
    print("1. 🔄 确保按正确顺序操作:")
    print("   - 第一步: 上传物料数据文件")
    print("   - 第二步: 选择匹配模板")  
    print("   - 第三步: 点击'开始匹配'按钮")
    print("   - 第四步: 等待匹配完成后，'查看结果'按钮才会启用")
    
    print("\n2. 🐛 如果按钮仍无响应，检查:")
    print("   - 浏览器控制台是否有JavaScript错误")
    print("   - 网络请求是否成功完成")
    print("   - 数据是否正确上传和选择")
    
    print("\n3. 🔧 开发者调试:")
    print("   - 按F12打开开发者工具")
    print("   - 查看Console标签页的错误信息")
    print("   - 查看Network标签页的API请求状态")
    
    # 5. 提供测试用的curl命令
    print(f"\n🧪 手动测试命令:")
    print("# 测试批量匹配API:")
    print('curl -X POST "http://127.0.0.1:5001/api/batch_material_matching" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"materials": [["M001", "测试物料", "测试", "测试分类", "", "", "个"]], "template": "universal-manufacturing"}\'')

if __name__ == "__main__":
    diagnose_workflow_issue()