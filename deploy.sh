#!/bin/bash
# MMP系统服务器部署脚本
# 适用于 Ubuntu 20.04+ / CentOS 8+ / Debian 11+

set -e

# 配置变量
PROJECT_NAME="mmp"
DEPLOY_USER="mmp"
DEPLOY_DIR="/opt/mmp"
DOMAIN_NAME="${DOMAIN_NAME:-your-domain.com}"
EMAIL="${EMAIL:-admin@your-domain.com}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
    else
        error "无法检测操作系统版本"
    fi
    log "检测到操作系统: $OS $VERSION"
}

# 检查root权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "此脚本需要root权限运行"
    fi
}

# 安装Docker和Docker Compose
install_docker() {
    log "安装Docker和Docker Compose..."
    
    if command -v docker &> /dev/null; then
        log "Docker已安装，版本: $(docker --version)"
    else
        # 安装Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        
        # 启动Docker服务
        systemctl start docker
        systemctl enable docker
        
        log "Docker安装完成"
    fi
    
    # 安装Docker Compose
    if command -v docker-compose &> /dev/null; then
        log "Docker Compose已安装，版本: $(docker-compose --version)"
    else
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        log "Docker Compose安装完成"
    fi
}

# 创建部署用户
create_deploy_user() {
    log "创建部署用户: $DEPLOY_USER"
    
    if id "$DEPLOY_USER" &>/dev/null; then
        warn "用户 $DEPLOY_USER 已存在"
    else
        useradd -m -s /bin/bash $DEPLOY_USER
        usermod -aG docker $DEPLOY_USER
        log "用户 $DEPLOY_USER 创建完成"
    fi
}

# 创建项目目录
setup_directories() {
    log "设置项目目录结构..."
    
    mkdir -p $DEPLOY_DIR/{data,logs,uploads,session_data,ssl,backups}
    chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR
    chmod 755 $DEPLOY_DIR
    
    log "目录结构创建完成"
}

# 安装SSL证书 (Let's Encrypt)
install_ssl() {
    log "安装SSL证书..."
    
    if command -v certbot &> /dev/null; then
        log "Certbot已安装"
    else
        # 安装Certbot
        if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
            apt-get update
            apt-get install -y certbot
        elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
            yum install -y certbot
        fi
    fi
    
    # 获取证书
    if [[ ! -f "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" ]]; then
        certbot certonly --standalone --email $EMAIL --agree-tos --no-eff-email -d $DOMAIN_NAME -d www.$DOMAIN_NAME
        
        # 复制证书到项目目录
        cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem $DEPLOY_DIR/ssl/cert.pem
        cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem $DEPLOY_DIR/ssl/key.pem
        chown $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR/ssl/*
        
        log "SSL证书安装完成"
    else
        log "SSL证书已存在"
    fi
}

# 部署应用
deploy_app() {
    log "部署MMP应用..."
    
    # 切换到部署用户
    su - $DEPLOY_USER -c "
        cd $DEPLOY_DIR
        
        # 克隆或更新代码
        if [[ -d .git ]]; then
            git pull origin main
        else
            git clone https://github.com/your-username/mmp.git .
        fi
        
        # 复制环境配置
        if [[ ! -f .env ]]; then
            cp .env.example .env
            echo '请编辑 $DEPLOY_DIR/.env 文件配置生产环境变量'
        fi
        
        # 构建和启动服务
        docker-compose build
        docker-compose up -d
        
        # 等待服务启动
        sleep 10
        
        # 检查服务状态
        docker-compose ps
    "
    
    log "应用部署完成"
}

# 设置防火墙
setup_firewall() {
    log "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw --force enable
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
    fi
    
    log "防火墙配置完成"
}

# 设置系统服务
setup_systemd_service() {
    log "设置系统服务..."
    
    cat > /etc/systemd/system/mmp.service << EOF
[Unit]
Description=MMP Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=$DEPLOY_USER
Group=$DEPLOY_USER

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable mmp.service
    
    log "系统服务设置完成"
}

# 设置自动备份
setup_backup() {
    log "设置自动备份..."
    
    cat > /etc/cron.d/mmp-backup << EOF
# MMP系统每日备份 (凌晨2点)
0 2 * * * $DEPLOY_USER $DEPLOY_DIR/scripts/backup.sh
EOF
    
    # 创建备份脚本
    mkdir -p $DEPLOY_DIR/scripts
    cat > $DEPLOY_DIR/scripts/backup.sh << 'EOF'
#!/bin/bash
# MMP系统备份脚本

BACKUP_DIR="/opt/mmp/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="mmp_backup_$DATE.tar.gz"

cd /opt/mmp

# 备份数据
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude=logs \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    data/ uploads/ session_data/ .env

# 保留最近7天的备份
find "$BACKUP_DIR" -name "mmp_backup_*.tar.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_FILE"
EOF

    chmod +x $DEPLOY_DIR/scripts/backup.sh
    chown $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR/scripts/backup.sh
    
    log "自动备份设置完成"
}

# 主函数
main() {
    log "开始MMP系统服务器部署..."
    
    detect_os
    check_root
    
    log "安装系统依赖..."
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        apt-get update
        apt-get install -y curl wget git unzip
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        yum update -y
        yum install -y curl wget git unzip
    fi
    
    install_docker
    create_deploy_user
    setup_directories
    
    if [[ -n "$DOMAIN_NAME" ]] && [[ "$DOMAIN_NAME" != "your-domain.com" ]]; then
        install_ssl
    else
        warn "跳过SSL证书安装，请设置DOMAIN_NAME环境变量"
    fi
    
    deploy_app
    setup_firewall
    setup_systemd_service
    setup_backup
    
    log "MMP系统部署完成！"
    log "访问地址: https://$DOMAIN_NAME"
    log "管理命令:"
    log "  启动服务: systemctl start mmp"
    log "  停止服务: systemctl stop mmp"
    log "  查看日志: docker-compose -f $DEPLOY_DIR/docker-compose.yml logs -f"
    log "  备份数据: $DEPLOY_DIR/scripts/backup.sh"
}

# 运行主函数
main "$@"