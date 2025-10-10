#!/bin/bash
# MMP物料主数据管理平台后台启动脚本
# 创建时间: 2025-09-28
# 功能: 后台启动MMP Flask应用，支持日志记录和进程管理

# 脚本配置
SCRIPT_NAME="MMP后台启动脚本"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$SCRIPT_DIR"
PYTHON_EXEC="/usr/local/bin/python3.8"
APP_SCRIPT="run_app.py"
LOG_FILE="${PROJECT_DIR}/mmp_service_py38.log"
PID_FILE="${PROJECT_DIR}/mmp_py38.pid"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${msg}${NC}"
}

# 检查进程是否运行
check_process() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            return 0  # 进程存在
        else
            rm -f "$PID_FILE"  # 清理无效的PID文件
            return 1  # 进程不存在
        fi
    fi
    return 1
}

# 停止现有进程
stop_service() {
    print_msg $YELLOW "检查并停止现有MMP服务..."
    
    # 停止通过PID文件记录的进程
    if check_process; then
        local pid=$(cat "$PID_FILE")
        print_msg $YELLOW "发现运行中的MMP服务 (PID: $pid)，正在停止..."
        kill $pid
        sleep 3
        
        # 强制停止
        if ps -p $pid > /dev/null 2>&1; then
            print_msg $YELLOW "强制停止进程..."
            kill -9 $pid
            sleep 1
        fi
        
        rm -f "$PID_FILE"
        print_msg $GREEN "MMP服务已停止"
    fi
    
    # 额外停止所有相关Python进程
    pkill -f "python.*web_app\|python.*main\|python.*run_app" 2>/dev/null || true
    
    # 额外检查端口5001占用
    local port_process=$(lsof -i :5001 2>/dev/null | grep LISTEN | awk '{print $2}' | head -1)
    if [ ! -z "$port_process" ]; then
        print_msg $YELLOW "发现端口5001被进程$port_process占用，正在清理..."
        kill $port_process 2>/dev/null || true
        sleep 2
    fi
}

# 启动服务
start_service() {
    print_msg $BLUE "准备启动MMP服务..."
    
    # 切换到项目目录
    cd "$PROJECT_DIR"
    
    # 检查Python可执行文件
    if ! $PYTHON_EXEC --version >/dev/null 2>&1; then
        print_msg $RED "❌ Python 3.8未安装或路径不正确: $PYTHON_EXEC"
        exit 1
    fi
    
    print_msg $GREEN "✅ Python版本: $($PYTHON_EXEC --version)"
    
    # 检查Flask
    if ! $PYTHON_EXEC -c "import flask" 2>/dev/null; then
        print_msg $YELLOW "⚠️  Flask未安装，正在安装..."
        $PYTHON_EXEC -m pip install flask werkzeug
    fi
    
    # 检查应用脚本
    if [ ! -f "$APP_SCRIPT" ]; then
        print_msg $RED "❌ 应用脚本不存在: $APP_SCRIPT"
        exit 1
    fi
    
    # 检查关键文件
    if [ ! -f "app/web_app.py" ]; then
        print_msg $RED "❌ app/web_app.py 不存在"
        exit 1
    fi
    
    # 创建必要目录
    mkdir -p uploads session_data static backups
    
    # 语法检查
    print_msg $BLUE "🔍 检查语法..."
    if ! $PYTHON_EXEC -m py_compile app/web_app.py; then
        print_msg $RED "❌ 语法错误"
        exit 1
    fi
    print_msg $GREEN "✅ 语法检查通过"
    
    # 创建日志文件
    touch "$LOG_FILE"
    
    print_msg $BLUE "🚀 启动MMP Flask应用..."
    print_msg $BLUE "项目目录: $PROJECT_DIR"
    print_msg $BLUE "日志文件: $LOG_FILE"
    
    # 后台启动应用
    nohup $PYTHON_EXEC $APP_SCRIPT > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # 保存PID
    echo $pid > "$PID_FILE"
    
    print_msg $GREEN "MMP服务已启动 (PID: $pid)"
    print_msg $BLUE "服务地址: http://localhost:5001"
    print_msg $BLUE "日志文件: $LOG_FILE"
    print_msg $BLUE "PID文件: $PID_FILE"
    
    # 等待服务启动
    print_msg $YELLOW "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    if check_process; then
        print_msg $GREEN "✅ MMP服务启动成功!"
        
        # 检查端口监听
        if lsof -i :5001 > /dev/null 2>&1; then
            print_msg $GREEN "✅ 端口5001监听正常"
        else
            print_msg $YELLOW "⚠️  端口5001未检测到监听，请检查日志"
        fi
        
        # 显示管理命令
        print_msg $BLUE "===================="
        print_msg $BLUE "管理命令:"
        print_msg $BLUE "  查看状态: $0 status"
        print_msg $BLUE "  查看日志: $0 logs"
        print_msg $BLUE "  停止服务: $0 stop"
        print_msg $BLUE "  重启服务: $0 restart"
        print_msg $BLUE "===================="
        
        # 显示最新日志
        print_msg $BLUE "=== 最新服务日志 ==="
        tail -10 "$LOG_FILE" 2>/dev/null || echo "暂无日志输出"
        print_msg $BLUE "===================="
        
    else
        print_msg $RED "❌ MMP服务启动失败，请检查日志文件: $LOG_FILE"
        if [ -f "$LOG_FILE" ]; then
            print_msg $RED "错误日志:"
            tail -20 "$LOG_FILE"
        fi
        return 1
    fi
}

