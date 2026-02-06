# MMP 项目完整功能清单与需求整理

**更新日期**: 2026年2月6日  
**项目规模**: 132个Python文件 | 6.69 MB代码  
**当前状态**: v12232分支 + main分支

---

## 📋 核心功能模块总览

### 1️⃣ 物料主数据管理（Material Master Data）
**相关文件**：
- `app/master_data_manager.py` - 主数据管理
- `app/business_data_manager.py` - 业务数据管理
- `app/data_loader.py` - 数据加载
- `init_master_data.py` - 数据初始化
- `init_database.py` - 数据库初始化

**功能清单**：
- ✅ 物料数据导入（Excel/CSV）
- ✅ 物料搜索与查询
- ✅ 主数据维护与更新
- ✅ 字段映射管理
- ✅ 业务数据模板配置

**关键API**：
- `GET /api/master_data/materials/search` - 搜索物料
- `GET /api/master_data/categories` - 获取分类列表
- `GET /api/field_mappings` - 获取字段映射
- `POST /api/field_mappings` - 创建字段映射

---

### 2️⃣ 智能分类系统（Smart Classification）
**相关文件**：
- `app/smart_classifier.py` - 智能分类器核心
- `app/unified_classifier.py` - 统一分类器
- `app/external_classifier.py` - 外部分类器适配
- `enhanced_classifier_methods.py` - 分类方法实现
- `enhanced_classifier_config.json` - 分类规则配置（76个类别）

**功能清单**：
- ✅ TF-IDF + 多算法融合分类
- ✅ 单物料智能分类
- ✅ 批量物料分类
- ✅ 分类规则热加载
- ✅ 分类准确率评估（85%+）
- ✅ 质量评估与优化建议

**关键API**：
- `POST /api/smart_classification` - 单物料分类
- `POST /api/batch_recommend` - 批量分类推荐
- `POST /api/classify` - 统一分类接口
- `POST /api/quality/classify-with-quality` - 带质量评估的分类
- `GET /api/categories/tree` - 分类树形结构
- `GET /api/categories/search` - 分类搜索

---

### 3️⃣ 模糊匹配引擎（Fuzzy Matching）
**相关文件**：
- `app/material_matching_engine.py` - 匹配引擎
- `app/matcher.py` - 基础匹配器
- `app/advanced_matcher.py` - 高级匹配器
- `similar_material_matcher.py` - 相似物料匹配
- `single_fuzzy_matching_api.py` - 逐条模糊匹配API

**功能清单**：
- ✅ 精确匹配（厂家、分类）
- ✅ 模糊匹配（规格、名称）
- ✅ 相似物料推荐
- ✅ 可调阈值（30-80%）
- ✅ 逐条模糊匹配界面
- ✅ 批量模糊匹配处理
- ✅ 相似度算法优化

**关键API**：
- `POST /api/single_fuzzy_matching` - 逐条模糊匹配
- `POST /api/batch_material_matching` - 批量匹配
- `POST /api/similar_materials/search` - 物料搜索
- `GET /api/similar_materials/categories` - 类别列表

---

### 4️⃣ 数据去重系统（Deduplication）
**相关文件**：
- `app/material_deduplication_engine.py` - 去重引擎
- `app/integrated_deduplication_manager.py` - 去重管理器
- `app/deduplication_api.py` - 去重API接口

**功能清单**：
- ✅ 重复物料检测
- ✅ 去重分析与建议
- ✅ 批量合并执行
- ✅ 去重仪表板
- ✅ 用户反馈机制
- ✅ 冲突解决管理

**关键API**：
- `POST /api/deduplication/analyze` - 去重分析
- `POST /api/deduplication/merge` - 执行合并
- `GET /api/deduplication/dashboard` - 去重仪表板
- `POST /api/deduplication/feedback` - 提交反馈
- `GET /api/deduplication/status` - 获取状态

---

### 5️⃣ 数据质量评估（Quality Assessment）
**相关文件**：
- `app/base_quality_assessment.py` - 质量评估基础
- `app/quality_api.py` - 质量评估API

**功能清单**：
- ✅ 单物料质量评分
- ✅ 批量质量评估
- ✅ 数据质量建议
- ✅ 与分类器集成评估
- ✅ 质量指标报告

**关键API**：
- `POST /api/quality/assess` - 单物料评估
- `POST /api/quality/batch-assess` - 批量评估
- `POST /api/quality/classify-with-quality` - 分类+质量评估

