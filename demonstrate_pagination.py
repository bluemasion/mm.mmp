#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
分页功能演示脚本
演示material-workflow页面的分页效果
"""

import webbrowser
import time
import requests
import json

def demonstrate_pagination():
    """演示分页功能"""
    
    print("🎬 分页功能演示")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5001"
    
    # 1. 检查服务状态
    print("1️⃣ 检查服务状态...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ MMP服务运行正常")
        else:
            print("❌ 服务异常，请重启服务")
            return
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        return
    
    # 2. 显示分页功能特性
    print("\n2️⃣ 分页功能特性:")
    print("   📄 每页显示: 20条数据")
    print("   🔢 可选页面大小: 10/20/50/100")
    print("   🧭 导航功能: 首页/上一页/下一页/末页")
    print("   📊 数据统计: 总计数量和当前范围")
    print("   📱 响应式设计: 支持移动设备")
    
    # 3. 测试数据信息
    print("\n3️⃣ 测试数据信息:")
    print("   📁 测试文件: test_pagination_data.csv")
    print("   📋 数据量: 50条物料数据")
    print("   📄 分页效果: 3页 (20+20+10)")
    print("   🏷️ 数据类型: 阀门、管件、紧固件、电气设备等")
    
    # 4. 实际测试一下API
    print("\n4️⃣ 快速API测试...")
    try:
        # 读取测试数据
        with open('test_pagination_data.csv', 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]  # 跳过标题行
        
        # 解析前5条数据进行快速测试
        materials = []
        for i, line in enumerate(lines[:5]):
            parts = line.strip().split(',')
            if len(parts) >= 7:
                materials.append([
                    parts[0],  # 物料编码
                    parts[1],  # 物料名称
                    parts[2],  # 物料简称
                    parts[3],  # 物料类别
                    parts[4],  # 规格型号
                    parts[5],  # 制造商
                    parts[6]   # 单位
                ])
        
        # 调用API
        response = requests.post(
            f"{base_url}/api/batch_material_matching",
            json={
                "materials": materials,
                "template": "universal-manufacturing"
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                results = result.get('results', [])
                print(f"   ✅ API测试成功: {len(results)} 条结果")
                
                # 显示分类结果示例
                print("\n   📊 分类结果示例:")
                for i, res in enumerate(results[:3]):
                    name = res.get('material_name', '未知')
                    classification = res.get('classification', '未分类')
                    confidence = res.get('classification_confidence', 0)
                    print(f"      {i+1}. {name} → {classification} ({confidence}%)")
            else:
                print(f"   ❌ API调用失败: {result.get('error')}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️ 快速测试跳过: {e}")
    
    # 5. 使用指南
    print("\n" + "=" * 60)
    print("📖 分页功能使用指南:")
    print("\n🚀 快速体验步骤:")
    print("   1. 访问: http://127.0.0.1:5001/material-workflow")
    print("   2. 上传测试文件: test_pagination_data.csv")
    print("   3. 选择模板: '物料统一模板'") 
    print("   4. 点击: '开始匹配'")
    print("   5. 查看分页效果")
    
    print("\n🎛️ 分页操作:")
    print("   • 页面导航: 首页/上页/下页/末页按钮")
    print("   • 页面大小: 下拉选择 10/20/50/100")
    print("   • 数据统计: 总数/当前范围/页数显示")
    print("   • 快速跳转: 点击页码直接跳转")
    
    print("\n📱 界面特色:")
    print("   • 序号列: 显示全局数据序号")
    print("   • 统计信息: 实时显示数据范围")
    print("   • 响应式表格: 适配不同屏幕尺寸")
    print("   • 悬停效果: 表格行悬停高亮")
    
    print("\n💡 性能优势:")
    print("   • 前端分页: 不需要重新请求服务器")
    print("   • 快速导航: 即时页面切换")
    print("   • 内存优化: 只渲染当前页面数据")
    print("   • 用户体验: 平滑过渡和动画效果")
    
    # 6. 打开浏览器
    print(f"\n🌐 自动打开浏览器...")
    try:
        webbrowser.open(f"{base_url}/material-workflow")
        print("✅ 浏览器已打开，请按照上述步骤进行测试")
    except Exception as e:
        print(f"⚠️ 无法自动打开浏览器: {e}")
        print(f"   请手动访问: {base_url}/material-workflow")
    
    print("\n🎉 分页功能演示完成!")

if __name__ == "__main__":
    demonstrate_pagination()