#!/bin/bash
# CentOS 7 Python 3.8 自动升级脚本
# 使用方法: sudo bash upgrade_python38_centos7.sh

set -e  # 遇到错误时退出

echo "==========================================="
echo "  CentOS 7 Python 3.8 自动升级脚本 v1.0"
echo "==========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查系统版本
check_system() {
    echo -e "${BLUE}检查系统版本...${NC}"
    if ! grep -q "CentOS Linux release 7" /etc/redhat-release 2>/dev/null; then
        echo -e "${YELLOW}警告: 此脚本专为CentOS 7设计，当前系统可能不兼容${NC}"
        echo "当前系统: $(cat /etc/redhat-release 2>/dev/null || echo 'Unknown')"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查权限
check_permissions() {
    echo -e "${BLUE}检查运行权限...${NC}"
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}错误: 请使用sudo权限运行此脚本${NC}"
        echo "使用方法: sudo bash $0"
        exit 1
    fi
    echo -e "${GREEN}✓ 权限检查通过${NC}"
}

# 备份当前Python环境
backup_current_python() {
    echo -e "${BLUE}备份当前Python环境...${NC}"
    
    # 检查当前Python版本
    if command -v python3.6 &> /dev/null; then
        echo "当前Python 3.6版本: $(python3.6 --version)"
        
        # 创建备份目录
        BACKUP_DIR="/tmp/python_backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # 备份已安装的包列表
        if command -v pip3.6 &> /dev/null; then
            pip3.6 freeze > "$BACKUP_DIR/requirements_py36_backup.txt" 2>/dev/null || true
            echo -e "${GREEN}✓ 已备份Python 3.6包列表到: $BACKUP_DIR/requirements_py36_backup.txt${NC}"
        fi
        
        echo -e "${GREEN}✓ 备份完成，备份目录: $BACKUP_DIR${NC}"
    else
        echo -e "${YELLOW}未发现Python 3.6，跳过备份${NC}"
    fi
}

# 安装必要的仓库和工具
install_repositories() {
    echo -e "${BLUE}安装必要的仓库和开发工具...${NC}"
    
    # 安装EPEL仓库
    echo "安装EPEL仓库..."
    yum install -y epel-release
    
    # 安装CentOS SCL仓库
    echo "安装CentOS SCL仓库..."
    yum install -y centos-release-scl
    
    # 更新系统
    echo "更新系统包..."
    yum update -y
    
    # 安装开发工具
    echo "安装开发工具..."
    yum groupinstall -y "Development Tools"
    
    # 安装Python编译依赖
    echo "安装Python编译依赖..."
    yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel \
                   sqlite-devel readline-devel tk-devel gdbm-devel \
                   db4-devel libpcap-devel xz-devel expat-devel libffi-devel
    
    echo -e "${GREEN}✓ 仓库和工具安装完成${NC}"
}

# 安装Python 3.8
install_python38() {
    echo -e "${BLUE}安装Python 3.8...${NC}"
    
    # 方法1: 尝试从SCL安装
    echo "尝试从SCL仓库安装Python 3.8..."
    if yum install -y rh-python38 rh-python38-python-pip rh-python38-python-devel; then
        echo -e "${GREEN}✓ Python 3.8 通过SCL安装成功${NC}"
        PYTHON_PATH="/opt/rh/rh-python38/root/usr/bin/python3"
        PIP_PATH="/opt/rh/rh-python38/root/usr/bin/pip3"
        PYTHON_TYPE="SCL"
        return 0
    fi
    
    # 方法2: 从IUS仓库安装
    echo -e "${YELLOW}SCL安装失败，尝试从IUS仓库安装...${NC}"
    if yum install -y https://repo.ius.io/ius-release-el7.rpm; then
        if yum install -y python38 python38-pip python38-devel; then
            echo -e "${GREEN}✓ Python 3.8 通过IUS安装成功${NC}"
            PYTHON_PATH="/usr/bin/python3.8"
            PIP_PATH="/usr/bin/pip3.8"
            PYTHON_TYPE="IUS"
            return 0
        fi
    fi
    
    echo -e "${RED}❌ Python 3.8 安装失败${NC}"
    echo "请检查网络连接和仓库配置"
    exit 1
}

