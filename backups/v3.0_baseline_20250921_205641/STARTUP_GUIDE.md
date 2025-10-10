# 物料主数据管理智能应用 - 启动指南

## 📋 系统要求

- Python 3.8+
- 8GB+ 内存
- 2GB+ 可用磁盘空间
- 支持的操作系统：Linux/macOS/Windows

## 🚀 快速启动

### 1. 环境准备

```bash
# 1. 进入项目目录
cd /path/to/mmp

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt
```

### 2. 配置检查

```bash
# 检查配置文件
ls -la enhanced_config.py

# 确认数据库配置（如果使用数据库）
# 编辑 enhanced_config.py 中的 DATABASE_CONNECTIONS 部分
```

### 3. 启动应用

#### 方式一：使用主程序启动（推荐生产环境）
```bash
python main.py
```

#### 方式二：使用Web应用启动（开发测试）
```bash
python app/web_app.py
```

#### 方式三：使用Flask命令启动
```bash
export FLASK_APP=app/web_app.py
export FLASK_ENV=development  # 开发环境
flask run --host=0.0.0.0 --port=5000
```

### 4. 访问应用

- 本地访问：http://localhost:5000
- 远程访问：http://your-server-ip:5000
- 默认端口：5000（可在配置中修改）

## 🔧 详细配置说明

### 1. 端口配置

在 `app/web_app.py` 文件末尾修改：
```python
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',      # 监听所有网卡
        port=5000,           # 端口号
        debug=False,         # 生产环境设为False
        threaded=True        # 启用多线程
    )
```

### 2. 数据库配置（可选）

如需使用数据库功能，编辑 `enhanced_config.py`：
```python
DATABASE_CONNECTIONS = {
    'mysql': {
        'host': 'your-mysql-host',
        'port': 3306,
        'database': 'your-database',
        'username': 'your-username',
        'password': 'your-password'
    }
}
```

### 3. 文件上传配置

确保有足够的磁盘空间和权限：
```bash
# 创建上传目录
mkdir -p uploads
chmod 755 uploads

# 检查磁盘空间
df -h
```

## 🏃‍♂️ 生产环境部署

### 1. 使用 Gunicorn（推荐）

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动应用
gunicorn -w 4 -b 0.0.0.0:5000 app.web_app:app

# 后台运行
nohup gunicorn -w 4 -b 0.0.0.0:5000 app.web_app:app > app.log 2>&1 &
```

### 2. 使用 uWSGI

```bash
# 安装 uWSGI
pip install uwsgi

# 创建配置文件 uwsgi.ini
[uwsgi]
module = app.web_app:app
master = true
processes = 4
socket = /tmp/mmp.sock
chmod-socket = 666
vacuum = true
die-on-term = true

# 启动
uwsgi --ini uwsgi.ini
```

### 3. Nginx 反向代理（可选）

```nginx
# /etc/nginx/sites-available/mmp
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/mmp/static;
        expires 30d;
    }

    client_max_body_size 16M;  # 支持文件上传
}
```

## 🔍 启动验证

### 1. 检查服务状态
```bash
# 检查端口是否正在监听
netstat -tlnp | grep :5000
# 或
lsof -i :5000

# 检查进程
ps aux | grep python
```

### 2. 功能测试
访问以下URL确认功能正常：
- 首页：http://your-server:5000/
- 数据导入：http://your-server:5000/upload
- 参数提取：http://your-server:5000/extract_parameters
- 类别选择：http://your-server:5000/categorize

### 3. 日志检查
```bash
# 查看应用日志
tail -f app.log

# 查看系统日志
tail -f /var/log/syslog
```

## 🛠️ 常见问题排查

### 1. 端口被占用
```bash
# 查找占用端口的进程
lsof -i :5000

# 杀死进程
kill -9 PID
```

### 2. 权限问题
```bash
# 给予执行权限
chmod +x main.py
chmod +x app/web_app.py

# 检查目录权限
ls -la
```

### 3. 依赖包问题
```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt

# 检查Python版本
python --version
```

### 4. 内存不足
```bash
# 检查内存使用
free -h

# 检查磁盘空间
df -h
```

## 📊 性能优化建议

### 1. 系统资源配置
- **内存**：建议8GB+，处理大文件时需要更多内存
- **CPU**：多核心有助于并发处理
- **磁盘**：SSD可提升文件处理速度

### 2. 应用配置优化
```python
# 在 web_app.py 中调整
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB上传限制
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'         # 使用快速磁盘
```

### 3. 数据库连接池
```python
# 在 enhanced_config.py 中配置
DATABASE_POOL_SIZE = 10
DATABASE_MAX_OVERFLOW = 20
```

## 🔐 安全配置

### 1. 防火墙设置
```bash
# 开放应用端口
sudo ufw allow 5000

# 限制访问源
sudo ufw allow from specific-ip to any port 5000
```

### 2. SSL证书配置（生产环境）
```python
# 使用HTTPS
app.run(host='0.0.0.0', port=443, ssl_context='adhoc')
```

## 📝 启动脚本示例

创建启动脚本 `start_mmp.sh`：
```bash
#!/bin/bash
# MMP应用启动脚本

# 设置环境变量
export FLASK_APP=app/web_app.py
export FLASK_ENV=production

# 进入项目目录
cd /path/to/mmp

# 激活虚拟环境
source venv/bin/activate

# 启动应用
echo "启动物料主数据管理智能应用..."
python app/web_app.py

# 或使用Gunicorn
# gunicorn -w 4 -b 0.0.0.0:5000 app.web_app:app
```

```bash
# 给予执行权限
chmod +x start_mmp.sh

# 启动应用
./start_mmp.sh
```

## 🎯 快速启动命令总结

```bash
# 一键启动命令
cd /path/to/mmp && python app/web_app.py

# 生产环境启动
cd /path/to/mmp && gunicorn -w 4 -b 0.0.0.0:5000 app.web_app:app

# 后台运行
cd /path/to/mmp && nohup python app/web_app.py > app.log 2>&1 &
```

启动成功后，您就可以通过浏览器访问应用，开始使用物料主数据管理的完整功能了！

## 📞 技术支持

如遇到启动问题，请检查：
1. Python版本和依赖包是否正确安装
2. 端口是否被占用
3. 文件权限是否正确
4. 系统资源是否充足
5. 防火墙和网络配置是否正确
