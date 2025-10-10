#!/bin/bash
# MMP应用生产环境启动脚本
# 适用于CentOS 7 Python 3.8环境

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 应用配置
APP_NAME="MMP物料主数据管理系统"
APP_DIR="/path/to/mmp"  # 请修改为实际路径
PYTHON_CMD="python3"
GUNICORN_CMD="gunicorn"
WORKERS=4
BIND_HOST="0.0.0.0"
BIND_PORT="5000"
PID_FILE="/tmp/mmp_app.pid"
LOG_FILE="/var/log/mmp_app.log"
ERROR_LOG="/var/log/mmp_error.log"

# 函数：显示使用方法
show_usage() {
    echo "使用方法: $0 {start|stop|restart|status|logs}"
    echo
    echo "命令说明:"
    echo "  start   - 启动应用"
    echo "  stop    - 停止应用"
    echo "  restart - 重启应用"
    echo "  status  - 查看应用状态"
    echo "  logs    - 查看应用日志"
    echo "  dev     - 开发模式启动"
}

# 函数：检查Python和依赖
check_environment() {
    echo -e "${BLUE}检查运行环境...${NC}"
    
    # 检查Python版本
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo -e "${RED}错误: 未找到 $PYTHON_CMD${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    echo "Python版本: $PYTHON_VERSION"
    
    # 检查是否为Python 3.8+
    if ! $PYTHON_CMD -c "import sys; assert sys.version_info >= (3, 8)" 2>/dev/null; then
        echo -e "${YELLOW}警告: 建议使用Python 3.8或更高版本${NC}"
    fi
    
    # 检查Flask是否可用
    if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
        echo -e "${RED}错误: Flask未安装，请运行: pip3 install -r requirements.txt${NC}"
        exit 1
    fi
    
    # 检查应用目录
    if [[ ! -d "$APP_DIR" ]]; then
        echo -e "${RED}错误: 应用目录不存在: $APP_DIR${NC}"
        echo "请修改脚本中的APP_DIR变量"
        exit 1
    fi
    
    # 检查应用文件
    if [[ ! -f "$APP_DIR/run_app.py" ]]; then
        echo -e "${RED}错误: 启动文件不存在: $APP_DIR/run_app.py${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 环境检查通过${NC}"
}

# 函数：启动应用
start_app() {
    echo -e "${BLUE}启动 $APP_NAME...${NC}"
    
    # 检查是否已经运行
    if [[ -f "$PID_FILE" ]] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${YELLOW}应用已经在运行中 (PID: $(cat $PID_FILE))${NC}"
        return 1
    fi
    
    # 切换到应用目录
    cd "$APP_DIR"
    
    # 创建日志目录
    sudo mkdir -p $(dirname "$LOG_FILE") 2>/dev/null || true
    sudo mkdir -p $(dirname "$ERROR_LOG") 2>/dev/null || true
    
    # 检查是否安装了gunicorn
    if command -v $GUNICORN_CMD &> /dev/null; then
        echo "使用Gunicorn启动应用..."
        
        # 使用Gunicorn启动
        $GUNICORN_CMD \
            --workers $WORKERS \
            --bind $BIND_HOST:$BIND_PORT \
            --daemon \
            --pid $PID_FILE \
            --access-logfile $LOG_FILE \
            --error-logfile $ERROR_LOG \
            --capture-output \
            --enable-stdio-inheritance \
            run_app:app
        
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}✓ 应用启动成功${NC}"
            echo "- 访问地址: http://$BIND_HOST:$BIND_PORT"
            echo "- PID文件: $PID_FILE"
            echo "- 日志文件: $LOG_FILE"
            echo "- 错误日志: $ERROR_LOG"
        else
            echo -e "${RED}❌ 应用启动失败${NC}"
            return 1
        fi
    else
        echo "使用Python直接启动应用..."
        
        # 使用nohup后台启动
        nohup $PYTHON_CMD run_app.py > $LOG_FILE 2> $ERROR_LOG &
        APP_PID=$!
        echo $APP_PID > $PID_FILE
        
        # 等待一下检查是否启动成功
        sleep 2
        if kill -0 $APP_PID 2>/dev/null; then
            echo -e "${GREEN}✓ 应用启动成功${NC}"
            echo "- 访问地址: http://$BIND_HOST:$BIND_PORT"
            echo "- 进程PID: $APP_PID"
            echo "- 日志文件: $LOG_FILE"
        else
            echo -e "${RED}❌ 应用启动失败${NC}"
            rm -f $PID_FILE
            return 1
        fi
    fi
}