---

### 6️⃣ 增量同步系统（Incremental Sync）
**相关文件**：
- `app/simplified_incremental_sync.py` - 简化版同步
- `app/hybrid_sync_engine.py` - 混合同步引擎
- `app/sync_api.py` - 同步API接口

**功能清单**：
- ✅ 增量同步检测
- ✅ 外部数据源对接
- ✅ 冲突自动解决
- ✅ 手动审核流程
- ✅ 同步状态报告
- ✅ 增量更新管理

**关键API**：
- `POST /api/sync/from-source` - 从外部源同步
- `GET /api/sync/status` - 获取同步状态
- `GET /api/sync/conflicts` - 获取冲突记录

---

### 7️⃣ 工作流引擎（Workflow Service）
**相关文件**：
- `app/workflow_service.py` - 工作流服务核心
- `app/web_app.py` - Web应用主文件（2346行）

**功能清单**：
- ✅ 完整工作流：导入 → 分类 → 匹配 → 决策 → 导出
- ✅ 参数提取（规格、DN、PN等）
- ✅ 表单自动生成
- ✅ 历史回溯与审计
- ✅ 会话管理
- ✅ 批量处理协调

**关键API**：
- `POST /api/material-workflow/process` - 工作流处理
- `POST /api/batch_material_matching` - 批量匹配
- `POST /api/upload_material_data` - 数据上传
- `POST /api/save_workflow_results` - 保存结果
- `GET /api/status` - API状态检查

---

### 8️⃣ 统一API接口（Unified API v2）
**相关文件**：
- `app/unified_api.py` - 统一API主文件

**功能清单**：
- ✅ 健康检查接口
- ✅ 统一分类接口
- ✅ 综合物料处理
- ✅ 批量处理协调
- ✅ 系统仪表板
- ✅ API文档与文档生成

**关键API**：
- `GET /api/v2/health` - 健康检查
- `POST /api/v2/classify` - 统一分类
- `POST /api/v2/process-material` - 综合处理
- `POST /api/v2/batch-process` - 批量处理
- `GET /api/v2/dashboard` - 仪表板数据
- `GET /api/v2/docs` - API文档

---

### 9️⃣ 数据处理管道（Data Pipeline）
**相关文件**：
- `app/advanced_preprocessor.py` - 高级预处理器
- `app/preprocessor.py` - 基础预处理器
- `app/data_source_recognizer.py` - 数据源识别
- `app/manufacturing_adapter.py` - 制造业适配器
- `app/medical_adapter.py` - 医疗业适配器

**功能清单**：
- ✅ 中文分词（jieba）
- ✅ 数据清洗与标准化
- ✅ 参数自动提取
- ✅ 多行业适配器
- ✅ 特殊字符处理

---

### 🔟 数据库与会话管理（Database & Session）
**相关文件**：
- `app/database_connector.py` - 数据库连接器
- `app/database_session_manager.py` - 会话管理器
- `init_database.py` - 数据库初始化

**功能清单**：
- ✅ SQLite（开发）/ PostgreSQL（生产）双模式
- ✅ ORM模型：Material, MatchingRecord, ProcessingSession
- ✅ 会话数据存储
- ✅ Redis缓存支持
- ✅ 事务管理

**相关表**：
- `materials` - 物料主数据
- `matching_records` - 匹配记录
- `processing_sessions` - 处理会话
- `system_logs` - 系统日志

---

## 🎯 前端功能页面

**已实现的页面**（见 `templates/` 目录）：
- ✅ 首页（index.html）
- ✅ 批量处理（batch_management.html）
- ✅ 逐条模糊匹配（single_fuzzy_matching.html）
- ✅ 分类选择（category_selection.html）
- ✅ 表单生成（form_generation.html）
- ✅ 物料匹配（matching.html）
- ✅ 决策界面（decision.html）
- ✅ 结果展示（results.html）
- ✅ 分类管理（categories.html）
- ✅ 智能分类（smart_classification.html）

---

## 🔧 高级功能模块

### 错误处理系统
**文件**：`app/error_handler.py`
- 统一错误响应格式
- 安全的API装饰器
- 堆栈跟踪隐藏

