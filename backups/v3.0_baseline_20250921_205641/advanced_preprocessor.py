# app/advanced_preprocessor.py
import jieba
import re
from collections import defaultdict
import logging
from typing import Dict, List, Tuple, Optional

class AdvancedPreprocessor:
    """增强版预处理器，支持智能分词和参数提取"""
    
    def __init__(self):
        # 初始化分词器
        jieba.initialize()
        
        # 定义提取模式
        self.extraction_patterns = {
            'brand': [
                r'[\u4e00-\u9fff]+(?:集团|公司|厂|制药|医药|生物|科技)',  # 中文企业名
                r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|Co))?',  # 英文品牌
                r'(?:进口|国产)?\s*[\u4e00-\u9fff]{2,6}(?:牌|品牌)?'  # 品牌标识
            ],
            'specification': [
                r'\d+(?:\.\d+)?(?:mg|ml|g|l|kg|片|粒|支|盒|瓶|袋|包)',  # 药品规格
                r'\d+(?:\.\d+)?[*×]\d+(?:\.\d+)?(?:[*×]\d+(?:\.\d+)?)?(?:mm|cm|m)?',  # 尺寸规格
                r'\d+(?:\.\d+)?(?:A|V|W|Hz|℃|bar|MPa)',  # 电气/物理参数
                r'(?:型号|规格)[：:]?\s*([A-Z0-9\-/]+)',  # 型号规格
            ],
            'model': [
                r'(?:型号|model)[：:]?\s*([A-Z0-9\-/]+)',
                r'[A-Z]{1,3}\d{2,6}[A-Z]?',  # 常见型号格式
                r'\d{3,6}[A-Z]{1,3}'
            ],
            'material': [
                r'(?:材质|材料)[：:]?\s*([\u4e00-\u9fff]+|[A-Z]+)',
                r'(?:不锈钢|铝合金|塑料|橡胶|钢材|铜)'
            ],
            'usage': [
                r'(?:用于|适用于|用途)[：:]?\s*([\u4e00-\u9fff]+)',
                r'(?:治疗|预防|检测|测量|控制)'
            ]
        }
        
        # 医疗器械/药品关键词
        self.medical_keywords = {
            '药品': ['注射液', '胶囊', '片剂', '颗粒', '口服液', '软膏', '贴剂'],
            '医疗器械': ['监护仪', '呼吸机', '除颤器', '输液泵', '心电图机', '超声设备'],
            '检验试剂': ['试剂盒', '检测卡', '标准品', '质控品', '校准品'],
            '耗材': ['导管', '导丝', '支架', '缝合线', '敷料', '手套']
        }
        
        # 工业品关键词
        self.industrial_keywords = {
            '电气设备': ['变压器', '开关', '电缆', '电机', '控制器'],
            '机械设备': ['泵', '阀门', '轴承', '齿轮', '密封件'],
            '仪器仪表': ['传感器', '流量计', '压力表', '温度计', '分析仪'],
            '五金工具': ['螺丝', '螺母', '垫片', '弹簧', '紧固件']
        }

    def extract_comprehensive_parameters(self, text: str) -> Dict[str, List[str]]:
        """
        综合参数提取
        
        Args:
            text: 输入文本（物料描述）
            
        Returns:
            提取的参数字典
        """
        if not text or not text.strip():
            return {}
            
        text = str(text).strip()
        params = defaultdict(list)
        
        # 1. 基于正则表达式的提取
        for param_type, patterns in self.extraction_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # 处理捕获组
                    if isinstance(matches[0], tuple):
                        params[param_type].extend([match for match in matches if match])
                    else:
                        params[param_type].extend(matches)
        
        # 2. 基于分词的关键词提取
        words = jieba.lcut(text)
        params.update(self._extract_keywords_from_words(words))
        
        # 3. 去重和清理
        cleaned_params = {}
        for key, values in params.items():
            if values:
                # 去重并保持顺序
                seen = set()
                unique_values = []
                for value in values:
                    if value not in seen and len(value.strip()) > 0:
                        seen.add(value)
                        unique_values.append(value.strip())
                if unique_values:
                    cleaned_params[key] = unique_values
        
        logging.info(f"从文本中提取参数: {dict(cleaned_params)}")
        return dict(cleaned_params)

    def _extract_keywords_from_words(self, words: List[str]) -> Dict[str, List[str]]:
        """从分词结果中提取关键词"""
        keyword_params = defaultdict(list)
        
        # 检查医疗相关关键词
        for category, keywords in self.medical_keywords.items():
            for keyword in keywords:
                if any(keyword in word for word in words):
                    keyword_params['medical_category'].append(category)
        
        # 检查工业品相关关键词
        for category, keywords in self.industrial_keywords.items():
            for keyword in keywords:
                if any(keyword in word for word in words):
                    keyword_params['industrial_category'].append(category)
        
        return keyword_params

    def recommend_category_advanced(self, text: str, extracted_params: Dict) -> List[Tuple[str, float]]:
        """
        高级分类推荐
        
        Args:
            text: 原始文本
            extracted_params: 提取的参数
            
        Returns:
            分类推荐列表 [(分类名, 置信度)]
        """
        recommendations = []
        
        # 基于关键词的规则推荐
        if 'medical_category' in extracted_params:
            for category in extracted_params['medical_category']:
                confidence = self._calculate_category_confidence(text, category, 'medical')
                recommendations.append((f"医疗用品-{category}", confidence))
        
        if 'industrial_category' in extracted_params:
            for category in extracted_params['industrial_category']:
                confidence = self._calculate_category_confidence(text, category, 'industrial')
                recommendations.append((f"工业用品-{category}", confidence))
        
        # 基于品牌的推荐
        if 'brand' in extracted_params:
            brands = extracted_params['brand']
            for brand in brands:
                if any(med_word in brand for med_word in ['医药', '制药', '生物']):
                    recommendations.append(("医疗用品-药品", 0.8))
        
        # 基于规格的推荐  
        if 'specification' in extracted_params:
            specs = extracted_params['specification']
            for spec in specs:
                if any(unit in spec for unit in ['mg', 'ml', '片', '粒']):
                    recommendations.append(("医疗用品-药品", 0.7))
                elif any(unit in spec for unit in ['A', 'V', 'W', 'Hz']):
                    recommendations.append(("工业用品-电气设备", 0.7))
        
        # 排序并去重
        recommendations = list(set(recommendations))
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        # 如果没有匹配的分类，返回默认推荐
        if not recommendations:
            recommendations = [("未分类", 0.1)]
        
        logging.info(f"分类推荐结果: {recommendations}")
        return recommendations[:5]  # 返回Top5

    def _calculate_category_confidence(self, text: str, category: str, domain: str) -> float:
        """计算分类置信度"""
        confidence = 0.5  # 基础置信度
        
        # 根据关键词密度调整置信度
        if domain == 'medical':
            keywords = self.medical_keywords.get(category, [])
        else:
            keywords = self.industrial_keywords.get(category, [])
        
        keyword_count = sum(1 for keyword in keywords if keyword in text)
        confidence += min(0.4, keyword_count * 0.1)
        
        return min(1.0, confidence)

    def standardize_extracted_values(self, params: Dict[str, List[str]], 
                                   field_type: str) -> List[str]:
        """
        标准化提取的值
        
        Args:
            params: 提取的参数
            field_type: 字段类型（brand, specification等）
            
        Returns:
            标准化后的值列表
        """
        if field_type not in params:
            return []
        
        values = params[field_type]
        standardized = []
        
        for value in values:
            if field_type == 'specification':
                # 规格标准化：统一单位格式
                value = re.sub(r'(\d+(?:\.\d+)?)\s*(mg|ml|g|l)', r'\1\2', value)
                value = re.sub(r'[*×]', '×', value)  # 统一乘号
            elif field_type == 'brand':
                # 品牌标准化：去除多余词汇
                value = re.sub(r'(集团|公司|厂|制药|医药|有限)$', '', value)
            elif field_type == 'model':
                # 型号标准化：转换为大写
                value = value.upper()
            
            standardized.append(value.strip())
        
        return standardized

