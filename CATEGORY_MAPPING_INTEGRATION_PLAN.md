# 物料分类映射和数据整合方案

**目标**: 将2000条相似物料数据统一到标准分类体系中

## 🎯 实施步骤

### Step 1: 创建分类映射表
```sql
CREATE TABLE category_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    similar_category TEXT NOT NULL,      -- 相似物料中的分类名
    standard_category TEXT NOT NULL,     -- 标准分类名
    mapping_type TEXT DEFAULT 'manual',  -- 映射类型: manual, auto, exact
    confidence REAL DEFAULT 1.0,        -- 映射置信度
    data_count INTEGER DEFAULT 0,       -- 该分类下的数据量
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Step 2: 分类映射建议

#### 已精确匹配 (19个分类):
✅ 直接使用，无需映射

#### 需要映射的分类 (53个):

**高优先级 (数据量大)**:
1. `其它管道配件` (1288条) → `管道配件`
2. `金属软管` (205条) → `软管总成` 或新建标准分类
3. `带颈对焊法兰` (143条) → 已匹配 ✅
4. `过滤器` (56条) → `过滤器` (如果标准分类中存在)

**中优先级**:
5. `疏水器` (14条) → 可能需要新建标准分类
6. `管道架构件` (28条) → `管道支架` 或相关分类
7. `无缝三通` (25条) → 已匹配 ✅

**低优先级 (数据量小)**:
- 各种细分法兰、管件类别

### Step 3: 实施建议

#### 选项A: 扩展标准分类 (推荐)
将相似物料中的专业分类补充到标准分类中，丰富标准分类体系

#### 选项B: 强制映射 
将所有相似物料分类映射到现有标准分类，可能丢失精度

#### 选项C: 混合方式
- 高匹配度的直接映射
- 专业分类作为标准分类的补充
- 建立父子分类关系

## 🔧 技术实现

### API增强方案:
```python
# 在模糊匹配结果中同时提供:
{
    "similar_materials": [...],
    "recommended_categories": [
        {
            "category_name": "疏水器",
            "source": "similar_data",  # 来源标识
            "standard_mapping": "管道配件", # 对应的标准分类
            "confidence": 0.74
        },
        {
            "category_name": "管道配件", 
            "source": "standard_data", # 标准分类
            "confidence": 0.68
        }
    ]
}
```

## 📊 预期效果

1. **数据完整性**: 2000条物料数据 + 532个标准分类
2. **分类准确性**: 保持专业细分的同时符合标准规范
3. **用户体验**: 提供既专业又标准的分类建议
4. **系统扩展性**: 为后续数据导入建立标准