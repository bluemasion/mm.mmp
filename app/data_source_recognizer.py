# -*- coding: utf-8 -*-
"""
数据源模式识别器
支持制造业和医疗行业的自动识别和适配
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import pandas as pd
import numpy as np

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataSourceSchema:
    """数据源模式定义"""
    source_id: str
    industry_type: str                    # 行业类型
    field_types: Dict[str, str]          # 字段类型映射
    naming_patterns: Dict[str, Any]       # 命名规律
    value_distributions: Dict[str, Any]   # 值分布特征
    field_mappings: Dict[str, str]        # 字段映射规则
    quality_metrics: Dict[str, float]     # 数据质量指标
    confidence_score: float               # 识别置信度

class DataSourcePatternRecognizer:
    """数据源模式自动识别器"""
    
    def __init__(self):
        self.industry_indicators = self._load_industry_indicators()
        
    def _load_industry_indicators(self) -> Dict[str, Dict]:
        """加载行业指标库"""
        return {
            'manufacturing': {
                'keywords': [
                    '阀门', '管道', '法兰', '泵', '压缩机', '轴承', '密封', '螺栓',
                    '疏水器', '疏水阀', '弯头', '三通', '异径管', '封头', '管件',
                    '球阀', '蝶阀', '闸阀', '止回阀', '减压阀', '安全阀',
                    '离心泵', '齿轮泵', '螺杆泵', '往复泵', '计量泵',
                    '压缩机配件', '机械密封', '填料', '垫片', '紧固件'
                ],
                'patterns': [
                    r'DN\s*\d+',           # 公称直径
                    r'PN\s*\d+',           # 压力等级
                    r'φ\s*\d+',            # 直径符号
                    r'\d+\.?\d*\s*MPa',    # 压力单位
                    r'\d+\.?\d*\s*℃',      # 温度
                    r'CL\s*\d+',           # Class等级
                    r'M\d+\*\d+',          # 螺纹规格
                    r'G\d+/\d+',           # 管螺纹
                ],
                'units': ['mm', 'MPa', '℃', 'kg/h', 'm³/h', 'L/min', '个', '套', '台'],
                'materials': ['304', '316', '316L', 'CS', 'WCB', 'CF8', 'CF8M', '不锈钢', '碳钢'],
                'standards': ['GB', 'ANSI', 'JIS', 'DIN', 'API', 'ASME', 'HG']
            },
            'medical': {
                'keywords': [
                    '医疗器械', '药品', '手术', '诊断', '治疗', '一次性', '无菌',
                    '注射器', '输液器', '导管', '血袋', '试剂', '耗材',
                    '心电', '超声', '内镜', '监护', '呼吸机', '除颤器',
                    '手术刀', '钳子', '镊子', '缝合线', '敷料', '绷带',
                    '药物', '胶囊', '片剂', '注射液', '滴眼液', '软膏'
                ],
                'patterns': [
                    r'规格.*\d+ml',         # 容量规格
                    r'浓度.*\d+%',          # 浓度
                    r'批号.*\w+',           # 批号
                    r'\d+mg/ml',            # 药物浓度
                    r'有效期.*\d+',         # 有效期
                    r'型号.*\w+',           # 设备型号
                    r'Fr\d+',               # French规格
                    r'\d+G',                # 针头规格
                ],
                'units': ['ml', 'mg', 'μg', 'IU', '支', '盒', '瓶', '袋', '个'],
                'categories': ['I类', 'II类', 'III类', '处方药', '非处方药', 'OTC'],
                'standards': ['YY', 'GB/T', 'ISO', 'CE', 'FDA', 'CFDA', '国药准字']
            }
        }
    
    def analyze_data_structure(self, data_sample: List[Dict], 
                             source_metadata: Dict = None) -> DataSourceSchema:
        """
        分析数据源结构特征
        
        Args:
            data_sample: 数据样本，建议100-1000条
            source_metadata: 可选的源数据元信息
            
        Returns:
            DataSourceSchema: 数据源模式定义
        """
        if not data_sample:
            raise ValueError("数据样本不能为空")
            
        logger.info(f"开始分析数据源结构，样本数量: {len(data_sample)}")
        
        # 1. 基础字段分析
        field_types = self._detect_field_types(data_sample)
        
        # 2. 命名模式分析
        naming_patterns = self._analyze_naming_patterns(data_sample)
        
        # 3. 数值分布分析
        value_distributions = self._analyze_value_distributions(data_sample)
        
        # 4. 行业类型识别
        industry_type, confidence = self._identify_industry_with_confidence(data_sample)
        
        # 5. 字段映射生成
        field_mappings = self._generate_field_mappings(field_types, industry_type)
        
        # 6. 数据质量评估
        quality_metrics = self._assess_data_quality(data_sample)
        
        # 7. 创建数据源模式
        schema = DataSourceSchema(
            source_id=source_metadata.get('source_id', f"auto_{int(pd.Timestamp.now().timestamp())}") if source_metadata else f"auto_{int(pd.Timestamp.now().timestamp())}",
            industry_type=industry_type,
            field_types=field_types,
            naming_patterns=naming_patterns,
            value_distributions=value_distributions,
            field_mappings=field_mappings,
            quality_metrics=quality_metrics,
            confidence_score=confidence
        )
        
        logger.info(f"数据源分析完成 - 行业类型: {industry_type}, 置信度: {confidence:.2f}")
        return schema
    
    def _identify_industry_with_confidence(self, data_sample: List[Dict]) -> Tuple[str, float]:
        """识别行业类型并返回置信度"""
        
        # 将所有数据转换为文本进行分析
        text_content = ' '.join([str(item) for item in data_sample])
        text_lower = text_content.lower()
        
        industry_scores = {}
        
        for industry, indicators in self.industry_indicators.items():
            score = 0
            total_possible = 0
            
            # 1. 关键词匹配 (权重: 40%)
            keyword_matches = 0
            for keyword in indicators['keywords']:
                matches = text_content.count(keyword)
                keyword_matches += matches
            keyword_score = min(keyword_matches / len(indicators['keywords']), 1.0) * 0.4
            score += keyword_score
            total_possible += 0.4
            
            # 2. 模式匹配 (权重: 30%)
            pattern_matches = 0
            for pattern in indicators['patterns']:
                matches = len(re.findall(pattern, text_content, re.IGNORECASE))
                pattern_matches += matches
            pattern_score = min(pattern_matches / max(len(indicators['patterns']), 1), 1.0) * 0.3
            score += pattern_score
            total_possible += 0.3
            
            # 3. 单位匹配 (权重: 20%)
            unit_matches = 0
            for unit in indicators['units']:
                matches = text_content.count(unit)
                unit_matches += matches
            unit_score = min(unit_matches / len(indicators['units']), 1.0) * 0.2
            score += unit_score
            total_possible += 0.2
            
            # 4. 特定标识匹配 (权重: 10%)
            if industry == 'manufacturing' and 'materials' in indicators:
                material_matches = 0
                for material in indicators['materials']:
                    material_matches += text_content.count(material)
                material_score = min(material_matches / len(indicators['materials']), 1.0) * 0.1
                score += material_score
            elif industry == 'medical' and 'categories' in indicators:
                category_matches = 0
                for category in indicators['categories']:
                    category_matches += text_content.count(category)
                category_score = min(category_matches / len(indicators['categories']), 1.0) * 0.1
                score += category_score
            total_possible += 0.1
            
            # 标准化分数
            industry_scores[industry] = score / total_possible if total_possible > 0 else 0
        
        # 选择得分最高的行业
        if not industry_scores or max(industry_scores.values()) < 0.1:
            return 'generic', 0.0
        
        best_industry = max(industry_scores, key=industry_scores.get)
        confidence = industry_scores[best_industry]
        
        logger.info(f"行业识别结果: {dict(industry_scores)}")
        return best_industry, confidence
    
    def _detect_field_types(self, data_sample: List[Dict]) -> Dict[str, str]:
        """检测字段类型"""
        if not data_sample:
            return {}
            
        field_types = {}
        sample_item = data_sample[0]
        
        for field_name in sample_item.keys():
            values = [item.get(field_name, '') for item in data_sample[:100] if item.get(field_name)]
            
            if not values:
                field_types[field_name] = 'unknown'
                continue
            
            # 数值型检测
            if self._is_numeric_field(values):
                field_types[field_name] = 'numeric'
            # 分类型检测
            elif self._is_categorical_field(values):
                field_types[field_name] = 'categorical'
            # 文本型
            else:
                field_types[field_name] = 'text'
                
        return field_types
    
    def _is_numeric_field(self, values: List) -> bool:
        """判断是否为数值字段"""
        numeric_count = 0
        for value in values:
            try:
                float(str(value).replace(',', '').replace(' ', ''))
                numeric_count += 1
            except (ValueError, TypeError):
                continue
        return numeric_count / len(values) > 0.7
    
    def _is_categorical_field(self, values: List) -> bool:
        """判断是否为分类字段"""
        unique_values = set(str(v).strip() for v in values)
        return len(unique_values) / len(values) < 0.1  # 唯一值比例小于10%
    
    def _analyze_naming_patterns(self, data_sample: List[Dict]) -> Dict[str, Any]:
        """分析命名规律"""
        if not data_sample:
            return {}
            
        patterns = {}
        sample_item = data_sample[0]
        
        for field_name in sample_item.keys():
            values = [str(item.get(field_name, '')) for item in data_sample[:100]]
            
            # 长度分布
            lengths = [len(v) for v in values if v.strip()]
            if lengths:
                patterns[f'{field_name}_length'] = {
                    'min': min(lengths),
                    'max': max(lengths),
                    'avg': sum(lengths) / len(lengths),
                    'std': np.std(lengths)
                }
            
            # 常见模式
            patterns[f'{field_name}_patterns'] = self._extract_common_patterns(values)
            
        return patterns
    
    def _extract_common_patterns(self, values: List[str]) -> List[str]:
        """提取常见模式"""
        patterns = []
        
        # 检测数字模式
        if any(re.search(r'\d+', v) for v in values):
            patterns.append('contains_numbers')
        
        # 检测特殊字符
        if any(re.search(r'[\/\-\*\+\(\)]', v) for v in values):
            patterns.append('contains_special_chars')
        
        # 检测单位模式
        if any(re.search(r'\d+\s*(mm|cm|m|kg|g|ml|l)', v, re.IGNORECASE) for v in values):
            patterns.append('contains_units')
            
        return patterns
    
    def _analyze_value_distributions(self, data_sample: List[Dict]) -> Dict[str, Any]:
        """分析值分布"""
        distributions = {}
        
        if not data_sample:
            return distributions
            
        sample_item = data_sample[0]
        
        for field_name in sample_item.keys():
            values = [item.get(field_name, '') for item in data_sample if item.get(field_name)]
            
            if not values:
                continue
                
            # 基础统计
            distributions[field_name] = {
                'total_count': len(values),
                'unique_count': len(set(str(v) for v in values)),
                'null_count': len([v for v in values if not str(v).strip()]),
                'most_common': Counter([str(v) for v in values]).most_common(5)
            }
            
        return distributions
    
    def _generate_field_mappings(self, field_types: Dict[str, str], 
                               industry_type: str) -> Dict[str, str]:
        """生成字段映射"""
        mappings = {}
        
        # 制造业字段映射规则
        if industry_type == 'manufacturing':
            name_patterns = ['名称', 'name', '物料名', '产品名', '商品名', '品名']
            spec_patterns = ['规格', 'spec', '型号', '参数', '尺寸', '技术参数']
            manufacturer_patterns = ['厂家', '制造商', '生产厂家', 'manufacturer', '品牌']
            category_patterns = ['分类', '类别', 'category', '物料分类']
            
        # 医疗行业字段映射规则
        elif industry_type == 'medical':
            name_patterns = ['器械名称', '药品名称', '产品名称', 'name', '商品名']
            spec_patterns = ['规格', '型号', '浓度', '剂量', '容量']
            manufacturer_patterns = ['生产企业', '制造商', '厂家', '药厂']
            category_patterns = ['分类', '类别', '器械分类', '药品分类']
        else:
            # 通用映射规则
            name_patterns = ['名称', 'name']
            spec_patterns = ['规格', 'spec']
            manufacturer_patterns = ['厂家', 'manufacturer']
            category_patterns = ['分类', 'category']
        
        # 执行字段匹配
        for field_name, field_type in field_types.items():
            field_lower = field_name.lower()
            
            # 名称字段匹配
            if any(pattern in field_lower for pattern in name_patterns):
                mappings['material_name'] = field_name
            
            # 规格字段匹配
            elif any(pattern in field_lower for pattern in spec_patterns):
                mappings['specification'] = field_name
            
            # 制造商字段匹配
            elif any(pattern in field_lower for pattern in manufacturer_patterns):
                mappings['manufacturer'] = field_name
            
            # 分类字段匹配
            elif any(pattern in field_lower for pattern in category_patterns):
                mappings['category'] = field_name
                
        return mappings
    
    def _assess_data_quality(self, data_sample: List[Dict]) -> Dict[str, float]:
        """评估数据质量"""
        if not data_sample:
            return {'overall_quality': 0.0}
            
        metrics = {}
        sample_item = data_sample[0]
        
        # 完整性评估
        total_fields = len(sample_item.keys())
        completeness_scores = []
        
        for field_name in sample_item.keys():
            values = [item.get(field_name, '') for item in data_sample]
            non_empty = len([v for v in values if str(v).strip()])
            completeness = non_empty / len(values) if values else 0
            completeness_scores.append(completeness)
            metrics[f'{field_name}_completeness'] = completeness
            
        # 整体质量指标
        metrics['overall_completeness'] = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        metrics['field_count'] = total_fields
        metrics['sample_size'] = len(data_sample)
        
        # 数据一致性
        consistency_scores = []
        for field_name in sample_item.keys():
            values = [str(item.get(field_name, '')) for item in data_sample]
            unique_patterns = len(set(re.sub(r'\d+', 'N', v) for v in values))
            consistency = 1 - (unique_patterns / len(values)) if values else 0
            consistency_scores.append(max(consistency, 0))
            
        metrics['overall_consistency'] = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0
        
        # 综合质量评分
        metrics['overall_quality'] = (metrics['overall_completeness'] * 0.6 + 
                                    metrics['overall_consistency'] * 0.4)
        
        return metrics


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    manufacturing_sample = [
        {"物料名称": "疏水器", "规格型号": "DN25 PN16", "制造商": "上海阀门厂", "材质": "304不锈钢"},
        {"物料名称": "球阀", "规格型号": "DN50 PN25", "制造商": "天津泵业", "材质": "WCB"},
        {"物料名称": "法兰", "规格型号": "DN100 CL150", "制造商": "江苏管件", "材质": "碳钢"},
    ]
    
    medical_sample = [
        {"器械名称": "一次性注射器", "规格": "5ml", "生产企业": "三鑫医疗", "分类": "II类医疗器械"},
        {"器械名称": "输液器", "规格": "150cm", "生产企业": "康德莱", "分类": "III类医疗器械"},
        {"器械名称": "血压计", "规格": "电子式", "生产企业": "欧姆龙", "分类": "II类医疗器械"},
    ]
    
    # 测试识别器
    recognizer = DataSourcePatternRecognizer()
    
    print("=== 制造业数据源分析 ===")
    manufacturing_schema = recognizer.analyze_data_structure(manufacturing_sample)
    print(f"行业类型: {manufacturing_schema.industry_type}")
    print(f"置信度: {manufacturing_schema.confidence_score:.2f}")
    print(f"字段映射: {manufacturing_schema.field_mappings}")
    print(f"数据质量: {manufacturing_schema.quality_metrics['overall_quality']:.2f}")
    
    print("\n=== 医疗行业数据源分析 ===")
    medical_schema = recognizer.analyze_data_structure(medical_sample)
    print(f"行业类型: {medical_schema.industry_type}")
    print(f"置信度: {medical_schema.confidence_score:.2f}")
    print(f"字段映射: {medical_schema.field_mappings}")
    print(f"数据质量: {medical_schema.quality_metrics['overall_quality']:.2f}")