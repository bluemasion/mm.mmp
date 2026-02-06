## MMP 物料主数据管理系统 - AI 开发指南

专为 AI 编码代理设计的快速上手文档,涵盖架构核心、关键工作流和项目特定约定。

---

## ⚠️ 重要提醒：本项目使用 Python 3.8

**所有命令、脚本执行必须使用 `python3.8` 而非 `python` 或 `python3`**

- ✅ 正确: `python3.8 run_app.py`
- ✅ 正确: `python3.8 -m pytest`
- ❌ 错误: `python run_app.py` (可能调用错误版本)
- ❌ 错误: `python3 api.py` (可能调用系统默认版本)

---

## 🔗 GitHub 版本控制

### 快速对接（一键脚本）

```bash
./git_setup.sh  # 交互式配置 Git 和 GitHub 连接
```

### 手动设置流程

1. **在 GitHub 创建仓库**: https://github.com/new
   - 仓库名建议: `mmp-material-management`
   - **不要勾选** "Initialize with README"（本地已有文件）

2. **本地关联远程仓库**:
```bash
git remote add origin git@github.com:username/mmp-material-management.git
# 或使用 HTTPS: https://github.com/username/mmp-material-management.git
```

3. **推送代码**:
```bash
git branch -M main
git push -u origin main
```

### 常用 Git 操作

```bash
git status              # 查看状态
git add .               # 添加所有更改
git commit -m "说明"    # 提交
git push                # 推送到 GitHub
git pull                # 拉取最新代码
git checkout -b feat/new-feature  # 创建新分支
```

### 问题排查

**Xcode 路径错误**:
```bash
sudo xcode-select --switch /Library/Developer/CommandLineTools
git --version  # 验证 Git 可用
```

详细文档: [GITHUB_SETUP.md](GITHUB_SETUP.md)

---

## 🏗️ 核心架构

### 技术栈

- **Python 3.8** + Flask 框架
- **数据库**: 开发环境 SQLite,生产环境 PostgreSQL + Redis
- **机器学习**: scikit-learn (TF-IDF), jieba 分词
- **部署**: Docker Compose(4服务编排:app/postgres/redis/nginx)

### 三层服务入口(理解端口分配)

- **生产环境**: `python run_app.py` → `app/web_app.py`,端口 **5001**,多线程模式
- **开发调试**: `python api.py`,端口 **5000**,精简 API(仅 `/match` 端点),快速验证核心逻辑
- **容器部署**: `docker-compose up` 编排 4 服务,构建时自动执行数据库初始化脚本

### 数据层架构

**双模式运行**:
- 开发: SQLite (`data/production.db`)
- 生产: PostgreSQL + Redis(通过 `DATABASE_URL` 环境变量切换)

**ORM 模型** (`init_database.py`):
- `Material` - 物料主数据
- `MatchingRecord` - 匹配历史
- `ProcessingSession` - 批量处理会话
- `MaterialCategory` - 物料分类(548 个类别)

### ⚠️ 全局服务实例模式(性能关键)

**这是系统最严重的性能陷阱**

`app/workflow_service.py` 的 `MaterialWorkflowService` 在**模块导入时实例化一次**(加载 TF-IDF 模型、2000+ 主数据、分类器)
- `app/web_app.py` (2346行) 在模块顶层调用 `init_service()` 创建全局 `workflow_service`
- **禁止在路由函数内创建新服务实例** —— 这会导致每次请求重新加载模型,造成严重性能问题

```python
# ✅ 正确做法:复用全局实例
@app.route('/api/classify', methods=['POST'])
def classify():
    return workflow_service.classify(request.json)

# ❌ 错误做法:每次请求创建新实例
@app.route('/api/classify', methods=['POST'])
def classify():
    service = MaterialWorkflowService()  # 严重性能问题!
    return service.classify(request.json)
```

### 可选功能降级机制

- 多处使用 `try-except ImportError` + `*_AVAILABLE` 标志(`ADVANCED_PREPROCESSOR_AVAILABLE`、`ERROR_HANDLER_AVAILABLE`)
- 当增强模块不可用时自动回退到基础实现,确保系统在依赖缺失时仍可运行
- **修改增强功能时必须保留降级逻辑**,否则破坏系统弹性

### 智能分类系统(配置驱动架构)

- **规则存储**: `enhanced_classifier_config.json` (7082行) - 定义 548 个物料类别、关键词映射表、层级关系、优先级
- **算法实现**: `enhanced_classifier_methods.py` (规格模式) + `app/smart_classifier.py` (TF-IDF + 多算法融合)
- **数据处理管道**: `app/advanced_preprocessor.py` → `app/material_matching_engine.py` → 分类器