# 查看服务状态
status_service() {
    print_msg $BLUE "检查MMP服务状态..."
    
    if check_process; then
        local pid=$(cat "$PID_FILE")
        print_msg $GREEN "✅ MMP服务正在运行 (PID: $pid)"
        
        # 检查端口
        if lsof -i :5001 > /dev/null 2>&1; then
            print_msg $GREEN "✅ 端口5001监听正常"
        else
            print_msg $YELLOW "⚠️  端口5001未监听"
        fi
        
        # 显示进程信息
        echo "进程信息:"
        ps -p $pid -o pid,ppid,%cpu,%mem,cmd 2>/dev/null || echo "无法获取进程信息"
        
        return 0
    else
        print_msg $RED "❌ MMP服务未运行"
        return 1
    fi
}

# 查看日志
view_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_msg $BLUE "=== MMP服务日志 (最近50行) ==="
        tail -50 "$LOG_FILE"
        print_msg $BLUE "================================"
    else
        print_msg $YELLOW "日志文件不存在: $LOG_FILE"
    fi
}

# 重启服务
restart_service() {
    print_msg $BLUE "重启MMP服务..."
    stop_service
    sleep 2
    start_service
}

# 显示使用帮助
show_help() {
    echo "======================================"
    echo "  $SCRIPT_NAME"
    echo "======================================"
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动MMP服务 (默认)"
    echo "  stop      停止MMP服务"  
    echo "  restart   重启MMP服务"
    echo "  status    查看服务状态"
    echo "  logs      查看服务日志"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动服务"
    echo "  $0 status   # 查看状态"
    echo "  $0 logs     # 查看日志"
    echo ""
    echo "服务信息:"
    echo "  服务地址: http://localhost:5001"
    echo "  日志文件: $LOG_FILE"
    echo "  PID文件: $PID_FILE"
    echo "======================================"
}

# 主程序逻辑
main() {
    case "${1:-start}" in
        "start")
            stop_service
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            restart_service
            ;;
        "status")
            status_service
            ;;
        "logs")
            view_logs
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_msg $RED "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 脚本入口
print_msg $BLUE "======================================"
print_msg $BLUE "  $SCRIPT_NAME"  
print_msg $BLUE "======================================"

main "$@"
