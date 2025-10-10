# 🚀 MMP系统服务器部署指南

> **MMP物料主数据管理智能应用** 生产环境部署完整指南

## 📋 部署概览

### 系统架构
```
Internet
    ↓
  Nginx (80/443)
    ↓
  MMP App (5001)
    ↓
├── PostgreSQL (5432)
├── Redis (6379)  
└── File Storage
```

### 技术栈
- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx (反向代理 + SSL终结)
- **应用服务器**: Gunicorn + Flask
- **数据库**: PostgreSQL / SQLite
- **缓存**: Redis
- **监控**: Prometheus + Grafana

---

## 🛠️ 快速部署

### 方式一：一键自动部署 (推荐)

```bash
# 1. 下载部署脚本
wget https://raw.githubusercontent.com/your-repo/mmp/main/deploy.sh

# 2. 设置环境变量
export DOMAIN_NAME="your-domain.com"
export EMAIL="your-email@domain.com"

# 3. 执行部署 (需要root权限)
sudo bash deploy.sh
```

### 方式二：手动部署

#### 1. 准备服务器环境

**系统要求**:
- Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- 2核CPU, 4GB内存, 20GB磁盘 (最低)
- 4核CPU, 8GB内存, 50GB磁盘 (推荐)

**安装Docker**:
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# CentOS/RHEL
sudo yum install -y docker docker-compose

# 启动服务
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2. 克隆项目代码

```bash
# 创建部署目录
sudo mkdir -p /opt/mmp
cd /opt/mmp

# 克隆代码
git clone https://github.com/your-username/mmp.git .

# 设置权限
sudo chown -R $USER:$USER /opt/mmp
```

#### 3. 配置环境变量

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**重要配置项**:
```bash
# 应用配置
MMP_SECRET_KEY="your-super-secret-key-change-me"
MMP_DEBUG=false

# 数据库配置
DATABASE_URL="postgresql://mmp_user:strong_password@postgres:5432/mmp"
POSTGRES_PASSWORD="strong_password"

# 域名配置
DOMAIN_NAME="your-domain.com"
```

#### 4. SSL证书配置

**Let's Encrypt免费证书** (推荐):
```bash
# 安装Certbot
sudo apt install certbot

# 获取证书
sudo certbot certonly --standalone \
  -d your-domain.com \
  -d www.your-domain.com \
  --email your-email@domain.com \
  --agree-tos

# 复制证书到项目目录
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
```

**自签名证书** (测试环境):
```bash
# 创建自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=CN/ST=State/L=City/O=Org/OU=Unit/CN=your-domain.com"
```

#### 5. 启动服务

```bash
# 构建镜像
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mmp-app
```

---

## 🔧 配置详解

### Docker Compose服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| **mmp-app** | 5001 | MMP主应用 |
| **nginx** | 80, 443 | Web服务器 |
| **postgres** | 5432 | PostgreSQL数据库 |
| **redis** | 6379 | Redis缓存 |
| **prometheus** | 9090 | 监控系统 (可选) |
| **grafana** | 3000 | 可视化面板 (可选) |

### 环境变量详解

#### 应用配置
```bash
MMP_SECRET_KEY=                 # Flask密钥 (必须修改)
MMP_DEBUG=false                 # 调试模式
MMP_PORT=5001                   # 应用端口
MAX_FILE_SIZE=50MB              # 最大上传文件大小
```

#### 数据库配置
```bash
# PostgreSQL (生产推荐)
DATABASE_URL=postgresql://user:pass@host:port/db
POSTGRES_DB=mmp
POSTGRES_USER=mmp_user  
POSTGRES_PASSWORD=secure_password

# SQLite (小规模部署)
DATABASE_URL=sqlite:///data/production.db
```

#### 安全配置
```bash
CORS_ORIGINS=https://your-domain.com    # CORS允许域名
CSRF_SECRET_KEY=another-secret-key      # CSRF保护密钥
```

### Nginx配置自定义

编辑 `nginx/sites/mmp.conf`:

```nginx
# 修改域名
server_name your-actual-domain.com www.your-actual-domain.com;

# 调整上传限制
client_max_body_size 100M;

# 添加自定义headers
add_header X-Custom-Header "MMP-System";
```

