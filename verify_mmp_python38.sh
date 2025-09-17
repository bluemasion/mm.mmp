#!/bin/bash
# MMP应用验证脚本 - Python 3.8升级后验证
# 使用方法: bash verify_mmp_python38.sh

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   MMP应用 Python 3.8 升级验证${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# 检查Python版本
check_python_version() {
    echo -e "${BLUE}1. Python版本检查:${NC}"
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        echo "   $PYTHON_VERSION"
        
        if [[ "$PYTHON_VERSION" == *"3.8"* ]]; then
            echo -e "   ${GREEN}✓ Python 3.8 可用${NC}"
            return 0
        else
            echo -e "   ${YELLOW}⚠ Python版本不是3.8${NC}"
            return 1
        fi
    else
        echo -e "   ${RED}❌ python3 命令不可用${NC}"
        return 1
    fi
}

# 检查pip版本
check_pip_version() {
    echo -e "${BLUE}2. pip版本检查:${NC}"
    
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version 2>&1)
        echo "   $PIP_VERSION"
        echo -e "   ${GREEN}✓ pip3 可用${NC}"
        return 0
    else
        echo -e "   ${RED}❌ pip3 命令不可用${NC}"
        return 1
    fi
}

# 检查关键Python包
check_python_packages() {
    echo -e "${BLUE}3. 关键包导入测试:${NC}"
    
    # 创建临时Python测试脚本
    cat > /tmp/test_packages.py << 'EOF'
import sys
import traceback

packages_to_test = [
    ('sys', 'Python系统模块'),
    ('os', '操作系统接口'),
    ('json', 'JSON处理'),
    ('datetime', '日期时间'),
    ('urllib', 'URL处理'),
    ('ssl', 'SSL支持'),
    ('sqlite3', 'SQLite数据库'),
    ('flask', 'Flask Web框架'),
    ('pandas', 'Pandas数据处理'),
    ('numpy', 'NumPy数值计算'),
    ('sklearn', 'Scikit-learn机器学习'),
    ('werkzeug', 'Werkzeug WSGI工具'),
    ('jinja2', 'Jinja2模板引擎')
]

print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.executable}")
print()

success_count = 0
total_count = len(packages_to_test)

for package_name, description in packages_to_test:
    try:
        module = __import__(package_name)
        version = getattr(module, '__version__', 'N/A')
        print(f"✓ {description} ({package_name}): {version}")
        success_count += 1
    except ImportError as e:
        print(f"❌ {description} ({package_name}): 导入失败 - {e}")
    except Exception as e:
        print(f"⚠ {description} ({package_name}): 测试异常 - {e}")

print()
print(f"包测试结果: {success_count}/{total_count} 成功")

if success_count >= total_count - 2:  # 允许2个包失败
    print("✅ 关键包测试通过")
    exit(0)
else:
    print("❌ 关键包测试失败")
    exit(1)
EOF

    if python3 /tmp/test_packages.py; then
        echo -e "   ${GREEN}✓ 关键包测试通过${NC}"
        rm -f /tmp/test_packages.py
        return 0
    else
        echo -e "   ${RED}❌ 关键包测试失败${NC}"
        rm -f /tmp/test_packages.py
        return 1
    fi
}

# 检查MMP应用结构
check_mmp_structure() {
    echo -e "${BLUE}4. MMP应用结构检查:${NC}"
    
    # 检查关键文件
    files_to_check=(
        "app/web_app.py:主应用文件"
        "app/data_loader.py:数据加载器"
        "app/preprocessor.py:数据预处理器"
        "app/matcher.py:匹配算法"
        "config.py:配置文件"
        "requirements.txt:依赖列表"
    )
    
    missing_files=0
    for file_info in "${files_to_check[@]}"; do
        file_path="${file_info%:*}"
        file_desc="${file_info#*:}"
        
        if [[ -f "$file_path" ]]; then
            echo -e "   ✓ $file_desc ($file_path)"
        else
            echo -e "   ${YELLOW}⚠ 缺失: $file_desc ($file_path)${NC}"
            ((missing_files++))
        fi
    done
    
    if [[ $missing_files -eq 0 ]]; then
        echo -e "   ${GREEN}✓ MMP应用结构完整${NC}"
        return 0
    else
        echo -e "   ${YELLOW}⚠ 发现 $missing_files 个缺失文件${NC}"
        return 1
    fi
}

