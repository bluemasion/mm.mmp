# -*- coding: utf-8 -*-
"""
动态模板生成器
根据识别的数据源模式自动生成适配的分类模板
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import sqlite3
from pathlib import Path
import pandas as pd
from collections import defaultdict, Counter

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CategoryTemplate:
    """分类模板定义"""
    template_id: str
    industry_type: str                    # 行业类型
    template_name: str                    # 模板名称
    category_structure: Dict[str, Any]    # 分类结构
    field_mappings: Dict[str, str]        # 字段映射
    matching_rules: List[Dict[str, Any]]  # 匹配规则
    quality_weights: Dict[str, float]     # 质量权重
    confidence_threshold: float           # 置信度阈值
    created_time: str                     # 创建时间
    last_updated: str                     # 最后更新时间

@dataclass
class TemplateRule:
    """模板规则定义"""
    rule_id: str
    rule_type: str          # 规则类型: keyword, pattern, similarity, composite
    priority: int           # 优先级 (1-10, 10最高)
    conditions: Dict[str, Any]  # 匹配条件
    actions: Dict[str, Any]     # 执行动作
    weight: float           # 权重
    enabled: bool           # 是否启用

class DynamicTemplateGenerator:
    """动态模板生成器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "template_generator.db"
        self.templates_cache = {}
        self.rules_cache = {}
        self._init_database()
        
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建模板表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_templates (
                template_id TEXT PRIMARY KEY,
                industry_type TEXT NOT NULL,
                template_name TEXT NOT NULL,
                category_structure TEXT NOT NULL,
                field_mappings TEXT NOT NULL,
                matching_rules TEXT NOT NULL,
                quality_weights TEXT NOT NULL,
                confidence_threshold REAL NOT NULL,
                created_time TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        
        # 创建规则表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_rules (
                rule_id TEXT PRIMARY KEY,
                template_id TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                conditions TEXT NOT NULL,
                actions TEXT NOT NULL,
                weight REAL NOT NULL,
                enabled INTEGER NOT NULL,
                FOREIGN KEY (template_id) REFERENCES category_templates (template_id)
            )
        """)
        
        # 创建应用历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_application_history (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT NOT NULL,
                source_data_sample TEXT NOT NULL,
                matching_results TEXT NOT NULL,
                accuracy_score REAL,
                application_time TEXT NOT NULL,
                FOREIGN KEY (template_id) REFERENCES category_templates (template_id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def generate_template_from_schema(self, 
                                   data_source_schema,
                                   existing_categories: List[Dict] = None,
                                   sample_data: List[Dict] = None) -> CategoryTemplate:
        """
        根据数据源模式生成分类模板
        
        Args:
            data_source_schema: 数据源模式定义
            existing_categories: 现有分类数据
            sample_data: 样本数据用于规则优化
            
        Returns:
            CategoryTemplate: 生成的分类模板
        """
        logger.info(f"开始为{data_source_schema.industry_type}生成分类模板")
        
        # 1. 分析现有分类结构
        category_structure = self._analyze_category_structure(
            data_source_schema.industry_type, existing_categories
        )
        
        # 2. 生成字段映射
        field_mappings = self._generate_field_mappings(data_source_schema)
        
        # 3. 创建匹配规则
        matching_rules = self._create_matching_rules(
            data_source_schema, category_structure, sample_data
        )
        
        # 4. 设置质量权重
        quality_weights = self._calculate_quality_weights(data_source_schema)
        
        # 5. 确定置信度阈值
        confidence_threshold = self._determine_confidence_threshold(
            data_source_schema.confidence_score, data_source_schema.industry_type
        )
        
        # 6. 创建模板
        template = CategoryTemplate(
            template_id=f"{data_source_schema.industry_type}_{data_source_schema.source_id}",
            industry_type=data_source_schema.industry_type,
            template_name=f"{data_source_schema.industry_type}分类模板",
            category_structure=category_structure,
            field_mappings=field_mappings,
            matching_rules=matching_rules,
            quality_weights=quality_weights,
            confidence_threshold=confidence_threshold,
            created_time=pd.Timestamp.now().isoformat(),
            last_updated=pd.Timestamp.now().isoformat()
        )
        
        # 7. 保存到数据库
        self._save_template_to_db(template)
        
        logger.info(f"模板生成完成: {template.template_id}")
        return template
    
    def _analyze_category_structure(self, 
                                  industry_type: str, 
                                  existing_categories: List[Dict]) -> Dict[str, Any]:
        """分析分类结构"""
        
        if industry_type == 'manufacturing':
            return self._create_manufacturing_category_structure(existing_categories)
        elif industry_type == 'medical':
            return self._create_medical_category_structure(existing_categories)
        else:
            return self._create_generic_category_structure(existing_categories)
    
    def _create_manufacturing_category_structure(self, 
                                               existing_categories: List[Dict]) -> Dict[str, Any]:
        """创建制造业分类结构"""
        structure = {
            "hierarchy_levels": 3,
            "level_names": ["一级分类", "二级分类", "三级分类"],
            "categories": {
                "管道阀门": {
                    "description": "各类阀门产品",
                    "subcategories": {
                        "控制阀门": ["球阀", "蝶阀", "闸阀", "截止阀", "调节阀"],
                        "安全阀门": ["安全阀", "泄压阀", "呼吸阀"],
                        "止回阀门": ["升降式止回阀", "旋启式止回阀", "蝶式止回阀"],
                        "特殊阀门": ["疏水阀", "减压阀", "过滤器"]
                    }
                },
                "管道连接件": {
                    "description": "管道系统连接配件",
                    "subcategories": {
                        "管道配件": ["弯头", "三通", "四通", "异径管", "管帽"],
                        "法兰系列": ["平焊法兰", "对焊法兰", "螺纹法兰", "盲板法兰"],
                        "管道支架": ["固定支架", "滑动支架", "弹簧支架"]
                    }
                },
                "流体输送设备": {
                    "description": "流体输送相关设备",
                    "subcategories": {
                        "泵类设备": ["离心泵", "齿轮泵", "螺杆泵", "往复泵", "计量泵"],
                        "风机设备": ["离心风机", "轴流风机", "混流风机"],
                        "压缩设备": ["空气压缩机", "制冷压缩机", "工艺压缩机"]
                    }
                },
                "通用机械配件": {
                    "description": "通用机械零部件",
                    "subcategories": {
                        "密封元件": ["机械密封", "填料密封", "垫片", "O型圈"],
                        "传动元件": ["轴承", "联轴器", "齿轮", "皮带"],
                        "连接件": ["螺栓", "螺母", "垫圈", "销钉", "铆钉"]
                    }
                }
            },
            "classification_attributes": [
                "功能用途", "结构形式", "材质等级", "连接方式", 
                "压力等级", "温度等级", "尺寸规格", "执行标准"
            ]
        }
        
        # 如果有现有分类，进行整合
        if existing_categories:
            structure = self._integrate_existing_categories(structure, existing_categories)
        
        return structure
    
    def _create_medical_category_structure(self, 
                                         existing_categories: List[Dict]) -> Dict[str, Any]:
        """创建医疗行业分类结构"""
        structure = {
            "hierarchy_levels": 3,
            "level_names": ["产品大类", "产品子类", "产品细类"],
            "categories": {
                "医疗器械": {
                    "description": "各类医疗器械产品",
                    "subcategories": {
                        "基础医疗器械": ["手术器械", "注射器械", "穿刺器械", "缝合材料"],
                        "诊断设备": ["影像设备", "检验设备", "监护设备", "测量设备"],
                        "治疗设备": ["手术设备", "康复设备", "急救设备", "理疗设备"],
                        "植入器械": ["心血管植入物", "骨科植入物", "神经植入物"],
                        "一次性医疗用品": ["输液器具", "注射用品", "医用敷料", "防护用品"]
                    }
                },
                "药品": {
                    "description": "各类药物制剂",
                    "subcategories": {
                        "处方药": ["化学药品", "生物制品", "中药制剂"],
                        "非处方药": ["感冒药", "止痛药", "维生素", "保健品"],
                        "外用药物": ["皮肤用药", "眼科用药", "耳鼻喉科用药"],
                        "特殊药品": ["麻醉药品", "精神药品", "毒性药品", "放射性药品"]
                    }
                }
            },
            "classification_attributes": [
                "风险等级", "管理类别", "注册分类", "适应症", 
                "给药途径", "剂型规格", "生产工艺", "质量标准"
            ]
        }
        
        # 如果有现有分类，进行整合
        if existing_categories:
            structure = self._integrate_existing_categories(structure, existing_categories)
        
        return structure
    
    def _create_generic_category_structure(self, 
                                         existing_categories: List[Dict]) -> Dict[str, Any]:
        """创建通用分类结构"""
        structure = {
            "hierarchy_levels": 2,
            "level_names": ["主分类", "子分类"],
            "categories": {
                "通用产品": {
                    "description": "通用产品分类",
                    "subcategories": {
                        "标准产品": ["产品A", "产品B", "产品C"],
                        "定制产品": ["定制A", "定制B", "定制C"]
                    }
                }
            },
            "classification_attributes": [
                "产品类型", "规格型号", "制造商", "用途"
            ]
        }
        
        if existing_categories:
            structure = self._integrate_existing_categories(structure, existing_categories)
        
        return structure
    
    def _integrate_existing_categories(self, 
                                     base_structure: Dict[str, Any],
                                     existing_categories: List[Dict]) -> Dict[str, Any]:
        """整合现有分类数据"""
        
        # 分析现有分类的层次结构
        category_levels = defaultdict(set)
        
        for category in existing_categories:
            if 'category_level1' in category:
                category_levels[1].add(category['category_level1'])
            if 'category_level2' in category:
                category_levels[2].add(category['category_level2'])
            if 'category_level3' in category:
                category_levels[3].add(category['category_level3'])
        
        # 更新分类结构
        if category_levels[1]:
            # 更新主分类
            for level1_cat in category_levels[1]:
                if level1_cat not in base_structure['categories']:
                    base_structure['categories'][level1_cat] = {
                        "description": f"{level1_cat}相关产品",
                        "subcategories": {}
                    }
        
        return base_structure
    
    def _generate_field_mappings(self, data_source_schema) -> Dict[str, str]:
        """生成字段映射"""
        
        # 基础映射
        mappings = data_source_schema.field_mappings.copy()
        
        # 根据行业类型补充映射
        if data_source_schema.industry_type == 'manufacturing':
            manufacturing_mappings = {
                'pressure_rating': '压力等级',
                'temperature_rating': '温度等级',
                'material_standard': '材质标准',
                'connection_type': '连接方式',
                'size_parameters': '尺寸参数'
            }
            mappings.update(manufacturing_mappings)
            
        elif data_source_schema.industry_type == 'medical':
            medical_mappings = {
                'device_classification': '器械分类',
                'registration_number': '注册证号',
                'dosage_form': '剂型',
                'concentration': '浓度含量',
                'indication': '适应症',
                'storage_condition': '储存条件'
            }
            mappings.update(medical_mappings)
        
        return mappings
    
    def _create_matching_rules(self, 
                             data_source_schema,
                             category_structure: Dict[str, Any],
                             sample_data: List[Dict] = None) -> List[Dict[str, Any]]:
        """创建匹配规则"""
        
        rules = []
        
        # 1. 关键词匹配规则
        keyword_rules = self._create_keyword_rules(
            data_source_schema.industry_type, category_structure
        )
        rules.extend(keyword_rules)
        
        # 2. 模式匹配规则
        pattern_rules = self._create_pattern_rules(data_source_schema)
        rules.extend(pattern_rules)
        
        # 3. 相似度匹配规则
        similarity_rules = self._create_similarity_rules(data_source_schema)
        rules.extend(similarity_rules)
        
        # 4. 复合匹配规则
        if sample_data:
            composite_rules = self._create_composite_rules(sample_data, category_structure)
            rules.extend(composite_rules)
        
        return rules
    
    def _create_keyword_rules(self, 
                            industry_type: str, 
                            category_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建关键词匹配规则"""
        
        rules = []
        
        for main_category, info in category_structure['categories'].items():
            for sub_category, items in info.get('subcategories', {}).items():
                
                # 为每个细分类别创建关键词规则
                rule = {
                    "rule_type": "keyword",
                    "priority": 8,
                    "conditions": {
                        "keywords": items,
                        "field_targets": ["material_name", "specification", "category"],
                        "match_threshold": 0.7
                    },
                    "actions": {
                        "assign_category": {
                            "level1": main_category,
                            "level2": sub_category,
                            "confidence_boost": 0.2
                        }
                    },
                    "weight": 0.4,
                    "enabled": True
                }
                rules.append(rule)
        
        return rules
    
    def _create_pattern_rules(self, data_source_schema) -> List[Dict[str, Any]]:
        """创建模式匹配规则"""
        
        rules = []
        
        if data_source_schema.industry_type == 'manufacturing':
            # 制造业特有模式
            manufacturing_patterns = [
                {
                    "rule_type": "pattern",
                    "priority": 7,
                    "conditions": {
                        "patterns": [r'DN\s*\d+', r'PN\s*\d+'],
                        "field_targets": ["specification"],
                        "pattern_type": "size_specification"
                    },
                    "actions": {
                        "extract_parameters": {
                            "diameter": r'DN\s*(\d+)',
                            "pressure": r'PN\s*(\d+)'
                        },
                        "confidence_boost": 0.15
                    },
                    "weight": 0.3,
                    "enabled": True
                }
            ]
            rules.extend(manufacturing_patterns)
            
        elif data_source_schema.industry_type == 'medical':
            # 医疗行业特有模式
            medical_patterns = [
                {
                    "rule_type": "pattern",
                    "priority": 7,
                    "conditions": {
                        "patterns": [r'\d+mg/ml', r'\d+%', r'规格.*\d+ml'],
                        "field_targets": ["specification", "concentration"],
                        "pattern_type": "medical_specification"
                    },
                    "actions": {
                        "extract_parameters": {
                            "concentration": r'(\d+(?:\.\d+)?)\s*(mg/ml|%)',
                            "volume": r'(\d+(?:\.\d+)?)\s*ml'
                        },
                        "confidence_boost": 0.15
                    },
                    "weight": 0.3,
                    "enabled": True
                }
            ]
            rules.extend(medical_patterns)
        
        return rules
    
    def _create_similarity_rules(self, data_source_schema) -> List[Dict[str, Any]]:
        """创建相似度匹配规则"""
        
        rules = [
            {
                "rule_type": "similarity",
                "priority": 6,
                "conditions": {
                    "similarity_method": "tfidf_cosine",
                    "field_targets": ["material_name", "specification"],
                    "min_similarity": 0.6
                },
                "actions": {
                    "similarity_matching": {
                        "algorithm": "advanced_matcher",
                        "threshold_adjustment": data_source_schema.confidence_score
                    }
                },
                "weight": 0.25,
                "enabled": True
            },
            {
                "rule_type": "similarity",
                "priority": 5,
                "conditions": {
                    "similarity_method": "fuzzy_string",
                    "field_targets": ["manufacturer"],
                    "min_similarity": 0.8
                },
                "actions": {
                    "manufacturer_matching": {
                        "normalize_names": True,
                        "confidence_boost": 0.1
                    }
                },
                "weight": 0.15,
                "enabled": True
            }
        ]
        
        return rules
    
    def _create_composite_rules(self, 
                              sample_data: List[Dict],
                              category_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建复合匹配规则"""
        
        # 基于样本数据分析创建复合规则
        rules = []
        
        # 分析样本数据中的模式
        field_combinations = self._analyze_field_combinations(sample_data)
        
        for combination, frequency in field_combinations.items():
            if frequency > 0.3:  # 如果组合出现频率超过30%
                rule = {
                    "rule_type": "composite",
                    "priority": 9,
                    "conditions": {
                        "field_combination": list(combination),
                        "combination_weight": frequency,
                        "validation_method": "multi_field_consensus"
                    },
                    "actions": {
                        "composite_matching": {
                            "weight_distribution": self._calculate_field_weights(combination),
                            "confidence_multiplier": 1.2
                        }
                    },
                    "weight": 0.35,
                    "enabled": True
                }
                rules.append(rule)
        
        return rules
    
    def _analyze_field_combinations(self, sample_data: List[Dict]) -> Dict[Tuple, float]:
        """分析字段组合模式"""
        
        combinations = defaultdict(int)
        total_samples = len(sample_data)
        
        for record in sample_data:
            available_fields = [field for field, value in record.items() if value]
            
            # 分析2-3字段组合
            for i in range(len(available_fields)):
                for j in range(i+1, len(available_fields)):
                    combo = tuple(sorted([available_fields[i], available_fields[j]]))
                    combinations[combo] += 1
                    
                    # 三字段组合
                    for k in range(j+1, len(available_fields)):
                        combo3 = tuple(sorted([available_fields[i], available_fields[j], available_fields[k]]))
                        combinations[combo3] += 1
        
        # 计算频率
        combination_frequencies = {
            combo: count / total_samples 
            for combo, count in combinations.items()
        }
        
        return combination_frequencies
    
    def _calculate_field_weights(self, field_combination: Tuple) -> Dict[str, float]:
        """计算字段权重"""
        
        # 基础权重定义
        base_weights = {
            'material_name': 0.4,
            'specification': 0.3,
            'manufacturer': 0.15,
            'category': 0.35,
            'model': 0.2,
            'standard': 0.1
        }
        
        # 根据字段组合调整权重
        weights = {}
        total_weight = sum(base_weights.get(field, 0.1) for field in field_combination)
        
        for field in field_combination:
            weights[field] = base_weights.get(field, 0.1) / total_weight
        
        return weights
    
    def _calculate_quality_weights(self, data_source_schema) -> Dict[str, float]:
        """计算质量权重"""
        
        # 基础权重
        base_weights = {
            'name_matching': 0.35,
            'specification_matching': 0.25,
            'category_matching': 0.20,
            'manufacturer_matching': 0.10,
            'technical_params': 0.10
        }
        
        # 根据数据源质量调整权重
        quality_score = data_source_schema.quality_metrics.get('overall_quality', 0.7)
        
        if quality_score > 0.8:
            # 高质量数据源，提高精确匹配权重
            base_weights['name_matching'] += 0.1
            base_weights['specification_matching'] += 0.05
        elif quality_score < 0.5:
            # 低质量数据源，增加模糊匹配容错性
            base_weights['category_matching'] += 0.1
            base_weights['manufacturer_matching'] += 0.05
        
        return base_weights
    
    def _determine_confidence_threshold(self, 
                                      data_confidence: float, 
                                      industry_type: str) -> float:
        """确定置信度阈值"""
        
        # 基础阈值
        base_thresholds = {
            'manufacturing': 0.75,
            'medical': 0.80,  # 医疗行业要求更高精度
            'generic': 0.70
        }
        
        base_threshold = base_thresholds.get(industry_type, 0.70)
        
        # 根据数据源识别置信度调整
        if data_confidence > 0.8:
            return base_threshold - 0.05  # 高置信度数据源，可以降低匹配阈值
        elif data_confidence < 0.6:
            return base_threshold + 0.10  # 低置信度数据源，提高匹配阈值
        
        return base_threshold
    
    def _save_template_to_db(self, template: CategoryTemplate):
        """保存模板到数据库"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 保存主模板
            cursor.execute("""
                INSERT OR REPLACE INTO category_templates 
                (template_id, industry_type, template_name, category_structure, 
                 field_mappings, matching_rules, quality_weights, confidence_threshold,
                 created_time, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template.template_id,
                template.industry_type,
                template.template_name,
                json.dumps(template.category_structure, ensure_ascii=False),
                json.dumps(template.field_mappings, ensure_ascii=False),
                json.dumps(template.matching_rules, ensure_ascii=False),
                json.dumps(template.quality_weights, ensure_ascii=False),
                template.confidence_threshold,
                template.created_time,
                template.last_updated
            ))
            
            # 保存规则详情
            for i, rule in enumerate(template.matching_rules):
                rule_id = f"{template.template_id}_rule_{i}"
                cursor.execute("""
                    INSERT OR REPLACE INTO template_rules
                    (rule_id, template_id, rule_type, priority, conditions, actions, weight, enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule_id,
                    template.template_id,
                    rule['rule_type'],
                    rule['priority'],
                    json.dumps(rule['conditions'], ensure_ascii=False),
                    json.dumps(rule['actions'], ensure_ascii=False),
                    rule['weight'],
                    1 if rule['enabled'] else 0
                ))
            
            conn.commit()
            logger.info(f"模板保存成功: {template.template_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"保存模板失败: {e}")
            raise
        finally:
            conn.close()
    
    def load_template(self, template_id: str) -> Optional[CategoryTemplate]:
        """从数据库加载模板"""
        
        if template_id in self.templates_cache:
            return self.templates_cache[template_id]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM category_templates WHERE template_id = ?
            """, (template_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # 加载规则
            cursor.execute("""
                SELECT * FROM template_rules WHERE template_id = ?
            """, (template_id,))
            
            rules_rows = cursor.fetchall()
            matching_rules = []
            
            for rule_row in rules_rows:
                rule = {
                    'rule_type': rule_row[2],
                    'priority': rule_row[3],
                    'conditions': json.loads(rule_row[4]),
                    'actions': json.loads(rule_row[5]),
                    'weight': rule_row[6],
                    'enabled': bool(rule_row[7])
                }
                matching_rules.append(rule)
            
            # 创建模板对象
            template = CategoryTemplate(
                template_id=row[0],
                industry_type=row[1],
                template_name=row[2],
                category_structure=json.loads(row[3]),
                field_mappings=json.loads(row[4]),
                matching_rules=matching_rules,
                quality_weights=json.loads(row[6]),
                confidence_threshold=row[7],
                created_time=row[8],
                last_updated=row[9]
            )
            
            # 缓存模板
            self.templates_cache[template_id] = template
            
            return template
            
        except Exception as e:
            logger.error(f"加载模板失败: {e}")
            return None
        finally:
            conn.close()
    
    def list_templates_by_industry(self, industry_type: str) -> List[CategoryTemplate]:
        """按行业类型列出模板"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        templates = []
        
        try:
            cursor.execute("""
                SELECT template_id FROM category_templates 
                WHERE industry_type = ? 
                ORDER BY last_updated DESC
            """, (industry_type,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                template = self.load_template(row[0])
                if template:
                    templates.append(template)
            
        except Exception as e:
            logger.error(f"列出模板失败: {e}")
        finally:
            conn.close()
        
        return templates
    
    def update_template_performance(self, 
                                  template_id: str, 
                                  application_results: Dict[str, Any]):
        """更新模板性能数据"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 记录应用历史
            cursor.execute("""
                INSERT INTO template_application_history
                (template_id, source_data_sample, matching_results, accuracy_score, application_time)
                VALUES (?, ?, ?, ?, ?)
            """, (
                template_id,
                json.dumps(application_results.get('sample_data', {}), ensure_ascii=False),
                json.dumps(application_results.get('results', {}), ensure_ascii=False),
                application_results.get('accuracy_score', 0.0),
                pd.Timestamp.now().isoformat()
            ))
            
            # 更新模板最后更新时间
            cursor.execute("""
                UPDATE category_templates 
                SET last_updated = ? 
                WHERE template_id = ?
            """, (pd.Timestamp.now().isoformat(), template_id))
            
            conn.commit()
            
            # 清除缓存以强制重新加载
            if template_id in self.templates_cache:
                del self.templates_cache[template_id]
            
            logger.info(f"模板性能数据更新完成: {template_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"更新模板性能失败: {e}")
        finally:
            conn.close()
    
    def optimize_template(self, 
                         template_id: str, 
                         performance_data: Dict[str, Any]) -> CategoryTemplate:
        """基于性能数据优化模板"""
        
        template = self.load_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        # 分析性能数据
        accuracy_score = performance_data.get('accuracy_score', 0.0)
        common_errors = performance_data.get('common_errors', [])
        
        # 优化规则权重
        if accuracy_score < 0.7:
            # 准确率低，调整规则权重
            for rule in template.matching_rules:
                if rule['rule_type'] == 'keyword':
                    rule['weight'] *= 1.1  # 增加关键词匹配权重
                elif rule['rule_type'] == 'similarity':
                    rule['weight'] *= 0.9  # 降低相似度匹配权重
        
        # 调整置信度阈值
        if len(common_errors) > 10:
            template.confidence_threshold += 0.05  # 提高阈值减少错误
        elif accuracy_score > 0.9:
            template.confidence_threshold -= 0.02  # 降低阈值提高召回率
        
        # 更新时间戳
        template.last_updated = pd.Timestamp.now().isoformat()
        
        # 保存优化后的模板
        self._save_template_to_db(template)
        
        logger.info(f"模板优化完成: {template_id}")
        return template


# 测试代码
if __name__ == "__main__":
    # 测试动态模板生成器
    generator = DynamicTemplateGenerator("test_templates.db")
    
    # 模拟数据源模式
    from data_source_recognizer import DataSourceSchema
    
    # 制造业数据源模式
    manufacturing_schema = DataSourceSchema(
        source_id="manufacturing_001",
        industry_type="manufacturing",
        field_types={"物料名称": "text", "规格型号": "text", "制造商": "text"},
        naming_patterns={},
        value_distributions={},
        field_mappings={"material_name": "物料名称", "specification": "规格型号"},
        quality_metrics={"overall_quality": 0.85},
        confidence_score=0.9
    )
    
    print("=== 制造业模板生成测试 ===")
    manufacturing_template = generator.generate_template_from_schema(
        manufacturing_schema, 
        existing_categories=[
            {"category_level1": "管道阀门", "category_level2": "控制阀门", "category_level3": "球阀"}
        ]
    )
    
    print(f"模板ID: {manufacturing_template.template_id}")
    print(f"行业类型: {manufacturing_template.industry_type}")
    print(f"分类结构层级: {manufacturing_template.category_structure['hierarchy_levels']}")
    print(f"匹配规则数量: {len(manufacturing_template.matching_rules)}")
    print(f"置信度阈值: {manufacturing_template.confidence_threshold}")
    
    # 测试模板加载
    print("\n=== 模板加载测试 ===")
    loaded_template = generator.load_template(manufacturing_template.template_id)
    if loaded_template:
        print(f"加载成功: {loaded_template.template_name}")
    
    # 测试按行业列出模板
    print("\n=== 按行业列出模板 ===")
    manufacturing_templates = generator.list_templates_by_industry("manufacturing")
    print(f"制造业模板数量: {len(manufacturing_templates)}")
    
    # 清理测试数据库
    import os
    if os.path.exists("test_templates.db"):
        os.remove("test_templates.db")
        print("测试数据库已清理")