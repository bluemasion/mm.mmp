# -*- coding: utf-8 -*-
"""
医疗行业数据源适配器
针对医疗器械和药品数据的专门处理和优化
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MedicalFeature:
    """医疗行业特征定义"""
    name: str                    # 产品名称
    specification: str           # 规格型号
    device_type: str            # 器械类型/药品类型
    classification: str         # 分类等级 (I类/II类/III类/处方药/非处方药)
    manufacturer: str           # 生产企业
    registration_no: Optional[str]  # 注册证号/批准文号
    model: Optional[str]        # 型号
    batch_no: Optional[str]     # 批号
    expiry_date: Optional[str]  # 有效期
    dosage_form: Optional[str]  # 剂型
    concentration: Optional[str] # 浓度/含量
    package_spec: Optional[str] # 包装规格
    indication: Optional[str]   # 适应症/用途
    contraindication: Optional[str] # 禁忌症
    storage_condition: Optional[str] # 储存条件
    standard: Optional[str]     # 执行标准
    category_level1: str        # 一级分类
    category_level2: str        # 二级分类
    category_level3: Optional[str]  # 三级分类
    clinical_params: Dict[str, Any]  # 临床参数

class MedicalAdapter:
    """医疗行业数据源适配器"""
    
    def __init__(self):
        self.device_classification = self._load_device_classification()
        self.drug_classification = self._load_drug_classification()
        self.dosage_forms = self._load_dosage_forms()
        self.medical_standards = self._load_medical_standards()
        
    def _load_device_classification(self) -> Dict[str, Dict]:
        """加载医疗器械分类"""
        return {
            # 基础医疗器械
            '基础器械': {
                'level1': '医疗器械',
                'level2': '基础医疗器械',
                'keywords': ['手术刀', '镊子', '钳子', '剪刀', '针头', '注射器', '输液器'],
                'class_risk': 'I-II类'
            },
            
            # 诊断器械
            '诊断器械': {
                'level1': '医疗器械',
                'level2': '诊断设备',
                'keywords': ['心电图', '超声', '内镜', 'CT', 'MRI', '血压计', '体温计', '血糖仪'],
                'class_risk': 'II-III类'
            },
            
            # 治疗器械
            '治疗器械': {
                'level1': '医疗器械',
                'level2': '治疗设备',
                'keywords': ['呼吸机', '监护仪', '除颤器', '透析机', '激光治疗仪', '电刀'],
                'class_risk': 'III类'
            },
            
            # 植入器械
            '植入器械': {
                'level1': '医疗器械',
                'level2': '植入物',
                'keywords': ['支架', '起搏器', '人工关节', '假体', '植入材料'],
                'class_risk': 'III类'
            },
            
            # 康复器械
            '康复器械': {
                'level1': '医疗器械',
                'level2': '康复辅助器具',
                'keywords': ['轮椅', '助听器', '义肢', '矫形器', '理疗设备'],
                'class_risk': 'I-II类'
            },
            
            # 一次性器械
            '一次性器械': {
                'level1': '医疗器械',
                'level2': '一次性医疗用品',
                'keywords': ['一次性', '无菌', '导管', '血袋', '敷料', '绷带', '口罩', '手套'],
                'class_risk': 'I-III类'
            }
        }
    
    def _load_drug_classification(self) -> Dict[str, Dict]:
        """加载药品分类"""
        return {
            # 处方药
            '处方药': {
                'level1': '药品',
                'level2': '处方药',
                'keywords': ['注射液', '胶囊', '片剂', '颗粒', '口服液', '栓剂'],
                'prescription_type': 'Rx'
            },
            
            # 非处方药
            '非处方药': {
                'level1': '药品',
                'level2': '非处方药',
                'keywords': ['OTC', '维生素', '感冒药', '止痛药', '消炎药'],
                'prescription_type': 'OTC'
            },
            
            # 中药
            '中药': {
                'level1': '药品',
                'level2': '中药',
                'keywords': ['中药', '中成药', '汤剂', '丸剂', '散剂', '膏药'],
                'prescription_type': 'TCM'
            },
            
            # 生物制品
            '生物制品': {
                'level1': '药品',
                'level2': '生物制品',
                'keywords': ['疫苗', '血液制品', '单克隆抗体', '重组蛋白', '细胞治疗'],
                'prescription_type': 'Biological'
            },
            
            # 外用药
            '外用药': {
                'level1': '药品',
                'level2': '外用药物',
                'keywords': ['软膏', '乳膏', '凝胶', '溶液', '滴眼液', '滴耳液', '喷雾剂'],
                'prescription_type': 'External'
            }
        }
    
    def _load_dosage_forms(self) -> Dict[str, Dict]:
        """加载剂型分类"""
        return {
            '口服固体': ['片剂', '胶囊', '颗粒', '丸剂', '散剂'],
            '口服液体': ['口服液', '糖浆', '合剂', '酊剂'],
            '注射剂': ['注射液', '冻干粉针', '输液', '注射用粉'],
            '外用制剂': ['软膏', '乳膏', '凝胶', '贴剂', '喷雾剂'],
            '特殊剂型': ['栓剂', '吸入剂', '滴眼液', '鼻用制剂']
        }
    
    def _load_medical_standards(self) -> Dict[str, Dict]:
        """加载医疗标准"""
        return {
            'YY': {
                'type': '医疗器械标准',
                'description': '医疗器械行业标准',
                'scope': '医疗器械'
            },
            'GB/T': {
                'type': '国家推荐标准',
                'description': '国家推荐性标准',
                'scope': '通用'
            },
            'ISO': {
                'type': '国际标准',
                'description': '国际标准化组织标准',
                'scope': '国际通用'
            },
            'CE': {
                'type': '欧盟认证',
                'description': '欧盟符合性标志',
                'scope': '欧盟市场'
            },
            'FDA': {
                'type': '美国认证',
                'description': '美国食品药品监督管理局',
                'scope': '美国市场'
            }
        }
    
    def extract_features(self, data_record: Dict[str, Any]) -> MedicalFeature:
        """
        提取医疗行业特征
        
        Args:
            data_record: 原始数据记录
            
        Returns:
            MedicalFeature: 标准化特征
        """
        logger.debug(f"提取医疗行业特征: {data_record}")
        
        # 基础信息提取
        name = self._extract_product_name(data_record)
        specification = self._extract_specification(data_record)
        device_type = self._extract_device_type(data_record)
        manufacturer = self._extract_manufacturer(data_record)
        
        # 分类等级识别
        classification = self._extract_classification(data_record, name)
        
        # 注册信息提取
        registration_no = self._extract_registration_no(data_record)
        model = self._extract_model(data_record)
        batch_no = self._extract_batch_no(data_record)
        expiry_date = self._extract_expiry_date(data_record)
        
        # 药品特有信息
        dosage_form = self._extract_dosage_form(data_record, name)
        concentration = self._extract_concentration(data_record)
        package_spec = self._extract_package_spec(data_record)
        
        # 临床信息
        indication = self._extract_indication(data_record)
        contraindication = self._extract_contraindication(data_record)
        storage_condition = self._extract_storage_condition(data_record)
        standard = self._extract_standard(data_record)
        
        # 分类识别
        category_info = self._classify_medical_product(name, device_type, classification)
        
        # 临床参数提取
        clinical_params = self._extract_clinical_parameters(data_record)
        
        return MedicalFeature(
            name=name,
            specification=specification,
            device_type=device_type,
            classification=classification,
            manufacturer=manufacturer,
            registration_no=registration_no,
            model=model,
            batch_no=batch_no,
            expiry_date=expiry_date,
            dosage_form=dosage_form,
            concentration=concentration,
            package_spec=package_spec,
            indication=indication,
            contraindication=contraindication,
            storage_condition=storage_condition,
            standard=standard,
            category_level1=category_info.get('level1', '未分类'),
            category_level2=category_info.get('level2', '未分类'),
            category_level3=category_info.get('level3'),
            clinical_params=clinical_params
        )
    
    def _extract_product_name(self, data_record: Dict[str, Any]) -> str:
        """提取产品名称"""
        name_fields = ['产品名称', '器械名称', '药品名称', '商品名', '通用名', 'name', '名称']
        
        for field in name_fields:
            if field in data_record and data_record[field]:
                name = str(data_record[field]).strip()
                # 清理名称
                name = re.sub(r'\s+', ' ', name)
                name = re.sub(r'[^\w\u4e00-\u9fff\s\-\(\)]', '', name)
                return name
        
        return '未知产品'
    
    def _extract_specification(self, data_record: Dict[str, Any]) -> str:
        """提取规格型号"""
        spec_fields = ['规格', '型号', '规格型号', 'spec', 'specification', '产品规格']
        
        specifications = []
        for field in spec_fields:
            if field in data_record and data_record[field]:
                spec = str(data_record[field]).strip()
                if spec and spec not in specifications:
                    specifications.append(spec)
        
        return ' | '.join(specifications) if specifications else ''
    
    def _extract_device_type(self, data_record: Dict[str, Any]) -> str:
        """提取器械/药品类型"""
        type_fields = ['产品类型', '器械类型', '药品类型', 'type', '类别']
        
        for field in type_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        # 从名称推断类型
        name = str(data_record.get('产品名称', ''))
        if any(keyword in name for keyword in ['注射器', '输液', '导管', '敷料']):
            return '一次性医疗用品'
        elif any(keyword in name for keyword in ['心电', '超声', '监护']):
            return '诊断设备'
        elif any(keyword in name for keyword in ['片', '胶囊', '注射液']):
            return '药品'
        
        return '未知类型'
    
    def _extract_manufacturer(self, data_record: Dict[str, Any]) -> str:
        """提取生产企业"""
        manufacturer_fields = ['生产企业', '制造商', '厂家', 'manufacturer', '生产厂家', '企业名称']
        
        for field in manufacturer_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        return '未知企业'
    
    def _extract_classification(self, data_record: Dict[str, Any], name: str) -> str:
        """提取分类等级"""
        class_fields = ['分类', '类别', '风险等级', 'classification', '管理类别']
        
        for field in class_fields:
            if field in data_record and data_record[field]:
                classification = str(data_record[field]).strip()
                # 标准化分类表示
                if 'I类' in classification or '一类' in classification:
                    return 'I类医疗器械'
                elif 'II类' in classification or '二类' in classification:
                    return 'II类医疗器械'
                elif 'III类' in classification or '三类' in classification:
                    return 'III类医疗器械'
                elif '处方药' in classification or 'Rx' in classification:
                    return '处方药'
                elif 'OTC' in classification or '非处方' in classification:
                    return '非处方药'
                return classification
        
        # 从名称推断分类
        if any(keyword in name for keyword in ['注射器', '体温计', '血压计']):
            return 'II类医疗器械'
        elif any(keyword in name for keyword in ['呼吸机', '监护仪', '起搏器']):
            return 'III类医疗器械'
        elif any(keyword in name for keyword in ['片剂', '胶囊', '注射液']):
            return '处方药'
        
        return '未分类'
    
    def _extract_registration_no(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取注册证号/批准文号"""
        reg_fields = ['注册证号', '批准文号', '许可证号', 'registration_no', '证号']
        
        for field in reg_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        # 从所有字段中搜索注册号模式
        all_text = ' '.join([str(v) for v in data_record.values()])
        
        # 医疗器械注册证号模式
        device_patterns = [
            r'国械注准\d+',
            r'国械注进\d+',
            r'械字\d+',
            r'准字\d+'
        ]
        
        # 药品批准文号模式
        drug_patterns = [
            r'国药准字[A-Z]\d+',
            r'国药准字[HZS]\d+',
            r'国药试字[A-Z]\d+',
            r'进口药品注册证号[A-Z]\d+'
        ]
        
        for pattern in device_patterns + drug_patterns:
            match = re.search(pattern, all_text)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_model(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取型号"""
        model_fields = ['型号', '产品型号', 'model', '货号']
        
        for field in model_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        return None
    
    def _extract_batch_no(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取批号"""
        batch_fields = ['批号', '生产批号', 'batch_no', 'lot_no']
        
        for field in batch_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        return None
    
    def _extract_expiry_date(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取有效期"""
        expiry_fields = ['有效期', '失效期', '过期时间', 'expiry_date', '保质期']
        
        for field in expiry_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        # 从所有字段中搜索日期模式
        all_text = ' '.join([str(v) for v in data_record.values()])
        
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',      # 2024-12-31
            r'\d{4}/\d{2}/\d{2}',      # 2024/12/31
            r'\d{4}\.\d{2}\.\d{2}',    # 2024.12.31
            r'\d{2}/\d{2}/\d{4}',      # 12/31/2024
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, all_text)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_dosage_form(self, data_record: Dict[str, Any], name: str) -> Optional[str]:
        """提取剂型"""
        form_fields = ['剂型', '给药途径', 'dosage_form']
        
        for field in form_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        # 从名称中识别剂型
        combined_text = f"{name} {data_record.get('规格', '')}"
        
        for category, forms in self.dosage_forms.items():
            for form in forms:
                if form in combined_text:
                    return form
        
        return None
    
    def _extract_concentration(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取浓度/含量"""
        conc_fields = ['浓度', '含量', '规格', 'concentration', '强度']
        
        for field in conc_fields:
            if field in data_record and data_record[field]:
                value = str(data_record[field])
                # 检查是否包含浓度信息
                if re.search(r'\d+\s*(mg|μg|g|ml|%|IU)', value, re.IGNORECASE):
                    return value.strip()
        
        # 从规格中提取浓度
        all_text = ' '.join([str(v) for v in data_record.values()])
        conc_patterns = [
            r'\d+(?:\.\d+)?\s*mg/ml',    # mg/ml
            r'\d+(?:\.\d+)?\s*%',        # 百分比浓度
            r'\d+(?:\.\d+)?\s*mg',       # 毫克
            r'\d+(?:\.\d+)?\s*μg',       # 微克
            r'\d+(?:\.\d+)?\s*IU'        # 国际单位
        ]
        
        for pattern in conc_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_package_spec(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取包装规格"""
        package_fields = ['包装规格', '包装', '装量', 'package', '规格']
        
        for field in package_fields:
            if field in data_record and data_record[field]:
                value = str(data_record[field])
                # 检查是否包含包装信息
                if re.search(r'\d+\s*(支|盒|瓶|袋|个|粒|ml)', value):
                    return value.strip()
        
        # 从规格中提取包装信息
        all_text = ' '.join([str(v) for v in data_record.values()])
        package_patterns = [
            r'\d+\s*支/盒',
            r'\d+\s*粒/盒',
            r'\d+\s*ml/瓶',
            r'\d+\s*袋/盒'
        ]
        
        for pattern in package_patterns:
            match = re.search(pattern, all_text)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_indication(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取适应症/用途"""
        indication_fields = ['适应症', '用途', '功能主治', 'indication', '应用']
        
        for field in indication_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        return None
    
    def _extract_contraindication(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取禁忌症"""
        contra_fields = ['禁忌症', '禁忌', 'contraindication', '注意事项']
        
        for field in contra_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        return None
    
    def _extract_storage_condition(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取储存条件"""
        storage_fields = ['储存条件', '贮存', '保存条件', 'storage', '存储']
        
        for field in storage_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        return None
    
    def _extract_standard(self, data_record: Dict[str, Any]) -> Optional[str]:
        """提取执行标准"""
        standard_fields = ['执行标准', '标准', 'standard', '技术要求']
        
        for field in standard_fields:
            if field in data_record and data_record[field]:
                return str(data_record[field]).strip()
        
        # 从所有字段中搜索标准模式
        all_text = ' '.join([str(v) for v in data_record.values()])
        
        standard_patterns = [
            r'YY/T\s*\d+[-.]?\d*',      # YY/T标准
            r'YY\s*\d+[-.]?\d*',        # YY标准
            r'GB/T\s*\d+[-.]?\d*',      # GB/T标准
            r'ISO\s*\d+[-.]?\d*',       # ISO标准
            r'CE\s*\w*',                # CE认证
            r'FDA\s*\w*'                # FDA认证
        ]
        
        for pattern in standard_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _classify_medical_product(self, name: str, device_type: str, 
                                classification: str) -> Dict[str, str]:
        """医疗产品分类识别"""
        category_info = {'level1': '未分类', 'level2': '未分类'}
        
        combined_text = f"{name} {device_type} {classification}".lower()
        
        # 优先检查器械分类
        for category, info in self.device_classification.items():
            for keyword in info['keywords']:
                if keyword in combined_text:
                    category_info['level1'] = info['level1']
                    category_info['level2'] = info['level2']
                    
                    # 细分三级分类
                    if category == '基础器械':
                        if '注射器' in combined_text:
                            category_info['level3'] = '注射器械'
                        elif '手术' in combined_text:
                            category_info['level3'] = '手术器械'
                    elif category == '诊断器械':
                        if '心电' in combined_text:
                            category_info['level3'] = '心电设备'
                        elif '超声' in combined_text:
                            category_info['level3'] = '超声设备'
                    elif category == '一次性器械':
                        if '输液' in combined_text:
                            category_info['level3'] = '输液器具'
                        elif '敷料' in combined_text:
                            category_info['level3'] = '医用敷料'
                    
                    return category_info
        
        # 检查药品分类
        for category, info in self.drug_classification.items():
            for keyword in info['keywords']:
                if keyword in combined_text:
                    category_info['level1'] = info['level1']
                    category_info['level2'] = info['level2']
                    
                    # 细分三级分类
                    if category == '处方药':
                        if '注射液' in combined_text:
                            category_info['level3'] = '注射剂'
                        elif '片剂' in combined_text or '胶囊' in combined_text:
                            category_info['level3'] = '口服制剂'
                    
                    return category_info
        
        return category_info
    
    def _extract_clinical_parameters(self, data_record: Dict[str, Any]) -> Dict[str, Any]:
        """提取临床参数"""
        clinical_params = {}
        
        # 定义临床参数字段
        clinical_fields = [
            '用法用量', '不良反应', '药理作用', '药代动力学', '临床试验',
            'dosage', 'side_effects', 'pharmacology', 'clinical_data'
        ]
        
        for field in clinical_fields:
            if field in data_record and data_record[field]:
                clinical_params[field] = data_record[field]
        
        # 提取特定临床参数
        # 用法用量
        if any(field in data_record for field in ['用法用量', '给药方案', 'dosage']):
            for field in ['用法用量', '给药方案', 'dosage']:
                if field in data_record and data_record[field]:
                    clinical_params['用法用量'] = data_record[field]
                    break
        
        # 不良反应
        if any(field in data_record for field in ['不良反应', '副作用', 'side_effects']):
            for field in ['不良反应', '副作用', 'side_effects']:
                if field in data_record and data_record[field]:
                    clinical_params['不良反应'] = data_record[field]
                    break
        
        return clinical_params
    
    def normalize_for_matching(self, feature: MedicalFeature) -> Dict[str, Any]:
        """
        标准化特征用于匹配
        
        Args:
            feature: 医疗行业特征
            
        Returns:
            Dict: 标准化匹配特征
        """
        normalized = {
            'name_keywords': self._extract_name_keywords(feature.name),
            'category_hierarchy': [feature.category_level1, feature.category_level2, feature.category_level3],
            'classification_level': self._normalize_classification(feature.classification),
            'dosage_category': self._categorize_dosage_form(feature.dosage_form),
            'concentration_range': self._normalize_concentration(feature.concentration),
            'manufacturer_normalized': self._normalize_manufacturer(feature.manufacturer),
            'therapeutic_area': self._extract_therapeutic_area(feature.indication)
        }
        
        return normalized
    
    def _extract_name_keywords(self, name: str) -> List[str]:
        """提取名称关键词"""
        # 医疗产品的停用词
        stop_words = ['一次性', '无菌', '医用', '临床', '专用', '型', '式', '进口', '国产']
        
        keywords = []
        words = re.findall(r'\w+', name)
        
        for word in words:
            if len(word) > 1 and word not in stop_words:
                keywords.append(word)
        
        return keywords
    
    def _normalize_classification(self, classification: str) -> int:
        """标准化分类等级为数值"""
        if 'I类' in classification:
            return 1
        elif 'II类' in classification:
            return 2
        elif 'III类' in classification:
            return 3
        elif '处方药' in classification:
            return 4
        elif 'OTC' in classification or '非处方' in classification:
            return 5
        return 0
    
    def _categorize_dosage_form(self, dosage_form: Optional[str]) -> Optional[str]:
        """剂型分类"""
        if not dosage_form:
            return None
        
        for category, forms in self.dosage_forms.items():
            if dosage_form in forms:
                return category
        
        return None
    
    def _normalize_concentration(self, concentration: Optional[str]) -> Optional[Dict]:
        """标准化浓度信息"""
        if not concentration:
            return None
        
        # 提取数值和单位
        pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z/%μ]+)'
        match = re.search(pattern, concentration)
        
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            
            return {
                'value': value,
                'unit': unit,
                'normalized_value': self._convert_to_standard_unit(value, unit)
            }
        
        return None
    
    def _convert_to_standard_unit(self, value: float, unit: str) -> float:
        """转换为标准单位（mg）"""
        unit_conversions = {
            'g': 1000,      # 克转毫克
            'mg': 1,        # 毫克
            'μg': 0.001,    # 微克转毫克
            'mcg': 0.001,   # 微克转毫克
        }
        
        return value * unit_conversions.get(unit.lower(), 1)
    
    def _normalize_manufacturer(self, manufacturer: str) -> str:
        """标准化制造商名称"""
        # 移除常见后缀
        suffixes = ['有限公司', '股份有限公司', '集团', '公司', '企业', '厂', 
                   'Co.,Ltd', 'Corp', 'Inc', 'Ltd', '制药']
        
        normalized = manufacturer
        for suffix in suffixes:
            normalized = normalized.replace(suffix, '')
        
        return normalized.strip()
    
    def _extract_therapeutic_area(self, indication: Optional[str]) -> Optional[str]:
        """提取治疗领域"""
        if not indication:
            return None
        
        therapeutic_areas = {
            '心血管': ['高血压', '心脏病', '冠心病', '心律失常', '心衰'],
            '呼吸系统': ['哮喘', '肺炎', '支气管炎', '咳嗽', '感冒'],
            '消化系统': ['胃炎', '胃溃疡', '腹泻', '便秘', '肝炎'],
            '神经系统': ['头痛', '癫痫', '抑郁', '焦虑', '失眠'],
            '内分泌': ['糖尿病', '甲亢', '甲减', '骨质疏松'],
            '感染': ['细菌感染', '病毒感染', '真菌感染', '抗生素'],
            '肿瘤': ['癌症', '化疗', '肿瘤', '恶性', '良性'],
            '免疫': ['过敏', '免疫', '风湿', '关节炎']
        }
        
        indication_lower = indication.lower()
        for area, keywords in therapeutic_areas.items():
            if any(keyword in indication_lower for keyword in keywords):
                return area
        
        return None


# 测试代码
if __name__ == "__main__":
    # 测试医疗适配器
    adapter = MedicalAdapter()
    
    # 测试数据
    test_data = [
        {
            "产品名称": "一次性使用无菌注射器",
            "规格": "5ml",
            "生产企业": "山东威高集团医用高分子制品股份有限公司",
            "分类": "II类医疗器械",
            "注册证号": "国械注准20153660334",
            "型号": "WG-05",
            "包装规格": "100支/盒"
        },
        {
            "药品名称": "阿莫西林胶囊",
            "规格": "0.25g",
            "生产企业": "华北制药股份有限公司",
            "批准文号": "国药准字H13020959",
            "分类": "处方药",
            "适应症": "用于敏感菌所致的各种感染",
            "用法用量": "口服，一次0.5g，一日3次",
            "包装规格": "24粒/盒"
        }
    ]
    
    print("=== 医疗适配器测试 ===")
    for i, record in enumerate(test_data):
        print(f"\n--- 测试记录 {i+1} ---")
        feature = adapter.extract_features(record)
        
        print(f"产品名称: {feature.name}")
        print(f"规格: {feature.specification}")
        print(f"分类: {feature.classification}")
        print(f"分类层级: {feature.category_level1} > {feature.category_level2} > {feature.category_level3}")
        print(f"生产企业: {feature.manufacturer}")
        print(f"注册证号: {feature.registration_no}")
        print(f"剂型: {feature.dosage_form}")
        print(f"浓度: {feature.concentration}")
        print(f"包装规格: {feature.package_spec}")
        print(f"适应症: {feature.indication}")
        
        # 测试标准化
        normalized = adapter.normalize_for_matching(feature)
        print(f"标准化特征: {normalized}")