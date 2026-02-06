# GitHub 对接指南

## 🚀 快速设置步骤

### 1. 初始化本地仓库（如果未初始化）
```bash
cd "/Users/mason/Desktop/code /mmp"
git init
git add .
git commit -m "Initial commit: MMP Material Master Data Management System"
```

### 2. 在GitHub创建远程仓库
1. 访问 https://github.com/new
2. 仓库名称建议：`mmp-material-management`
3. 描述：MMP物料主数据管理智能应用系统
4. **不要勾选** "Initialize this repository with a README"（本地已有文件）
5. 点击 "Create repository"

### 3. 关联远程仓库
```bash
# 替换 YOUR_USERNAME 为你的GitHub用户名
git remote add origin https://github.com/YOUR_USERNAME/mmp-material-management.git

# 或使用SSH（推荐，需要先配置SSH密钥）
git remote add origin git@github.com:YOUR_USERNAME/mmp-material-management.git
```

### 4. 推送代码到GitHub
```bash
git branch -M main
git push -u origin main
```

## 🔑 SSH密钥配置（推荐）

### 生成SSH密钥
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# 按回车使用默认路径，可以设置密码（可选）
```

### 添加到SSH Agent
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### 添加公钥到GitHub
```bash
# 复制公钥
cat ~/.ssh/id_ed25519.pub | pbcopy

# 然后访问：
# https://github.com/settings/ssh/new
# 粘贴公钥并保存
```

## 📝 常用Git操作

### 查看状态
```bash
git status
```

### 提交更改
```bash
git add .
git commit -m "描述你的更改"
git push
```

### 拉取最新代码
```bash
git pull origin main
```

### 创建新分支
```bash
git checkout -b feature/new-feature
git push -u origin feature/new-feature
```

## 🔧 问题排查

### 如果遇到Xcode路径错误
```bash
sudo xcode-select --switch /Library/Developer/CommandLineTools
git --version  # 验证git可用
```

### 查看远程仓库配置
```bash
git remote -v
```

### 修改远程仓库地址
```bash
git remote set-url origin NEW_URL
```

## 🎯 GitHub Actions CI/CD（可选）

在 `.github/workflows/` 目录下已有基础配置，推送后会自动触发测试。

## 📚 参考资料
- [GitHub文档](https://docs.github.com)
- [Git基础教程](https://git-scm.com/book/zh/v2)
