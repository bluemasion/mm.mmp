#!/usr/bin/env python3
# start_web_app.py
"""启动MMP Web应用"""

from app.web_app import app

if __name__ == '__main__':
    print("🚀 启动MMP智能分类平台...")
    print("📊 平台地址: http://localhost:5001") 
    print("💡 请在浏览器中访问上述地址进行测试")
    print("🔧 基于数据库的智能分类系统已就绪")
    print("")
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        print("\n👋 平台已停止运行")
    except Exception as e:
        print(f"❌ 启动失败: {e}")