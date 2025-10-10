#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
工作流数据流调试工具
检查从文件上传到算法匹配的完整数据流
"""

import requests
import json
import os

def test_file_upload():
    """测试文件上传API"""
    print("=" * 60)
    print("📁 测试文件上传API")
    print("=" * 60)
    
    # 创建测试文件
    test_data = """物料编码,物料名称,物料简称,当前分类,规格型号,制造商,单位
M001,304不锈钢疏水器,疏水器,管道配件,DN25,,个
M002,碳钢螺塞,螺塞,紧固件,M8,,个
M003,法兰盘,法兰,管道配件,DN100,,个"""
    
    test_file = 'test_upload_data.csv'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_data)
    
    try:
        # 上传文件
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post('http://127.0.0.1:5001/api/upload_material_data', files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 文件上传成功")
            print(f"📊 成功状态: {result.get('success', False)}")
            print(f"📋 数据条数: {len(result.get('data', []))}")
            print(f"📈 统计信息: {result.get('stats', {})}")
            print(f"🔍 预览数据: {json.dumps(result.get('preview', [])[:2], ensure_ascii=False, indent=2)}")
            
            # 返回上传的数据供后续测试使用
            return result.get('data', [])
        else:
            print(f"❌ 上传失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return None
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)


def test_batch_matching(materials_data):
    """测试批量匹配API"""
    print("\n" + "=" * 60)
    print("🔍 测试批量匹配API")
    print("=" * 60)
    
    if not materials_data:
        print("❌ 没有材料数据进行测试")
        return
    
    test_payload = {
        "materials": materials_data,
        "template": "universal-manufacturing"
    }
    
    print(f"📤 发送数据:")
    print(f"   材料数量: {len(materials_data)}")
    print(f"   模板: {test_payload['template']}")
    print(f"   材料样本: {json.dumps(materials_data[:2], ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            'http://127.0.0.1:5001/api/batch_material_matching',
            json=test_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 匹配请求成功")
            print(f"📊 成功状态: {result.get('success', False)}")
            print(f"📋 结果数量: {len(result.get('results', []))}")
            print(f"📈 总计: {result.get('total', 0)}")
            
            if result.get('results'):
                print("🎯 匹配结果样本:")
                for i, match in enumerate(result['results'][:2]):
                    print(f"   [{i+1}] {match.get('material_name', 'N/A')} -> {match.get('classification', 'N/A')} ({match.get('classification_confidence', 0)}%)")
            else:
                print("❌ 没有匹配结果！")
                print("🔍 详细响应:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
        else:
            print(f"❌ 匹配失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 匹配异常: {e}")


def test_direct_api():
    """直接测试API，不依赖文件上传"""
    print("\n" + "=" * 60)
    print("🎯 直接API测试")
    print("=" * 60)
    
    direct_materials = [
        ["M001", "304不锈钢疏水器", "疏水器", "管道配件", "DN25", "", "个"],
        ["M002", "碳钢螺塞", "螺塞", "紧固件", "M8", "", "个"],
        ["M003", "法兰盘", "法兰", "管道配件", "DN100", "", "个"]
    ]
    
    test_payload = {
        "materials": direct_materials,
        "template": "universal-manufacturing"
    }
    
    print(f"📤 直接发送材料数据:")
    print(json.dumps(test_payload, ensure_ascii=False, indent=2))
    
    try:
        response = requests.post(
            'http://127.0.0.1:5001/api/batch_material_matching',
            json=test_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 直接API测试成功")
            print(f"📊 响应数据:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 直接API测试失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 直接API异常: {e}")


def check_workflow_state():
    """检查工作流状态"""
    print("\n" + "=" * 60)
    print("🔄 检查工作流状态")
    print("=" * 60)
    
    try:
        response = requests.get('http://127.0.0.1:5001/api/status')
        if response.status_code == 200:
            result = response.json()
            print("✅ 工作流状态:")
            print(json.dumps(result.get('workflow_status', {}), ensure_ascii=False, indent=2))
        else:
            print(f"❌ 状态检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 状态检查异常: {e}")


def main():
    """主测试流程"""
    print("🔬 MMP工作流数据流调试工具")
    print("检查从文件上传到算法匹配的完整数据流")
    print("=" * 60)
    
    # 1. 检查工作流状态
    check_workflow_state()
    
    # 2. 测试文件上传
    uploaded_data = test_file_upload()
    
    # 3. 使用上传的数据测试匹配
    if uploaded_data:
        test_batch_matching(uploaded_data)
    
    # 4. 直接测试API（不依赖上传）
    test_direct_api()
    
    print("\n" + "=" * 60)
    print("🏁 数据流调试完成")
    print("=" * 60)
    print("请查看上述输出，定位数据丢失的具体环节")


if __name__ == "__main__":
    main()