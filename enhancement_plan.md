# MMP系统完善计划

## Phase 1: 核心功能增强（1-2个月）

### 1.1 增强数据处理能力
```python
# 新增文件：app/data_extractor.py
class DataExtractor:
    def extract_from_excel(self, file_path):
        """处理多sheet Excel，支持.xlsx/.xls"""
        pass
    
    def extract_from_ocr(self, image_path):
        """OCR文字识别 - 使用PaddleOCR/Tesseract"""
        pass
    
    def extract_from_pdf(self, pdf_path):
        """PDF文档解析 - 使用PyPDF2/pdfplumber"""
        pass
```

### 1.2 智能分词与参数提取
```python
# 增强：app/preprocessor.py
import jieba
import re
from collections import defaultdict

class AdvancedPreprocessor:
    def __init__(self):
        self.brand_patterns = [
            r'[\u4e00-\u9fff]+(?:集团|公司|厂|制药)',
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*'
        ]
        self.spec_patterns = [
            r'\d+(?:\.\d+)?[mg|ml|g|l|kg|片|粒|支|盒]',
            r'\d+[*×]\d+(?:[*×]\d+)?'
        ]
    
    def extract_parameters(self, text):
        """提取关键参数：品牌、规格、型号等"""
        words = jieba.lcut(text)
        params = defaultdict(list)
        
        # 品牌提取
        for pattern in self.brand_patterns:
            matches = re.findall(pattern, text)
            params['brand'].extend(matches)
        
        # 规格提取  
        for pattern in self.spec_patterns:
            matches = re.findall(pattern, text)
            params['specification'].extend(matches)
            
        return dict(params)
    
    def recommend_category_advanced(self, params):
        """基于参数的高级分类推荐"""
        # 使用机器学习分类器或规则引擎
        pass
```

### 1.3 分类推荐系统
```python
# 新增：app/category_recommender.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

class CategoryRecommender:
    def __init__(self, category_api_endpoint):
        self.api_endpoint = category_api_endpoint
        self.category_tree = self.load_category_tree()
        self.classifier = None
        self.vectorizer = TfidfVectorizer()
    
    def load_category_tree(self):
        """从API加载分类体系"""
        pass
    
    def train_classifier(self, training_data):
        """训练分类器"""
        pass
    
    def recommend(self, material_text, top_k=3):
        """推荐分类，返回置信度排序结果"""
        pass
```

### 1.4 特征模型表单生成
```python
# 新增：app/feature_model.py
class FeatureModelManager:
    def __init__(self):
        self.models = {}  # 分类ID -> 特征模型映射
    
    def get_feature_model(self, category_id):
        """获取分类的特征模型"""
        pass
    
    def generate_form(self, category_id, extracted_params):
        """生成动态表单并预填充"""
        model = self.get_feature_model(category_id)
        form = {}
        
        for field in model['fields']:
            # 自动匹配提取的参数到表单字段
            if field['name'] in extracted_params:
                form[field['name']] = self.normalize_value(
                    extracted_params[field['name']], 
                    field['type']
                )
        return form
    
    def normalize_value(self, value, field_type):
        """值标准化处理"""
        pass
```

## Phase 2: 高级匹配策略（2-3个月）

### 2.1 属性级匹配
```python
# 增强：app/matcher.py
class AdvancedMaterialMatcher:
    def __init__(self, df_master, rules, feature_models):
        self.feature_models = feature_models
        # ... 现有初始化代码
    
    def find_matches_by_attributes(self, new_item, category_id, top_n=3):
        """按属性分别匹配"""
        model = self.feature_models.get_feature_model(category_id)
        
        # 1. 严格匹配字段
        candidates = self.df_master.copy()
        for field in model['strict_fields']:
            if field in new_item:
                candidates = candidates[candidates[field] == new_item[field]]
        
        # 2. 模糊匹配字段 - 分别计算相似度
        similarity_scores = {}
        for field in model['fuzzy_fields']:
            field_similarity = self.calculate_field_similarity(
                new_item[field], candidates[field]
            )
            similarity_scores[field] = field_similarity
        
        # 3. 加权组合相似度
        final_scores = self.combine_similarities(
            similarity_scores, model['field_weights']
        )
        
        return candidates.assign(similarity=final_scores).nlargest(top_n, 'similarity')
```

