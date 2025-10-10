# 🚀 MMP项目上下文生成器 - 快速使用指南

## 📱 一键使用

```bash
# 方法1: 使用快速脚本（推荐）
./quick_context.sh

# 方法2: 直接运行生成器  
python3.8 project_context_generator.py

# 方法3: Python3通用版本
python3 project_context_generator.py
```

## 🎯 使用步骤

### 第一步：生成上下文
```bash
cd /Users/mason/Desktop/code\ /mmp
./quick_context.sh
```

### 第二步：复制内容
生成的文件名格式：`PROJECT_CONTEXT_SNAPSHOT_20250120_143022.md`

**macOS复制到剪贴板：**
```bash
cat PROJECT_CONTEXT_SNAPSHOT_20250120_143022.md | pbcopy
```

**查看文件大小：**
```bash
ls -lh PROJECT_CONTEXT_SNAPSHOT_*.md
```

### 第三步：在AI会话中使用
1. 开启新的AI对话
2. 粘贴完整的上下文内容
3. 说明你的需求开始开发

## 📊 生成内容包含

✅ **环境信息**
- Python版本：3.8.10
- 操作系统：macOS 
- 项目依赖：57个包（requirements.txt）

✅ **项目结构**  
- 核心文档：README.md, 配置文件等
- Python代码：类、函数、行数统计
- 数据库：5个SQLite文件的表结构

✅ **关键文档**
- API文档、部署指南
- 功能增强计划、需求分析
- 技术架构和数据库设计

## ⚡ 快速技巧

**查看最新快照：**
```bash
ls -t PROJECT_CONTEXT_SNAPSHOT_*.md | head -1
```

**计算内容大小：**
```bash
wc -l PROJECT_CONTEXT_SNAPSHOT_*.md | tail -1
# 通常输出 ~600行
```

**清理旧快照：**
```bash
# 保留最新5个，删除其他
ls -t PROJECT_CONTEXT_SNAPSHOT_*.md | tail -n +6 | xargs rm -f
```

## 🔧 自定义配置

编辑 `project_context_generator.py` 中的配置：

```python
# 修改包含的文档类型
CORE_DOCUMENTS = [
    '*.md', '*.txt', '*.ini', 
    'requirements*.txt'  # 可添加更多
]

# 修改Python文件包含范围  
PYTHON_FILES = [
    '*.py'  # 可添加特定目录
]
```

## ❓ 常见问题

**Q: 脚本提示权限错误？**
```bash
chmod +x quick_context.sh
```

**Q: Python版本不对？**
```bash
# 检查可用版本
python3.8 --version
python3 --version  
python --version
```

**Q: 生成失败怎么办？**
```bash
# 直接运行查看错误
python3.8 project_context_generator.py
```

**Q: 内容太大无法复制？**
- 快照通常600行，约30KB
- 如果太大，可以编辑生成器减少内容

## 🎉 使用效果

使用此工具后，你可以：
- ✅ 在任何新AI会话中快速恢复项目上下文
- ✅ 避免重复解释项目结构和需求  
- ✅ 保持开发的连续性和一致性
- ✅ 让AI快速理解你的MMP项目全貌

---

**💡 提示：建议每次重要代码修改后重新生成快照，保持上下文的时效性！**