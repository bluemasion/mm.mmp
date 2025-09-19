# Git替代版本管理方案

## 📋 当前状况
由于系统Git配置问题（Xcode命令行工具路径问题），暂时无法使用Git进行版本管理。已创建备份方案作为替代。

## 🔄 备份版本管理

### 当前备份位置
```
📁 ../mmp_backups/mmp_v1.2.0_20250919_222845/
├── 📄 BACKUP_INFO.txt                    # 备份信息
├── 📁 app/                              # 应用核心文件
├── 📁 templates/                        # 前端模板
├── 📁 session_data/                     # 会话数据  
├── 📄 run_app.py                        # 启动脚本(已修正)
├── 📄 MMP_PRD_2025.md                   # 产品需求文档
├── 📄 VERSION_SNAPSHOT_20250919.md      # 版本快照
└── 📄 其他配置和文档文件
```

### 备份信息
- **版本**: v1.2.0
- **日期**: 2025年9月19日 22:28
- **大小**: 1.2MB
- **状态**: ✅ 完整备份

## 🛠️ 版本管理操作

### 创建新版本备份
```bash
cd "/Users/mason/Desktop/code /mmp"
./backup_version.sh
```

### 恢复到指定版本
```bash
# 列出所有备份
ls -la ../mmp_backups/

# 恢复到指定版本
cp -r "../mmp_backups/mmp_v1.2.0_20250919_222845"/* .
```

### 比较版本差异
```bash
# 手动比较文件
diff run_app.py "../mmp_backups/mmp_v1.2.0_20250919_222845/run_app.py"

# 或使用工具
code --diff run_app.py "../mmp_backups/mmp_v1.2.0_20250919_222845/run_app.py"
```

## 📝 版本变更记录

### v1.2.0 (2025-09-19)
**主要更新**:
- ✅ 修复端口配置不一致问题 (5005 → 5001)
- ✅ 新增完整PRD产品需求文档
- ✅ 创建版本快照管理系统
- ✅ 服务成功启动并验证

**修改文件**:
- `run_app.py` - 端口配置修正
- `MMP_PRD_2025.md` - 新增
- `VERSION_SNAPSHOT_20250919.md` - 新增
- `backup_version.sh` - 新增

## 🔧 Git问题解决方案

### 问题诊断
```bash
# 当前Git错误
xcrun: error: invalid active developer path (/Applications/Xcode.app/Contents/Developer)
```

### 解决步骤
1. **重新安装Xcode命令行工具**:
   ```bash
   sudo rm -rf /Applications/Xcode.app/Contents/Developer
   xcode-select --install
   ```

2. **或者使用独立Git安装**:
   ```bash
   # 通过Homebrew安装
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   brew install git
   ```

3. **验证Git安装**:
   ```bash
   git --version
   ```

### 恢复Git使用后的操作
```bash
# 初始化仓库
git init

# 添加所有文件
git add .

# 提交当前版本
git commit -m "v1.2.0: 修复端口配置，新增PRD文档，创建版本管理系统"

# 设置远程仓库
git remote add origin <repository-url>

# 推送到远程
git push -u origin main
```

## 📋 临时版本管理检查清单

### 每次重要更新后:
- [ ] 运行 `./backup_version.sh` 创建备份
- [ ] 更新 `VERSION_SNAPSHOT_*.md` 文档
- [ ] 记录主要变更内容
- [ ] 测试服务启动和核心功能
- [ ] 验证备份完整性

### 备份验证步骤:
1. 检查备份目录是否创建成功
2. 确认核心文件是否完整复制
3. 验证BACKUP_INFO.txt内容正确
4. 测试恢复命令是否有效

## 🎯 下一步行动

### 立即任务:
1. ✅ 创建完整版本备份 
2. ✅ 建立版本管理文档
3. ⏳ 解决Git配置问题
4. ⏳ 提交代码到远程仓库

### 长期计划:
- 建立自动化备份脚本
- 集成CI/CD流水线  
- 完善版本标签管理
- 实现回滚自动化

---

**注**: 此文档作为Git问题期间的临时版本管理方案，一旦Git问题解决，应立即迁移到标准Git工作流。