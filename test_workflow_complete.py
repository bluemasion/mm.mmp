#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流测试 - 完整步骤验证
"""

import requests
import json
import time

def test_complete_workflow():
    """测试完整的工作流程"""
    print("🎯 测试完整物料工作流程...")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5001"
    
    # 1. 访问工作流页面
    print("1️⃣ 访问工作流页面...")
    try:
        response = requests.get(f"{base_url}/material-workflow")
        if response.status_code == 200:
            print("   ✅ 页面加载成功")
        else:
            print(f"   ❌ 页面加载失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 页面访问错误: {e}")
        return False
    
    # 2. 测试批量匹配API（模拟第三步之后的操作）
    print("\n2️⃣ 测试批量匹配功能...")
    test_materials = [
        ["M001", "304不锈钢疏水器", "疏水器", "管道配件", "DN25", "", "个"],
        ["M002", "碳钢螺塞", "螺塞", "紧固件", "M27*2", "", "个"]
    ]
    
    try:
        response = requests.post(
            f"{base_url}/api/batch_material_matching",
            json={
                "materials": test_materials,
                "template": "universal-manufacturing"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("   ✅ 批量匹配成功")
                print(f"   📊 处理物料数量: {len(result.get('results', []))}")
                
                # 显示匹配结果
                for i, material_result in enumerate(result.get('results', [])):
                    print(f"   📦 物料{i+1}: {material_result.get('material_name', 'N/A')}")
                    print(f"      分类: {material_result.get('classification', 'N/A')}")
                    print(f"      置信度: {material_result.get('classification_confidence', 0)}%")
                
                print("\n   🎉 API功能正常，这意味着：")
                print("      - 如果您完成了前面步骤（上传数据、选择模板）")
                print("      - 点击'开始匹配'按钮应该会成功")
                print("      - 匹配完成后'查看结果'按钮会自动启用")
                
                return True
            else:
                print(f"   ⚠️ 匹配失败: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ API请求错误: {e}")
        return False

def check_javascript_functions():
    """检查页面JavaScript函数"""
    print("\n3️⃣ 检查JavaScript函数...")
    
    try:
        response = requests.get("http://127.0.0.1:5001/material-workflow")
        content = response.text
        
        js_functions = {
            "nextStep": "function nextStep" in content,
            "startMatchingAndProgress": "startMatchingAndProgress" in content,
            "WorkflowManager": "class WorkflowManager" in content,
            "按钮启用逻辑": "nextStep3.*disabled.*false" in content or "getElementById('nextStep3').disabled = false" in content
        }
        
        all_good = True
        for func_name, exists in js_functions.items():
            if exists:
                print(f"   ✅ {func_name}: 存在")
            else:
                print(f"   ❌ {func_name}: 缺失")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"   ❌ JavaScript检查错误: {e}")
        return False

def provide_troubleshooting_guide():
    """提供故障排除指南"""
    print("\n🔧 故障排除指南:")
    print("=" * 30)
    
    print("📋 按钮无响应的可能原因:")
    print("1. 未按顺序完成前面步骤")
    print("   - 必须先上传物料数据文件")
    print("   - 必须选择匹配模板")
    print("   - 然后点击'开始匹配'")
    print("   - 最后才能点击'查看结果'")
    
    print("\n2. JavaScript错误")
    print("   - 按F12打开开发者工具")
    print("   - 查看Console标签是否有红色错误")
    print("   - 如有错误请提供错误信息")
    
    print("\n3. 浏览器缓存问题")
    print("   - 按Ctrl+F5强制刷新页面")
    print("   - 或者按Ctrl+Shift+Delete清除缓存")
    
    print("\n4. 按钮状态检查")
    print("   - '查看结果'按钮默认是灰色disabled状态")
    print("   - 只有匹配成功后才会变成蓝色可点击")
    
    print("\n🧪 测试步骤:")
    print("1. 刷新页面: http://127.0.0.1:5001/material-workflow")
    print("2. 上传测试文件（CSV格式）")
    print("3. 选择'通用制造业'模板")
    print("4. 点击'开始匹配'按钮")
    print("5. 等待进度条完成")
    print("6. '查看结果'按钮应该会启用（变蓝色）")

def main():
    print("🚀 MMP工作流完整测试")
    print("=" * 50)
    
    # 执行测试
    api_ok = test_complete_workflow()
    js_ok = check_javascript_functions()
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"API功能: {'✅ 正常' if api_ok else '❌ 异常'}")
    print(f"JavaScript: {'✅ 正常' if js_ok else '❌ 异常'}")
    
    if api_ok and js_ok:
        print("\n🎉 系统功能正常！")
        print("💡 如果按钮仍无响应，请检查操作步骤是否正确")
    else:
        print("\n⚠️ 系统存在问题，需要修复")
    
    provide_troubleshooting_guide()

if __name__ == "__main__":
    main()