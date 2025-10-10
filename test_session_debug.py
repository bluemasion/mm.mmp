#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试会话数据存储和获取功能
"""

import sys
import os
sys.path.append('.')

from app.web_app import app

def test_session_workflow():
    """测试完整的会话工作流程"""
    
    print("🔍 测试MMP平台会话数据功能")
    print("=" * 50)
    
    with app.test_client() as client:
        # 1. 访问上传页面，建立会话
        print("1. 访问上传页面...")
        response = client.get('/upload')
        print(f"   上传页面状态: HTTP {response.status_code}")
        
        # 2. 模拟文件上传，创建会话数据
        print("\n2. 模拟文件上传...")
        
        # 创建测试文件内容
        import io
        import pandas as pd
        
        test_data = {
            '资产代码': ['TEST001', 'TEST002'],
            '资产名称': ['测试医用口罩', '测试一次性手套'],
            '规格型号': ['N95型', '乳胶L码'],
            '品牌': ['3M', '安思尔'],
            '医保码': ['YB001', 'YB002'],
            '生产厂家名称': ['3M公司', '安思尔公司']
        }
        
        df = pd.DataFrame(test_data)
        
        # 将DataFrame转换为Excel文件的字节流
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        # 上传文件
        upload_response = client.post('/upload', 
                                    data={'file': (excel_buffer, 'test_session.xlsx')},
                                    content_type='multipart/form-data')
        
        print(f"   文件上传状态: HTTP {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            upload_result = upload_response.get_json()
            print(f"   上传成功: file_id={upload_result.get('file_id', 'N/A')}")
            print(f"   映射列数: {len(upload_result.get('mapped_columns', []))}")
        else:
            print(f"   上传失败: {upload_response.get_data(as_text=True)}")
            return
        
        # 3. 直接访问参数提取页面，检查会话数据是否存在
        print("\n3. 访问参数提取页面...")
        extract_response = client.get('/extract_parameters')
        print(f"   参数提取页面状态: HTTP {extract_response.status_code}")
        
        if extract_response.status_code == 200:
            print("   ✅ 成功访问参数提取页面 - 会话数据正常")
        elif extract_response.status_code == 302:
            print("   ❌ 被重定向回上传页面 - 会话数据丢失")
            print(f"   重定向位置: {extract_response.headers.get('Location', 'Unknown')}")
        else:
            print(f"   ❌ 其他错误: HTTP {extract_response.status_code}")
        
        # 4. 检查工作流状态
        print("\n4. 检查工作流状态...")
        status_response = client.get('/api/workflow_status')
        print(f"   工作流状态API: HTTP {status_response.status_code}")
        
        if status_response.status_code == 200:
            status_data = status_response.get_json()
            print(f"   uploaded_data状态: {status_data.get('uploaded_data', False)}")
            print(f"   extraction_results状态: {status_data.get('extraction_results', False)}")
        
        # 5. 测试会话持久性 - 再次访问参数提取页面
        print("\n5. 再次测试参数提取页面...")
        extract_response2 = client.get('/extract_parameters')
        print(f"   第二次访问状态: HTTP {extract_response2.status_code}")
        
        if extract_response2.status_code == 200:
            print("   ✅ 会话数据持久化成功")
            # 检查页面内容
            page_content = extract_response2.get_data(as_text=True)
            if 'uploaded_data' in page_content:
                print("   ✅ 页面包含上传数据信息")
            else:
                print("   ❌ 页面缺少上传数据信息")
        else:
            print("   ❌ 会话数据仍然丢失")

if __name__ == "__main__":
    test_session_workflow()