### 强化功能管理
**可选功能**：
- `ADVANCED_PREPROCESSOR_AVAILABLE` - 高级预处理器
- `ENHANCED_CONFIG_AVAILABLE` - 增强配置
- `ERROR_HANDLER_AVAILABLE` - 错误处理器
- 所有功能都有降级回退机制

### 训练数据管理
**文件**：`app/training_data_manager.py`
- 分类模型训练数据管理
- 特征工程

---

## 📊 系统架构概览

```
MMP System
├── 📥 数据层
│   ├── SQLite/PostgreSQL 数据库
│   ├── Redis 缓存
│   └── Session 存储
├── 🎯 业务逻辑层
│   ├── 智能分类系统
│   ├── 模糊匹配引擎
│   ├── 去重系统
│   ├── 质量评估
│   ├── 增量同步
│   └── 工作流引擎
├── 🔌 API 接口层
│   ├── 传统API（向后兼容）
│   ├── 统一API v2
│   ├── 去重API
│   ├── 质量API
│   └── 同步API
├── 💻 前端展示层
│   ├── Bootstrap 5 UI
│   ├── jQuery 交互
│   └── 实时预览
└── 🛠️ 配置与初始化
    ├── enhanced_classifier_config.json
    ├── database_config.ini
    └── config.py
```

---

## 🚀 部署模式

### 本地开发
- `python run_app.py` → 5001端口
- `python api.py` → 5000端口（简化版）

### Docker容器
- `docker-compose up` → 完整服务栈
  - mmp-app (5001)
  - mmp-postgres (5432)
  - mmp-redis (6379)
  - mmp-nginx (80/443)
  - mmp-prometheus (9090) - 可选
  - mmp-grafana (3000) - 可选

---

## ✅ 功能完整度评估

| 功能模块 | 完成度 | 状态 | 备注 |
|---------|--------|------|------|
| 物料主数据管理 | 95% | ✅ | 字段映射配置完整 |
| 智能分类系统 | 95% | ✅ | 76个类别，85%准确率 |
| 模糊匹配引擎 | 100% | ✅ | 单/批量均支持 |
| 数据去重系统 | 90% | ✅ | 冲突解决需完善 |
| 质量评估系统 | 85% | ⚠️ | 指标体系可扩展 |
| 增量同步系统 | 80% | ⚠️ | 外部源对接待测试 |
| 工作流引擎 | 95% | ✅ | 端到端完整 |
| 统一API v2 | 85% | ⚠️ | 部分端点需注册 |
| 前端UI | 90% | ✅ | 响应式设计完整 |
| Docker部署 | 100% | ✅ | 生产就绪 |

---

## ⚠️ 已知问题与待优化项

1. **API路由注册** - `/api/v2/*` 端点部分未注册到主Flask应用
2. **Blueprint集成** - `deduplication_bp`, `quality_bp`, `sync_bp` 需在web_app.py注册
3. **外部源对接** - 增量同步的真实数据源对接需测试
4. **监控系统** - Prometheus/Grafana集成可选但未验证
5. **性能优化** - 大规模数据处理（10000+条）的性能基准待测
6. **文档同步** - 部分文档与代码实现不同步

---

## 📚 核心配置文件

| 文件名 | 功能 | 优先级 |
|--------|------|--------|
| `enhanced_classifier_config.json` | 分类规则（7082行） | 🔴 关键 |
| `config.py` | 应用配置 | 🔴 关键 |
| `database_config.ini` | 数据库连接 | 🔴 关键 |
| `docker-compose.yml` | 容器编排 | 🟠 重要 |
| `Dockerfile` | 镜像构建 | 🟠 重要 |
| `.github/copilot-instructions.md` | AI开发指南 | 🟡 参考 |

---

## 🎯 后续优化方向

**高优先级**：
1. [ ] API端点完全注册与测试
2. [ ] Blueprint统一集成
3. [ ] 性能基准测试
4. [ ] 端到端自动化测试

**中优先级**：
5. [ ] 外部数据源真实对接测试
6. [ ] 监控告警系统
7. [ ] 日志统一收集
8. [ ] 权限控制系统

**低优先级**：
9. [ ] UI主题自定义
10. [ ] 国际化支持
11. [ ] 插件扩展机制
12. [ ] 高可用部署方案

---

**生成于**: 2026年2月6日  
**项目语言**: Python 3.8+  
**主要框架**: Flask, SQLAlchemy, scikit-learn  
**前端**: Bootstrap 5, jQuery
