# app/material_matching_engine.py
"""
通用物料智能对码引擎
支持多数据源、灵活字段映射和自适应匹配算法
"""
import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# ===================== 数据源适配器基类 =====================
class DataSourceAdapter(ABC):
    """数据源适配器抽象基类"""
    
    @abstractmethod
    def load_data(self, source_config: Dict) -> pd.DataFrame:
        """加载数据"""
        pass
    
    @abstractmethod  
    def validate_data(self, df: pd.DataFrame) -> bool:
        """验证数据格式"""
        pass

class FileAdapter(DataSourceAdapter):
    """文件数据源适配器"""
    
    def load_data(self, source_config: Dict) -> pd.DataFrame:
        file_path = source_config['file_path']
        file_type = source_config.get('file_type', 'auto')
        
        try:
            if file_type == 'csv' or file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding=source_config.get('encoding', 'utf-8'))
            elif file_type == 'excel' or file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_type == 'json' or file_path.endswith('.json'):
                df = pd.read_json(file_path)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
                
            return df.fillna('')
        except Exception as e:
            logger.error(f"文件加载失败: {e}")
            raise

    def validate_data(self, df: pd.DataFrame) -> bool:
        return not df.empty and len(df.columns) > 0

class DatabaseAdapter(DataSourceAdapter):
    """数据库数据源适配器"""
    
    def load_data(self, source_config: Dict) -> pd.DataFrame:
        # TODO: 实现数据库连接和查询
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        return not df.empty

class APIAdapter(DataSourceAdapter):
    """API数据源适配器"""
    
    def load_data(self, source_config: Dict) -> pd.DataFrame:
        # TODO: 实现API调用和数据获取
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        return not df.empty

