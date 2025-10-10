# app/material_recognizer.py - 材质识别增强器
import re
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

@dataclass
class MaterialInfo:
    """材质信息数据结构"""
    keyword: str
    weight: float
    category: str
    grade: str
    aliases: List[str]

class MaterialRecognizer:
    """材质识别和权重增强器
    
    功能：
    1. 从物料名称中识别材质关键词
    2. 提取净化后的核心概念
    3. 计算材质权重加成
    4. 支持多种材质表示方式
    """
    
    def __init__(self):
        self.setup_logging()
        self.material_keywords = self._build_material_database()
        
    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger(__name__)
        
    def _build_material_database(self) -> Dict[str, MaterialInfo]:
        """构建材质数据库"""
        materials = {}
        
        # 不锈钢系列 - 高权重，精确识别
        stainless_steels = [
            ('304', 0.9, '不锈钢', 'A', ['304SS', '304不锈钢', '0Cr18Ni9']),
            ('316', 0.95, '不锈钢', 'A+', ['316SS', '316不锈钢', '0Cr17Ni12Mo2']),
            ('316L', 0.95, '不锈钢', 'A+', ['316LSS', '316L不锈钢', '00Cr17Ni14Mo2']),
            ('321', 0.9, '不锈钢', 'A', ['321SS', '321不锈钢', '0Cr18Ni10Ti']),
            ('310S', 0.88, '不锈钢', 'A', ['310SSS', '310S不锈钢']),
            ('904L', 0.92, '不锈钢', 'A+', ['904LSS', '904L不锈钢']),
            ('不锈钢', 0.8, '不锈钢', 'B+', ['SS', 'stainless steel'])
        ]
        
        # 碳钢系列 - 中高权重
        carbon_steels = [
            ('20#', 0.85, '碳钢', 'A-', ['20号钢', '20钢', '20#钢']),
            ('Q235', 0.8, '碳钢', 'B+', ['Q235A', 'Q235B', 'Q235C']),
            ('A105', 0.85, '碳钢', 'A-', ['ASTM A105', 'A105锻件']),
            ('A182', 0.85, '碳钢', 'A-', ['ASTM A182', 'A182锻件']),
            ('碳钢', 0.75, '碳钢', 'B', ['CS', 'carbon steel', '普碳钢'])
        ]
        
        # 有色金属系列 - 中等权重
        non_ferrous_metals = [
            ('黄铜', 0.75, '铜合金', 'B', ['brass', '铜', '青铜']),
            ('紫铜', 0.75, '铜合金', 'B', ['copper', '纯铜', 'T2']),
            ('铝合金', 0.7, '铝合金', 'B-', ['aluminum', '铝', 'AL']),
            ('钛合金', 0.9, '钛合金', 'A', ['titanium', '钛', 'Ti'])
        ]
        
        # 表面处理 - 低权重但重要
        surface_treatments = [
            ('镀锌', 0.7, '表面处理', 'B', ['galvanized', '热镀锌', '电镀锌']),
            ('镀镍', 0.65, '表面处理', 'B-', ['nickel plated', '电镀镍']),
            ('阳极氧化', 0.65, '表面处理', 'B-', ['anodized', '氧化处理']),
            ('涂塑', 0.6, '表面处理', 'C+', ['plastic coated', '塑料涂层'])
        ]
        
        # 合并所有材质
        all_materials = stainless_steels + carbon_steels + non_ferrous_metals + surface_treatments
        
        for keyword, weight, category, grade, aliases in all_materials:
            materials[keyword] = MaterialInfo(
                keyword=keyword,
                weight=weight,
                category=category,
                grade=grade,
                aliases=aliases
            )
            
            # 添加别名映射
            for alias in aliases:
                materials[alias.lower()] = MaterialInfo(
                    keyword=keyword,  # 指向主关键词
                    weight=weight,
                    category=category,
                    grade=grade,
                    aliases=aliases
                )
                
        return materials
        
    def extract_material_info(self, material_name: str) -> Dict[str, Any]:
        """提取材质信息并计算权重加成
        
        Args:
            material_name: 原始物料名称，如"304不锈钢疏水器"
            
        Returns:
            包含材质分析结果的字典
        """
        if not material_name or not material_name.strip():
            return {
                'base_concept': material_name,
                'materials': [],
                'material_weight': 0.0,
                'enhanced_name': material_name,
                'material_categories': []
            }
            
        name_lower = material_name.lower().strip()
        detected_materials = []
        base_name = material_name
        
        # 按优先级排序检测材质（长关键词优先）
        sorted_keywords = sorted(self.material_keywords.keys(), key=len, reverse=True)
        
        for keyword in sorted_keywords:
            material_info = self.material_keywords[keyword]
            
            # 使用正则表达式精确匹配，避免误匹配
            patterns = [
                rf'\b{re.escape(keyword.lower())}\b',  # 单词边界匹配
                rf'{re.escape(keyword.lower())}(?=不锈钢|钢|合金|$)',  # 后缀匹配
                rf'(?<![a-z]){re.escape(keyword.lower())}(?![a-z])'  # 非字母包围
            ]
            
            for pattern in patterns:
                if re.search(pattern, name_lower):
                    # 避免重复检测相同材质
                    if not any(m['base_keyword'] == material_info.keyword for m in detected_materials):
                        detected_materials.append({
                            'detected_keyword': keyword,
                            'base_keyword': material_info.keyword,
                            'weight': material_info.weight,
                            'category': material_info.category,
                            'grade': material_info.grade,
                            'confidence': self._calculate_material_confidence(keyword, name_lower)
                        })
                        
                        # 从名称中移除材质词汇，保留核心概念
                        base_name = self._remove_material_keyword(base_name, keyword, material_info.aliases)
                    break
        
        # 计算总权重和类别
        total_weight = sum(m['weight'] for m in detected_materials)
        material_categories = list(set(m['category'] for m in detected_materials))
        
        # 净化基础概念
        enhanced_name = self._clean_base_concept(base_name)
        
        result = {
            'base_concept': enhanced_name,
            'materials': detected_materials,
            'material_weight': total_weight,
            'enhanced_name': enhanced_name,
            'material_categories': material_categories,
            'has_stainless_steel': '不锈钢' in material_categories,
            'has_carbon_steel': '碳钢' in material_categories,
            'has_surface_treatment': '表面处理' in material_categories
        }
        
        # 调试日志
        if detected_materials:
            self.logger.info(f"材质识别: '{material_name}' -> 基础概念: '{enhanced_name}', 材质: {[m['base_keyword'] for m in detected_materials]}, 权重: {total_weight:.2f}")
        else:
            self.logger.debug(f"未检测到材质: '{material_name}'")
            
        return result
        
    def _calculate_material_confidence(self, keyword: str, name_lower: str) -> float:
        """计算材质识别的置信度"""
        # 基础置信度
        base_confidence = 0.8
        
        # 完整关键词匹配加分
        if keyword in name_lower:
            base_confidence += 0.1
            
        # 上下文匹配加分
        context_keywords = ['不锈钢', '钢', '合金', '金属', '材质']
        for ctx in context_keywords:
            if ctx in name_lower:
                base_confidence += 0.05
                break
                
        return min(base_confidence, 1.0)
        
    def _remove_material_keyword(self, base_name: str, keyword: str, aliases: List[str]) -> str:
        """从名称中移除材质关键词"""
        cleaned_name = base_name
        
        # 移除主关键词和别名
        keywords_to_remove = [keyword] + aliases
        
        for kw in keywords_to_remove:
            # 使用多种模式移除
            patterns = [
                rf'\b{re.escape(kw)}\b',
                rf'{re.escape(kw)}(?=不锈钢|钢|合金)',
                rf'(?<![a-z]){re.escape(kw)}(?![a-z])'
            ]
            
            for pattern in patterns:
                cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE)
                
        return cleaned_name.strip()
        
    def _clean_base_concept(self, base_name: str) -> str:
        """净化基础概念，移除多余的修饰词"""
        if not base_name:
            return base_name
            
        # 移除常见的修饰词
        modifiers_to_remove = [
            r'\b(优质|精密|高强度|耐腐蚀|防锈|加厚|标准|非标|定制)\b',
            r'\b(国标|美标|欧标|日标|德标|英标)\b',
            r'\b(内六角|外六角|十字|一字|梅花)\b',
            r'\s+',  # 多余空格
        ]
        
        cleaned = base_name
        for pattern in modifiers_to_remove:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
            
        # 清理首尾空格和多余字符
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'^[^\u4e00-\u9fff\w]*|[^\u4e00-\u9fff\w]*$', '', cleaned)
        
        return cleaned if cleaned else base_name
        
    def get_material_enhancement_bonus(self, detected_materials: List[Dict], target_category: str) -> float:
        """计算材质匹配的置信度加成
        
        Args:
            detected_materials: 检测到的材质列表
            target_category: 目标分类名称
            
        Returns:
            置信度加成值 (0.0 - 0.3)
        """
        if not detected_materials:
            return 0.0
            
        bonus = 0.0
        
        # 材质等级加成
        for material in detected_materials:
            grade = material['grade']
            if grade == 'A+':
                bonus += 0.15  # 高等级材质(316L等)
            elif grade == 'A':
                bonus += 0.12  # 优质材质(304等)
            elif grade in ['A-', 'B+']:
                bonus += 0.08  # 良好材质
            else:
                bonus += 0.05  # 基础材质
                
        # 材质与分类匹配度加成
        material_categories = [m['category'] for m in detected_materials]
        
        # 不锈钢材质与相关分类的匹配加成
        if '不锈钢' in material_categories:
            stainless_categories = ['疏水阀', '法兰', '阀门', '管道配件', '接头']
            if any(cat in target_category for cat in stainless_categories):
                bonus += 0.1
                
        # 碳钢材质与相关分类的匹配加成  
        if '碳钢' in material_categories:
            carbon_categories = ['紧固件', '螺栓', '螺母', '垫片']
            if any(cat in target_category for cat in carbon_categories):
                bonus += 0.08
                
        return min(bonus, 0.3)  # 最大30%加成
        
    def get_supported_materials(self) -> Dict[str, List[str]]:
        """获取支持的材质列表，用于调试和文档"""
        categories = {}
        for keyword, info in self.material_keywords.items():
            if info.category not in categories:
                categories[info.category] = []
            if info.keyword not in categories[info.category]:
                categories[info.category].append(info.keyword)
                
        return categories

# 使用示例和测试
if __name__ == "__main__":
    # 测试材质识别器
    recognizer = MaterialRecognizer()
    
    test_materials = [
        "304不锈钢疏水器",
        "316L不锈钢法兰DN100", 
        "碳钢螺塞M20*2.5",
        "镀锌管接头",
        "黄铜球阀",
        "普通疏水器"  # 无材质信息
    ]
    
    print("=== 材质识别测试 ===")
    for material in test_materials:
        result = recognizer.extract_material_info(material)
        print(f"\n输入: {material}")
        print(f"基础概念: {result['base_concept']}")
        print(f"检测材质: {[m['base_keyword'] for m in result['materials']]}")
        print(f"材质权重: {result['material_weight']:.2f}")
        print(f"材质类别: {result['material_categories']}")
        
    print(f"\n=== 支持的材质类型 ===")
    supported = recognizer.get_supported_materials()
    for category, materials in supported.items():
        print(f"{category}: {', '.join(materials)}")