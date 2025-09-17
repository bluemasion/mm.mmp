# Python 3.6 兼容性部署指南

## ⚠️ Python 3.6 兼容性说明

**重要提醒**: 您提到使用Python 3.6，需要注意以下兼容性问题：

### 🔍 版本兼容性分析

❌ **完全不兼容的包**:
- Flask 2.3.3 (最低需要Python 3.8)
- pandas 1.5.0+ (最低需要Python 3.8)
- scikit-learn 1.2.0+ (最低需要Python 3.8)

✅ **提供Python 3.6兼容方案**:
- Flask 1.1.4
- pandas 1.1.5  
- scikit-learn 0.24.2

### 🛠️ Python 3.6 部署步骤

#### 1. 使用兼容版本的依赖包

```bash
# 使用Python 3.6兼容的requirements文件
pip install -r requirements_py36.txt
```

#### 2. 代码调整（类型注解兼容性）

由于Python 3.6对类型注解支持有限，需要做以下调整：

**选项A: 移除类型注解（推荐Python 3.6）**

在 `app/web_app.py` 中：
```python
# 原代码
from typing import Dict, List, Any, Optional

def process_data(data: Dict[str, Any]) -> Optional[List[Dict]]:
    pass

# 修改为
def process_data(data):
    """
    处理数据
    Args:
        data: 输入数据字典
    Returns:
        处理后的数据列表或None
    """
    pass
```

**选项B: 保留类型注解但添加兼容导入**
```python
try:
    from typing import Dict, List, Any, Optional
except ImportError:
    # Python 3.6 fallback
    Dict = dict
    List = list
    Any = object
    Optional = object
```

#### 3. 启动方式

```bash
# 确认Python版本
python3.6 --version

# 进入项目目录
cd /path/to/mmp

# 安装Python 3.6兼容的依赖
pip3.6 install -r requirements_py36.txt

# 启动应用
python3.6 app/web_app.py
```

### 🚨 Python 3.6 限制说明

使用Python 3.6版本将有以下限制：

1. **功能限制**:
   - 深度学习模型支持受限（transformers, torch等不可用）
   - OCR功能可能受限（paddleocr不支持）
   - 部分高级数据处理功能降级

2. **性能影响**:
   - 较老版本的pandas和scikit-learn性能较低
   - 缺少最新的优化特性

3. **安全风险**:
   - 使用较老版本的包，可能存在已知安全漏洞

### 💡 强烈建议升级Python版本

**推荐升级路径**:

1. **Python 3.8** (最低推荐版本)
   - 支持所有功能
   - 更好的性能和安全性

2. **Python 3.9/3.10** (推荐版本)
   - 最佳性能和兼容性
   - 完整功能支持

升级命令参考：
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-pip

# CentOS/RHEL
sudo yum install python38 python38-pip

# 使用pyenv管理多版本Python
curl https://pyenv.run | bash
pyenv install 3.8.10
pyenv global 3.8.10
```

### 🔧 如果必须使用Python 3.6

#### 1. 创建兼容启动脚本

```bash
#!/bin/bash
# start_mmp_py36.sh - Python 3.6 兼容启动脚本

echo "检查Python版本..."
python_version=$(python3.6 --version 2>&1)
echo "当前Python版本: $python_version"

if [[ $python_version == *"3.6"* ]]; then
    echo "Python 3.6 检测成功，使用兼容模式启动..."
    
    # 设置环境变量
    export PYTHONPATH=$PWD
    export FLASK_APP=app/web_app.py
    export FLASK_ENV=production
    
    # 启动应用
    python3.6 -c "
import sys
print('Python版本:', sys.version)
print('正在启动MMP应用（Python 3.6兼容模式）...')

# 导入并启动应用
try:
    from app.web_app import app
    print('应用模块加载成功')
    app.run(host='0.0.0.0', port=5000, debug=False)
except Exception as e:
    print('启动失败:', str(e))
    print('请检查依赖包是否正确安装')
"
else
    echo "错误: 需要Python 3.6版本"
    exit 1
fi
```

#### 2. 代码兼容性补丁

创建 `py36_compatibility.py`:

```python
"""Python 3.6 兼容性补丁"""
import sys

# 检查Python版本
if sys.version_info < (3, 6):
    raise RuntimeError("需要Python 3.6或更高版本")

# 类型注解兼容性
try:
    from typing import Dict, List, Any, Optional, Union
except ImportError:
    # 如果typing模块不完整，创建占位符
    class TypePlaceholder:
        def __getitem__(self, item):
            return self
        def __call__(self, item):
            return item
    
    Dict = List = Any = Optional = Union = TypePlaceholder()

# f-string兼容性检查
try:
    test = f"test"
except SyntaxError:
    print("警告: 当前Python版本不支持f-string语法")

print("Python 3.6 兼容性模块加载完成")
```

### 📋 Python 3.6 快速检查清单

部署前请确认：

- [ ] Python版本确实是3.6.x
- [ ] 使用了requirements_py36.txt
- [ ] 所有依赖包安装成功
- [ ] 代码中的类型注解已处理
- [ ] 测试基本功能正常

### 🎯 一键部署命令（Python 3.6）

```bash
# 创建部署脚本
cat > deploy_py36.sh << 'EOF'
#!/bin/bash
echo "MMP系统 Python 3.6 兼容部署"
echo "================================"

# 检查Python版本
python3.6 --version || { echo "Python 3.6 未安装"; exit 1; }

# 安装依赖
echo "安装Python 3.6兼容依赖..."
pip3.6 install -r requirements_py36.txt

# 启动应用
echo "启动MMP应用..."
python3.6 app/web_app.py
EOF

chmod +x deploy_py36.sh
./deploy_py36.sh
```

虽然提供了Python 3.6的兼容方案，但**强烈建议升级到Python 3.8+**以获得完整功能和更好的性能！
