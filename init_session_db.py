#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本 - 包含会话管理表
"""

import os
import sys
from pathlib import Path

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.database_session_manager import DatabaseSessionManager

def init_session_tables():
    """初始化会话管理相关的数据库表"""
    db_path = os.path.join(current_dir, 'mmp_database.db')
    
    print("🚀 开始初始化数据库会话管理表...")
    
    try:
        # 创建数据库会话管理器
        session_manager = DatabaseSessionManager(db_path)
        print("✅ 数据库表结构创建成功")
        
        # 清理过期会话（如果有的话）
        session_manager.cleanup_expired_sessions()
        print("🧹 清理过期会话完成")
        
        # 测试基本功能
        test_session_id = "test-session-123"
        session_manager.create_session(test_session_id)
        session_manager.store_data(test_session_id, "test_key", {"message": "数据库会话管理测试"})
        test_data = session_manager.get_data(test_session_id, "test_key")
        
        if test_data and test_data.get("message") == "数据库会话管理测试":
            print("✅ 会话管理功能测试通过")
        else:
            print("❌ 会话管理功能测试失败")
            return False
        
        # 清理测试数据
        session_manager.delete_data(test_session_id)
        
        print("\n📊 数据库表结构信息:")
        print("- sessions: 会话基本信息")
        print("- session_data: 会话数据存储")
        print("- extraction_results: 参数提取结果")
        print("- classification_recommendations: 分类推荐")
        print("- category_selections: 分类选择记录")
        print("- workflow_status: 工作流状态跟踪")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_session_tables()
    if success:
        print("\n🎉 数据库会话管理系统初始化完成！")
    else:
        print("\n💥 数据库初始化失败，请检查错误信息")
        sys.exit(1)