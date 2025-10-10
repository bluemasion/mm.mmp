# config.py

# 1. 文件路径配置
MASTER_DATA_PATH = 'data/e4p9.xlsx - Sheet1.csv'
NEW_DATA_PATH = 'data/e4.xlsx - Sheet1.csv'
OUTPUT_RESULT_PATH = 'data/batch_matching_results.csv'

# 2. 匹配规则配置
MATCH_RULES = {
    'master_fields': {
        'id': '商品操作码',
        'exact': ['生产厂家', '医保代码'],
        'fuzzy': ['产品名称', '产品规格']
    },
    'new_item_fields': {
        'id': '资产代码',
        'exact': ['生产厂家名称', '医保码'],
        'fuzzy': ['资产名称', '规格型号']
    }
}

# 3. 其他应用配置
LOG_LEVEL = 'INFO'