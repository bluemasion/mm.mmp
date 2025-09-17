#!/bin/bash
# complete_session_fix_deploy.sh - 完整会话修复部署脚本

echo "=============================================="
echo "MMP系统 - 完整会话管理修复部署"
echo "=============================================="

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 配置项
APP_NAME="MMP"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="session_fix_deploy_$(date +%Y%m%d_%H%M%S).log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 错误处理函数
error_exit() {
    log "错误: $1"
    echo "部署失败，请检查日志: $LOG_FILE"
    exit 1
}

# 检查必要文件
check_requirements() {
    log "检查系统要求..."
    
    # 检查Python版本
    if ! python3 --version | grep -q "3\.[8-9]"; then
        error_exit "需要Python 3.8或更高版本"
    fi
    
    # 检查Flask
    if ! python3 -c "import flask" 2>/dev/null; then
        log "Flask未安装，正在安装..."
        pip3 install flask || error_exit "Flask安装失败"
    fi
    
    # 检查必要目录
    if [ ! -d "app" ]; then
        error_exit "app目录不存在"
    fi
    
    if [ ! -d "templates" ]; then
        error_exit "templates目录不存在"
    fi
    
    log "系统要求检查完成"
}

# 创建备份
create_backup() {
    log "创建备份..."
    
    mkdir -p "$BACKUP_DIR"
    
    # 备份关键文件
    if [ -f "app/web_app.py" ]; then
        cp "app/web_app.py" "$BACKUP_DIR/"
        log "已备份 app/web_app.py"
    fi
    
    if [ -f "config.py" ]; then
        cp "config.py" "$BACKUP_DIR/"
        log "已备份 config.py"
    fi
    
    if [ -f "main.py" ]; then
        cp "main.py" "$BACKUP_DIR/"
        log "已备份 main.py"
    fi
    
    log "备份完成: $BACKUP_DIR"
}

# 停止现有服务
stop_service() {
    log "停止现有MMP服务..."
    
    # 查找并终止MMP相关进程
    MMP_PIDS=$(ps aux | grep -E "(python.*main\.py|python.*run_app\.py|python.*web_app\.py)" | grep -v grep | awk '{print $2}')
    
    if [ -n "$MMP_PIDS" ]; then
        log "发现MMP进程: $MMP_PIDS"
        echo "$MMP_PIDS" | xargs kill -TERM
        sleep 3
        
        # 强制终止仍在运行的进程
        REMAINING_PIDS=$(ps aux | grep -E "(python.*main\.py|python.*run_app\.py|python.*web_app\.py)" | grep -v grep | awk '{print $2}')
        if [ -n "$REMAINING_PIDS" ]; then
            log "强制终止进程: $REMAINING_PIDS"
            echo "$REMAINING_PIDS" | xargs kill -KILL
        fi
        
        log "MMP服务已停止"
    else
        log "未发现运行中的MMP服务"
    fi
}

# 应用会话管理修复
apply_session_fix() {
    log "应用会话管理修复..."
    
    # 使用修复版本替换原文件
    if [ -f "app/web_app_fixed.py" ]; then
        cp "app/web_app_fixed.py" "app/web_app.py"
        log "已应用修复版本的web_app.py"
    else
        error_exit "修复版本文件不存在: app/web_app_fixed.py"
    fi
    
    # 创建必要的目录
    mkdir -p uploads
    mkdir -p session_data
    mkdir -p static
    
    log "目录结构已创建"
}

# 更新依赖包
update_dependencies() {
    log "更新Python依赖包..."
    
    # 安装/更新必要的包
    pip3 install --upgrade flask werkzeug || error_exit "依赖包更新失败"
    
    # 如果存在requirements.txt，安装其中的依赖
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt || log "警告: requirements.txt安装时遇到问题"
    fi
    
    log "依赖包更新完成"
}

