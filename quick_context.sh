#!/bin/bash
# quick_context.sh - 快速生成项目上下文快照

echo "🚀 快速生成MMP项目上下文快照"
echo "=================================="

# 检查Python版本
if command -v python3.8 &> /dev/null; then
    PYTHON_CMD="python3.8"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 未找到Python，请先安装Python"
    exit 1
fi

echo "🐍 使用Python命令: $PYTHON_CMD"
echo ""

# 检查生成器文件
if [ ! -f "project_context_generator.py" ]; then
    echo "❌ 未找到project_context_generator.py文件"
    echo "请确保在项目根目录下运行此脚本"
    exit 1
fi

# 运行生成器
echo "⚡ 开始生成上下文快照..."
echo ""

$PYTHON_CMD project_context_generator.py

# 检查执行结果
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 上下文快照生成成功！"
    echo ""
    
    # 查找最新生成的文件
    LATEST_SNAPSHOT=$(ls -t PROJECT_CONTEXT_SNAPSHOT_*.md 2>/dev/null | head -1)
    
    if [ -n "$LATEST_SNAPSHOT" ]; then
        echo "📄 最新快照文件: $LATEST_SNAPSHOT"
        echo "📊 文件大小: $(wc -c < "$LATEST_SNAPSHOT") 字节"
        echo "📏 文件行数: $(wc -l < "$LATEST_SNAPSHOT") 行"
        echo ""
        echo "💡 使用方法:"
        echo "   1. 复制文件内容: cat \"$LATEST_SNAPSHOT\" | pbcopy"
        echo "   2. 在新AI会话中粘贴内容"
        echo "   3. 开始你的开发对话"
        echo ""
        echo "📂 所有快照文件:"
        ls -la PROJECT_CONTEXT_SNAPSHOT_*.md 2>/dev/null | head -5
        
        # 提供一键复制选项
        echo ""
        read -p "🔄 是否复制最新快照到剪贴板? (y/N): " copy_choice
        if [[ $copy_choice =~ ^[Yy]$ ]]; then
            if command -v pbcopy &> /dev/null; then
                cat "$LATEST_SNAPSHOT" | pbcopy
                echo "✅ 已复制到剪贴板，可直接在AI会话中粘贴！"
            elif command -v xclip &> /dev/null; then
                cat "$LATEST_SNAPSHOT" | xclip -selection clipboard
                echo "✅ 已复制到剪贴板（Linux）！"
            else
                echo "ℹ️  请手动复制文件内容: cat \"$LATEST_SNAPSHOT\""
            fi
        fi
        
    else
        echo "⚠️  未找到生成的快照文件"
    fi
    
else
    echo ""
    echo "❌ 上下文快照生成失败"
    echo "请检查错误信息并重试"
    exit 1
fi

echo ""
echo "🎯 完成！"