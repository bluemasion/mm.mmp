# app/preprocessor.py
import logging
# 未来可以引入 import jieba

def recommend_category(item_data, new_item_fields_map):
    """
    根据物料信息推荐分类 (当前为简化版逻辑)。
    未来可以基于分词和关键词匹配来实现。
    """
    name = item_data.get(new_item_fields_map['fuzzy'][0], '')
    logging.info(f"为 '{name}' 推荐物料分类...")
    
    # 示例逻辑：如果名称中包含“注射”，则推荐“药品-注射剂”
    if '注射' in name:
        return "药品-注射剂"
    elif '胶囊' in name:
        return "药品-口服剂"
    else:
        return "未识别分类"

def extract_parameters(item_data):
    """
    从物料信息中提取关键参数 (当前为占位符)。
    未来可以使用分词和正则表达式等技术。
    """
    logging.info("提取关键参数...")
    # 这是一个占位符，实际应用中会更复杂
    params = {
        'raw_text': ' '.join(str(val) for val in item_data.values()),
        'auto_extracted_brand': '示例品牌'
    }
    return params