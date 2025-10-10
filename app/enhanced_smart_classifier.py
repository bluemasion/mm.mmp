# app/enhanced_smart_classifier.py - 增强智能分类器
import os
import sys
import logging
from typing import List, Dict, Any

# 添加app模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smart_classifier import SmartClassifier, MaterialFeature
from material_recognizer import MaterialRecognizer

class EnhancedSmartClassifier(SmartClassifier):
    """增强智能分类器
    
    在SmartClassifier基础上增加：
    1. 材质识别和权重加成
    2. 复合语义分解处理
    3. 动态置信度调整
    4. 材质匹配度评估
    """
    
    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.material_recognizer = MaterialRecognizer()
        self.logger.info("EnhancedSmartClassifier initialized with MaterialRecognizer")
        
    def classify_material(self, material: MaterialFeature) -> List[Dict[str, Any]]:
        """
        增强材料分类方法
        
        Args:
            material: 物料特征数据
            
        Returns:
            增强后的分类结果列表
        """
        try:
            self.logger.info(f"开始增强分类: {material.name}")
            
            # 1. 材质信息提取和分析
            material_analysis = self.material_recognizer.extract_material_info(material.name)
            
            # 2. 使用净化后的名称进行基础分类
            enhanced_material = MaterialFeature(
                name=material_analysis['enhanced_name'] or material.name,
                spec=material.spec,
                unit=material.unit,
                dn=material.dn,
                pn=material.pn,
                material=material.material
            )
            
            self.logger.info(f"材质分析: 原名称='{material.name}' -> 基础概念='{enhanced_material.name}', 检测材质={[m['base_keyword'] for m in material_analysis['materials']]}")
            
            # 3. 调用父类的分类方法
            base_results = super().classify_material(enhanced_material)
            
            # 4. 应用材质增强和置信度调整
            enhanced_results = []
            for result in base_results:
                enhanced_result = self._apply_material_enhancement(
                    result, 
                    material_analysis, 
                    material.name
                )
                enhanced_results.append(enhanced_result)
                
            # 5. 重新排序结果
            enhanced_results = self._resort_enhanced_results(enhanced_results)
            
            # 6. 记录增强效果
            if enhanced_results and base_results:
                original_confidence = base_results[0]['confidence']
                enhanced_confidence = enhanced_results[0]['confidence'] 
                improvement = enhanced_confidence - original_confidence
                
                self.logger.info(f"分类增强效果: {result['category']} 置信度 {original_confidence}% -> {enhanced_confidence}% (提升 {improvement:+.1f}%)")
            
            return enhanced_results
            
        except Exception as e:
            self.logger.error(f"增强分类错误: {str(e)}")
            # 降级到基础分类
            return super().classify_material(material)
            
    def _apply_material_enhancement(self, base_result: Dict[str, Any], 
                                  material_analysis: Dict[str, Any],
                                  original_name: str) -> Dict[str, Any]:
        """应用材质增强到分类结果"""
        
        enhanced_result = base_result.copy()
        
        # 1. 材质权重加成
        material_bonus = self.material_recognizer.get_material_enhancement_bonus(
            material_analysis['materials'],
            base_result['category']
        )
        
        # 2. 原始置信度
        original_confidence = base_result['confidence']
        
        # 3. 计算增强置信度
        enhanced_confidence = original_confidence + (material_bonus * 100)
        
        # 4. 应用材质特定的规则增强
        if material_analysis['materials']:
            # 材质匹配精度加成
            material_categories = material_analysis['material_categories']
            target_category = base_result['category'].lower()
            
            # 不锈钢材质特定增强
            if '不锈钢' in material_categories:
                if any(keyword in target_category for keyword in ['疏水', '法兰', '阀门', '管道']):
                    enhanced_confidence += 8  # 不锈钢+管道设备高匹配度
                elif '紧固件' in target_category:
                    enhanced_confidence += 3  # 不锈钢紧固件中等匹配度
                    
            # 碳钢材质特定增强
            elif '碳钢' in material_categories:
                if '紧固件' in target_category:
                    enhanced_confidence += 10  # 碳钢+紧固件高匹配度
                elif any(keyword in target_category for keyword in ['法兰', '管道']):
                    enhanced_confidence += 5  # 碳钢+管道设备中等匹配度
                    
            # 表面处理特定增强
            elif '表面处理' in material_categories:
                if any(keyword in target_category for keyword in ['接头', '管道', '紧固件']):
                    enhanced_confidence += 6  # 表面处理+标准件匹配度
                    
        # 5. 限制最大置信度
        enhanced_confidence = min(enhanced_confidence, 100.0)
        
        # 6. 更新结果
        enhanced_result['confidence'] = round(enhanced_confidence, 1)
        enhanced_result['material_info'] = material_analysis['materials']
        enhanced_result['original_confidence'] = original_confidence
        enhanced_result['material_bonus'] = round(material_bonus * 100, 1)
        enhanced_result['original_name'] = original_name
        
        # 7. 增强属性信息
        if material_analysis['materials']:
            enhanced_result['attributes'] = self._enhance_attributes(
                base_result.get('attributes', []),
                material_analysis
            )
            
        return enhanced_result
        
    def _enhance_attributes(self, base_attributes: List[Dict], 
                           material_analysis: Dict[str, Any]) -> List[Dict]:
        """增强属性信息，添加材质相关属性"""
        
        enhanced_attributes = base_attributes.copy()
        
        # 添加材质信息到属性
        for material in material_analysis['materials']:
            enhanced_attributes.append({
                'label': '材质类型',
                'value': f"{material['base_keyword']} ({material['category']})"
            })
            
            enhanced_attributes.append({
                'label': '材质等级',  
                'value': material['grade']
            })
            
        # 添加材质分类
        if material_analysis['material_categories']:
            enhanced_attributes.append({
                'label': '材质分类',
                'value': ', '.join(material_analysis['material_categories'])
            })
            
        return enhanced_attributes
        
    def _resort_enhanced_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重新排序增强后的结果"""
        
        def enhanced_sort_key(result):
            confidence = result['confidence']
            category_name = result['category']
            has_material = len(result.get('material_info', [])) > 0
            
            # 有材质信息的结果优先
            if has_material and confidence > 70:
                return confidence + 5  # 材质匹配加分
                
            # 精确分类优先
            specific_categories = ['疏水阀', '球阀', '法兰', '紧固件']
            if any(spec in category_name for spec in specific_categories):
                return confidence + 2
                
            return confidence
            
        results.sort(key=enhanced_sort_key, reverse=True)
        return results
        
    def compare_with_original(self, material: MaterialFeature) -> Dict[str, Any]:
        """对比原始算法和增强算法的效果"""
        
        # 原始算法结果
        original_results = super().classify_material(material)
        
        # 增强算法结果  
        enhanced_results = self.classify_material(material)
        
        comparison = {
            'material_name': material.name,
            'original_best': original_results[0] if original_results else None,
            'enhanced_best': enhanced_results[0] if enhanced_results else None,
            'improvement': 0.0,
            'material_detected': False
        }
        
        if original_results and enhanced_results:
            original_conf = original_results[0]['confidence']
            enhanced_conf = enhanced_results[0]['confidence']
            comparison['improvement'] = enhanced_conf - original_conf
            comparison['material_detected'] = len(enhanced_results[0].get('material_info', [])) > 0
            
        return comparison

# 兼容性适配器，确保向后兼容
class EnhancedClassifierAdapter:
    """增强分类器适配器，提供与现有API的兼容性"""
    
    def __init__(self, db_path: str):
        self.enhanced_classifier = EnhancedSmartClassifier(db_path)
        self.logger = logging.getLogger(__name__)
        
    def classify_material_dict(self, material_dict: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        接收字典格式的物料信息，返回分类结果
        
        适配现有API调用格式
        """
        material = MaterialFeature(
            name=material_dict.get('name', ''),
            spec=material_dict.get('spec', ''),
            unit=material_dict.get('unit', ''),
            dn=material_dict.get('dn', ''),
            pn=material_dict.get('pn', ''),
            material=material_dict.get('material', '')
        )
        
        return self.enhanced_classifier.classify_material(material)
        
    def batch_classify(self, materials: List[Dict[str, str]]) -> List[List[Dict[str, Any]]]:
        """批量分类"""
        results = []
        for material_dict in materials:
            result = self.classify_material_dict(material_dict)
            results.append(result)
        return results

