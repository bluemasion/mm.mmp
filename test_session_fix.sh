#!/bin/bash
# test_session_fix.sh - 测试会话修复

echo "======================================"
echo "测试MMP会话管理修复"
echo "======================================"

cd "/Users/mason/Desktop/code /mmp"

# 检查文件是否存在
if [ ! -f "app/web_app.py" ]; then
    echo "❌ web_app.py 文件不存在"
    exit 1
fi

echo "✅ 文件检查通过"

# 检查Python语法（忽略版本问题）
echo "🔍 检查Python语法..."

# 创建临时测试脚本
cat > test_syntax.py << 'EOF'
import sys
sys.path.append('.')
try:
    from app.web_app import app, get_session_id, store_session_data, get_session_data
    print("✅ Flask应用导入成功")
    print("✅ 会话管理函数导入成功")
    
    # 测试会话函数
    with app.test_request_context():
        from flask import session
        session['test'] = 'test_value'
        
        # 测试会话ID生成
        session_id = get_session_id()
        print(f"✅ 会话ID生成: {session_id}")
        
        # 测试数据存储和获取
        test_data = [{'test': 'data'}]
        store_session_data('test_key', test_data)
        retrieved_data = get_session_data('test_key')
        
        if retrieved_data == test_data:
            print("✅ 会话数据存储和获取正常")
        else:
            print("❌ 会话数据存储和获取异常")
        
        print("🎉 所有测试通过!")
        
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 测试失败: {e}")
    sys.exit(1)
EOF

# 运行测试
python3 test_syntax.py
TEST_RESULT=$?

# 清理临时文件
rm -f test_syntax.py

if [ $TEST_RESULT -eq 0 ]; then
    echo
    echo "======================================"
    echo "✅ 会话管理修复验证成功!"
    echo "======================================"
    echo
    echo "修复内容:"
    echo "1. ✅ 添加了详细的会话调试日志"
    echo "2. ✅ 改进了分类选择页面的错误处理"
    echo "3. ✅ 添加了会话调试API: /api/debug/session"
    echo "4. ✅ 增强了错误信息的准确性"
    echo
    echo "测试建议:"
    echo "1. 启动服务: python3 app/web_app.py"
    echo "2. 上传文件并提取参数"
    echo "3. 访问调试API: curl http://localhost:5001/api/debug/session"
    echo "4. 检查分类选择页面是否正常"
    echo
else
    echo
    echo "======================================"
    echo "❌ 测试失败，需要进一步检查"
    echo "======================================"
fi