# ===================== 字段映射管理器 =====================
class FieldMappingManager:
    """字段映射管理器"""
    
    def __init__(self):
        self.standard_schema = {
            'material_id': '物料唯一标识',
            'material_name': '物料名称', 
            'specification': '规格型号',
            'manufacturer': '生产厂家',
            'standard_code': '标准编码',
            'category': '分类信息',
            'unit': '计量单位',
            'brand': '品牌信息'
        }
        
        # 预定义映射模板
        self.mapping_templates = self._load_mapping_templates()
    
    def _load_mapping_templates(self) -> Dict:
        """加载预定义的字段映射模板"""
        return {
            'medical_device': {
                'material_name': ['产品名称', '商品名称', '器械名称', '设备名称', '物料名称'],
                'specification': ['产品规格', '规格型号', '技术参数', '型号', '规格'],
                'manufacturer': ['生产厂家', '制造商', '厂家名称', '供应商', '生产商'],
                'material_id': ['商品操作码', '物料编码', '产品编码', '资产代码', '设备编码'],
                'standard_code': ['医保代码', '医保码', '注册证号', '标准编码']
            },
            'office_supplies': {
                'material_name': ['物品名称', '产品名称', '商品名称', '物料名称'],
                'specification': ['规格', '型号', '尺寸', '规格型号'],
                'manufacturer': ['品牌', '厂家', '制造商', '供应商'],
                'material_id': ['商品编码', '物料编码', '产品ID']
            }
        }
    
    def auto_detect_mapping(self, df_columns: List[str], template_name: str = 'auto') -> Dict[str, str]:
        """自动检测字段映射关系"""
        if template_name == 'auto':
            # 智能检测最佳模板
            template_name = self._detect_best_template(df_columns)
        
        template = self.mapping_templates.get(template_name, self.mapping_templates['medical_device'])
        mapping = {}
        
        for standard_field, possible_names in template.items():
            for col in df_columns:
                if any(name in col for name in possible_names):
                    mapping[standard_field] = col
                    break
        
        logger.info(f"自动检测字段映射: {mapping}")
        return mapping
    
    def _detect_best_template(self, columns: List[str]) -> str:
        """检测最佳映射模板"""
        scores = {}
        for template_name, template in self.mapping_templates.items():
            score = 0
            for standard_field, possible_names in template.items():
                for col in columns:
                    if any(name in col for name in possible_names):
                        score += 1
                        break
            scores[template_name] = score
        
        best_template = max(scores.items(), key=lambda x: x[1])[0]
        logger.info(f"检测到最佳模板: {best_template}, 匹配分数: {scores}")
        return best_template
    
    def apply_mapping(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """应用字段映射，转换为标准格式"""
        standardized_df = pd.DataFrame()
        
        for standard_field, source_field in mapping.items():
            if source_field in df.columns:
                standardized_df[standard_field] = df[source_field]
            else:
                logger.warning(f"源字段 '{source_field}' 不存在，跳过映射")
        
        # 添加缺失的必填字段
        required_fields = ['material_name', 'specification', 'manufacturer']
        for field in required_fields:
            if field not in standardized_df.columns:
                standardized_df[field] = ''
                logger.warning(f"缺少必填字段 '{field}', 已填充空值")
        
        return standardized_df

# ===================== 智能对码引擎 =====================  
class IntelligentMatchingEngine:
    """智能物料对码引擎"""
    
    def __init__(self):
        self.field_mapping_manager = FieldMappingManager()
        self.data_adapters = {
            'file': FileAdapter(),
            'database': DatabaseAdapter(), 
            'api': APIAdapter()
        }
        self.matching_strategies = self._init_matching_strategies()
    
    def _init_matching_strategies(self):
        """初始化匹配策略"""
        return {
            'exact_match': self._exact_match,
            'text_similarity': self._text_similarity_match,
            'spec_pattern': self._specification_pattern_match,
            'manufacturer_match': self._manufacturer_match
        }
    
    def load_and_standardize_data(self, source_config: Dict) -> pd.DataFrame:
        """加载并标准化数据"""
        # 1. 根据数据源类型选择适配器
        adapter = self.data_adapters[source_config['type']]
        
        # 2. 加载原始数据
        raw_df = adapter.load_data(source_config)
        
        # 3. 数据验证
        if not adapter.validate_data(raw_df):
            raise ValueError("数据验证失败")
        
        # 4. 字段映射
        mapping_config = source_config.get('field_mapping')
        if mapping_config:
            # 使用用户配置的映射
            field_mapping = mapping_config
        else:
            # 自动检测映射
            template = source_config.get('template', 'auto')
            field_mapping = self.field_mapping_manager.auto_detect_mapping(
                raw_df.columns.tolist(), template
            )
        
        # 5. 应用映射转换为标准格式
        standardized_df = self.field_mapping_manager.apply_mapping(raw_df, field_mapping)
        
        logger.info(f"数据标准化完成，原始数据: {len(raw_df)}行 -> 标准数据: {len(standardized_df)}行")
        return standardized_df
    
    def match_materials(self, source_df: pd.DataFrame, target_df: pd.DataFrame, 
                       match_config: Dict = None) -> List[Dict]:
        """执行物料智能对码"""
        if match_config is None:
            match_config = {
                'strategies': ['exact_match', 'text_similarity'],
                'thresholds': {'exact_match': 1.0, 'text_similarity': 0.7},
                'weights': {'material_name': 0.4, 'specification': 0.3, 'manufacturer': 0.3}
            }
        
        matches = []
        
        for idx, source_row in source_df.iterrows():
            best_match = self._find_best_match(source_row, target_df, match_config)
            if best_match:
                matches.append({
                    'source_index': idx,
                    'target_index': best_match['index'],
                    'confidence': best_match['confidence'],
                    'strategy': best_match['strategy'],
                    'details': best_match['details']
                })
        
        logger.info(f"对码完成，找到 {len(matches)} 个匹配对")
        return matches
    
    def _find_best_match(self, source_row: pd.Series, target_df: pd.DataFrame, 
                        match_config: Dict) -> Optional[Dict]:
        """为单条记录找到最佳匹配"""
        best_match = None
        best_confidence = 0
        
        for strategy_name in match_config['strategies']:
            strategy_func = self.matching_strategies[strategy_name]
            threshold = match_config['thresholds'][strategy_name]
            
            for idx, target_row in target_df.iterrows():
                confidence = strategy_func(source_row, target_row, match_config)
                
                if confidence >= threshold and confidence > best_confidence:
                    best_match = {
                        'index': idx,
                        'confidence': confidence,
                        'strategy': strategy_name,
                        'details': {
                            'source': source_row.to_dict(),
                            'target': target_row.to_dict()
                        }
                    }
                    best_confidence = confidence
        
        return best_match
    
    def _exact_match(self, source: pd.Series, target: pd.Series, config: Dict) -> float:
        """精确匹配策略"""
        # 标准编码精确匹配
        if 'standard_code' in source and 'standard_code' in target:
            if source['standard_code'] and target['standard_code']:
                if source['standard_code'] == target['standard_code']:
                    return 1.0
        return 0.0
    
    def _text_similarity_match(self, source: pd.Series, target: pd.Series, config: Dict) -> float:
        """文本相似度匹配策略"""
        # 这里可以集成现有的TF-IDF算法
        # TODO: 实现基于TF-IDF/BERT的文本相似度计算
        return 0.0
    
    def _specification_pattern_match(self, source: pd.Series, target: pd.Series, config: Dict) -> float:
        """规格模式匹配策略"""
        # TODO: 实现规格模式识别和匹配
        return 0.0
    
    def _manufacturer_match(self, source: pd.Series, target: pd.Series, config: Dict) -> float:
        """制造商匹配策略"""
        # TODO: 实现制造商名称标准化和匹配
        return 0.0

# ===================== 使用示例 =====================
def example_usage():
    """使用示例"""
    engine = IntelligentMatchingEngine()
    
    # 配置数据源1 (主数据库)
    source1_config = {
        'type': 'file',
        'file_path': 'e4p9.xlsx',
        'template': 'medical_device'
    }
    
    # 配置数据源2 (待匹配数据)
    source2_config = {
        'type': 'file', 
        'file_path': 'e4.xlsx',
        'field_mapping': {  # 自定义字段映射
            'material_name': '资产名称',
            'specification': '规格型号', 
            'manufacturer': '生产厂家名称',
            'material_id': '资产代码',
            'standard_code': '医保码'
        }
    }
    
    # 加载并标准化数据
    df1 = engine.load_and_standardize_data(source1_config)
    df2 = engine.load_and_standardize_data(source2_config)
    
    # 执行智能对码
    matches = engine.match_materials(df2, df1)
    
    return matches

if __name__ == "__main__":
    matches = example_usage()
    print(f"找到 {len(matches)} 个匹配对")