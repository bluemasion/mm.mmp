#!/bin/bash
# 快速GitHub对接 - 适合首次使用

echo "🚀 MMP项目快速推送到GitHub"
echo ""

# 检查是否在正确目录
if [ ! -f "run_app.py" ]; then
    echo "❌ 错误：请在MMP项目根目录运行"
    exit 1
fi

# 初始化Git（如果需要）
if [ ! -d ".git" ]; then
    echo "📦 初始化Git仓库..."
    git init
    git add .
    git commit -m "Initial commit: MMP Material Master Data Management System"
    echo "✅ 仓库已初始化"
else
    echo "✅ Git仓库已存在"
fi

# 检查远程仓库
if ! git remote get-url origin &> /dev/null; then
    echo ""
    echo "⚠️  还未配置GitHub远程仓库"
    echo ""
    echo "请按以下步骤操作："
    echo "1. 访问 https://github.com/new 创建新仓库"
    echo "2. 仓库名建议: mmp-material-management"
    echo "3. 不要勾选'Initialize with README'"
    echo "4. 创建后，复制仓库地址（SSH或HTTPS）"
    echo ""
    read -p "输入仓库地址（例如 git@github.com:username/repo.git）: " repo_url
    
    if [ -n "$repo_url" ]; then
        git remote add origin "$repo_url"
        git branch -M main
        git push -u origin main
        echo ""
        echo "🎉 成功推送到GitHub！"
    else
        echo "⏭️  已取消"
        exit 0
    fi
else
    echo "✅ 远程仓库: $(git remote get-url origin)"
    echo ""
    read -p "推送当前更改到GitHub? (y/n): " do_push
    
    if [ "$do_push" = "y" ]; then
        git add .
        git commit -m "Update: $(date '+%Y-%m-%d %H:%M')" || echo "没有新的更改"
        git push
        echo "✅ 推送完成"
    fi
fi

echo ""
echo "📚 更多Git操作："
echo "  git status           - 查看状态"
echo "  git add .            - 添加所有更改"
echo "  git commit -m '...'  - 提交更改"
echo "  git push             - 推送到GitHub"
echo ""