# 配置Python 3.8
configure_python38() {
    echo -e "${BLUE}配置Python 3.8为默认版本...${NC}"
    
    # 检查Python路径是否存在
    if [[ ! -f "$PYTHON_PATH" ]]; then
        echo -e "${RED}❌ Python路径不存在: $PYTHON_PATH${NC}"
        exit 1
    fi
    
    if [[ ! -f "$PIP_PATH" ]]; then
        echo -e "${RED}❌ pip路径不存在: $PIP_PATH${NC}"
        exit 1
    fi
    
    # 配置alternatives
    alternatives --install /usr/bin/python3 python3 "$PYTHON_PATH" 1
    alternatives --install /usr/bin/pip3 pip3 "$PIP_PATH" 1
    
    # 创建额外的符号链接（可选）
    ln -sf "$PYTHON_PATH" /usr/local/bin/python3.8 2>/dev/null || true
    ln -sf "$PIP_PATH" /usr/local/bin/pip3.8 2>/dev/null || true
    
    echo -e "${GREEN}✓ Python 3.8 配置完成${NC}"
}

# 验证安装
verify_installation() {
    echo -e "${BLUE}验证Python 3.8安装...${NC}"
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        echo "Python版本: $PYTHON_VERSION"
        
        if [[ "$PYTHON_VERSION" == *"3.8"* ]]; then
            echo -e "${GREEN}✓ Python 3.8 安装成功${NC}"
        else
            echo -e "${YELLOW}⚠ Python版本可能不是3.8: $PYTHON_VERSION${NC}"
        fi
    else
        echo -e "${RED}❌ python3 命令不可用${NC}"
        exit 1
    fi
    
    # 检查pip版本
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version 2>&1)
        echo "pip版本: $PIP_VERSION"
        echo -e "${GREEN}✓ pip3 可用${NC}"
    else
        echo -e "${RED}❌ pip3 命令不可用${NC}"
        exit 1
    fi
    
    # 测试基本导入
    echo "测试基本Python功能..."
    if python3 -c "import sys; print(f'Python路径: {sys.executable}'); import ssl; print('✓ SSL支持正常')" 2>/dev/null; then
        echo -e "${GREEN}✓ Python基本功能正常${NC}"
    else
        echo -e "${YELLOW}⚠ Python基本功能测试失败${NC}"
    fi
}

# 安装MMP依赖
install_mmp_dependencies() {
    echo -e "${BLUE}安装MMP项目依赖...${NC}"
    
    # 升级pip
    echo "升级pip..."
    pip3 install --upgrade pip
    
    # 检查requirements.txt是否存在
    if [[ -f "requirements.txt" ]]; then
        echo "安装MMP依赖包..."
        if pip3 install -r requirements.txt; then
            echo -e "${GREEN}✓ MMP依赖安装成功${NC}"
        else
            echo -e "${YELLOW}⚠ 部分依赖安装失败，请手动检查${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ 未找到requirements.txt文件${NC}"
        echo "请手动安装依赖: pip3 install flask pandas scikit-learn"
    fi
}

# 创建启动脚本
create_startup_script() {
    echo -e "${BLUE}创建应用启动脚本...${NC}"
    
    cat > start_mmp.sh << 'EOF'
#!/bin/bash
# MMP应用启动脚本

# 设置Python环境（如果使用SCL）
if [[ -f /opt/rh/rh-python38/enable ]]; then
    source /opt/rh/rh-python38/enable
fi

# 启动应用
echo "启动MMP应用..."
python3 app/web_app.py
EOF

    chmod +x start_mmp.sh
    echo -e "${GREEN}✓ 启动脚本创建完成: start_mmp.sh${NC}"
}

# 显示完成信息
show_completion_info() {
    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    Python 3.8 升级完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo -e "${BLUE}升级信息:${NC}"
    echo "- 安装方式: $PYTHON_TYPE"
    echo "- Python路径: $PYTHON_PATH"
    echo "- pip路径: $PIP_PATH"
    echo
    echo -e "${BLUE}使用方法:${NC}"
    echo "1. 验证安装: python3 --version"
    echo "2. 使用pip: pip3 install package_name"
    
    if [[ "$PYTHON_TYPE" == "SCL" ]]; then
        echo "3. 激活环境: scl enable rh-python38 bash"
    fi
    
    echo
    echo -e "${BLUE}启动MMP应用:${NC}"
    echo "cd /path/to/mmp"
    echo "./start_mmp.sh"
    echo
    echo -e "${YELLOW}注意: 如果遇到问题，请检查防火墙和端口设置${NC}"
}

# 主函数
main() {
    echo -e "${BLUE}开始Python 3.8升级过程...${NC}"
    
    check_system
    check_permissions
    backup_current_python
    install_repositories
    install_python38
    configure_python38
    verify_installation
    
    # 如果在MMP项目目录中，安装依赖
    if [[ -f "app/web_app.py" ]] && [[ -f "requirements.txt" ]]; then
        install_mmp_dependencies
        create_startup_script
    fi
    
    show_completion_info
    
    echo -e "${GREEN}升级脚本执行完成！${NC}"
}

# 运行主函数
main "$@"
