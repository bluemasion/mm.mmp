# app/intelligent_classifier.py
"""
智能分类推荐引擎
基于现有数据和机器学习算法实现智能物料分类推荐
"""
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sqlite3
from app.master_data_manager import master_data_manager
from app.business_data_manager import BusinessDataManager

logger = logging.getLogger(__name__)

class IntelligentClassifier:
    """智能分类推荐引擎 - 数据库增强版"""
    
    def __init__(self, business_manager: BusinessDataManager):
        self.business_manager = business_manager
        self.master_manager = master_data_manager
        
        # 初始化训练数据管理器
        from app.training_data_manager import TrainingDataManager
        self.training_manager = TrainingDataManager('training_data.db')
        
        # 从数据库加载训练结果增强分类器
        self.training_results = self._load_training_results_from_db()
        
        # 从数据库加载分类规则
        self.cached_rules = self.training_manager.get_classification_rules()
        
        # 加载TF-IDF模型
        self.tfidf_model = self._load_tfidf_model()
        
        # 预定义的关键词分类映射 - 基于实际548个制造业分类增强
        self.keyword_mappings = {
                    '化工三剂': ['溶剂', '助剂', '化工', '催化剂', '化学品', '化工三剂', '化学', '添加剂'],
                    '包装物': ['袋子', '包装', '包装物', '桶', '包装袋', '容器', '包装箱', '纸箱'],
                    '化验用品': ['试验', '实验', '检测', '化验', '测试', '分析', '仪器', '化验用品'],
                    '劳动防护用品': ['防护', '安全', '防护用品', '安全用品', '劳动防护用品', '劳保用品', '劳保'],
                    '消防设施、器材': ['报警', '灭火器', '消防器材', '消防', '火灾', '灭火', '消防设施、器材'],
                    '通用机械设备': ['通用', '泵', '机械设备', '机械', '机械备件', '工业设备', '管件', '阀门'],
                    '通用机械设备配件': ['通用机械设备配件', '通用', '泵', '机械设备', '机械', '机械备件', '工业设备', '管件'],
                    '催化剂': ['sio2', '溶剂', 'al2o3', '助剂', '化工', '载体', '催化剂', '催化'],
                    '化工助剂': ['溶剂', '改性剂', '稳定剂', '助剂', '化工', '催化剂', '化学品', '增塑剂'],
                    '无机化工产品': ['溶剂', '助剂', '化工', '无机化工产品', '催化剂', '化学品', '化学', '添加剂'],
                    '非金属包装物': ['袋子', '包装', '桶', '包装袋', '容器', '包装箱', '非金属包装物', '纸箱'],
                    '其它包装物': ['其它包装物', '包装', '袋子', '桶', '包装袋', '容器', '包装箱', '纸箱'],
                    '头部防护用品': ['防护', '头部防护用品', '安全', '防护用品', '安全用品', '劳保用品', '劳保'],
                    '呼吸防护用品': ['防护', '安全', '防护用品', '安全用品', '劳保用品', '劳保', '呼吸防护用品'],
                    '眼面部防护用品': ['防护', '安全', '眼面部防护用品', '防护用品', '安全用品', '劳保用品', '劳保'],
                    '听力防护用品': ['防护', '安全', '防护用品', '安全用品', '劳保用品', '劳保', '听力防护用品'],
                    '手部防护用品': ['防护', '安全', '防护用品', '安全用品', '手部防护用品', '劳保用品', '劳保'],
                    '足部防护用品': ['防护', '安全', '防护用品', '安全用品', '足部防护用品', '劳保用品', '劳保'],
                    '躯干防护用品': ['防护', '安全', '防护用品', '安全用品', '劳保用品', '劳保', '躯干防护用品'],
                    '坠落防护用品': ['防护', '安全', '防护用品', '安全用品', '劳保用品', '劳保', '坠落防护用品'],
                    '消防设施': ['报警', '消防器材', '消防', '消防设施', '火灾', '灭火', '灭火器'],
                    '消防器材': ['报警', '消防', '火灾', '灭火', '消防器材', '灭火器'],
                    '炼化辅助机械': ['泵', '机械设备', '机械', '工业设备', '管件', '阀门', '炼化辅助机械', '设备'],
                    '其他通用机械设备': ['通用', '泵', '机械设备', '机械', '其他通用机械设备', '机械备件', '工业设备', '管件'],
                    '包装机配件': ['包装机配件', '袋子', '包装', '桶', '包装袋', '容器', '包装箱', '纸箱'],
                    '加料机械配件': ['泵', '机械设备', '机械', '工业设备', '管件', '阀门', '加料机械配件', '设备'],
                    '其他通用机械设备配件': ['通用', '泵', '机械设备', '其他通用机械设备配件', '机械', '机械备件', '工业设备', '管件'],
                    '非金属建筑材料': ['非金属建筑材料', '水泥', '建筑', '砂石', '建材', '钢材', '建筑材料'],
                    '建筑五金': ['建筑五金', '水泥', '建筑', '砂石', '建材', '钢材', '建筑材料'],
                    '机械密封及配件': ['机械密封及配件', '泵', '机械设备', '机械', '工业设备', '管件', '阀门', '设备'],
                    '化工催化剂': ['sio2', '溶剂', 'al2o3', '助剂', '化工', '载体', '催化剂', '催化'],
                    '固定床催化剂': ['sio2', '固定床催化剂', '溶剂', 'al2o3', '助剂', '化工', '载体', '催化剂'],
                    '催化剂载体': ['sio2', '溶剂', '催化剂载体', 'al2o3', '助剂', '化工', '载体', '催化剂'],
                    '塑料包装物': ['袋子', '包装', '塑料包装物', '桶', '包装袋', '容器', '包装箱', '纸箱'],
                    '纸包装物': ['纸包装物', '袋子', '包装', '桶', '包装袋', '容器', '包装箱', '纸箱'],
                    '纺织品包装物': ['袋子', '包装', '桶', '包装袋', '容器', '纺织品包装物', '包装箱', '纸箱'],
                    '复合材料包装物': ['袋子', '包装', '复合材料包装物', '桶', '包装袋', '容器', '包装箱', '纸箱'],
                    '包装膜': ['袋子', '包装', '桶', '包装袋', '容器', '包装膜', '包装箱', '纸箱'],
                    '防护面屏': ['防护', '安全', '防护面屏', '防护用品', '安全用品', '劳保用品', '劳保'],
                    '化学防护服（轻型）': ['防护', '安全', '防护用品', '安全用品', '劳保用品', '劳保', '化学防护服（轻型）'],
                    '化学防护服（全密闭）': ['化学防护服（全密闭）', '防护', '安全', '防护用品', '安全用品', '劳保用品', '劳保'],
                    '消防炮（固定式）': ['报警', '消防器材', '消防', '消防炮（固定式）', '火灾', '灭火', '灭火器'],
                    '消防炮（移动式）': ['报警', '消防器材', '消防', '消防炮（移动式）', '火灾', '灭火', '灭火器'],
                    '消防水枪': ['报警', '消防器材', '消防', '消防水枪', '火灾', '灭火', '灭火器'],
                    '消防水带': ['报警', '消防器材', '消防', '消防水带', '火灾', '灭火', '灭火器'],
                    '包装机': ['袋子', '包装', '包装机', '桶', '包装袋', '容器', '包装箱', '纸箱'],
                    '加料机械': ['泵', '机械设备', '机械', '加料机械', '工业设备', '管件', '阀门', '设备'],
                    '化工流程泵': ['泵', '溶剂', '机械设备', '机械', '工业设备', '管件', '助剂', '化工流程泵'],
                    '粒料包装机配件': ['袋子', '包装', '桶', '包装袋', '容器', '包装箱', '粒料包装机配件', '纸箱'],
                    '辅助机械': ['辅助机械', '泵', '机械设备', '机械', '工业设备', '管件', '阀门', '设备'],
                }
        # 制造商分类映射 - 从数据库加载
        self.manufacturer_mappings = self._load_manufacturer_mappings_from_db()
        
        # 规格模式识别 - 基于训练结果增强
        self.spec_patterns = {
            'size': r'(\d+(?:\.\d+)?)\s*[×xX*]\s*(\d+(?:\.\d+)?)\s*[×xX*]\s*(\d+(?:\.\d+)?)',
            'diameter': r'[φΦ直径]\s*(\d+(?:\.\d+)?)',
            'length': r'长\s*(\d+(?:\.\d+)?)',
            'width': r'宽\s*(\d+(?:\.\d+)?)', 
            'height': r'高\s*(\d+(?:\.\d+)?)',
            'voltage': r'(\d+(?:\.\d+)?)\s*[VvKk电压]',
            'power': r'(\d+(?:\.\d+)?)\s*[WwKk功率]',
            'capacity': r'(\d+(?:\.\d+)?)\s*[LlMm容量升]',
            # 医疗器械规格模式
            'medical_device': r'(电极|导管|植入物|一次性)',
            # 电子设备规格模式
            'electronic': r'(\d+(?:\.\d+)?\s*[VWHzAΩ])',
            # 机械零件规格模式
            'mechanical': r'(\d+\s*mm|\d+\s*cm|M\d+|不锈钢)'
        }
        
        # 规格分类映射 - 从数据库加载
        self.spec_category_mappings = self._load_spec_mappings_from_db()
    
    def _load_training_results_from_db(self) -> Optional[Dict]:
        """从数据库加载训练结果"""
        try:
            results = self.training_manager.get_latest_training_results()
            if results:
                logger.info(f"从数据库加载训练结果，会话ID: {results['training_session_id']}")
                return results
            else:
                logger.warning("数据库中未找到训练结果，尝试从文件加载")
                return self._load_training_results_from_file()
        except Exception as e:
            logger.error(f"从数据库加载训练结果失败: {e}")
            return self._load_training_results_from_file()
    
    def _load_training_results_from_file(self) -> Optional[Dict]:
        """从文件加载训练结果（备用方法）"""
        try:
            import os
            training_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'training_results.json')
            if os.path.exists(training_file):
                with open(training_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"从文件加载训练结果失败: {e}")
        return None
    
    def _load_manufacturer_mappings_from_db(self) -> Dict[str, str]:
        """从数据库加载制造商映射"""
        try:
            manufacturer_rules = self.cached_rules.get('manufacturer', {})
            mappings = {}
            for category, rules in manufacturer_rules.items():
                for rule in rules:
                    mappings[rule['keyword']] = category
            return mappings
        except Exception as e:
            logger.error(f"从数据库加载制造商映射失败: {e}")
            return {}
    
    def _load_spec_mappings_from_db(self) -> Dict[str, List[str]]:
        """从数据库加载规格映射"""
        try:
            spec_rules = self.cached_rules.get('specification', {})
            mappings = {}
            for category, rules in spec_rules.items():
                mappings[category] = [rule['keyword'] for rule in rules]
            return mappings
        except Exception as e:
            logger.error(f"从数据库加载规格映射失败: {e}")
            return {}
    
    def _load_tfidf_model(self):
        """加载TF-IDF模型"""
        try:
            model_data = self.training_manager.load_active_classification_model("tfidf_classifier")
            if model_data:
                model, feature_names, parameters = model_data
                logger.info(f"TF-IDF模型加载成功，特征数: {len(feature_names)}")
                return model
        except Exception as e:
            logger.warning(f"加载TF-IDF模型失败: {e}")
        return None
    
    def enhanced_category_matching(self, material_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        增强分类匹配方法 - 基于532个实际分类的智能映射
        
        Args:
            material_info: 物料信息，包含name, spec, manufacturer等
            
        Returns:
            推荐分类列表，按置信度排序
        """
        material_name = material_info.get('name', '').lower()
        spec = material_info.get('spec', '').lower()
        manufacturer = material_info.get('manufacturer', '').lower()
        text_to_analyze = f"{material_name} {spec} {manufacturer}".strip()
        
        logger.info(f"增强分类匹配分析文本: '{text_to_analyze}'")
        
        recommendations = []
        
        # 加载增强分类配置
        try:
            enhanced_config_path = '/Users/mason/Desktop/code /mmp/enhanced_classifier_config.json'
            with open(enhanced_config_path, 'r') as f:
                enhanced_config = json.load(f)
                category_mappings = enhanced_config.get('keyword_mappings', {})
                
            logger.info(f"加载增强配置，共{len(category_mappings)}个分类映射")
            
            # 对每个分类进行匹配
            for category_name, keywords in category_mappings.items():
                confidence = 0.0
                matched_keywords = []
                
                # 关键词匹配
                for keyword in keywords:
                    if keyword.lower() in text_to_analyze:
                        confidence += 0.3  # 每个关键词匹配增加0.3置信度
                        matched_keywords.append(keyword)
                
                # 如果有匹配，创建推荐
                if confidence > 0:
                    # 限制最高置信度
                    confidence = min(confidence, 0.95)
                    
                    # 获取分类信息
                    category_info = self._get_category_by_name(category_name)
                    if category_info and not category_info.get('temp'):
                        recommendations.append({
                            'category_id': category_info['id'],
                            'category_name': category_name,
                            'confidence': confidence,
                            'reason': f"增强关键词匹配: {', '.join(matched_keywords[:3])}",
                            'source': 'enhanced_matching'
                        })
                        logger.info(f"增强匹配 - 分类'{category_name}': {matched_keywords}, 置信度: {confidence}")
            
            # 按置信度排序并返回前5个
            recommendations.sort(key=lambda x: x['confidence'], reverse=True)
            logger.info(f"增强分类匹配完成，生成{len(recommendations)}个推荐")
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f"增强分类匹配失败: {e}")
            return []

    def recommend_categories(self, material_info: Dict[str, Any], session_id: str = None) -> List[Dict[str, Any]]:
        """
        智能推荐物料分类
        
        Args:
            material_info: 物料信息，包含name, spec, manufacturer等
            session_id: 会话ID，用于记录推荐历史
            
        Returns:
            推荐分类列表，按置信度排序
        """
        try:
            logger.info(f"开始为物料推荐分类: {material_info}")
            
            # 0. 增强分类匹配（优先）
            enhanced_recommendations = self.enhanced_category_matching(material_info)
            
            # 1. 关键词匹配推荐
            keyword_recommendations = self._keyword_based_recommendation(material_info)
            
            # 2. 规格模式匹配推荐
            spec_recommendations = self._spec_pattern_recommendation(material_info)
            
            # 3. 历史数据学习推荐
            history_recommendations = self._history_based_recommendation(material_info)
            
            # 4. 厂家信息推荐
            manufacturer_recommendations = self._manufacturer_based_recommendation(material_info)
            
            # 5. 合并和排序推荐结果
            final_recommendations = self._merge_recommendations([
                enhanced_recommendations,
                keyword_recommendations,
                spec_recommendations, 
                history_recommendations,
                manufacturer_recommendations
            ])
            
            # 6. 记录推荐历史
            if session_id:
                self._save_recommendation_history(session_id, material_info, final_recommendations)
            
            logger.info(f"推荐完成，共生成{len(final_recommendations)}个推荐结果")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"智能推荐失败: {e}")
            return self._fallback_recommendations(material_info)
    
    def _keyword_based_recommendation(self, material_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于关键词的推荐 - 使用训练结果增强"""
        material_name = material_info.get('name', '').lower()
        spec = material_info.get('spec', '').lower()
        manufacturer = material_info.get('manufacturer', '').lower()
        text_to_analyze = f"{material_name} {spec} {manufacturer}".strip()
        
        logger.info(f"分析文本: '{text_to_analyze}'")
        
        recommendations = []
        
        # 1. 使用数据库中的关键词规则进行匹配
        keyword_rules = self.cached_rules.get('keyword', {})
        for category, rules in keyword_rules.items():
            confidence = 0.0
            matched_keywords = []
            
            for rule in rules:
                keyword = rule['keyword']
                if keyword.lower() in text_to_analyze:
                    confidence += 0.25 * rule.get('confidence', 0.7)
                    matched_keywords.append(keyword)
            
            if confidence > 0:
                confidence = min(confidence, 1.0)
                logger.info(f"数据库关键词匹配 - 分类'{category}': {matched_keywords}, 置信度: {confidence}")
                
                category_info = self._get_category_by_name(category)
                if category_info:
                    recommendations.append({
                        'category_id': category_info['id'],
                        'category_name': category,
                        'confidence': confidence,
                        'reason': f"数据库关键词匹配: {', '.join(matched_keywords[:3])}",
                        'source': 'db_trained_keywords'
                    })
        
        # 2. 使用TF-IDF模型进行相似性匹配
        if self.tfidf_model and text_to_analyze.strip():
            try:
                # 使用TF-IDF模型计算文本向量
                text_vector = self.tfidf_model.transform([text_to_analyze])
                
                # 这里可以添加基于向量相似度的分类逻辑
                # 暂时使用简单的特征权重分析
                feature_names = self.tfidf_model.get_feature_names_out()
                feature_scores = text_vector.toarray()[0]
                
                # 找出权重最高的特征词
                top_features = [(feature_names[i], feature_scores[i]) 
                              for i in feature_scores.argsort()[-5:][::-1] 
                              if feature_scores[i] > 0]
                
                if top_features:
                    logger.info(f"TF-IDF关键特征: {top_features}")
                    
            except Exception as e:
                logger.warning(f"TF-IDF模型匹配失败: {e}")
        
        # 3. 特殊处理：医疗器械品牌和关键词优先匹配
        if any(keyword in text_to_analyze for keyword in ['depuy', '强生', 'johnson', '等离子', '射频', '气化', '电极']):
            medical_categories = ['治疗设备', '手术器械', '医疗器械']
            for category in medical_categories:
                category_info = self._get_category_by_name(category)
                if category_info and not category_info.get('temp'):
                    recommendations.append({
                        'category_id': category_info['id'],
                        'category_name': category,
                        'confidence': 0.85,
                        'reason': "医疗器械品牌/关键词匹配",
                        'source': 'medical_keyword_priority'
                    })
                    break
        
        # 4. 常规关键词匹配（预定义映射）
        for category, keywords in self.keyword_mappings.items():
            confidence = 0.0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in text_to_analyze:
                    confidence += 0.15  # 预定义关键词权重稍低
                    matched_keywords.append(keyword)
            
            if confidence > 0:
                logger.info(f"预定义关键词匹配 - 分类'{category}': {matched_keywords}, 置信度: {confidence}")
                
                # 获取分类的详细信息
                category_info = self._get_category_by_name(category)
                if category_info and not category_info.get('temp'):
                    recommendations.append({
                        'category_id': category_info['id'],
                        'category_name': category,
                        'confidence': min(confidence, 0.95),  # 最高置信度不超过0.95
                        'reason': f"关键词匹配: {', '.join(matched_keywords)}",
                        'source': 'keyword_matching'
                    })
        
        logger.info(f"关键词推荐结果: {len(recommendations)}个")
        return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)[:3]
    
    def _spec_pattern_recommendation(self, material_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于规格模式的推荐 - 使用训练结果增强"""
        spec = material_info.get('spec', '')
        name = material_info.get('name', '')
        text_to_analyze = f"{spec} {name}".lower()
        recommendations = []
        
        # 1. 使用训练结果中的规格规则
        for category, spec_keywords in self.spec_category_mappings.items():
            confidence = 0.0
            matched_patterns = []
            
            for keyword in spec_keywords:
                if keyword.lower() in text_to_analyze:
                    confidence += 0.3
                    matched_patterns.append(keyword)
            
            if confidence > 0:
                category_info = self._get_category_by_name(category)
                if category_info:
                    recommendations.append({
                        'category_id': category_info['id'],
                        'category_name': category,
                        'confidence': min(confidence, 0.8),
                        'reason': f"训练规格模式: {', '.join(matched_patterns)}",
                        'source': 'trained_spec_pattern'
                    })
        
        # 2. 原有的规格模式检查
        for pattern_name, pattern in self.spec_patterns.items():
            match = re.search(pattern, spec, re.IGNORECASE)
            if match:
                confidence = 0.25
                category_suggestions = []
                
                if pattern_name in ['size', 'diameter', 'length']:
                    category_suggestions = ['建筑材料', '钢材', '管材', '机械零件']
                elif pattern_name in ['voltage', 'power', 'electronic']:
                    category_suggestions = ['电子设备', '电气设备']
                elif pattern_name == 'capacity':
                    category_suggestions = ['容器', '储罐', '医疗器械']
                elif pattern_name == 'medical_device':
                    category_suggestions = ['医疗器械', '手术器械']
                elif pattern_name == 'mechanical':
                    category_suggestions = ['机械零件', '钢材']
                
                for category in category_suggestions:
                    category_info = self._get_category_by_name(category)
                    if category_info:
                        recommendations.append({
                            'category_id': category_info['id'],
                            'category_name': category,
                            'confidence': confidence,
                            'reason': f"规格模式匹配: {pattern_name}",
                            'source': 'spec_pattern'
                        })
        
        return recommendations[:3]
    
    def _history_based_recommendation(self, material_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于历史数据的推荐"""
        try:
            # 查找相似的历史物料
            similar_materials = self._find_similar_historical_materials(material_info)
            
            recommendations = []
            for material in similar_materials[:3]:
                if 'category_id' in material and material['category_id']:
                    category_info = self._get_category_by_id(material['category_id'])
                    if category_info:
                        # 计算相似度置信度
                        similarity = self._calculate_similarity(material_info, material)
                        recommendations.append({
                            'category_id': material['category_id'],
                            'category_name': category_info.get('name', ''),
                            'confidence': similarity * 0.8,  # 历史匹配的置信度稍低
                            'reason': f"相似历史物料: {material.get('name', '')}",
                            'source': 'history_learning'
                        })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"历史数据推荐失败: {e}")
            return []
    
    def _manufacturer_based_recommendation(self, material_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于生产厂家的推荐 - 使用训练结果增强"""
        manufacturer = material_info.get('manufacturer', '')
        if not manufacturer:
            return []
        
        recommendations = []
        
        try:
            # 1. 使用训练结果的制造商映射
            for mfg_name, category_name in self.manufacturer_mappings.items():
                if manufacturer in mfg_name or mfg_name in manufacturer:
                    category_info = self._get_category_by_name(category_name)
                    if category_info:
                        recommendations.append({
                            'category_id': category_info['id'],
                            'category_name': category_name,
                            'confidence': 0.75,  # 训练数据匹配置信度高
                            'reason': f"训练数据厂家匹配: {mfg_name[:50]}...",
                            'source': 'trained_manufacturer'
                        })
                        logger.info(f"训练数据匹配厂家: {manufacturer} -> {category_name}")
            
            # 2. 查找同厂家的其他物料分类（原有逻辑）
            if not recommendations:  # 只有在训练数据没匹配到时才使用原有逻辑
                manufacturer_categories = self._get_manufacturer_categories(manufacturer)
                for category_data in manufacturer_categories[:2]:
                    recommendations.append({
                        'category_id': category_data['category_id'],
                        'category_name': category_data['category_name'],
                        'confidence': 0.4,  # 厂家匹配置信度中等
                        'reason': f"同厂家产品: {manufacturer}",
                        'source': 'manufacturer_pattern'
                    })
            
            return recommendations[:3]  # 最多返回3个推荐
            
        except Exception as e:
            logger.error(f"厂家推荐失败: {e}")
            return []
    
    def _merge_recommendations(self, recommendation_lists: List[List[Dict]]) -> List[Dict[str, Any]]:
        """合并多个推荐结果"""
        merged_dict = {}
        
        for recommendations in recommendation_lists:
            for rec in recommendations:
                category_id = rec['category_id']
                if category_id in merged_dict:
                    # 合并置信度（加权平均）
                    existing = merged_dict[category_id]
                    total_weight = existing.get('weight', 1) + 1
                    new_confidence = (existing['confidence'] * existing.get('weight', 1) + rec['confidence']) / total_weight
                    
                    existing['confidence'] = new_confidence
                    existing['weight'] = total_weight
                    existing['reason'] += f"; {rec['reason']}"
                    existing['source'] += f", {rec['source']}"
                else:
                    rec['weight'] = 1
                    merged_dict[category_id] = rec
        
        # 转换为列表并按置信度排序
        final_recommendations = list(merged_dict.values())
        final_recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 清理辅助字段
        for rec in final_recommendations:
            rec.pop('weight', None)
        
        return final_recommendations[:5]  # 最多返回5个推荐
    
    def _get_category_by_name(self, category_name: str) -> Optional[Dict[str, Any]]:
        """根据分类名称获取分类信息"""
        try:
            categories = self.master_manager.get_material_categories()
            logger.info(f"查找分类'{category_name}'，总共有{len(categories)}个分类")
            
            for category in categories:
                # 尝试多种可能的字段名
                cat_name = category.get('category_name') or category.get('name') or category.get('category')
                if cat_name == category_name:
                    logger.info(f"找到匹配分类: {category}")
                    # 标准化返回格式
                    return {
                        'id': category.get('id') or category.get('category_id'),
                        'category_name': cat_name,
                        'name': cat_name,
                        'level': category.get('level', 1),
                        'temp': False
                    }
            
            # 如果没找到，创建一个临时的分类信息
            logger.warning(f"未找到分类'{category_name}'，创建临时分类")
            temp_id = f'TEMP_{hash(category_name) % 10000}'
            return {
                'id': temp_id,
                'category_id': temp_id,
                'category_name': category_name,
                'name': category_name,
                'level': 1,
                'temp': True
            }
        except Exception as e:
            logger.error(f"获取分类信息失败: {e}")
            # 返回临时分类信息
            temp_id = f'TEMP_{hash(category_name) % 10000}'
            return {
                'id': temp_id,
                'category_id': temp_id,
                'category_name': category_name,
                'name': category_name,
                'level': 1,
                'temp': True
            }
    
    def _get_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        """根据分类ID获取分类信息"""
        try:
            categories = self.master_manager.get_material_categories()
            for category in categories:
                if category.get('id') == category_id or str(category.get('id')) == str(category_id):
                    return category
            return None
        except Exception as e:
            logger.error(f"获取分类信息失败: {e}")
            return None
    
    def _find_similar_historical_materials(self, material_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查找相似的历史物料"""
        # 这里可以实现更复杂的相似度算法
        # 暂时使用简单的关键词匹配
        material_name = material_info.get('name', '').lower()
        
        try:
            # 从业务数据库中查找相似物料
            # 这里需要业务数据管理器提供查询接口
            return []  # 暂时返回空列表
        except Exception as e:
            logger.error(f"查找历史物料失败: {e}")
            return []
    
    def _calculate_similarity(self, material1: Dict, material2: Dict) -> float:
        """计算两个物料的相似度"""
        name1 = material1.get('name', '').lower()
        name2 = material2.get('name', '').lower()
        
        # 简单的字符串相似度计算
        if name1 == name2:
            return 1.0
        
        # 计算共同词汇比例
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 and not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _get_manufacturer_categories(self, manufacturer: str) -> List[Dict[str, Any]]:
        """获取指定厂家的产品分类分布"""
        # 这里可以查询历史数据库，获取该厂家产品的分类分布
        # 暂时返回空列表
        return []
    
    def _save_recommendation_history(self, session_id: str, material_info: Dict, recommendations: List[Dict]):
        """保存推荐历史"""
        try:
            history_data = {
                'session_id': session_id,
                'material_info': material_info,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
            # 保存到会话数据中
            if hasattr(self, 'business_manager') and self.business_manager:
                # 这里可以保存推荐历史到数据库
                pass
                
        except Exception as e:
            logger.error(f"保存推荐历史失败: {e}")
    
    def _fallback_recommendations(self, material_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """备用推荐方案"""
        return [
            {
                'category_id': 'CAT999',
                'category_name': '未分类',
                'confidence': 0.1,
                'reason': '系统推荐失败，建议手动分类',
                'source': 'fallback'
            }
        ]

# 全局实例
def get_intelligent_classifier(business_manager: BusinessDataManager = None) -> IntelligentClassifier:
    """获取智能分类器实例"""
    if business_manager is None:
        # 这里可以创建默认的business_manager实例
        pass
    return IntelligentClassifier(business_manager)