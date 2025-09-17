#!/bin/bash
# start_mmp_py38.sh - 使用Python 3.8启动MMP服务

echo "=========================================="
echo "MMP服务启动 - Python 3.8版本"
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 停止现有服务
echo "停止现有服务..."
pkill -f "python.*web_app\|python.*main\|python.*run_app" 2>/dev/null || echo "没有运行的服务"

# 检查Python 3.8
if ! python3.8 --version >/dev/null 2>&1; then
    echo "❌ Python 3.8 未安装"
    exit 1
fi

echo "✅ Python版本: $(python3.8 --version)"

# 检查Flask
if ! python3.8 -c "import flask" 2>/dev/null; then
    echo "❌ Flask未安装，正在安装..."
    python3.8 -m pip install flask werkzeug
fi

# 创建必要目录
mkdir -p uploads session_data static

# 检查文件
if [ ! -f "app/web_app.py" ]; then
    echo "❌ app/web_app.py 不存在"
    exit 1
fi

# 语法检查
echo "🔍 检查语法..."
if ! python3.8 -m py_compile app/web_app.py; then
    echo "❌ 语法错误"
    exit 1
fi
echo "✅ 语法检查通过"

# 启动服务
echo "🚀 启动MMP服务..."
if [ -f "run_app.py" ]; then
    nohup python3.8 run_app.py > mmp_service_py38.log 2>&1 &
elif [ -f "main.py" ]; then
    nohup python3.8 main.py > mmp_service_py38.log 2>&1 &
else
    nohup python3.8 app/web_app.py > mmp_service_py38.log 2>&1 &
fi

APP_PID=$!
echo $APP_PID > mmp_py38.pid

sleep 3

# 检查服务状态
if ps -p $APP_PID > /dev/null 2>&1; then
    echo "✅ 服务启动成功!"
    echo "📋 进程ID: $APP_PID"
    echo "🌐 访问地址: http://localhost:5001"
    echo "📝 日志文件: mmp_service_py38.log"
    echo ""
    echo "管理命令:"
    echo "  查看日志: tail -f mmp_service_py38.log"
    echo "  停止服务: kill $APP_PID"
    echo "  调试接口: curl http://localhost:5001/api/debug/session"
else
    echo "❌ 服务启动失败"
    echo "查看日志:"
    tail -20 mmp_service_py38.log
    exit 1
fi
