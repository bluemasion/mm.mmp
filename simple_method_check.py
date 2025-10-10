#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试 - 验证enhanced_category_matching方法是否已添加
"""

import os
import sys

def simple_test():
    print("=== 简单验证enhanced_category_matching方法 ===")
    
    # 直接读取文件内容检查方法是否存在
    classifier_file = '/Users/mason/Desktop/code /mmp/app/intelligent_classifier.py'
    
    try:
        with open(classifier_file, 'r') as f:
            content = f.read()
            
        # 检查方法是否存在
        if 'def enhanced_category_matching(' in content:
            print("✅ enhanced_category_matching方法已存在")
            
            # 检查方法被调用的地方
            if 'enhanced_recommendations = self.enhanced_category_matching(material_info)' in content:
                print("✅ enhanced_category_matching方法已被正确调用")
            else:
                print("❌ enhanced_category_matching方法未被调用")
                
            # 统计代码行数
            method_start = content.find('def enhanced_category_matching(')
            if method_start != -1:
                method_content = content[method_start:content.find('def recommend_categories(', method_start)]
                method_lines = len(method_content.split('\n'))
                print("✅ enhanced_category_matching方法代码行数:", method_lines)
                
            print("\n=== 方法签名检查 ===")
            # 提取方法签名
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'def enhanced_category_matching(' in line:
                    print("方法签名:", line.strip())
                    # 显示接下来几行的文档字符串
                    for j in range(1, 6):
                        if i + j < len(lines):
                            next_line = lines[i + j].strip()
                            if next_line:
                                print("    ", next_line)
                            if '"""' in next_line and j > 1:
                                break
                    break
            
            print("\n🎉 增强分类器方法修复验证完成！")
            return True
        else:
            print("❌ enhanced_category_matching方法不存在")
            return False
            
    except Exception as e:
        print("❌ 读取文件失败:", e)
        return False

if __name__ == "__main__":
    simple_test()