# 函数：停止应用
stop_app() {
    echo -e "${BLUE}停止 $APP_NAME...${NC}"
    
    if [[ ! -f "$PID_FILE" ]]; then
        echo -e "${YELLOW}PID文件不存在，应用可能未运行${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if kill -0 $PID 2>/dev/null; then
        echo "停止进程 $PID..."
        kill $PID
        
        # 等待进程退出
        for i in {1..10}; do
            if ! kill -0 $PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # 如果还没退出，强制杀死
        if kill -0 $PID 2>/dev/null; then
            echo "强制停止进程..."
            kill -9 $PID
        fi
        
        rm -f $PID_FILE
        echo -e "${GREEN}✓ 应用已停止${NC}"
    else
        echo -e "${YELLOW}进程 $PID 不存在${NC}"
        rm -f $PID_FILE
    fi
}

# 函数：查看应用状态
show_status() {
    echo -e "${BLUE}$APP_NAME 运行状态:${NC}"
    echo
    
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo -e "${GREEN}✓ 应用正在运行${NC}"
            echo "- 进程PID: $PID"
            echo "- 启动时间: $(ps -o lstart= -p $PID 2>/dev/null)"
            echo "- 内存使用: $(ps -o rss= -p $PID 2>/dev/null | awk '{printf "%.1f MB", $1/1024}' 2>/dev/null)"
            
            # 检查端口是否监听
            if command -v netstat &> /dev/null; then
                if netstat -tuln | grep -q ":$BIND_PORT "; then
                    echo -e "- 端口状态: ${GREEN}$BIND_PORT 正在监听${NC}"
                else
                    echo -e "- 端口状态: ${YELLOW}$BIND_PORT 未监听${NC}"
                fi
            fi
            
            # 检查HTTP响应
            if command -v curl &> /dev/null; then
                HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$BIND_PORT/ --connect-timeout 5 2>/dev/null)
                if [[ "$HTTP_STATUS" == "200" ]]; then
                    echo -e "- HTTP状态: ${GREEN}正常 ($HTTP_STATUS)${NC}"
                else
                    echo -e "- HTTP状态: ${YELLOW}异常 ($HTTP_STATUS)${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ 应用未运行 (PID文件存在但进程不存在)${NC}"
            rm -f $PID_FILE
        fi
    else
        echo -e "${YELLOW}⚠ 应用未运行 (PID文件不存在)${NC}"
    fi
    
    echo
    echo "日志文件:"
    echo "- 访问日志: $LOG_FILE"
    echo "- 错误日志: $ERROR_LOG"
}

# 函数：查看日志
show_logs() {
    echo -e "${BLUE}查看 $APP_NAME 日志:${NC}"
    echo
    
    if [[ -f "$LOG_FILE" ]]; then
        echo -e "${GREEN}=== 访问日志 (最后20行) ===${NC}"
        tail -20 "$LOG_FILE"
        echo
    fi
    
    if [[ -f "$ERROR_LOG" ]]; then
        echo -e "${RED}=== 错误日志 (最后20行) ===${NC}"
        tail -20 "$ERROR_LOG"
        echo
    fi
    
    if [[ ! -f "$LOG_FILE" ]] && [[ ! -f "$ERROR_LOG" ]]; then
        echo -e "${YELLOW}日志文件不存在${NC}"
    fi
}

# 函数：开发模式启动
dev_start() {
    echo -e "${BLUE}以开发模式启动 $APP_NAME...${NC}"
    
    # 检查是否已经运行
    if [[ -f "$PID_FILE" ]] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${YELLOW}应用已在运行，请先停止${NC}"
        return 1
    fi
    
    # 切换到应用目录
    cd "$APP_DIR"
    
    echo "使用开发模式启动应用..."
    echo "- 地址: http://localhost:5000"
    echo "- 模式: 开发模式 (调试开启)"
    echo "- 按 Ctrl+C 停止应用"
    echo
    
    # 直接运行，不后台
    $PYTHON_CMD run_app.py
}

# 主逻辑
case "$1" in
    start)
        check_environment
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        check_environment
        stop_app
        sleep 2
        start_app
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    dev)
        check_environment
        dev_start
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
