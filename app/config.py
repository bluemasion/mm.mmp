# app/config.py
"""应用配置模块"""

# 1. 文件路径配置
MASTER_DATA_PATH = 'data/e4p9.xlsx - Sheet1.csv'
NEW_DATA_PATH = 'data/e4.xlsx - Sheet1.csv'
OUTPUT_RESULT_PATH = 'data/batch_matching_results.csv'

# 2. 匹配规则配置
MATCH_RULES = {
    'master_fields': {
        'id': 'id',  # 对应加载数据的字段名
        'exact': ['manufacturer', 'category'],  # 对应加载数据的字段名
        'fuzzy': ['name', 'specification']  # 对应加载数据的字段名
    },
    'new_item_fields': {
        'id': '资产代码',
        'exact': ['生产厂家名称', '分类'],  # 映射到实际字段
        'fuzzy': ['资产名称', '规格型号']
    }
}

# 3. 其他应用配置
LOG_LEVEL = 'INFO'

# 4. 数据库配置
DATABASE_PATH = 'master_data.db'
BUSINESS_DATABASE_PATH = 'business_data.db'

# 5. Web应用配置
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000