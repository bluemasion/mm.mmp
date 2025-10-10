#!/bin/bash
# session_debug_fix.sh - 修复会话数据持久化问题

echo "正在修复会话数据持久化问题..."

# 备份原文件
cp app/web_app.py app/web_app.py.session_backup_$(date +%Y%m%d_%H%M%S)

# 创建增强的会话管理修复补丁
cat > session_fix.patch << 'EOF'
--- app/web_app.py.orig	2024-01-01 00:00:00.000000000 +0800
+++ app/web_app.py	2024-01-01 00:00:00.000000000 +0800
@@ -34,7 +34,16 @@
 # 创建Flask应用，指定正确的模板和静态文件路径
 app = Flask(__name__, 
            template_folder=os.path.join(project_root, 'templates'),
            static_folder=os.path.join(project_root, 'static'))
-app.secret_key = 'your-secret-key-change-in-production'
+
+# 配置Flask会话
+app.secret_key = 'your-secret-key-change-in-production'
+app.config['SESSION_TYPE'] = 'filesystem'
+app.config['SESSION_PERMANENT'] = False
+app.config['SESSION_USE_SIGNER'] = True
+app.config['SESSION_KEY_PREFIX'] = 'mmp_session:'
+app.config['SESSION_COOKIE_HTTPONLY'] = True
+app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为False，生产环境应为True
+app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1小时过期
 
 # 配置文件上传
 UPLOAD_FOLDER = 'uploads'
@@ -49,7 +58,12 @@
 
 # 全局服务实例
 workflow_service = None
-session_data = {}  # 简单的会话数据存储
+
+# 增强的会话数据存储 - 使用Flask session而不是全局字典
+def get_session_storage():
+    """获取会话存储字典"""
+    if 'mmp_data' not in session:
+        session['mmp_data'] = {}
+    return session['mmp_data']
 
 def init_service():
     """初始化工作流服务"""
@@ -81,19 +95,29 @@
     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 
-def get_session_id():
-    """获取或创建会话ID"""
-    if 'session_id' not in session:
-        session['session_id'] = str(uuid.uuid4())
-    return session['session_id']
-
 def store_session_data(key: str, data: Any):
-    """存储会话数据"""
-    session_id = get_session_id()
-    if session_id not in session_data:
-        session_data[session_id] = {}
-    session_data[session_id][key] = data
+    """存储会话数据到Flask session"""
+    try:
+        storage = get_session_storage()
+        storage[key] = data
+        session.permanent = True  # 确保session被保存
+        logging.info(f"存储会话数据: {key}, 数据长度: {len(str(data)) if data else 0}")
+        return True
+    except Exception as e:
+        logging.error(f"存储会话数据失败 {key}: {e}")
+        return False
 
 def get_session_data(key: str, default=None):
-    """获取会话数据"""
-    session_id = get_session_id()
-    return session_data.get(session_id, {}).get(key, default)
+    """从Flask session获取会话数据"""
+    try:
+        storage = get_session_storage()
+        data = storage.get(key, default)
+        logging.info(f"获取会话数据: {key}, 是否存在: {data is not None}, 数据长度: {len(str(data)) if data else 0}")
+        return data
+    except Exception as e:
+        logging.error(f"获取会话数据失败 {key}: {e}")
+        return default
+
+def clear_session_data():
+    """清除所有会话数据"""
+    session.pop('mmp_data', None)
+    logging.info("已清除所有会话数据")
EOF

# 应用补丁
echo "应用会话管理修复补丁..."
patch -p0 < session_fix.patch

if [ $? -eq 0 ]; then
    echo "✓ 会话管理修复补丁应用成功"
else
    echo "✗ 补丁应用失败，手动修复..."
    
    # 手动修复关键部分
    python3 << 'PYTHON_EOF'
import re

# 读取原文件
with open('app/web_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修复Flask配置部分
flask_config = '''# 创建Flask应用，指定正确的模板和静态文件路径
app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))

# 配置Flask会话
app.secret_key = 'your-secret-key-change-in-production'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'mmp_session:'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为False，生产环境应为True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1小时过期'''

# 替换Flask应用创建部分
content = re.sub(
    r'# 创建Flask应用，指定正确的模板和静态文件路径\napp = Flask\(__name__, [^)]+\)\napp\.secret_key = [^\n]+',
    flask_config,
    content,
    flags=re.MULTILINE
)

# 2. 替换会话数据存储部分
session_storage = '''# 全局服务实例
workflow_service = None

# 增强的会话数据存储 - 使用Flask session而不是全局字典
def get_session_storage():
    """获取会话存储字典"""
    if 'mmp_data' not in session:
        session['mmp_data'] = {}
    return session['mmp_data']'''

content = re.sub(
    r'# 全局服务实例\nworkflow_service = None\nsession_data = \{\}  # 简单的会话数据存储',
    session_storage,
    content
)

# 3. 替换会话管理函数
new_session_funcs = '''def store_session_data(key: str, data: Any):
    """存储会话数据到Flask session"""
    try:
        storage = get_session_storage()
        storage[key] = data
        session.permanent = True  # 确保session被保存
        logging.info(f"存储会话数据: {key}, 数据长度: {len(str(data)) if data else 0}")
        return True
    except Exception as e:
        logging.error(f"存储会话数据失败 {key}: {e}")
        return False

def get_session_data(key: str, default=None):
    """从Flask session获取会话数据"""
    try:
        storage = get_session_storage()
        data = storage.get(key, default)
        logging.info(f"获取会话数据: {key}, 是否存在: {data is not None}, 数据长度: {len(str(data)) if data else 0}")
        return data
    except Exception as e:
        logging.error(f"获取会话数据失败 {key}: {e}")
        return default

def clear_session_data():
    """清除所有会话数据"""
    session.pop('mmp_data', None)
    logging.info("已清除所有会话数据")'''

# 找到并替换原有的会话函数
old_funcs_pattern = r'def get_session_id\(\):[^}]+}[^}]+}[^}]+}[^}]+def get_session_data[^}]+}'
content = re.sub(old_funcs_pattern, new_session_funcs, content, flags=re.DOTALL)

# 如果上面的正则没匹配到，尝试更简单的替换
if 'def get_session_id():' in content:
    # 找到所有旧函数并替换
    lines = content.split('\n')
    new_lines = []
    skip_until_next_func = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith('def get_session_id():'):
            skip_until_next_func = True
            # 插入新的会话函数
            new_lines.extend(new_session_funcs.split('\n'))
        elif skip_until_next_func and line.strip().startswith('def ') and 'session' not in line:
            skip_until_next_func = False
            new_lines.append(line)
        elif not skip_until_next_func:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)

# 保存修改后的文件
with open('app/web_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("手动修复完成")
PYTHON_EOF
fi

# 清理临时文件
rm -f session_fix.patch

echo ""
echo "会话数据持久化修复完成！"
echo ""
echo "主要修复内容："
echo "1. 使用Flask session替代全局字典存储会话数据"
echo "2. 增加详细的会话数据存储和获取日志"
echo "3. 配置Flask session参数提高稳定性"
echo "4. 添加会话数据清理功能"
echo ""
echo "建议测试步骤："
echo "1. 重启应用: ./start_mmp.sh"
echo "2. 完成参数提取步骤"
echo "3. 检查是否能正常进入分类选择页面"
echo "4. 查看应用日志中的会话数据状态信息"