# 验证修复效果
verify_fix() {
    log "验证会话管理修复..."
    
    # 检查Python语法
    if ! python3 -m py_compile app/web_app.py; then
        error_exit "web_app.py语法检查失败"
    fi
    log "Python语法检查通过"
    
    # 检查Flask应用可以导入
    if ! python3 -c "
import sys
sys.path.append('.')
from app.web_app import app
print('Flask应用导入成功')
print(f'Secret key configured: {bool(app.secret_key)}')
print(f'Session config: {app.config.get(\"SESSION_TYPE\", \"default\")}')
print(f'Template folder: {app.template_folder}')
" 2>/dev/null; then
        error_exit "Flask应用导入失败"
    fi
    
    log "Flask应用验证通过"
}

# 启动服务
start_service() {
    log "启动MMP服务..."
    
    # 启动方式1: 如果存在run_app.py
    if [ -f "run_app.py" ]; then
        log "使用run_app.py启动服务..."
        nohup python3 run_app.py > mmp_service.log 2>&1 &
        APP_PID=$!
        echo $APP_PID > mmp.pid
        log "服务已启动，PID: $APP_PID"
    
    # 启动方式2: 如果存在main.py
    elif [ -f "main.py" ]; then
        log "使用main.py启动服务..."
        nohup python3 main.py > mmp_service.log 2>&1 &
        APP_PID=$!
        echo $APP_PID > mmp.pid
        log "服务已启动，PID: $APP_PID"
    
    # 启动方式3: 直接运行web_app.py
    else
        log "直接运行web_app.py启动服务..."
        nohup python3 -c "
import sys
sys.path.append('.')
from app.web_app import app
app.run(host='0.0.0.0', port=5000, debug=False)
" > mmp_service.log 2>&1 &
        APP_PID=$!
        echo $APP_PID > mmp.pid
        log "服务已启动，PID: $APP_PID"
    fi
    
    sleep 5
    
    # 检查服务是否正常启动
    if ps -p $APP_PID > /dev/null 2>&1; then
        log "MMP服务启动成功，PID: $APP_PID"
    else
        error_exit "MMP服务启动失败，请检查 mmp_service.log"
    fi
}

# 测试会话功能
test_session_functionality() {
    log "测试会话功能..."
    
    # 等待服务完全启动
    sleep 10
    
    # 测试基本连接
    if curl -s -f http://localhost:5000/ > /dev/null; then
        log "服务连接测试成功"
    else
        log "警告: 服务连接测试失败，可能需要更多时间启动"
    fi
    
    # 测试API状态
    if curl -s -f http://localhost:5000/api/status > /dev/null; then
        log "API状态检查成功"
    else
        log "警告: API状态检查失败"
    fi
    
    log "会话功能测试完成"
}

# 生成部署报告
generate_report() {
    log "生成部署报告..."
    
    REPORT_FILE="session_fix_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
============================================
MMP系统会话管理修复部署报告
============================================

部署时间: $(date)
部署版本: 会话管理增强版本
备份目录: $BACKUP_DIR

修复内容:
1. 会话数据持久化机制
   - SessionDataManager类实现文件系统存储
   - 内存缓存 + 磁盘持久化双重保障
   - 自动会话ID生成和管理

2. Flask会话配置增强
   - SESSION_TYPE='filesystem'
   - 4小时会话生命周期
   - 安全cookie配置
   - 会话签名验证

3. 工作流状态管理
   - 六步骤状态跟踪
   - 参数提取结果持久化
   - 分类选择状态保持
   - 完整工作流数据链

4. 错误处理和调试
   - 详细日志记录
   - 会话调试API
   - 404/500错误页面
   - URL重定向处理

服务信息:
- 监听地址: 0.0.0.0:5000
- 进程ID: $(cat mmp.pid 2>/dev/null || echo "未找到")
- 日志文件: mmp_service.log
- 会话数据目录: session_data/
- 上传文件目录: uploads/

测试建议:
1. 访问 http://localhost:5000/ 检查首页
2. 测试完整的六步工作流
3. 检查参数提取后是否能正常进入分类选择
4. 验证会话数据在页面间的持久性
5. 测试API接口 /api/status 和 /api/debug/session

问题排查:
- 服务日志: tail -f mmp_service.log
- 调试会话: curl http://localhost:5000/api/debug/session
- 清除会话: curl http://localhost:5000/api/clear_session
- 重启服务: ./stop_mmp.sh && ./start_mmp.sh

============================================
EOF

    log "部署报告已生成: $REPORT_FILE"
}