---

## 🔧 开发工作流速查

### 本地启动(按场景选择)

```bash
# 推荐:快速开发(SQLite,无需 Docker)
python3.8 run_app.py              # 访问 http://localhost:5001

# 最小化 API 测试(仅核心匹配功能)
python3.8 api.py                  # 访问 http://localhost:5000/match

# 生产环境(Docker)
docker-compose up -d              # 启动完整服务栈
```

### 测试执行

**集成测试**: `enhanced_integration_test.py` - HTTP 端到端测试
```bash
python3.8 enhanced_integration_test.py  # 默认连接 localhost:5001
```

**单元测试**: `test_*.py` 文件
```bash
python3.8 -m pytest tests/        # 如果有 tests 目录
```

### 数据库操作

```bash
# 初始化/重建(⚠️ 会清空数据)
python3.8 init_database.py

# 查看 SQLite 数据
sqlite3 data/production.db "SELECT * FROM materials LIMIT 10;"

# 容器内操作 PostgreSQL
docker exec -it mmp-postgres psql -U mmp_user -d mmp_db
```

### 部署脚本

- `deploy.sh` - 生产环境一键部署
- `deploy_update.sh` - 增量更新

---

## 📝 常见修改场景

### 场景 1: 新增/调整分类规则

1. **编辑**: `enhanced_classifier_config.json`
2. **测试**: `curl -X POST http://localhost:5001/api/recommend_categories ...`
3. **无需重启服务** - 配置文件支持热加载

### 场景 2: 添加新 API 端点

1. 在 `app/web_app.py` 中添加路由,**复用全局** `workflow_service`
2. 在 `app/workflow_service.py` 中实现业务逻辑
3. 更新 `enhanced_integration_test.py` 测试用例

### 场景 3: 修改数据库模式

1. 编辑 `init_database.py` 中的 SQLAlchemy 模型
2. 重新初始化: `python3.8 init_database.py`
3. ⚠️ 生产环境需手动编写 SQL 迁移脚本(系统无 Alembic)

---

## ⚠️ 关键约束与陷阱

### 路径处理规范

- 所有文件操作必须基于项目根目录
- 禁止使用相对路径

### Docker 构建陷阱

- `Dockerfile` 在构建期运行 `python init_database.py`
- PostgreSQL 的 `init_scripts/` 仅在容器首次创建时运行
- 需要重置?删除卷:`docker-compose down -v`

### 并发限制

- SQLite 存在并发写入锁,生产环境必须使用 PostgreSQL

### 配置文件优先级

1. `enhanced_classifier_config.json` - 分类规则(548 类别)
2. `database_config.ini` - 数据库连接配置
3. `config.py` - 应用级配置

---

## 🔍 快速定位代码

### 核心服务初始化流程

1. `run_app.py` 启动 Flask
2. `app/web_app.py` (行175) 调用 `init_service()` 创建全局服务
3. `app/workflow_service.py` (行30-45) 初始化数据、匹配器、预处理器

### 数据处理管道

```
用户上传 Excel/CSV
   ↓
[app/data_loader.py] 数据加载
   ↓
[app/advanced_preprocessor.py] 中文分词、参数提取
   ↓
[app/material_matching_engine.py] 模糊匹配
   ↓
[app/smart_classifier.py] TF-IDF 分类
   ↓
结果返回
```

### 关键文件索引

**核心服务**:
- `app/web_app.py` - 主应用 (2346 行)
- `app/workflow_service.py` - 工作流引擎

**数据处理**:
- `app/advanced_preprocessor.py` - 高级预处理器
- `enhanced_classifier_methods.py` - 分类算法实现

**配置与初始化**:
- `config.py` - 应用配置
- `enhanced_classifier_config.json` - 分类规则 (7082行)
- `init_database.py` - 数据库初始化 (266行)

---

## 📋 提交 Checklist

在提交 PR 前确认:

- [ ] 指明改动的配置文件(JSON/INI)及是否影响 Docker 镜像构建
- [ ] 数据库模式变更说明了向后兼容策略(系统无 Alembic 迁移)
- [ ] 修改分类规则附上 5-10 条测试样例和预期分类结果
- [ ] 新增路由复用了全局 `workflow_service`,未在函数内重新实例化
- [ ] 增强功能保留了降级逻辑(`try-except ImportError` + `*_AVAILABLE`)
- [ ] 运行了 `enhanced_integration_test.py` 验证核心功能
- [ ] 更新了相关文档(如本文件)