# 测试MMP应用导入
test_mmp_import() {
    echo -e "${BLUE}5. MMP应用导入测试:${NC}"
    
    # 创建导入测试脚本
    cat > /tmp/test_mmp_import.py << 'EOF'
import sys
import os

# 添加应用路径
sys.path.insert(0, os.getcwd())

try:
    # 测试核心模块导入
    print("测试核心模块导入...")
    
    from app.web_app import app
    print("✓ Flask应用导入成功")
    
    from app.data_loader import DataLoader
    print("✓ DataLoader导入成功")
    
    from app.preprocessor import Preprocessor
    print("✓ Preprocessor导入成功")
    
    from app.matcher import Matcher
    print("✓ Matcher导入成功")
    
    print("✅ 所有核心模块导入成功")
    
    # 测试Flask应用配置
    if hasattr(app, 'config'):
        print(f"✓ Flask应用配置可用")
        
    print("✅ MMP应用导入测试通过")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 测试异常: {e}")
    sys.exit(1)
EOF

    if python3 /tmp/test_mmp_import.py; then
        echo -e "   ${GREEN}✓ MMP应用导入测试通过${NC}"
        rm -f /tmp/test_mmp_import.py
        return 0
    else
        echo -e "   ${RED}❌ MMP应用导入测试失败${NC}"
        rm -f /tmp/test_mmp_import.py
        return 1
    fi
}

# 测试Flask应用启动
test_flask_startup() {
    echo -e "${BLUE}6. Flask应用启动测试:${NC}"
    
    # 创建启动测试脚本
    cat > /tmp/test_flask_startup.py << 'EOF'
import sys
import os
import threading
import time
import requests
from urllib.parse import urljoin

# 添加应用路径
sys.path.insert(0, os.getcwd())

def start_app():
    try:
        from app.web_app import app
        app.run(host='127.0.0.1', port=5555, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask启动失败: {e}")

def test_app():
    time.sleep(2)  # 等待应用启动
    
    try:
        # 测试首页
        response = requests.get('http://127.0.0.1:5555/', timeout=5)
        if response.status_code == 200:
            print("✓ 首页访问成功")
            return True
        else:
            print(f"⚠ 首页返回状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 首页访问失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == "__main__":
    print("启动Flask应用进行测试...")
    
    # 在后台线程启动Flask应用
    app_thread = threading.Thread(target=start_app, daemon=True)
    app_thread.start()
    
    # 测试应用
    if test_app():
        print("✅ Flask应用启动测试通过")
        sys.exit(0)
    else:
        print("❌ Flask应用启动测试失败")
        sys.exit(1)
EOF

    # 运行启动测试（设置超时）
    timeout 15 python3 /tmp/test_flask_startup.py 2>/dev/null
    test_result=$?
    
    rm -f /tmp/test_flask_startup.py
    
    if [[ $test_result -eq 0 ]]; then
        echo -e "   ${GREEN}✓ Flask应用启动测试通过${NC}"
        return 0
    else
        echo -e "   ${YELLOW}⚠ Flask应用启动测试超时或失败${NC}"
        echo -e "   ${YELLOW}  这可能是由于依赖缺失或配置问题${NC}"
        return 1
    fi
}

# 生成验证报告
generate_report() {
    echo
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}           验证报告${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    local total_tests=6
    local passed_tests=$1
    
    echo "总测试项目: $total_tests"
    echo "通过测试: $passed_tests"
    echo "成功率: $(( passed_tests * 100 / total_tests ))%"
    echo
    
    if [[ $passed_tests -eq $total_tests ]]; then
        echo -e "${GREEN}🎉 所有验证测试通过！${NC}"
        echo -e "${GREEN}   MMP应用已准备就绪，可以正常使用${NC}"
        echo
        echo -e "${BLUE}启动应用:${NC}"
        echo "   cd /path/to/mmp"
        echo "   python3 app/web_app.py"
        echo
        echo -e "${BLUE}或使用后台模式:${NC}"
        echo "   nohup python3 app/web_app.py > app.log 2>&1 &"
    elif [[ $passed_tests -ge $(( total_tests - 1 )) ]]; then
        echo -e "${YELLOW}⚠ 大部分验证测试通过${NC}"
        echo -e "${YELLOW}  应用可能可以运行，但建议检查失败的测试项${NC}"
    else
        echo -e "${RED}❌ 多个验证测试失败${NC}"
        echo -e "${RED}  请检查Python 3.8安装和依赖配置${NC}"
        echo
        echo -e "${BLUE}建议操作:${NC}"
        echo "1. 重新运行升级脚本: sudo bash upgrade_python38_centos7.sh"
        echo "2. 手动安装依赖: pip3 install -r requirements.txt"
        echo "3. 检查错误日志并解决问题"
    fi
}

# 主函数
main() {
    local passed_tests=0
    
    if check_python_version; then ((passed_tests++)); fi
    echo
    
    if check_pip_version; then ((passed_tests++)); fi
    echo
    
    if check_python_packages; then ((passed_tests++)); fi
    echo
    
    if check_mmp_structure; then ((passed_tests++)); fi
    echo
    
    if test_mmp_import; then ((passed_tests++)); fi
    echo
    
    if test_flask_startup; then ((passed_tests++)); fi
    echo
    
    generate_report $passed_tests
}

# 运行主函数
main "$@"
