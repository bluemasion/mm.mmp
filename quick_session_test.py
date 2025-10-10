#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的会话数据测试
"""

import sys
import os
sys.path.append('.')

import requests
import pandas as pd
import io

def test_session_flow():
    """测试完整的会话流程"""
    
    print("🔍 测试会话流程")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    
    try:
        # 1. 创建会话并上传文件
        print("1. 测试文件上传...")
        
        # 创建测试数据
        test_data = {
            '资产代码': ['TEST001', 'TEST002'],
            '资产名称': ['测试医用口罩', '测试一次性手套'],  
            '规格型号': ['N95型', '乳胶L码'],
            '品牌': ['3M', '安思尔'],
            '医保码': ['YB001', 'YB002'],
            '生产厂家名称': ['3M公司', '安思尔公司']
        }
        
        df = pd.DataFrame(test_data)
        
        # 保存为临时文件
        test_file = 'temp_session_test.xlsx'
        df.to_excel(test_file, index=False)
        
        # 上传文件
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(f'{base_url}/upload', files=files, timeout=30)
        
        print(f"   上传状态: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 文件上传成功: file_id={result.get('file_id', 'N/A')}")
            
            # 获取会话cookie
            session_cookie = response.cookies.get('session')
            print(f"   会话Cookie: {session_cookie[:20] if session_cookie else 'None'}...")
            
        else:
            print(f"   ❌ 上传失败: {response.text}")
            return
        
        # 2. 使用相同会话访问参数提取页面
        print("\\n2. 测试参数提取页面访问...")
        
        # 保持会话cookie
        cookies = response.cookies
        extract_response = requests.get(f'{base_url}/extract_parameters', cookies=cookies, timeout=10)
        
        print(f"   参数提取页面状态: HTTP {extract_response.status_code}")
        
        if extract_response.status_code == 200:
            print("   ✅ 成功访问参数提取页面 - 会话数据正常")
            
            # 检查页面内容
            if 'uploaded_data' in extract_response.text:
                print("   ✅ 页面包含上传数据信息") 
            else:
                print("   ⚠️ 页面可能缺少上传数据信息")
                
        elif extract_response.status_code == 302:
            print("   ❌ 被重定向 - 会话数据可能丢失")
            redirect_location = extract_response.headers.get('Location', 'Unknown')
            print(f"   重定向到: {redirect_location}")
            
        else:
            print(f"   ❌ 其他错误: HTTP {extract_response.status_code}")
        
        # 3. 测试工作流状态API
        print("\\n3. 检查工作流状态...")
        
        status_response = requests.get(f'{base_url}/api/workflow_status', cookies=cookies, timeout=10)
        print(f"   工作流状态API: HTTP {status_response.status_code}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   uploaded_data: {status_data.get('uploaded_data', False)}")
            print(f"   extraction_results: {status_data.get('extraction_results', False)}")
            print(f"   category_selections: {status_data.get('category_selections', False)}")
        
        # 清理临时文件
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_session_flow()