---

## 📊 监控与运维

### 启用监控服务

```bash
# 启动监控服务
docker-compose --profile monitoring up -d

# 访问监控面板
# Prometheus: http://your-domain:9090
# Grafana: http://your-domain:3000 (admin/admin123)
```

### 常用运维命令

```bash
# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart mmp-app

# 查看实时日志
docker-compose logs -f --tail=100 mmp-app

# 进入应用容器
docker-compose exec mmp-app bash

# 数据库备份
docker-compose exec postgres pg_dump -U mmp_user mmp > backup.sql

# 更新应用
git pull origin main
docker-compose build mmp-app
docker-compose up -d mmp-app
```

### 日志管理

**查看不同类型日志**:
```bash
# 应用日志
docker-compose logs mmp-app

# Nginx访问日志
docker-compose logs nginx

# 数据库日志
docker-compose logs postgres

# 系统日志文件位置
ls -la logs/
```

**日志轮转配置** (`/etc/logrotate.d/mmp`):
```
/opt/mmp/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
```

### 备份策略

**自动备份脚本** (已包含在部署中):
```bash
# 手动执行备份
/opt/mmp/scripts/backup.sh

# 查看备份文件
ls -la /opt/mmp/backups/

# 恢复备份
cd /opt/mmp
tar -xzf backups/mmp_backup_20231201_020000.tar.gz
```

---

## 🔒 安全配置

### 防火墙设置

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### SSL证书自动续期

```bash
# 添加自动续期任务
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# 测试续期
sudo certbot renew --dry-run
```

### 数据库安全

```bash
# 修改默认密码
docker-compose exec postgres psql -U postgres
\password postgres

# 限制网络访问 (仅容器内部)
# 在docker-compose.yml中移除postgres的ports配置
```

---

## 🚀 性能优化

### 应用性能调优

**Gunicorn配置** (在Dockerfile中):
```dockerfile
CMD ["gunicorn", 
     "--bind", "0.0.0.0:5001",
     "--workers", "4",                    # CPU核数 * 2 + 1
     "--worker-class", "sync",            # 同步worker
     "--max-requests", "1000",            # 防止内存泄漏
     "--timeout", "120",                  # 请求超时
     "--keep-alive", "5",                 # 连接保持
     "run_app:app"]
```

**Redis缓存优化**:
```bash
# 修改docker-compose.yml中的Redis配置
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### 数据库性能优化

**PostgreSQL配置**:
```bash
# 进入容器修改配置
docker-compose exec postgres psql -U postgres -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
"
```

---

## 🆘 故障排除

### 常见问题

**1. 服务无法启动**
```bash
# 检查端口占用
netstat -tulpn | grep :5001

# 检查Docker服务
sudo systemctl status docker

# 查看详细错误
docker-compose logs mmp-app
```

**2. 数据库连接失败**
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 测试连接
docker-compose exec mmp-app python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
print('数据库连接成功!')
"
```

**3. SSL证书问题**
```bash
# 检查证书有效期
openssl x509 -in ssl/cert.pem -text -noout | grep "Not After"

# 验证证书链
openssl verify -CAfile ssl/cert.pem ssl/cert.pem
```

**4. 文件上传失败**
```bash
# 检查上传目录权限
ls -la uploads/

# 修复权限
sudo chown -R 1000:1000 uploads/
```

### 健康检查

**应用健康检查**:
```bash
# HTTP健康检查
curl -f http://localhost:5001/health

# 详细状态检查
curl http://localhost:5001/api/status
```

**系统资源检查**:
```bash
# 容器资源使用
docker stats

# 磁盘使用
df -h

# 内存使用
free -h
```

---

## 📚 更多资源

### 相关文档
- [MMP用户手册](./MMP_PRD_2025.md)
- [API文档](./api-docs.md)
- [架构设计](./ARCHITECTURE_REFACTORING_PLAN.md)

### 技术支持
- **GitHub Issues**: [项目地址]/issues
- **邮件支持**: support@your-domain.com
- **文档网站**: https://docs.your-domain.com

### 更新日志
查看 [CHANGELOG.md](./CHANGELOG.md) 了解版本更新信息。

---

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](./LICENSE) 文件。