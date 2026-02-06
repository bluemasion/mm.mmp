# MMP 物料主数据管理智能应用系统

> 🚀 **v2.1 智能模糊匹配增强版** - 2025年10月14日发布

**MMP (Material Master data Processing)** 是一个基于人工智能的物料主数据管理系统，专门为中文物料数据的智能分类、模糊匹配和批量处理而设计。

## ✨ 核心功能特性

### 🎯 智能模糊匹配 (🆕 v2.1新功能)
- **逐条模糊匹配**: 单个物料的智能相似物料推荐
- **批量模糊匹配**: Excel文件批量处理和匹配 (开发中)
- **阈值智能控制**: 30-80%可调节相似度阈值
- **双重推荐**: 近似物料 + 智能分类双重推荐

### 🧠 智能分类引擎
- **机器学习算法**: TF-IDF + 多算法集成
- **中文文本优化**: jieba分词和特征工程
- **高准确率**: 85%+ 分类准确率
- **76个类别**: 覆盖完整物料分类体系

### 📊 数据处理能力  
- **多格式支持**: Excel (.xlsx/.xls) 和 CSV 文件导入
- **智能数据清洗**: 自动检测和修复数据质量问题
- **批量操作**: 万级数据量高效处理
- **实时预览**: 处理过程实时监控和预览

### 🔧 工作流引擎
- **完整工作流**: 导入 → 分类 → 匹配 → 决策 → 导出
- **参数提取**: 智能识别规格参数和技术特征  
- **表单生成**: 自动化标准表单生成
- **历史追溯**: 完整的操作历史和回溯功能

## 🏗️ 系统架构

```
MMP System Architecture
├── 🌐 Web Frontend (Bootstrap 5 + jQuery)
│   ├── 逐条模糊匹配界面
│   ├── 批量处理界面  
│   ├── 数据导入导出界面
│   └── 系统管理界面
├── 🔧 Flask Backend
│   ├── single_fuzzy_matching_api.py    (模糊匹配API)
│   ├── web_app.py                      (主应用)
│   ├── workflow_service.py             (工作流引擎)  
│   └── smart_classifier.py             (智能分类器)
├── 🤖 AI Engine
│   ├── similar_material_matcher.py     (相似度算法)
│   ├── enhanced_smart_classifier.py    (增强分类器)
│   └── advanced_preprocessor.py        (数据预处理)
└── 💾 Data Layer
    ├── master_data.db                  (主数据库)
    ├── similar_materials table         (2000条相似物料)
    └── sessions.db                     (会话管理)
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 8GB+ 内存推荐
- macOS/Linux/Windows

### 安装和启动

1. **克隆项目**
```bash
git clone <repository-url>
cd mmp
```

2. **安装依赖**  
```bash
pip install -r requirements.txt
# 或者使用Python 3.8环境
pip install -r requirements_py36.txt
```

3. **启动服务**
```bash
# 推荐使用Python 3.8启动脚本
./start_mmp_py38.sh

# 或者直接启动
python3.8 run_app.py
```

4. **访问系统**
```
主页面: http://localhost:5001
逐条模糊匹配: http://localhost:5001/single-fuzzy-matching  
系统状态: http://localhost:5001/api/status
```

### 快速测试

```bash
# 测试模糊匹配API
curl -X POST "http://localhost:5001/api/single_fuzzy_matching" \
  -H "Content-Type: application/json" \
  -d '{
    "material": {
      "name": "疏水器", 
      "spec": "DN25 PN1.6"
    },
    "threshold": 0.5,
    "max_results": 5
  }'
```

## 📋 使用指南

### 逐条模糊匹配功能

1. **访问功能页面**
   - 打开 `http://localhost:5001/single-fuzzy-matching`

2. **输入物料信息**  
   - 物料名称: 输入要匹配的物料名称
   - 规格参数: 输入详细规格信息
   - 阈值设置: 调节相似度阈值 (推荐44%)

3. **查看匹配结果**
   - **近似物料**: 相似的已有物料推荐 (优先显示)
   - **推荐分类**: 智能分类系统推荐的物料类别
   - **相似度**: 百分比显示的匹配置信度

### 数据导入处理

1. **准备数据文件**
   - 支持格式: Excel (.xlsx/.xls) 或 CSV
   - 必需字段: 物料名称, 规格参数
   - 推荐字段: 物料编码, 单位, 描述

2. **上传和处理**  
   - 访问 `http://localhost:5001/upload`
   - 上传数据文件
   - 系统自动检测和清洗数据

3. **智能分类和匹配**
   - 系统自动进行智能分类
   - 查看分类结果和置信度
   - 手动调整和确认分类

4. **导出结果**
   - 下载处理后的标准格式数据
   - 生成分类报告和统计信息

