# CentOS 7 Python 3.8 升级指南

## 🚀 CentOS 7 升级 Python 3.6 → 3.8 完整指南

### 📋 升级前准备

```bash
# 检查当前系统和Python版本
cat /etc/redhat-release
python3.6 --version
which python3.6

# 检查现有Python安装
rpm -qa | grep python3
yum list installed | grep python3
```

### 🛠️ 方法一：使用EPEL和SCL仓库（推荐）

#### 1. 安装必要的仓库和工具

```bash
# 安装EPEL仓库
sudo yum install -y epel-release

# 安装CentOS SCL仓库
sudo yum install -y centos-release-scl

# 更新系统
sudo yum update -y

# 安装开发工具
sudo yum groupinstall -y "Development Tools"
sudo yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel
```

#### 2. 安装Python 3.8

```bash
# 方式A: 使用SCL仓库安装Python 3.8
sudo yum install -y rh-python38

# 启用Python 3.8环境
scl enable rh-python38 bash

# 验证安装
python3 --version  # 应该显示 Python 3.8.x

# 方式B: 如果SCL仓库没有Python 3.8，使用IUS仓库
sudo yum install -y https://repo.ius.io/ius-release-el7.rpm
sudo yum install -y python38 python38-pip python38-devel
```

#### 3. 配置Python 3.8为默认版本

```bash
# 创建符号链接
sudo alternatives --install /usr/bin/python3 python3 /opt/rh/rh-python38/root/usr/bin/python3 1
sudo alternatives --install /usr/bin/pip3 pip3 /opt/rh/rh-python38/root/usr/bin/pip3 1

# 或者如果使用IUS安装
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
sudo alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.8 1

# 验证
python3 --version
pip3 --version
```

### 🔧 方法二：源码编译安装（备选方案）

#### 1. 下载和编译Python 3.8

```bash
# 安装编译依赖
sudo yum install -y gcc gcc-c++ make zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel libffi-devel

# 下载Python 3.8源码
cd /tmp
wget https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz
tar xzf Python-3.8.10.tgz
cd Python-3.8.10

# 配置编译选项
./configure --enable-optimizations --prefix=/usr/local/python38

# 编译安装（这个过程需要较长时间）
make -j$(nproc)
sudo make altinstall

# 创建符号链接
sudo ln -sf /usr/local/python38/bin/python3.8 /usr/bin/python3.8
sudo ln -sf /usr/local/python38/bin/pip3.8 /usr/bin/pip3.8
```

### 🎯 推荐方案：使用pyenv管理多版本Python

```bash
# 安装pyenv依赖
sudo yum install -y git gcc gcc-c++ make zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel libffi-devel

# 安装pyenv
curl https://pyenv.run | bash

# 添加到shell配置
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# 重新加载shell配置
source ~/.bashrc

# 安装Python 3.8.10
pyenv install 3.8.10

# 设置全局Python版本
pyenv global 3.8.10

# 验证
python --version
```

### 📦 MMP项目迁移步骤

#### 1. 备份现有环境

```bash
# 进入MMP项目目录
cd /path/to/mmp

# 备份当前安装的包列表
pip3.6 freeze > backup_requirements_py36.txt

# 备份项目（可选）
cp -r /path/to/mmp /path/to/mmp_backup
```

#### 2. 使用Python 3.8重新部署

```bash
# 确认Python 3.8可用
python3.8 --version || python3 --version

# 升级pip
python3.8 -m pip install --upgrade pip

# 创建虚拟环境（推荐）
python3.8 -m venv venv38
source venv38/bin/activate

# 安装MMP依赖（使用原版requirements.txt）
pip install -r requirements.txt

# 验证关键包安装
python -c "import flask; print('Flask版本:', flask.__version__)"
python -c "import pandas; print('Pandas版本:', pandas.__version__)"
python -c "import sklearn; print('Scikit-learn版本:', sklearn.__version__)"
```

#### 3. 测试应用启动

