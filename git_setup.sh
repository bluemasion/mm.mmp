#!/bin/bash
# GitHub对接自动化脚本

set -e

echo "🚀 MMP项目GitHub对接助手"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Git是否可用
echo -e "${YELLOW}检查Git环境...${NC}"
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git未安装或不可用${NC}"
    echo "请先修复Xcode命令行工具问题："
    echo "  sudo xcode-select --switch /Library/Developer/CommandLineTools"
    exit 1
fi
echo -e "${GREEN}✅ Git可用: $(git --version)${NC}"
echo ""

# 检查是否在项目目录
if [ ! -f "run_app.py" ]; then
    echo -e "${RED}❌ 请在MMP项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查是否已初始化Git
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}📦 初始化Git仓库...${NC}"
    git init
    echo -e "${GREEN}✅ Git仓库已初始化${NC}"
else
    echo -e "${GREEN}✅ Git仓库已存在${NC}"
fi
echo ""

# 配置Git用户信息（如果未配置）
echo -e "${YELLOW}🔧 检查Git配置...${NC}"
if [ -z "$(git config user.name)" ]; then
    read -p "请输入你的GitHub用户名: " username
    git config user.name "$username"
    echo -e "${GREEN}✅ 用户名已设置: $username${NC}"
else
    echo -e "${GREEN}✅ 用户名: $(git config user.name)${NC}"
fi

if [ -z "$(git config user.email)" ]; then
    read -p "请输入你的GitHub邮箱: " email
    git config user.email "$email"
    echo -e "${GREEN}✅ 邮箱已设置: $email${NC}"
else
    echo -e "${GREEN}✅ 邮箱: $(git config user.email)${NC}"
fi
echo ""

# 检查远程仓库
echo -e "${YELLOW}🔗 检查远程仓库配置...${NC}"
if git remote get-url origin &> /dev/null; then
    echo -e "${GREEN}✅ 已配置远程仓库:${NC}"
    git remote -v
    echo ""
    read -p "是否要更改远程仓库地址? (y/n): " change_remote
    if [ "$change_remote" = "y" ]; then
        read -p "输入新的GitHub仓库地址: " new_remote
        git remote set-url origin "$new_remote"
        echo -e "${GREEN}✅ 远程仓库已更新${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  未配置远程仓库${NC}"
    echo ""
    echo "请先在GitHub创建仓库："
    echo "  1. 访问 https://github.com/new"
    echo "  2. 仓库名建议: mmp-material-management"
    echo "  3. 不要勾选 'Initialize with README'"
    echo ""
    read -p "输入GitHub仓库地址 (例如 git@github.com:username/repo.git): " repo_url
    
    if [ -n "$repo_url" ]; then
        git remote add origin "$repo_url"
        echo -e "${GREEN}✅ 远程仓库已添加${NC}"
    else
        echo -e "${YELLOW}⏭️  跳过远程仓库配置${NC}"
    fi
fi
echo ""

# 查看当前状态
echo -e "${YELLOW}📊 当前仓库状态:${NC}"
git status --short | head -20
echo ""

# 询问是否提交
read -p "是否添加所有文件并提交? (y/n): " do_commit
if [ "$do_commit" = "y" ]; then
    echo -e "${YELLOW}📝 添加文件...${NC}"
    git add .
    
    echo -e "${YELLOW}💾 提交更改...${NC}"
    read -p "输入提交信息 (默认: 'Initial commit'): " commit_msg
    commit_msg=${commit_msg:-"Initial commit: MMP Material Master Data Management System"}
    git commit -m "$commit_msg"
    echo -e "${GREEN}✅ 提交完成${NC}"
    echo ""
    
    # 询问是否推送
    if git remote get-url origin &> /dev/null; then
        read -p "是否推送到GitHub? (y/n): " do_push
        if [ "$do_push" = "y" ]; then
            echo -e "${YELLOW}⬆️  推送到GitHub...${NC}"
            
            # 检查分支名
            current_branch=$(git branch --show-current)
            if [ -z "$current_branch" ]; then
                git branch -M main
                current_branch="main"
            fi
            
            git push -u origin "$current_branch"
            echo -e "${GREEN}✅ 推送成功！${NC}"
            echo ""
            echo -e "${GREEN}🎉 GitHub对接完成！${NC}"
            
            # 获取远程URL并提取仓库地址
            remote_url=$(git remote get-url origin)
            if [[ $remote_url == git@github.com:* ]]; then
                repo_path=${remote_url#git@github.com:}
                repo_path=${repo_path%.git}
                echo "访问你的仓库: https://github.com/$repo_path"
            elif [[ $remote_url == https://github.com/* ]]; then
                repo_path=${remote_url#https://github.com/}
                repo_path=${repo_path%.git}
                echo "访问你的仓库: https://github.com/$repo_path"
            fi
        fi
    fi
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ 设置完成！${NC}"
echo ""
echo "📚 后续操作提示："
echo "  • 查看状态: git status"
echo "  • 提交更改: git add . && git commit -m '说明'"
echo "  • 推送代码: git push"
echo "  • 查看文档: cat GITHUB_SETUP.md"
echo ""