## 🔧 配置说明

### 数据库配置
```python
# config.py 或 enhanced_config.py
DATABASE_CONNECTIONS = {
    'master_data': 'master_data.db',
    'business_data': 'business_data.db', 
    'sessions': 'sessions.db'
}
```

### 算法参数调优
```python
# 相似度匹配参数
SIMILARITY_THRESHOLD_DEFAULT = 0.44    # 默认阈值44%
MAX_SIMILAR_RESULTS = 20               # 最大返回结果数
TF_IDF_MAX_FEATURES = 5000            # TF-IDF特征数

# 智能分类参数  
CLASSIFICATION_CONFIDENCE_MIN = 0.1    # 最低分类置信度
MAX_CATEGORIES_RETURNED = 5            # 最大返回类别数
```

## 📊 性能指标

### 数据处理能力
- **处理速度**: 10,000条/分钟  
- **内存占用**: 2GB (万级数据)
- **并发用户**: 支持10+并发会话
- **响应时间**: API < 1秒响应

### 智能算法精度
- **分类准确率**: 85%+ (实测)
- **模糊匹配准确率**: 65%+ (相似度阈值50%)
- **中文分词准确率**: 95%+ (jieba分词)
- **参数提取准确率**: 80%+ (规格参数)

### 数据规模支持
- **相似物料数据库**: 2,000条基准数据
- **物料类别覆盖**: 76个完整类别
- **测试数据集**: 7,107条管道组件数据  
- **生产数据处理**: 支持10万级数据量

## 🛠️ 开发和扩展

### API 接口文档

#### 模糊匹配API
```http
POST /api/single_fuzzy_matching
Content-Type: application/json

{
  "material": {
    "name": "物料名称",
    "spec": "规格参数"  
  },
  "threshold": 0.5,
  "max_results": 10
}
```

#### 类别查询API
```http
GET /api/similar_materials/categories
```

#### 物料搜索API  
```http
POST /api/similar_materials/search
Content-Type: application/json

{
  "query": "搜索关键词",
  "category": "物料类别",
  "limit": 20
}
```

### 扩展开发

1. **添加新的匹配算法**
```python
# 继承SimilarMaterialMatcher类
class CustomMatcher(SimilarMaterialMatcher):
    def find_similar_materials(self, material_info, threshold, max_results):
        # 实现自定义匹配逻辑
        pass
```

2. **集成新的分类器**  
```python  
# 继承EnhancedSmartClassifier类
class CustomClassifier(EnhancedSmartClassifier):
    def classify_material(self, material_feature):
        # 实现自定义分类逻辑
        pass
```

3. **添加新的API端点**
```python
# 在Blueprint中添加新路由
@single_matching_bp.route('/api/custom_endpoint', methods=['POST'])
def custom_endpoint():
    # 实现自定义功能
    pass
```

## 📝 更新日志

### v2.1 (2025-10-14) - 智能模糊匹配增强版 🆕
- ✅ **新增**: 逐条模糊匹配功能完整实现
- ✅ **新增**: 2000条相似物料数据库
- ✅ **新增**: TF-IDF + 余弦相似度算法引擎  
- ✅ **新增**: 响应式Bootstrap前端界面
- ✅ **改进**: Flask Blueprint模块化架构
- ✅ **优化**: API性能和错误处理
- 🚧 **开发中**: 批量模糊匹配功能

### v2.0 (2024-12) - 智能分类系统
- ✅ 完整的智能分类引擎
- ✅ 工作流引擎和会话管理  
- ✅ 数据导入导出功能
- ✅ 用户界面和交互优化

### v1.0 (2024-06) - 基础版本
- ✅ Flask Web框架搭建
- ✅ 基础数据处理功能
- ✅ SQLite数据库集成

## 🤝 贡献指南

### 代码贡献
1. Fork 项目仓库
2. 创建功能分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`  
4. 推送分支: `git push origin feature/AmazingFeature`
5. 创建 Pull Request

### Bug报告
请使用 GitHub Issues 报告问题，包含:
- 问题描述和重现步骤
- 系统环境信息
- 错误日志和截图

### 功能请求
欢迎提出新功能建议:
- 详细描述功能需求
- 说明使用场景和价值
- 提供设计思路或参考

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 支持和联系

- **项目主页**: [GitHub Repository]
- **技术文档**: `/docs` 目录
- **问题报告**: [GitHub Issues]  
- **功能请求**: [GitHub Discussions]

## 🌟 致谢

感谢所有为项目做出贡献的开发者和用户，特别感谢：
- 中文分词技术支持: jieba项目
- 机器学习算法: scikit-learn项目  
- Web框架支持: Flask项目
- 前端UI框架: Bootstrap项目

---

**Made with ❤️ for intelligent material data processing**