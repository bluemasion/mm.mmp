# app/smart_classifier.py - 智能物料分类器
import re
import sqlite3
import os
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import logging

@dataclass
class MaterialFeature:
    """物料特征数据结构"""
    name: str
    spec: str
    unit: str = ""
    dn: str = ""  # 公称直径
    pn: str = ""  # 压力等级
    material: str = ""  # 材质
    
class SmartClassifier:
    """智能物料分类器
    
    基于多维特征属性的物料分类系统，支持：
    1. 基础属性匹配（名称、单位）
    2. 特征属性分析（DN、PN、材质等）
    3. 规格参数解析（从长描述中提取关键信息）
    4. 相似度计算和排序
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def classify_material(self, material: MaterialFeature) -> List[Dict[str, Any]]:
        """
        对物料进行智能分类
        
        Args:
            material: 物料特征数据
            
        Returns:
            分类结果列表，按相似度降序排列
        """
        try:
            self.logger.info(f"开始分类物料: {material.name}, 规格: {material.spec}")
            
            # 1. 加载分类数据和示例
            classification_data = self._load_classification_data()
            sample_materials = self._load_sample_materials()
            
            self.logger.info(f"加载了 {len(classification_data)} 个分类, {len(sample_materials)} 个示例组")
            
            # 2. 特征提取和增强
            enhanced_features = self._extract_enhanced_features(material)
            
            # 3. 计算每个分类的相似度
            results = []
            for category in classification_data:
                similarity = self._calculate_similarity(
                    enhanced_features, 
                    category, 
                    sample_materials.get(category['name'], [])
                )
                
                if category['name'] in ['疏水阀', '管道配件']:
                    self.logger.info(f"重点分类 '{category['name']}' 相似度: {similarity}")
                else:
                    self.logger.debug(f"分类 '{category['name']}' 相似度: {similarity}")
                
                if similarity > 0.02:  # 降低阈值到2%
                    results.append({
                        'category': category['name'],
                        'description': category.get('description', ''),
                        'confidence': round(similarity * 100, 1),
                        'attributes': self._build_attributes(category, enhanced_features),
                        'matching_samples': self._get_matching_samples(
                            enhanced_features, 
                            sample_materials.get(category['name'], [])
                        )[:3]  # 最多返回3个相似样例
                    })
            
            # 4. 按相似度和分类精确度排序
            # 优先选择更精确的分类（避免选择过于宽泛的上级分类）
            def sort_key(result):
                confidence = result['confidence']
                category_name = result['category']
                
                # 给精确匹配的专业分类更高优先级
                specific_categories = ['疏水阀', '机械密封及配件', '金属软管', '离心泵配件', '往复泵配件', '计量泵配件', '活塞式压缩机配件']
                general_categories = ['管道配件', '通用机械设备配件', '工业泵配件', '气体压缩机配件', '其他']
                
                if category_name in specific_categories and confidence > 50:
                    return confidence + 20  # 精确分类加分
                elif category_name in general_categories:
                    return confidence - 10  # 通用分类减分
                else:
                    return confidence
            
            results.sort(key=sort_key, reverse=True)
            
            self.logger.info(f"找到 {len(results)} 个匹配的分类")
            if results:
                self.logger.info(f"最佳匹配: {results[0]['category']} (置信度: {results[0]['confidence']}%)")
            
            return results[:5]  # 返回前5个最相似的分类
            
        except Exception as e:
            self.logger.error(f"分类错误: {str(e)}")
            return []
    
    def _load_classification_data(self) -> List[Dict[str, Any]]:
        """加载分类数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT category_name, description, level
                FROM material_categories 
                WHERE level <= 3
                ORDER BY level, category_name
            ''')
            
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    'name': row[0],
                    'description': row[1] or '',
                    'level': row[2]
                })
            
            conn.close()
            return categories
            
        except Exception as e:
            self.logger.error(f"加载分类数据失败: {str(e)}")
            return []
    
    def _load_sample_materials(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载示例物料数据"""
        # 基于您提供的CSV数据，创建一些示例分类数据
        sample_data = {
            '金属软管': [
                {
                    'name': '金属软管',
                    'spec': 'DN25 PN2.0，材质304SS，L=3m，两端法兰连接',
                    'dn': 'DN25', 'pn': 'PN2.0', 'material': '304SS'
                },
                {
                    'name': '金属软管', 
                    'spec': 'DN50 PN16，304不锈钢，长度10米',
                    'dn': 'DN50', 'pn': 'PN16', 'material': '304SS'
                }
            ],
            '疏水器': [
                {
                    'name': '疏水器',
                    'spec': 'DN25 CL150，材质CS，介质温度100-180℃',
                    'dn': 'DN25', 'pn': 'CL150', 'material': 'CS'
                }
            ],
            '带颈对焊法兰': [
                {
                    'name': '全平面带颈对焊法兰',
                    'spec': '1.0MPa DN200 0Cr18Ni9',
                    'dn': 'DN200', 'pn': '1.0MPa', 'material': '0Cr18Ni9'
                },
                {
                    'name': '凸面带颈对焊法兰',
                    'spec': '4.0MPa DN50 20#',
                    'dn': 'DN50', 'pn': '4.0MPa', 'material': '20#'
                }
            ],
            '无缝三通': [
                {
                    'name': '无缝异径三通',
                    'spec': 'DN50*25 t=3.5 20#',
                    'dn': 'DN50*25', 'material': '20#'
                }
            ],
            '其它管道配件': [
                {
                    'name': '对焊式直通焊接终端接头',
                    'spec': 'PN63 BW Φ14/1/2"NPT(M) 316SS',
                    'pn': 'PN63', 'material': '316SS'
                }
            ]
        }
        
        return sample_data
    
    def _extract_enhanced_features(self, material: MaterialFeature) -> Dict[str, Any]:
        """提取增强特征"""
        features = {
            'name': material.name.lower().strip(),
            'spec': material.spec.lower().strip(),
            'unit': material.unit,
            'dn_input': material.dn,
            'pn_input': material.pn, 
            'material_input': material.material
        }
        
        # 从规格描述中提取特征
        spec_text = f"{material.spec} {material.dn} {material.pn} {material.material}".lower()
        
        # 提取DN值
        dn_patterns = [
            r'dn\s*(\d+(?:\*\d+)?)',
            r'φ\s*(\d+)',
            r'直径\s*(\d+)'
        ]
        features['extracted_dn'] = self._extract_by_patterns(spec_text, dn_patterns)
        
        # 提取压力等级
        pn_patterns = [
            r'pn\s*([\d.]+)',
            r'cl\s*(\d+)',
            r'(\d+\.?\d*)\s*mpa',
            r'(\d+)\s*lb'
        ]
        features['extracted_pn'] = self._extract_by_patterns(spec_text, pn_patterns)
        
        # 提取材质
        material_patterns = [
            r'(304ss?|316ss?|321ss?)',
            r'(cs|碳钢)',
            r'(20#|q235)',
            r'(a105|a182)',
            r'(0cr18ni9)'
        ]
        features['extracted_material'] = self._extract_by_patterns(spec_text, material_patterns)
        
        # 提取长度
        length_patterns = [
            r'l\s*=\s*([\d.]+)\s*m',
            r'长度\s*([\d.]+)\s*[米m]',
            r'([\d.]+)\s*[米m]'
        ]
        features['extracted_length'] = self._extract_by_patterns(spec_text, length_patterns)
        
        # 提取温度
        temp_patterns = [
            r'(\d+(?:-\d+)?)\s*℃',
            r'温度\s*[:：]?\s*(\d+(?:-\d+)?)'
        ]
        features['extracted_temp'] = self._extract_by_patterns(spec_text, temp_patterns)
        
        return features
    
    def _extract_by_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """按模式提取文本"""
        results = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results.extend([match.strip() for match in matches if match.strip()])
        return list(set(results))  # 去重
    
    def _calculate_similarity(self, features: Dict[str, Any], 
                            category: Dict[str, Any], 
                            samples: List[Dict[str, Any]]) -> float:
        """计算相似度"""
        
        # 1. 名称匹配（权重80%，大幅提高权重）
        name_score = self._calculate_name_similarity(features['name'], category['name'])
        
        # 2. 规格特征匹配（权重10%）
        spec_score = self._calculate_spec_similarity(features, samples)
        
        # 3. 单位匹配（权重5%）
        unit_score = self._calculate_unit_similarity(features['unit'], samples)
        
        # 4. 关键词匹配（权重5%）
        keyword_score = self._calculate_keyword_similarity(features, category)
        
        # 加权计算总相似度
        total_score = (
            name_score * 0.8 + 
            spec_score * 0.1 + 
            unit_score * 0.05 + 
            keyword_score * 0.05
        )
        
        # 精确匹配奖励：如果是高精度同义词匹配，给额外加分
        if name_score > 0.9:
            total_score = min(total_score * 1.2, 1.0)  # 最多120%，但不超过100%
        
        # 调试日志
        if total_score > 0:
            self.logger.debug(f"分类 '{category['name']}' 得分: name={name_score:.2f}, spec={spec_score:.2f}, unit={unit_score:.2f}, keyword={keyword_score:.2f}, total={total_score:.2f}")
        
        return min(total_score, 1.0)  # 确保不超过1.0
    
    def _calculate_name_similarity(self, input_name: str, category_name: str) -> float:
        """计算名称相似度"""
        input_name = input_name.lower().strip()
        category_name = category_name.lower().strip()
        
        # 完全匹配
        if input_name == category_name:
            return 1.0
            
        # 包含匹配
        if input_name in category_name or category_name in input_name:
            return 0.8
            
        # 关键词匹配
        input_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', input_name))
        category_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', category_name))
        
        if input_words and category_words:
            intersection = input_words.intersection(category_words)
            union = input_words.union(category_words)
            jaccard_score = len(intersection) / len(union)
            
            # 如果有交集，给予更高的基础分数
            if intersection:
                return max(jaccard_score * 0.6, 0.3)  # 至少给30%的分数
            
        # 管道配件相关的特殊匹配规则
        pipe_fittings = {
            '弯头': ['管道配件', '弯头', '弯管'],
            '三通': ['管道配件', '三通'],  
            '法兰': ['管道配件', '法兰', '带颈对焊法兰', '平焊法兰'],
            '管道': ['管道配件', '管道', '管子'],
            '软管': ['管道配件', '软管', '金属软管'],
            '疏水器': ['疏水阀', '管道配件', '疏水器'],
            '疏水阀': ['疏水阀', '管道配件', '疏水器'],
            '密封': ['机械密封及配件', '密封'],
            '接头': ['管道配件', '接头', '终端接头'],
            '对焊': ['管道配件', '对焊', '焊接'],
            '压缩机': ['气体压缩机配件', '活塞式压缩机配件', '螺杆式压缩机配件', '离心式压缩机配件'],
            '泵': ['工业泵配件', '离心泵配件', '往复泵配件', '计量泵配件'],
            '阀门': ['管道配件', '阀门', '阀'],
            '金属软管': ['管道配件', '软管', '金属软管'],
            '螺塞': ['紧固件', '螺栓', '螺丝'],
            '螺栓': ['紧固件', '螺塞', '螺丝'],
            '螺钉': ['紧固件', '螺栓', '螺丝'],
            '螺母': ['紧固件', '螺栓配件'],
            '垫片': ['紧固件', '密封件']
        }
        
        for material_type, related_categories in pipe_fittings.items():
            if material_type in input_name:
                for related in related_categories:
                    if related in category_name:
                        # 如果是完全匹配（如疏水器->疏水阀），给更高分数
                        if material_type == input_name.strip() and related == category_name.strip():
                            return 0.9
                        # 如果是相关匹配，给中等分数
                        return 0.6
        
        # 通用词汇相似度匹配 - 优先精确匹配
        similar_words = {
            '疏水器': ['疏水阀', '疏水', '蒸汽疏水器'],
            '疏水阀': ['疏水器', '疏水', '蒸汽疏水阀'],
            '蒸汽疏水器': ['疏水阀', '疏水器'],
            '压缩机': ['压缩', '空压机', '气体压缩机'],
            '接头': ['连接', '接口', '终端接头', '焊接接头'],
            '对焊接头': ['接头', '焊接终端接头'],
            '终端接头': ['接头', '对焊接头'],
            '法兰': ['连接', '接口', '带颈法兰', '平焊法兰'],
            '带颈对焊法兰': ['法兰', '对焊法兰'],
            '密封': ['密封件', '密封圈', '机械密封'],
            '机械密封': ['密封', '密封件'],
            '软管': ['管道', '管子', '管', '金属软管'],
            '金属软管': ['软管', '管道'],
            '阀门': ['阀', '开关'],
            '泵': ['水泵', '离心泵', '工业泵'],
            '离心泵': ['泵', '工业泵'],
            '往复泵': ['泵', '工业泵']
        }
        
        for word, similar_list in similar_words.items():
            if word in input_name:
                for similar in similar_list:
                    if similar in category_name:
                        # 疏水器和疏水阀应该高度匹配
                        if (word == '疏水器' and similar == '疏水阀') or (word == '疏水阀' and similar == '疏水器'):
                            return 0.95
                        return 0.7
                        
        return 0.0
    
    def _calculate_spec_similarity(self, features: Dict[str, Any], 
                                 samples: List[Dict[str, Any]]) -> float:
        """计算规格特征相似度"""
        if not samples:
            return 0.0
            
        max_score = 0.0
        
        for sample in samples:
            score = 0.0
            factors = 0
            
            # DN匹配
            if features['extracted_dn'] or features['dn_input']:
                input_dn = features['extracted_dn'] + [features['dn_input']]
                sample_dn = sample.get('dn', '')
                if any(dn and dn.lower() in sample_dn.lower() for dn in input_dn if dn):
                    score += 1.0
                factors += 1
                
            # PN/压力匹配  
            if features['extracted_pn'] or features['pn_input']:
                input_pn = features['extracted_pn'] + [features['pn_input']]
                sample_pn = sample.get('pn', '')
                if any(pn and pn.lower() in sample_pn.lower() for pn in input_pn if pn):
                    score += 1.0
                factors += 1
                
            # 材质匹配
            if features['extracted_material'] or features['material_input']:
                input_material = features['extracted_material'] + [features['material_input']]
                sample_material = sample.get('material', '')
                if any(mat and mat.lower() in sample_material.lower() 
                      for mat in input_material if mat):
                    score += 1.0
                factors += 1
                
            if factors > 0:
                sample_score = score / factors
                max_score = max(max_score, sample_score)
        
        return max_score
    
    def _calculate_unit_similarity(self, input_unit: str, 
                                 samples: List[Dict[str, Any]]) -> float:
        """计算单位相似度"""
        if not input_unit or not samples:
            return 0.5  # 默认分数
            
        # 从样例中推断常见单位
        common_units = {
            '金属软管': ['根', '米'],
            '疏水器': ['个', '台'],
            '法兰': ['件', '个'],
            '三通': ['个', '件']
        }
        
        for sample in samples:
            sample_name = sample.get('name', '')
            for key, units in common_units.items():
                if key in sample_name and input_unit in units:
                    return 1.0
                    
        return 0.3
    
    def _calculate_keyword_similarity(self, features: Dict[str, Any], 
                                    category: Dict[str, Any]) -> float:
        """计算关键词相似度"""
        input_text = f"{features['name']} {features['spec']}"
        category_text = f"{category['name']} {category.get('description', '')}"
        
        # 提取关键词
        input_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', input_text.lower()))
        category_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', category_text.lower()))
        
        if input_keywords and category_keywords:
            intersection = input_keywords.intersection(category_keywords)
            union = input_keywords.union(category_keywords)
            return len(intersection) / len(union)
            
        return 0.0
    
    def _build_attributes(self, category: Dict[str, Any], 
                         features: Dict[str, Any]) -> List[Dict[str, str]]:
        """构建属性展示"""
        attributes = [
            {'label': '分类名称', 'value': category['name']},
            {'label': '分类级别', 'value': f"第{category.get('level', 1)}级"}
        ]
        
        # 添加提取的特征属性
        if features['extracted_dn']:
            attributes.append({
                'label': '公称直径', 
                'value': ', '.join(features['extracted_dn'])
            })
            
        if features['extracted_pn']:
            attributes.append({
                'label': '压力等级', 
                'value': ', '.join(features['extracted_pn'])
            })
            
        if features['extracted_material']:
            attributes.append({
                'label': '材质', 
                'value': ', '.join(features['extracted_material'])
            })
            
        if features['extracted_length']:
            attributes.append({
                'label': '长度', 
                'value': ', '.join(features['extracted_length']) + 'm'
            })
            
        return attributes
    
    def _get_matching_samples(self, features: Dict[str, Any], 
                            samples: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """获取匹配的示例"""
        matching_samples = []
        
        for sample in samples:
            score = self._calculate_spec_similarity(features, [sample])
            if score > 0.3:  # 相似度大于30%的样例
                matching_samples.append({
                    'name': sample.get('name', ''),
                    'spec': sample.get('spec', ''),
                    'score': round(score * 100, 1)
                })
        
        # 按相似度排序
        matching_samples.sort(key=lambda x: x['score'], reverse=True)
        return matching_samples