# 兼容性函数，保持现有API
def recommend_category(item_data, new_item_fields_map):
    """兼容现有API的分类推荐函数"""
    preprocessor = AdvancedPreprocessor()
    
    # 提取文本信息
    text_parts = []
    for field in new_item_fields_map['fuzzy']:
        if field in item_data:
            text_parts.append(str(item_data[field]))
    
    text = ' '.join(text_parts)
    params = preprocessor.extract_comprehensive_parameters(text)
    recommendations = preprocessor.recommend_category_advanced(text, params)
    
    # 返回最佳推荐
    if recommendations:
        return recommendations[0][0]
    return "未识别分类"

def extract_parameters(item_data):
    """兼容现有API的参数提取函数"""
    preprocessor = AdvancedPreprocessor()
    
    # 合并所有文本信息
    text_parts = []
    for value in item_data.values():
        if value and str(value).strip():
            text_parts.append(str(value))
    
    full_text = ' '.join(text_parts)
    extracted = preprocessor.extract_comprehensive_parameters(full_text)
    
    # 转换为原有格式
    return {
        'raw_text': full_text,
        'extracted_params': extracted,
        'recommended_categories': preprocessor.recommend_category_advanced(full_text, extracted)
    }

if __name__ == "__main__":
    # 测试代码
    preprocessor = AdvancedPreprocessor()
    
    test_text = "阿莫西林胶囊 0.25g×24粒 华北制药集团 国药准字H13020959"
    params = preprocessor.extract_comprehensive_parameters(test_text)
    categories = preprocessor.recommend_category_advanced(test_text, params)
    
    print("提取参数:", params)
    print("推荐分类:", categories)