### 2.2 配置化匹配规则
```python
# 增强：config.py
ADVANCED_MATCH_CONFIG = {
    'similarity_threshold': 0.7,
    'field_weights': {
        'product_name': 0.4,
        'specification': 0.3,
        'brand': 0.2,
        'model': 0.1
    },
    'description_concat_template': '{product_name} {specification} {brand}',
    'custom_similarity_functions': {
        'specification': 'spec_similarity',
        'model': 'model_similarity'
    }
}
```

## Phase 3: 业务流程集成（3-4个月）

### 3.1 决策支持界面
```python
# 新增：app/decision_engine.py
class MaterialDecisionEngine:
    def __init__(self, threshold_config):
        self.thresholds = threshold_config
    
    def analyze_matches(self, matches):
        """分析匹配结果，给出建议"""
        if not matches:
            return {'action': 'create_new', 'confidence': 1.0}
        
        best_match = matches.iloc[0]
        if best_match['similarity'] >= self.thresholds['high_confidence']:
            return {
                'action': 'update_existing', 
                'target_id': best_match['id'],
                'confidence': best_match['similarity']
            }
        elif best_match['similarity'] >= self.thresholds['medium_confidence']:
            return {
                'action': 'manual_review',
                'candidates': matches.to_dict('records'),
                'confidence': best_match['similarity']
            }
        else:
            return {'action': 'create_new', 'confidence': 0.0}
```

### 3.2 工作流集成
```python
# 新增：app/workflow_integration.py
class WorkflowIntegration:
    def __init__(self, workflow_api):
        self.workflow_api = workflow_api
    
    def submit_for_approval(self, material_data, decision_result):
        """提交审批流程"""
        pass
    
    def handle_approval_callback(self, approval_result):
        """处理审批回调"""
        pass
```

## Phase 4: 数据清洗增强（4-5个月）

### 4.1 批量清洗引擎
```python
# 新增：app/batch_cleaner.py
class BatchDataCleaner:
    def __init__(self):
        self.cleaning_rules = self.load_cleaning_rules()
    
    def clean_duplicates(self, df):
        """去重处理"""
        pass
    
    def clean_anomalies(self, df):
        """异常值处理"""
        pass
    
    def validate_data_quality(self, df):
        """数据质量评估"""
        pass
```

## 技术栈增强建议

### 新增依赖
```txt
# 文本处理
jieba>=0.42.1
paddleocr>=2.6.0

# 文档处理  
PyPDF2>=3.0.0
python-docx>=0.8.11
openpyxl>=3.0.9

# 机器学习
scikit-learn>=1.2.0
transformers>=4.21.0

# 图像处理
Pillow>=9.0.0
opencv-python>=4.6.0

# API集成
requests>=2.28.0
celery>=5.2.0  # 异步任务
```

### 数据库支持
- **MongoDB**：存储非结构化特征模型
- **Redis**：缓存分类树和匹配结果
- **PostgreSQL**：存储结构化主数据

## 部署架构建议

```
Frontend (React/Vue)
    ↓
API Gateway (Flask/FastAPI) 
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   数据提取服务    │    匹配引擎服务   │   工作流服务      │
│   (OCR/PDF)     │   (ML Models)   │  (Approval)     │
└─────────────────┴─────────────────┴─────────────────┘
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│    MongoDB      │      Redis      │   PostgreSQL    │
│  (特征模型)      │    (缓存)       │   (主数据)       │
└─────────────────┴─────────────────┴─────────────────┘
```

## 关键指标定义
- **准确率**：推荐分类正确率 > 85%
- **召回率**：匹配识别率 > 95% 
- **处理效率**：单条处理 < 2秒，批量 1000条 < 5分钟
- **用户满意度**：人工修改率 < 20%
