# -*- coding: utf-8 -*-
"""
制造业数据源适配器
针对制造业物料数据的专门处理和优化
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ManufacturingFeature:
    """制造业特征定义"""
    name: str                    # 物料名称
    specification: str           # 规格型号
    material_type: str          # 材质
    size: Dict[str, float]      # 尺寸参数
    pressure_rating: Optional[str]  # 压力等级
    temperature_rating: Optional[str]  # 温度等级
    manufacturer: str           # 制造商
    standard: Optional[str]     # 执行标准
    category_level1: str        # 一级分类
    category_level2: str        # 二级分类
    category_level3: Optional[str]  # 三级分类
    technical_params: Dict[str, Any]  # 技术参数

class ManufacturingAdapter:
    """制造业数据源适配器"""
    
    def __init__(self):
        self.category_mapping = self._load_category_mapping()
        self.material_standards = self._load_material_standards()
        self.size_patterns = self._load_size_patterns()
        
    def _load_category_mapping(self) -> Dict[str, Dict]:
        """加载制造业分类映射"""
        return {
            # 阀门类
            '阀门': {
                'level1': '管道阀门',
                'level2': '控制阀门',
                'keywords': ['阀', '球阀', '蝶阀', '闸阀', '止回阀', '减压阀', '安全阀', '疏水阀', '疏水器']
            },
            
            # 管件类
            '管件': {
                'level1': '管道连接件',
                'level2': '管道配件',
                'keywords': ['管件', '弯头', '三通', '四通', '异径管', '封头', '法兰', '管帽']
            },
            
            # 泵类
            '泵': {
                'level1': '流体输送设备',
                'level2': '泵类设备',
                'keywords': ['泵', '离心泵', '齿轮泵', '螺杆泵', '往复泵', '计量泵', '潜水泵']
            },
            
            # 压缩机类
            '压缩机': {
                'level1': '动力设备',
                'level2': '压缩设备',
                'keywords': ['压缩机', '空压机', '制冷压缩机', '往复式压缩机', '离心式压缩机']
            },
            
            # 密封件类
            '密封件': {
                'level1': '通用机械配件',
                'level2': '密封元件',
                'keywords': ['密封', '垫片', '密封圈', '机械密封', '填料', 'O型圈']
            },
            
            # 轴承类
            '轴承': {
                'level1': '通用机械配件',
                'level2': '传动元件',
                'keywords': ['轴承', '球轴承', '滚子轴承', '滑动轴承', '推力轴承']
            },
            
            # 紧固件类
            '紧固件': {
                'level1': '通用机械配件',
                'level2': '连接件',
                'keywords': ['螺栓', '螺钉', '螺母', '垫圈', '销钉', '铆钉', '紧固件']
            }
        }
    
    def _load_material_standards(self) -> Dict[str, Dict]:
        """加载材质标准"""
        return {
            '不锈钢': {
                'aliases': ['304', '316', '316L', '321', '310S', 'SS304', 'SS316'],
                'properties': {'耐腐蚀': True, '耐高温': True, '强度': 'high'},
                'applications': ['化工', '食品', '制药', '海洋']
            },
            '碳钢': {
                'aliases': ['CS', 'WCB', 'A105', 'Q235', '20#', '45#'],
                'properties': {'强度': 'medium', '成本': 'low'},
                'applications': ['一般工业', '建筑', '机械']
            },
            '合金钢': {
                'aliases': ['A182F11', 'A182F22', 'Cr-Mo', '铬钼钢'],
                'properties': {'耐高温': True, '强度': 'high'},
                'applications': ['高温高压', '石化', '电力']
            },
            '铸铁': {
                'aliases': ['HT200', 'HT250', '灰铸铁', '球墨铸铁'],
                'properties': {'成本': 'low', '加工性': 'good'},
                'applications': ['低压管道', '泵体', '阀体']
            }
        }
    
    def _load_size_patterns(self) -> Dict[str, str]:
        """加载尺寸规格模式"""
        return {
            r'DN\s*(\d+)': 'nominal_diameter',      # 公称直径
            r'PN\s*(\d+(?:\.\d+)?)': 'pressure_rating',  # 压力等级
            r'CL\s*(\d+)': 'class_rating',          # Class等级
            r'φ\s*(\d+)': 'diameter',               # 直径
            r'(\d+)\s*x\s*(\d+)': 'dimensions',     # 长x宽
            r'M(\d+)\s*[x×]\s*(\d+(?:\.\d+)?)': 'thread_spec',  # 螺纹规格
            r'G(\d+/\d+)': 'pipe_thread',           # 管螺纹
            r'NPT(\d+/\d+)': 'npt_thread',          # NPT螺纹
            r'(\d+(?:\.\d+)?)\s*(mm|cm|m|inch|")': 'size_with_unit'  # 带单位尺寸
        }
    
    def extract_features(self, data_record: Dict[str, Any]) -> ManufacturingFeature:
        """
        提取制造业物料特征
        
        Args:
            data_record: 原始数据记录
            
        Returns:
            ManufacturingFeature: 标准化特征
        """
        logger.debug(f"提取制造业特征: {data_record}")
        
        # 基础信息提取
        name = self._extract_material_name(data_record)
        specification = self._extract_specification(data_record)
        material_type = self._extract_material_type(data_record)
        manufacturer = self._extract_manufacturer(data_record)
        
        # 尺寸参数提取
        size_info = self._extract_size_parameters(specification, data_record)
        
        # 等级参数提取
        pressure_rating = self._extract_pressure_rating(specification)
        temperature_rating = self._extract_temperature_rating(data_record)
        standard = self._extract_standard(data_record)
        
        # 分类识别
        category_info = self._classify_material(name, specification)
        
        # 技术参数提取
        technical_params = self._extract_technical_parameters(data_record)
        
        return ManufacturingFeature(
            name=name,
            specification=specification,
            material_type=material_type,
            size=size_info,
            pressure_rating=pressure_rating,
            temperature_rating=temperature_rating,
            manufacturer=manufacturer,
            standard=standard,
            category_level1=category_info.get('level1', '未分类'),
            category_level2=category_info.get('level2', '未分类'),
            category_level3=category_info.get('level3'),
            technical_params=technical_params
        )
    
    def _extract_material_name(self, data_record: Dict[str, Any]) -> str:
        """提取物料名称"""
        name_fields = ['物料名称', '产品名称', '名称', 'name', '品名', '商品名']
        
        for field in name_fields:
            if field in data_record and data_record[field]:
                name = str(data_record[field]).strip()
                # 清理名称
                name = re.sub(r'\s+', ' ', name)  # 多个空格合并为一个
                name = re.sub(r'[^\w\u4e00-\u9fff\s\-\(\)]', '', name)  # 保留中文、字母、数字、基本符号
                return name
        
        return '未知物料'
    
    def _extract_specification(self, data_record: Dict[str, Any]) -> str:
        """提取规格型号"""
        spec_fields = ['规格型号', '规格', '型号', 'spec', 'specification', '技术参数', '参数']
        
        specifications = []
        for field in spec_fields:
            if field in data_record and data_record[field]:
                spec = str(data_record[field]).strip()
                if spec and spec not in specifications:
                    specifications.append(spec)
        
        # 合并多个规格字段
        return ' | '.join(specifications) if specifications else ''
    
    def _extract_material_type(self, data_record: Dict[str, Any]) -> str:
        """提取材质类型"""
        material_fields = ['材质', '材料', 'material', '材质牌号', '材料类型']
        
        for field in material_fields:
            if field in data_record and data_record[field]:
                material = str(data_record[field]).strip().upper()
                
                # 标准化材质名称
                for standard_name, info in self.material_standards.items():
                    for alias in info['aliases']:
                        if alias.upper() in material:
                            return standard_name
                
                return material
        
        # 从名称和规格中推断材质
        all_text = ' '.join([str(v) for v in data_record.values()])
        for standard_name, info in self.material_standards.items():
            for alias in info['aliases']:
                if alias in all_text:
                    return standard_name
        
        return '未知材质'
    
    def _extract_manufacturer(self, data_record: Dict[str, Any]) -> str:
        """提取制造商"""
        manufacturer_fields = ['制造商', '厂家', '生产厂家', 'manufacturer', '品牌', '供应商']
        
        for field in manufacturer_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        return '未知厂家'
    
    def _extract_size_parameters(self, specification: str, data_record: Dict[str, Any]) -> Dict[str, float]:
        """提取尺寸参数"""
        size_info = {}
        
        # 从规格字符串提取
        for pattern, param_name in self.size_patterns.items():
            matches = re.finditer(pattern, specification, re.IGNORECASE)
            for match in matches:
                if param_name == 'nominal_diameter':
                    size_info['DN'] = float(match.group(1))
                elif param_name == 'pressure_rating':
                    size_info['PN'] = float(match.group(1))
                elif param_name == 'class_rating':
                    size_info['CL'] = float(match.group(1))
                elif param_name == 'diameter':
                    size_info['diameter'] = float(match.group(1))
                elif param_name == 'dimensions':
                    size_info['length'] = float(match.group(1))
                    size_info['width'] = float(match.group(2))
                elif param_name == 'thread_spec':
                    size_info['thread_diameter'] = float(match.group(1))
                    size_info['thread_pitch'] = float(match.group(2))
                elif param_name == 'size_with_unit':
                    unit = match.group(2).lower()
                    value = float(match.group(1))
                    # 统一转换为mm
                    if unit in ['cm']:
                        value *= 10
                    elif unit in ['m']:
                        value *= 1000
                    elif unit in ['inch', '"']:
                        value *= 25.4
                    size_info['size_mm'] = value
        
        # 从其他字段提取尺寸信息
        size_fields = ['尺寸', '直径', '长度', '宽度', '高度', 'size', 'diameter']
        for field in size_fields:
            if field in data_record and data_record[field]:
                value_str = str(data_record[field])
                numbers = re.findall(r'\d+(?:\.\d+)?', value_str)
                if numbers:
                    size_info[field] = float(numbers[0])
        
        return size_info
    
    def _extract_pressure_rating(self, specification: str) -> Optional[str]:
        """提取压力等级"""
        pressure_patterns = [
            r'PN\s*(\d+(?:\.\d+)?)',      # PN16, PN25
            r'CL\s*(\d+)',                # CL150, CL300
            r'(\d+(?:\.\d+)?)\s*MPa',     # 1.6MPa, 2.5MPa
            r'(\d+)\s*bar',               # 16bar, 25bar
            r'(\d+)\s*psi'                # 150psi, 300psi
        ]
        
        for pattern in pressure_patterns:
            match = re.search(pattern, specification, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_temperature_rating(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取温度等级"""
        temp_fields = ['使用温度', '工作温度', '温度范围', 'temperature']
        
        for field in temp_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        # 从规格中提取温度
        all_text = ' '.join([str(v) for v in data_record.values()])
        temp_match = re.search(r'(-?\d+(?:\.\d+)?)\s*[~～]\s*(-?\d+(?:\.\d+)?)\s*℃', all_text)
        if temp_match:
            return f"{temp_match.group(1)}~{temp_match.group(2)}℃"
        
        temp_match = re.search(r'(-?\d+(?:\.\d+)?)\s*℃', all_text)
        if temp_match:
            return f"{temp_match.group(1)}℃"
        
        return None
    
    def _extract_standard(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取执行标准"""
        standard_fields = ['执行标准', '标准', 'standard', '技术标准']
        
        for field in standard_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        # 从所有字段中搜索标准模式
        all_text = ' '.join([str(v) for v in data_record.values()])
        
        standard_patterns = [
            r'GB/T\s*\d+[-.]?\d*',       # GB/T标准
            r'GB\s*\d+[-.]?\d*',         # GB标准
            r'ANSI\s*[A-Z]?\d+[-.]?\d*', # ANSI标准
            r'API\s*\d+[A-Z]?',          # API标准
            r'ASME\s*[A-Z]?\d+[-.]?\d*', # ASME标准
            r'JIS\s*[A-Z]?\d+[-.]?\d*',  # JIS标准
            r'DIN\s*\d+[-.]?\d*',        # DIN标准
            r'HG/T\s*\d+[-.]?\d*'        # HG/T标准
        ]
        
        for pattern in standard_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _classify_material(self, name: str, specification: str) -> Dict[str, str]:
        """物料分类识别"""
        classification = {'level1': '未分类', 'level2': '未分类'}
        
        # 合并名称和规格进行分类
        combined_text = f"{name} {specification}".lower()
        
        # 遍历分类映射进行匹配
        for category, info in self.category_mapping.items():
            for keyword in info['keywords']:
                if keyword in combined_text:
                    classification['level1'] = info['level1']
                    classification['level2'] = info['level2']
                    
                    # 细分三级分类
                    if category == '阀门':
                        if any(valve_type in combined_text for valve_type in ['球阀', '球形阀']):
                            classification['level3'] = '球阀'
                        elif any(valve_type in combined_text for valve_type in ['蝶阀', '蝶形阀']):
                            classification['level3'] = '蝶阀'
                        elif any(valve_type in combined_text for valve_type in ['闸阀', '闸板阀']):
                            classification['level3'] = '闸阀'
                        elif any(valve_type in combined_text for valve_type in ['疏水器', '疏水阀']):
                            classification['level3'] = '疏水阀'
                    
                    elif category == '管件':
                        if '弯头' in combined_text:
                            classification['level3'] = '弯头'
                        elif '三通' in combined_text:
                            classification['level3'] = '三通'
                        elif '法兰' in combined_text:
                            classification['level3'] = '法兰'
                    
                    return classification
        
        return classification
    
    def _extract_technical_parameters(self, data_record: Dict[str, Any]) -> Dict[str, Any]:
        """提取技术参数"""
        tech_params = {}
        
        # 定义技术参数字段
        tech_fields = [
            '流量', '扬程', '功率', '转速', '效率', '介质', '连接方式',
            'flow_rate', 'head', 'power', 'speed', 'efficiency', 'media'
        ]
        
        for field in tech_fields:
            if field in data_record and data_record[field]:
                tech_params[field] = data_record[field]
        
        # 从规格中提取技术参数
        specification = str(data_record.get('规格型号', ''))
        
        # 提取流量参数
        flow_match = re.search(r'(\d+(?:\.\d+)?)\s*(m³/h|L/min|t/h)', specification)
        if flow_match:
            tech_params['流量'] = f"{flow_match.group(1)} {flow_match.group(2)}"
        
        # 提取功率参数
        power_match = re.search(r'(\d+(?:\.\d+)?)\s*(kW|W|HP)', specification)
        if power_match:
            tech_params['功率'] = f"{power_match.group(1)} {power_match.group(2)}"
        
        # 提取转速参数
        speed_match = re.search(r'(\d+)\s*(r/min|rpm)', specification)
        if speed_match:
            tech_params['转速'] = f"{speed_match.group(1)} {speed_match.group(2)}"
        
        return tech_params
    
    def normalize_for_matching(self, feature: ManufacturingFeature) -> Dict[str, Any]:
        """
        标准化特征用于匹配
        
        Args:
            feature: 制造业特征
            
        Returns:
            Dict: 标准化匹配特征
        """
        normalized = {
            'name_keywords': self._extract_name_keywords(feature.name),
            'category_hierarchy': [feature.category_level1, feature.category_level2, feature.category_level3],
            'size_signature': self._generate_size_signature(feature.size),
            'material_properties': self._get_material_properties(feature.material_type),
            'pressure_class': self._normalize_pressure(feature.pressure_rating),
            'manufacturer_normalized': self._normalize_manufacturer(feature.manufacturer)
        }
        
        return normalized
    
    def _extract_name_keywords(self, name: str) -> List[str]:
        """提取名称关键词"""
        # 移除常见修饰词
        stop_words = ['型', '式', '用', '专用', '通用', '标准', '特殊', '进口', '国产']
        
        # 分词处理
        keywords = []
        words = re.findall(r'\w+', name)
        
        for word in words:
            if len(word) > 1 and word not in stop_words:
                keywords.append(word)
        
        return keywords
    
    def _generate_size_signature(self, size_info: Dict[str, float]) -> str:
        """生成尺寸特征签名"""
        signature_parts = []
        
        # 按重要性排序的尺寸参数
        priority_params = ['DN', 'PN', 'CL', 'diameter', 'length', 'width']
        
        for param in priority_params:
            if param in size_info:
                signature_parts.append(f"{param}:{size_info[param]}")
        
        return "|".join(signature_parts)
    
    def _get_material_properties(self, material_type: str) -> Dict[str, Any]:
        """获取材质属性"""
        if material_type in self.material_standards:
            return self.material_standards[material_type].get('properties', {})
        return {}
    
    def _normalize_pressure(self, pressure_rating: Optional[str]) -> Optional[str]:
        """标准化压力等级"""
        if not pressure_rating:
            return None
        
        # 转换为标准PN等级
        pressure_rating = pressure_rating.upper()
        
        # PN转换表
        pn_mapping = {
            'CL150': 'PN20', 'CL300': 'PN50', 'CL600': 'PN110',
            'CL900': 'PN150', 'CL1500': 'PN260', 'CL2500': 'PN420'
        }
        
        for cl_rating, pn_equivalent in pn_mapping.items():
            if cl_rating in pressure_rating:
                return pn_equivalent
        
        return pressure_rating
    
    def _normalize_manufacturer(self, manufacturer: str) -> str:
        """标准化制造商名称"""
        # 移除常见后缀
        suffixes = ['有限公司', '股份有限公司', '集团', '厂', '公司', 'Co.,Ltd', 'Corp', 'Inc']
        
        normalized = manufacturer
        for suffix in suffixes:
            normalized = normalized.replace(suffix, '')
        
        return normalized.strip()


# 测试代码
if __name__ == "__main__":
    # 测试制造业适配器
    adapter = ManufacturingAdapter()
    
    # 测试数据
    test_data = [
        {
            "物料名称": "疏水器",
            "规格型号": "DN25 PN16 碳钢",
            "制造商": "上海阀门厂有限公司",
            "材质": "WCB",
            "执行标准": "GB/T 12246",
            "使用温度": "-10~200℃"
        },
        {
            "产品名称": "不锈钢球阀",
            "规格": "DN50 CL150",
            "厂家": "天津泵业",
            "材料": "304不锈钢",
            "流量": "50 m³/h"
        }
    ]
    
    print("=== 制造业适配器测试 ===")
    for i, record in enumerate(test_data):
        print(f"\n--- 测试记录 {i+1} ---")
        feature = adapter.extract_features(record)
        
        print(f"物料名称: {feature.name}")
        print(f"规格型号: {feature.specification}")
        print(f"材质: {feature.material_type}")
        print(f"尺寸参数: {feature.size}")
        print(f"压力等级: {feature.pressure_rating}")
        print(f"分类: {feature.category_level1} > {feature.category_level2} > {feature.category_level3}")
        print(f"技术参数: {feature.technical_params}")
        
        # 测试标准化
        normalized = adapter.normalize_for_matching(feature)
        print(f"标准化特征: {normalized}")