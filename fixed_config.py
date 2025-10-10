# -*- coding: utf-8 -*-
"""
修复后的匹配配置 - 使用实际数据库字段
"""

# 匹配规则配置 - 使用实际存在的字段
MATCH_RULES = {
    'master_fields': {
        'id': 'material_code',
        'exact': ['brand', 'model'],  # 品牌、型号精确匹配
        'fuzzy': ['material_name', 'specification'],  # 物料名称、规格模糊匹配
        'optional': ['insurance_code', 'supplier']  # 可选字段
    },
    'new_item_fields': {
        'id': '资产代码',
        'exact': ['品牌', '型号'],  
        'fuzzy': ['物料名称', '规格'],
        'optional': ['医保代码', '供应商']
    }
}

# 字段映射规则
FIELD_MAPPING = {
    '物料名称': 'material_name',
    '品牌': 'brand', 
    '型号': 'model',
    '规格': 'specification',
    '医保代码': 'insurance_code',
    '供应商': 'supplier',
    '物料代码': 'material_code'
}

# 匹配配置
MATCH_CONFIG = {
    'similarity_threshold': 0.3,
    'field_weights': {
        'exact_match': 1.0,
        'fuzzy_match': 0.8,
        'description_match': 0.6
    },
    'top_n_default': 5,
    'enable_fallback': True  # 启用降级匹配
}
