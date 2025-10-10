#!/usr/bin/env python3

import requests
import pandas as pd
import io

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
test_file = 'session_flow_test.xlsx'
df.to_excel(test_file, index=False)

print("🧪 会话流程测试")
print("=" * 50)

session = requests.Session()

try:
    # 1. 访问上传页面建立会话
    print("1. 访问上传页面...")
    response = session.get('http://localhost:5001/upload')
    print(f"   状态码: {response.status_code}")
    
    # 2. 上传文件
    print("2. 上传文件...")
    with open(test_file, 'rb') as f:
        files = {'file': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = session.post('http://localhost:5001/upload', files=files)
    
    print(f"   上传状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 文件上传成功: {result.get('file_id', 'N/A')}")
        
        # 3. 立即访问参数提取页面
        print("3. 访问参数提取页面...")
        extract_response = session.get('http://localhost:5001/extract_parameters')
        print(f"   状态码: {extract_response.status_code}")
        
        if extract_response.status_code == 200:
            print("   ✅ 成功访问参数提取页面!")
        elif extract_response.status_code == 302:
            print("   ❌ 被重定向回上传页面")
        else:
            print(f"   ❌ 其他错误: {extract_response.status_code}")
    
    else:
        print(f"   ❌ 上传失败: {response.text}")

except Exception as e:
    print(f"❌ 测试失败: {e}")

finally:
    # 清理
    import os
    if os.path.exists(test_file):
        os.remove(test_file)
        print("🧹 清理测试文件")