```bash
# 启动应用测试
python app/web_app.py

# 如果需要后台运行
nohup python app/web_app.py > app.log 2>&1 &

# 检查是否正常运行
curl http://localhost:5000/
```

### 🔍 常见问题解决

#### 问题1: SSL证书错误
```bash
# 更新CA证书
sudo yum update -y ca-certificates

# 或者使用--trusted-host参数
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

#### 问题2: 编译错误
```bash
# 安装完整的开发工具包
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python38-devel

# 检查gcc版本
gcc --version
```

#### 问题3: 权限问题
```bash
# 使用--user参数安装
pip install --user -r requirements.txt

# 或者修改pip目录权限
sudo chown -R $USER:$USER ~/.local
```

### 🚀 一键升级脚本

创建自动化升级脚本：

```bash
#!/bin/bash
# upgrade_python38_centos7.sh

set -e  # 遇到错误时退出

echo "==================================="
echo "CentOS 7 Python 3.8 升级脚本"
echo "==================================="

# 检查系统版本
if ! grep -q "CentOS Linux release 7" /etc/redhat-release; then
    echo "警告: 此脚本专为CentOS 7设计"
fi

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo "请使用sudo权限运行此脚本"
   exit 1
fi

echo "1. 安装必要仓库和工具..."
yum install -y epel-release centos-release-scl
yum groupinstall -y "Development Tools"
yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel libffi-devel

echo "2. 安装Python 3.8..."
# 尝试从SCL安装
if yum install -y rh-python38; then
    echo "Python 3.8 通过SCL安装成功"
    PYTHON_PATH="/opt/rh/rh-python38/root/usr/bin/python3"
    PIP_PATH="/opt/rh/rh-python38/root/usr/bin/pip3"
else
    # 备选：从IUS安装
    echo "尝试从IUS仓库安装..."
    yum install -y https://repo.ius.io/ius-release-el7.rpm
    yum install -y python38 python38-pip python38-devel
    PYTHON_PATH="/usr/bin/python3.8"
    PIP_PATH="/usr/bin/pip3.8"
fi

echo "3. 配置Python 3.8..."
alternatives --install /usr/bin/python3 python3 $PYTHON_PATH 1
alternatives --install /usr/bin/pip3 pip3 $PIP_PATH 1

echo "4. 验证安装..."
python3 --version
pip3 --version

echo "Python 3.8 升级完成！"
echo "现在可以使用 python3 和 pip3 命令"
```

### 📋 升级后验证清单

```bash
# 运行验证脚本
cat > verify_python38.sh << 'EOF'
#!/bin/bash
echo "Python 3.8 升级验证"
echo "==================="

echo "1. Python版本检查:"
python3 --version
echo

echo "2. pip版本检查:"
pip3 --version
echo

echo "3. 关键包安装测试:"
python3 -c "
try:
    import sys
    print(f'Python版本: {sys.version}')
    
    import flask
    print(f'Flask: {flask.__version__}')
    
    import pandas
    print(f'Pandas: {pandas.__version__}')
    
    import sklearn
    print(f'Scikit-learn: {sklearn.__version__}')
    
    print('✅ 所有关键包导入成功')
except ImportError as e:
    print(f'❌ 导入失败: {e}')
"

echo "4. MMP应用测试:"
cd /path/to/mmp
python3 -c "
try:
    from app.web_app import app
    print('✅ MMP应用导入成功')
except Exception as e:
    print(f'❌ MMP应用导入失败: {e}')
"
EOF

chmod +x verify_python38.sh
./verify_python38.sh
```

### 🎯 完整部署命令

执行以下命令完成整个升级过程：

```bash
# 1. 运行升级脚本（需要sudo权限）
sudo bash upgrade_python38_centos7.sh

# 2. 切换到MMP项目目录
cd /path/to/mmp

# 3. 创建Python 3.8虚拟环境
python3 -m venv venv38
source venv38/bin/activate

# 4. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 5. 启动应用
python app/web_app.py
```

升级完成后，您就可以享受Python 3.8的完整功能和更好的性能了！
