#!/usr/bin/env python3
"""测试工作流页面的功能"""

import requests
import re
from bs4 import BeautifulSoup

def test_workflow_page():
    """测试工作流页面"""
    try:
        # 测试页面加载
        response = requests.get('http://localhost:5001/material-workflow')
        print(f"页面状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 页面加载成功")
            
            # 检查HTML结构
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 检查步骤指示器
            steps = soup.find_all(class_="step")
            print(f"✅ 找到 {len(steps)} 个步骤指示器")
            
            # 检查上传区域
            upload_area = soup.find(id="uploadArea")
            if upload_area:
                print("✅ 找到文件上传区域")
            else:
                print("❌ 未找到文件上传区域")
                
            # 检查模板网格
            template_grid = soup.find(id="templateGrid")
            if template_grid:
                print("✅ 找到模板网格容器")
            else:
                print("❌ 未找到模板网格容器")
                
            # 检查JavaScript
            scripts = soup.find_all('script')
            js_found = False
            for script in scripts:
                if script.string and 'WorkflowManager' in script.string:
                    js_found = True
                    break
            
            if js_found:
                print("✅ 找到WorkflowManager JavaScript代码")
            else:
                print("❌ 未找到WorkflowManager JavaScript代码")
                
            # 检查模板字符串语法
            template_literals = re.findall(r'\$\{[^}]+\}', response.text)
            if template_literals:
                print(f"⚠️ 发现 {len(template_literals)} 个可能的模板字符串问题:")
                for i, literal in enumerate(template_literals[:5]):  # 只显示前5个
                    print(f"   {i+1}. {literal}")
            else:
                print("✅ 未发现模板字符串语法问题")
                
        else:
            print(f"❌ 页面加载失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_workflow_page()