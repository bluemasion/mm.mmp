# MMP系统部署更新指南

## 📋 更新概览

**更新日期**: 2025年9月17日  
**更新类型**: 重要修复更新（解决相对导入问题）  
**影响范围**: 28个核心文件 + 新增启动脚本  
**Python版本要求**: 3.8+

## 🔄 更新内容

### 修复的核心问题
1. **相对导入问题** - 修复了 `ImportError: attempted relative import with no known parent package` 错误
2. **启动方式优化** - 新增 `run_app.py` 统一启动脚本
3. **模块依赖优化** - 优化了各模块间的导入关系

### 更新的文件列表
```
核心应用文件:
✓ app/web_app.py            - Flask主应用
✓ app/workflow_service.py   - 工作流服务
✓ app/data_loader.py        - 数据加载器
✓ app/database_connector.py - 数据库连接器
✓ app/advanced_matcher.py   - 高级匹配器
✓ app/advanced_preprocessor.py - 高级预处理器
✓ app/matcher.py            - 基础匹配器
✓ app/preprocessor.py       - 基础预处理器

新增文件:
+ run_app.py                - 统一启动脚本
+ upgrade_python38_centos7.sh - Python升级脚本
+ verify_mmp_python38.sh    - 验证脚本
+ CENTOS7_PYTHON38_UPGRADE.md - 升级指南

配置和模板文件:
✓ requirements.txt          - 依赖配置
✓ config.py                - 应用配置
✓ templates/*.html          - 前端模板
```

## 🚀 部署建议

### 推荐方案：**完整更新部署**

**理由**：
- 修复了关键的相对导入问题
- 优化了应用启动方式
- 提供了更好的错误处理
- 兼容Python 3.8环境

## 📦 部署步骤

### 步骤1: 备份现有系统
```bash
# 在服务器上创建备份
cd /path/to/production/mmp
cp -r . ../mmp_backup_$(date +%Y%m%d_%H%M%S)
```

### 步骤2: 上传新版本文件
```bash
# 方法A: 使用rsync同步（推荐）
rsync -avz --exclude='.DS_Store' --exclude='__pycache__' \
      /Users/mason/Desktop/code\ /mmp/ \
      user@server:/path/to/production/mmp/

# 方法B: 使用scp上传压缩包
cd "/Users/mason/Desktop/code /mmp"
tar --exclude='.DS_Store' --exclude='__pycache__' \
    -czf mmp_update_$(date +%Y%m%d).tar.gz .
scp mmp_update_*.tar.gz user@server:/tmp/
```

### 步骤3: 在服务器上解压和部署
```bash
# 如果使用压缩包方式
cd /path/to/production/mmp
tar -xzf /tmp/mmp_update_*.tar.gz

# 设置执行权限
chmod +x run_app.py
chmod +x upgrade_python38_centos7.sh
chmod +x verify_mmp_python38.sh
chmod +x start_mmp.sh
```

### 步骤4: 验证Python环境
```bash
# 运行验证脚本
cd /path/to/production/mmp
bash verify_mmp_python38.sh
```

### 步骤5: 安装/更新依赖
```bash
# 升级pip并安装依赖
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
```

### 步骤6: 测试启动
```bash
# 使用新的启动脚本测试
python3 run_app.py

# 如果测试成功，按Ctrl+C停止，然后后台运行
nohup python3 run_app.py > app.log 2>&1 &
```

## 🔍 启动方式对比

### 旧方式（有问题）
```bash
python3 app/web_app.py  # ❌ 会出现相对导入错误
```

### 新方式（推荐）
```bash
python3 run_app.py      # ✅ 正确的启动方式
```

## 🎯 关键改进点

### 1. 解决相对导入问题
**之前**:
```python
from .workflow_service import MaterialWorkflowService  # ❌
```

**现在**:
```python
from app.workflow_service import MaterialWorkflowService  # ✅
```

### 2. 统一启动入口
- 新增 `run_app.py` 作为统一启动脚本
- 自动处理Python路径设置
- 提供详细的启动信息

### 3. 更好的错误处理
- 改进了模块导入的错误处理
- 提供更清晰的错误信息

## 🚨 重要注意事项

### 启动命令变更
```bash
# 旧命令（不再使用）
python3 app/web_app.py

# 新命令（必须使用）
python3 run_app.py
```

### 生产环境启动
```bash
# 开发测试
python3 run_app.py

# 生产环境（后台运行）
nohup python3 run_app.py > /var/log/mmp/app.log 2>&1 &

# 使用Gunicorn（推荐生产环境）
gunicorn -w 4 -b 0.0.0.0:5000 --chdir /path/to/mmp run_app:app
```

## 📋 部署检查清单

### 部署前检查
- [ ] 备份现有系统
- [ ] 确认Python 3.8环境
- [ ] 检查磁盘空间
- [ ] 停止现有服务

### 部署中检查
- [ ] 文件上传完成
- [ ] 权限设置正确
- [ ] 依赖安装成功
- [ ] 配置文件正确

### 部署后验证
- [ ] 运行验证脚本通过
- [ ] 应用启动成功
- [ ] 网页访问正常
- [ ] 核心功能测试通过
- [ ] 日志没有错误

## 🆘 回滚方案

如果新版本有问题，快速回滚：

```bash
# 停止新服务
pkill -f "python3 run_app.py"

# 恢复备份
cd /path/to/production
rm -rf mmp
mv mmp_backup_* mmp

# 重启旧服务
cd mmp
python3 app/web_app.py  # 或使用原来的启动方式
```

## 🎉 更新后的优势

1. **稳定性提升** - 解决了导入错误问题
2. **维护便利** - 统一的启动方式
3. **扩展性增强** - 更好的模块组织
4. **部署简化** - 完整的部署脚本和文档

## 📞 技术支持

如果部署过程中遇到问题：

1. 检查 `app.log` 日志文件
2. 运行 `verify_mmp_python38.sh` 诊断
3. 确认Python版本和依赖安装
4. 必要时使用回滚方案

---

**结论**: 强烈建议部署这个更新版本，它解决了关键的运行时错误，提供了更稳定的系统基础。