# 测试和示例
if __name__ == "__main__":
    # 测试增强分类器
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 使用master_data.db
    db_path = '../master_data.db'
    if not os.path.exists(db_path):
        db_path = 'master_data.db'
        
    classifier = EnhancedSmartClassifier(db_path)
    
    test_materials = [
        MaterialFeature("304不锈钢疏水器", "DN25", "个"),
        MaterialFeature("316L不锈钢法兰", "DN100 PN16", "个"),
        MaterialFeature("碳钢螺塞", "M20*2.5", "个"),
        MaterialFeature("黄铜球阀", "DN50", "个"),
        MaterialFeature("镀锌管接头", "1/2寸", "个")
    ]
    
    print("=== 增强分类测试 ===\n")
    
    for material in test_materials:
        print(f"物料: {material.name} {material.spec}")
        
        # 对比测试
        comparison = classifier.compare_with_original(material)
        
        original = comparison['original_best']
        enhanced = comparison['enhanced_best']
        
        if original and enhanced:
            print(f"  原始算法: {original['category']} ({original['confidence']}%)")
            print(f"  增强算法: {enhanced['category']} ({enhanced['confidence']}%)")
            print(f"  改进幅度: {comparison['improvement']:+.1f}%")
            print(f"  材质检测: {'是' if comparison['material_detected'] else '否'}")
        
        print()