#!/bin/bash
# Complete fix for MMP template and routing issues
# 修复MMP模板路径和路由问题

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    MMP Complete Template & Route Fix${NC}"
echo -e "${BLUE}========================================${NC}"

TARGET_PATH="${1:-/dt1/mmp/mmp}"

echo -e "${BLUE}[INFO]${NC} Target path: $TARGET_PATH"

# Check if target exists
if [[ ! -d "$TARGET_PATH" ]]; then
    echo -e "${RED}[ERROR]${NC} Target path does not exist: $TARGET_PATH"
    exit 1
fi

# Stop MMP service
echo -e "${BLUE}[INFO]${NC} Stopping MMP service..."
pkill -f "python.*run_app.py" || true
sleep 2

# Backup current web_app.py
echo -e "${BLUE}[INFO]${NC} Creating backup..."
cp "$TARGET_PATH/app/web_app.py" "$TARGET_PATH/app/web_app.py.backup"

# Create missing error.html template
echo -e "${BLUE}[INFO]${NC} Creating error.html template..."
cat > "$TARGET_PATH/templates/error.html" << 'EOF'
{% extends "base.html" %}

{% block title %}错误 - MMP物料主数据管理系统{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card border-danger">
                <div class="card-header bg-danger text-white">
                    <h4 class="mb-0">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        系统错误
                    </h4>
                </div>
                <div class="card-body">
                    <div class="text-center mb-4">
                        <h1 class="display-4 text-danger">{{ error_code or '500' }}</h1>
                        <h3 class="text-muted">{{ error_message or '系统出现了一个错误' }}</h3>
                    </div>
                    
                    {% if error_details %}
                    <div class="alert alert-light">
                        <h6>错误详情：</h6>
                        <p class="mb-0 font-monospace small">{{ error_details }}</p>
                    </div>
                    {% endif %}
                    
                    <div class="text-center">
                        <a href="{{ url_for('index') }}" class="btn btn-primary me-2">
                            <i class="fas fa-home me-1"></i>
                            返回首页
                        </a>
                        <button onclick="history.back()" class="btn btn-secondary">
                            <i class="fas fa-arrow-left me-1"></i>
                            返回上一页
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
EOF

# Apply comprehensive fixes to web_app.py
echo -e "${BLUE}[INFO]${NC} Applying comprehensive fixes to web_app.py..."

cat > /tmp/web_app_comprehensive_fix.py << 'EOF'
import re
import sys

def apply_comprehensive_fixes(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Flask app creation with template path
    flask_pattern = r"app = Flask\(__name__\)"
    if flask_pattern in content and "template_folder" not in content:
        flask_replacement = """# 获取项目根目录路径
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 创建Flask应用，指定正确的模板和静态文件路径
app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))"""
        content = re.sub(flask_pattern, flask_replacement, content)
        print("✓ Applied Flask template path fix")
    
    # Fix 2: Add URL redirects for common mistyped URLs
    if "/categorize" not in content and "@app.route('/category_selection')" in content:
        redirect_code = '''
# URL重定向处理（处理常见的错误URL）
@app.route('/categorize')
def categorize_redirect():
    """重定向到正确的分类选择页面"""
    return redirect(url_for('category_selection'))

@app.route('/category')
def category_redirect():
    """重定向到正确的分类选择页面"""
    return redirect(url_for('category_selection'))

'''
        # Insert before error handlers
        error_handler_pattern = r"# 错误处理\n@app\.errorhandler\(404\)"
        if error_handler_pattern in content:
            content = re.sub(error_handler_pattern, redirect_code + "# 错误处理\n@app.errorhandler(404)", content)
            print("✓ Added URL redirect routes")
        else:
            # Insert before the last route
            last_route_pattern = r"(@app\.route\('/api/status'\).*?\n.*?\n.*?\n.*?\n.*?\n.*?\n.*?\n)"
            if re.search(last_route_pattern, content, re.DOTALL):
                content = re.sub(last_route_pattern, r"\1" + redirect_code, content, flags=re.DOTALL)
                print("✓ Added URL redirect routes (alternative position)")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    apply_comprehensive_fixes(sys.argv[1])
EOF

python3 /tmp/web_app_comprehensive_fix.py "$TARGET_PATH/app/web_app.py"

# Verify the fix
echo -e "${BLUE}[INFO]${NC} Verifying the fix..."
if python3 -c "
import sys
sys.path.insert(0, '$TARGET_PATH')
try:
    from app.web_app import app
    print('✓ Flask app imports successfully')
    print('✓ Template folder:', app.template_folder)
except Exception as e:
    print('❌ Import failed:', str(e))
"; then
    echo -e "${GREEN}[SUCCESS]${NC} Fix applied successfully"
else
    echo -e "${YELLOW}[WARNING]${NC} Fix may need manual adjustment"
fi

# Restart MMP service
echo -e "${BLUE}[INFO]${NC} Restarting MMP service..."
cd "$TARGET_PATH"
nohup python3 run_app.py > app.log 2>&1 &
sleep 3

# Check if service started
if pgrep -f "python.*run_app.py" > /dev/null; then
    echo -e "${GREEN}[SUCCESS]${NC} MMP service restarted successfully"
    echo -e "${BLUE}[INFO]${NC} Testing web access..."
    
    # Test web access
    if command -v curl &> /dev/null; then
        if curl -s http://localhost:5000 > /dev/null 2>&1; then
            echo -e "${GREEN}[SUCCESS]${NC} Web service is responding"
        else
            echo -e "${YELLOW}[WARNING]${NC} Service may still be starting..."
        fi
    fi
else
    echo -e "${RED}[ERROR]${NC} Failed to restart MMP service"
    echo -e "${BLUE}[INFO]${NC} Check logs: tail -f $TARGET_PATH/app.log"
fi

echo -e "${BLUE}[INFO]${NC} Quick fix completed!"
echo -e "${BLUE}[INFO]${NC} If issues persist, check: tail -f $TARGET_PATH/app.log"

# Cleanup
rm -f /tmp/web_app_fix.py
