#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
上下文生成器验证脚本
验证项目上下文快照的完整性和准确性
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path

def validate_context_snapshot():
    """验证最新的上下文快照"""
    
    print("🔍 验证项目上下文快照...")
    
    # 查找最新的快照文件
    snapshot_files = []
    for file in os.listdir('.'):
        if file.startswith('PROJECT_CONTEXT_SNAPSHOT_') and file.endswith('.md'):
            snapshot_files.append(file)
    
    if not snapshot_files:
        print("❌ 未找到上下文快照文件")
        return False
    
    latest_snapshot = max(snapshot_files)
    print(f"📄 最新快照文件: {latest_snapshot}")
    
    # 验证文件内容
    with open(latest_snapshot, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查必需的章节
    required_sections = [
        "🎯 项目概览",
        "📚 核心文档摘要", 
        "🏗️ 代码结构概览",
        "💾 数据库结构",
        "📊 项目统计",
        "🔄 最近变更",
        "🎯 开发上下文"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ 缺失必需章节: {missing_sections}")
        return False
    
    # 验证数据库信息
    databases = ['mmp_database.db', 'master_data.db', 'training_data.db', 'business_data.db', 'sessions.db']
    for db in databases:
        if db in content:
            print(f"✅ 包含数据库结构: {db}")
        else:
            print(f"⚠️  未包含数据库: {db}")
    
    # 统计信息
    lines = content.split('\n')
    print(f"📏 快照总行数: {len(lines)}")
    print(f"📊 文件大小: {len(content.encode('utf-8')) / 1024:.1f} KB")
    
    # 验证最近变更部分
    if "最近变更" in content:
        print("✅ 包含最近文件变更信息")
    
    print("✅ 上下文快照验证完成")
    return True

def test_context_generator():
    """测试上下文生成器功能"""
    
    print("\n🧪 测试上下文生成器...")
    
    # 执行生成器
    result = os.system("python project_context_generator.py")
    
    if result == 0:
        print("✅ 上下文生成器执行成功")
        return validate_context_snapshot()
    else:
        print("❌ 上下文生成器执行失败")
        return False

def compare_snapshots():
    """比较两个最新的快照差异"""
    
    print("\n🔄 比较快照差异...")
    
    # 获取所有快照文件
    snapshot_files = []
    for file in os.listdir('.'):
        if file.startswith('PROJECT_CONTEXT_SNAPSHOT_') and file.endswith('.md'):
            snapshot_files.append(file)
    
    if len(snapshot_files) < 2:
        print("ℹ️  快照文件少于2个，无法比较")
        return
    
    # 排序并取最新的两个
    snapshot_files.sort()
    latest = snapshot_files[-1] 
    previous = snapshot_files[-2]
    
    print(f"📄 比较文件: {previous} vs {latest}")
    
    # 读取文件
    with open(previous, 'r', encoding='utf-8') as f:
        prev_content = f.read()
    
    with open(latest, 'r', encoding='utf-8') as f:
        latest_content = f.read()
    
    # 简单比较
    if prev_content == latest_content:
        print("🔄 两个快照内容相同")
    else:
        print("🔄 检测到快照差异")
        prev_lines = len(prev_content.split('\n'))
        latest_lines = len(latest_content.split('\n'))
        print(f"   行数变化: {prev_lines} -> {latest_lines} ({latest_lines - prev_lines:+d})")
        
        prev_size = len(prev_content.encode('utf-8'))
        latest_size = len(latest_content.encode('utf-8'))
        print(f"   大小变化: {prev_size} -> {latest_size} ({latest_size - prev_size:+d} bytes)")

def check_project_health():
    """检查项目健康状况"""
    
    print("\n💊 检查项目健康状况...")
    
    issues = []
    
    # 检查核心文件
    core_files = [
        'project_context_generator.py',
        'app/web_app.py',
        'app/intelligent_classifier.py',
        'main.py'
    ]
    
    for file in core_files:
        if os.path.exists(file):
            print(f"✅ 核心文件存在: {file}")
        else:
            issues.append(f"缺失核心文件: {file}")
            print(f"❌ 缺失核心文件: {file}")
    
    # 检查数据库文件
    databases = ['mmp_database.db', 'master_data.db', 'training_data.db', 'business_data.db', 'sessions.db']
    for db in databases:
        if os.path.exists(db):
            try:
                conn = sqlite3.connect(db)
                tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                print(f"✅ 数据库正常: {db} ({len(tables)}个表)")
                conn.close()
            except Exception as e:
                issues.append(f"数据库错误 {db}: {str(e)}")
        else:
            issues.append(f"缺失数据库: {db}")
            print(f"⚠️  数据库不存在: {db}")
    
    # 汇总
    if issues:
        print(f"\n⚠️  发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("\n✅ 项目健康状况良好")

def main():
    """主函数"""
    
    print("🚀 MMP项目上下文验证工具")
    print("=" * 50)
    
    # 检查是否在项目根目录
    if not os.path.exists('project_context_generator.py'):
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    try:
        # 运行所有测试
        test_context_generator()
        compare_snapshots() 
        check_project_health()
        
        print("\n" + "=" * 50)
        print("✅ 验证完成")
        
    except Exception as e:
        print(f"\n❌ 验证过程中出现错误: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())