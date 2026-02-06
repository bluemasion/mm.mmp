# MMP系统技术架构图

```
📱 前端用户界面层 (Frontend UI Layer)
├── 🏠 首页仪表板 (/)
├── 🔍 单物料模糊匹配 (/single-fuzzy-matching) ⭐
├── 📊 批量管理 (/batch_management)
├── 📤 数据导入 (/upload)
└── 🗂️ 分类管理 (/categories)

🌐 Web服务层 (Web Service Layer)
├── 🐍 Flask应用 (main.py, web_app.py)
├── 📋 Blueprint路由
│   ├── single_fuzzy_matching_api.py ⭐
│   ├── batch_management_api.py
│   └── upload_api.py
└── 🔧 中间件
    ├── 请求验证
    ├── 异常处理
    └── 日志记录

🧠 核心业务逻辑层 (Business Logic Layer)
├── 🎯 智能分类引擎
│   ├── 📝 参数提取器 (ParameterExtractor)
│   ├── 🤖 增强分类器 (EnhancedSmartClassifier) ⭐
│   ├── 🔍 相似物料匹配器 (SimilarMaterialMatcher)
│   └── 🏷️ 分类标准化引擎 (CategoryMappingEngine) ⭐新增
├── 📊 数据处理服务
│   ├── Excel解析器
│   ├── 批量处理器
│   └── 结果导出器
└── 🔄 工作流引擎
    ├── 会话管理
    ├── 状态跟踪
    └── 决策流程

💾 数据存储层 (Data Storage Layer)
├── 🗄️ 主数据库 (business_data.db)
│   ├── 物料主数据表
│   ├── 分类体系表
│   └── category_mapping表 ⭐新增
├── 📝 会话数据库 (sessions.db)
│   ├── 处理会话表
│   ├── 中间结果表
│   └── 用户操作记录
└── 📁 文件存储
    ├── 上传文件
    ├── 导出结果
    └── 系统日志

🔧 系统服务层 (System Service Layer)
├── 🚀 服务管理
│   ├── start_mmp_py38.sh
│   ├── stop_mmp.sh
│   └── 进程监控
├── 📊 监控日志
│   ├── mmp_service_py38.log
│   ├── 错误日志
│   └── 性能监控
└── 🔄 定时任务
    ├── 数据备份
    ├── 日志清理
    └── 性能优化

🌍 外部接口层 (External Interface Layer)
├── 🔌 REST API接口
│   ├── /api/single_fuzzy_matching ⭐
│   ├── /api/similar_materials/categories ⭐
│   ├── /api/similar_materials/search
│   └── /api/threshold/recommendations
├── 📤 文件接口
│   ├── Excel导入
│   ├── 数据导出
│   └── 模板下载
└── 🔗 第三方集成
    ├── 数据库连接
    ├── 外部API调用
    └── 文件系统访问
```

## 🎯 **核心数据流**

```
用户输入物料信息
         ↓
   参数提取器分析
         ↓
   智能分类器推荐
         ↓
   分类标准化映射 ⭐
         ↓
   相似物料匹配
         ↓
   结果综合展示
         ↓
   用户确认决策
```

## 🔄 **分类标准化流程** ⭐

```
原始分类
    ↓
category_mapping查询
    ↓
找到映射？
├── 是 → 返回标准分类 (绿色徽章)
└── 否 → 返回原始分类 (蓝色徽章)
    ↓
显示给用户
```

## 📊 **系统部署架构**

```
🖥️ 服务器环境
├── 🐍 Python 3.8 运行时
├── 🗄️ SQLite 数据库
├── 📁 文件系统存储
└── 🌐 HTTP服务 (端口5001)

🔄 进程管理
├── 主进程: PID 38665
├── 服务脚本: start_mmp_py38.sh
└── 监控日志: mmp_service_py38.log

🔗 网络配置
├── 内网地址: localhost:5001
├── 服务状态: 运行中 ✅
└── 端口监听: 正常 ✅
```

---

*系统架构说明: ⭐ 标记为最新完成的分类标准化功能相关组件*