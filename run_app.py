#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMP应用启动脚本
从项目根目录启动Flask应用，避免相对导入问题
"""

import sys
import os

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入并启动Flask应用
from app.web_app import app

if __name__ == '__main__':
    print("=" * 50)
    print("  MMP物料主数据管理智能应用")
    print("=" * 50)
    print("启动信息:")
    print(f"- Python版本: {sys.version}")
    print(f"- 工作目录: {current_dir}")
    print(f"- Flask版本: {app.__class__.__module__}")
    print("- 服务地址: http://localhost:5005")
    print("=" * 50)
    
    # 启动Flask应用
    app.run(
        host='0.0.0.0',    # 允许外部访问
        port=5005,         # 使用5005端口避免冲突
        debug=True,        # 开发模式
        threaded=True      # 多线程支持
    )