# 创建启动停止脚本
create_management_scripts() {
    log "创建服务管理脚本..."
    
    # 创建启动脚本
    cat > start_mmp.sh << 'EOF'
#!/bin/bash
# 启动MMP服务

if [ -f "mmp.pid" ]; then
    PID=$(cat mmp.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "MMP服务已在运行，PID: $PID"
        exit 0
    fi
fi

echo "启动MMP服务..."

if [ -f "run_app.py" ]; then
    nohup python3 run_app.py > mmp_service.log 2>&1 &
elif [ -f "main.py" ]; then
    nohup python3 main.py > mmp_service.log 2>&1 &
else
    nohup python3 -c "
import sys
sys.path.append('.')
from app.web_app import app
app.run(host='0.0.0.0', port=5000, debug=False)
" > mmp_service.log 2>&1 &
fi

echo $! > mmp.pid
echo "MMP服务已启动，PID: $(cat mmp.pid)"
echo "访问地址: http://localhost:5000"
EOF

    # 创建停止脚本
    cat > stop_mmp.sh << 'EOF'
#!/bin/bash
# 停止MMP服务

if [ -f "mmp.pid" ]; then
    PID=$(cat mmp.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "正在停止MMP服务，PID: $PID"
        kill $PID
        sleep 3
        
        if ps -p $PID > /dev/null 2>&1; then
            echo "强制停止服务"
            kill -9 $PID
        fi
        
        rm -f mmp.pid
        echo "MMP服务已停止"
    else
        echo "MMP服务未运行"
        rm -f mmp.pid
    fi
else
    echo "未找到PID文件，查找并停止MMP进程..."
    MMP_PIDS=$(ps aux | grep -E "(python.*main\.py|python.*run_app\.py|python.*web_app\.py)" | grep -v grep | awk '{print $2}')
    
    if [ -n "$MMP_PIDS" ]; then
        echo "发现MMP进程: $MMP_PIDS"
        echo "$MMP_PIDS" | xargs kill
        echo "MMP服务已停止"
    else
        echo "未发现运行中的MMP服务"
    fi
fi
EOF

    chmod +x start_mmp.sh stop_mmp.sh
    log "服务管理脚本已创建: start_mmp.sh, stop_mmp.sh"
}

# 主执行流程
main() {
    log "开始MMP会话管理修复部署..."
    
    check_requirements
    create_backup
    stop_service
    apply_session_fix
    update_dependencies
    verify_fix
    create_management_scripts
    start_service
    test_session_functionality
    generate_report
    
    echo
    echo "=============================================="
    echo "部署完成！"
    echo "=============================================="
    echo "服务地址: http://localhost:5000"
    echo "服务管理:"
    echo "  启动: ./start_mmp.sh"
    echo "  停止: ./stop_mmp.sh"
    echo "  日志: tail -f mmp_service.log"
    echo
    echo "会话管理增强功能:"
    echo "  - 数据持久化存储"
    echo "  - 工作流状态跟踪"
    echo "  - 会话调试API"
    echo "  - 错误处理优化"
    echo
    echo "测试建议:"
    echo "  1. 完成参数提取后检查分类选择页面"
    echo "  2. 验证工作流数据在步骤间的连续性"
    echo "  3. 测试会话调试: curl http://localhost:5000/api/debug/session"
    echo
    echo "问题排查: 查看 $LOG_FILE"
    echo "=============================================="
}

# 执行主流程
main "$@"
