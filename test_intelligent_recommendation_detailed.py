#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
智能分类推荐功能测试工具
测试参数提取页面的智能推荐功能
"""

import requests
import json
from datetime import datetime

def test_intelligent_recommendation():
    """测试智能分类推荐功能"""
    base_url = "http://localhost:5001"
    
    print("🧠 智能分类推荐功能测试")
    print("=" * 60)
    
    # 测试数据 - 不同类型的医疗器械
    test_materials = [
        {
            "name": "一次性使用无菌注射器",
            "spec": "5ml",
            "manufacturer": "山东威高集团医用高分子制品股份有限公司"
        },
        {
            "name": "心电监护仪电极片",
            "spec": "成人用", 
            "manufacturer": "深圳迈瑞生物医疗电子股份有限公司"
        },
        {
            "name": "医用防护口罩",
            "spec": "N95",
            "manufacturer": "3M公司"
        },
        {
            "name": "血糖试纸",
            "spec": "50片装",
            "manufacturer": "罗氏诊断产品（上海）有限公司"
        },
        {
            "name": "输液器",
            "spec": "一次性使用",
            "manufacturer": "江苏康泰医疗器械有限公司"
        }
    ]
    
    try:
        # 调用批量推荐API
        response = requests.post(
            f"{base_url}/api/batch_recommend",
            headers={
                'Content-Type': 'application/json'
            },
            json={
                'materials': test_materials
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ API调用成功")
            print(f"📊 测试物料数量: {result.get('total', 0)}")
            print(f"🆔 会话ID: {result.get('session_id', 'N/A')}")
            print()
            
            # 分析推荐结果
            results = result.get('results', [])
            
            for i, material_result in enumerate(results):
                material_info = material_result.get('material_info', {})
                recommendations = material_result.get('recommendations', [])
                
                print(f"📦 物料 {i+1}: {material_info.get('name', 'N/A')}")
                print(f"   📏 规格: {material_info.get('spec', 'N/A')}")
                print(f"   🏭 厂家: {material_info.get('manufacturer', 'N/A')}")
                
                if material_result.get('success'):
                    print(f"   💡 智能推荐结果 ({len(recommendations)}个):")
                    
                    if recommendations:
                        for j, rec in enumerate(recommendations):
                            confidence = rec.get('confidence', 0) * 100
                            category_name = rec.get('category_name', 'N/A')
                            reason = rec.get('reason', 'N/A')
                            source = rec.get('source', 'N/A')
                            
                            # 置信度颜色标识
                            if confidence >= 70:
                                confidence_icon = "🟢"
                            elif confidence >= 50:
                                confidence_icon = "🟡"
                            else:
                                confidence_icon = "🔴"
                            
                            print(f"      {j+1}. {confidence_icon} {category_name}")
                            print(f"         置信度: {confidence:.1f}%")
                            print(f"         推理依据: {reason}")
                            print(f"         匹配来源: {source}")
                    else:
                        print("      ❌ 无推荐结果")
                else:
                    error_msg = material_result.get('error', 'Unknown error')
                    print(f"   ❌ 推荐失败: {error_msg}")
                
                print("-" * 50)
            
            # 统计分析
            print("\n📈 推荐统计分析:")
            total_materials = len(results)
            successful_recommendations = sum(1 for r in results if r.get('success') and r.get('recommendations'))
            total_recommendations = sum(len(r.get('recommendations', [])) for r in results)
            
            print(f"   📦 测试物料总数: {total_materials}")
            print(f"   ✅ 成功推荐物料数: {successful_recommendations}")
            print(f"   📊 推荐成功率: {successful_recommendations/total_materials*100:.1f}%")
            print(f"   💡 总推荐数量: {total_recommendations}")
            print(f"   📈 平均每个物料推荐数: {total_recommendations/total_materials:.1f}")
            
            # 分析推荐质量
            high_confidence = sum(1 for r in results 
                                for rec in r.get('recommendations', []) 
                                if rec.get('confidence', 0) >= 0.7)
            medium_confidence = sum(1 for r in results 
                                  for rec in r.get('recommendations', []) 
                                  if 0.5 <= rec.get('confidence', 0) < 0.7)
            low_confidence = sum(1 for r in results 
                               for rec in r.get('recommendations', []) 
                               if rec.get('confidence', 0) < 0.5)
            
            print(f"\n🎯 推荐质量分析:")
            print(f"   🟢 高置信度推荐 (≥70%): {high_confidence}")
            print(f"   🟡 中等置信度推荐 (50-70%): {medium_confidence}")
            print(f"   🔴 低置信度推荐 (<50%): {low_confidence}")
            
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            print(f"   错误信息: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_single_material_recommendation():
    """测试单个物料推荐"""
    base_url = "http://localhost:5001"
    
    print("\n🔍 单个物料详细推荐测试")
    print("=" * 60)
    
    # 测试一个典型的医疗器械
    test_material = {
        "name": "医用外科手术刀片",
        "spec": "24号弯刃",
        "manufacturer": "上海金钟医疗器械股份有限公司"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/batch_recommend",
            headers={'Content-Type': 'application/json'},
            json={'materials': [test_material]},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            material_result = result.get('results', [{}])[0]
            
            print(f"📦 测试物料: {test_material['name']}")
            print(f"📏 规格: {test_material['spec']}")
            print(f"🏭 制造商: {test_material['manufacturer']}")
            print()
            
            if material_result.get('success'):
                recommendations = material_result.get('recommendations', [])
                print(f"💡 推荐结果数量: {len(recommendations)}")
                
                for i, rec in enumerate(recommendations):
                    print(f"\n推荐 {i+1}:")
                    print(f"  分类ID: {rec.get('category_id', 'N/A')}")
                    print(f"  分类名称: {rec.get('category_name', 'N/A')}")
                    print(f"  置信度: {rec.get('confidence', 0)*100:.1f}%")
                    print(f"  推理依据: {rec.get('reason', 'N/A')}")
                    print(f"  匹配来源: {rec.get('source', 'N/A')}")
            else:
                print(f"❌ 推荐失败: {material_result.get('error', 'Unknown error')}")
                
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    """主函数"""
    print(f"🚀 MMP智能分类推荐功能测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 检查服务状态
    try:
        response = requests.get("http://localhost:5001/", timeout=5)
        if response.status_code == 200:
            print("✅ MMP服务运行正常")
        else:
            print(f"⚠️  MMP服务状态异常: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到MMP服务: {e}")
        return
    
    print()
    
    # 执行测试
    test_intelligent_recommendation()
    test_single_material_recommendation()
    
    print("\n" + "=" * 60)
    print("✅ 智能分类推荐功能测试完成")
    print("\n💡 功能说明:")
    print("   - 基于物料名称、规格等信息进行智能分类推荐")
    print("   - 支持批量推荐，提高处理效率") 
    print("   - 提供置信度评分，帮助用户判断推荐质量")
    print("   - 显示推理依据，增强推荐的可解释性")
    print("   - 支持多种匹配策略：关键词、规格模式等")

if __name__ == "__main__":
    main()