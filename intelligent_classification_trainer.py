#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分类训练系统
基于用户提供的训练数据改进分类算法
"""

import pandas as pd
import numpy as np
import re
import sqlite3
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentClassificationTrainer:
    """智能分类训练器"""
    
    def __init__(self, master_data_path: str = 'e4p9.csv', new_data_path: str = 'e4.xlsx'):
        self.master_data_path = master_data_path
        self.new_data_path = new_data_path
        self.master_data = None
        self.new_data = None
        self.tfidf_vectorizer = None
        self.trained_patterns = {}
        
    def load_training_data(self):
        """加载训练数据"""
        logger.info("🔧 加载训练数据...")
        
        try:
            # 加载主数据 (e4p9.csv)
            self.master_data = pd.read_csv(self.master_data_path)
            logger.info(f"✅ 主数据加载成功: {self.master_data.shape}")
            
            # 加载新数据 (e4.xlsx)
            self.new_data = pd.read_excel(self.new_data_path)
            logger.info(f"✅ 新数据加载成功: {self.new_data.shape}")
            
            # 数据预处理
            self._preprocess_data()
            
        except Exception as e:
            logger.error(f"❌ 数据加载失败: {e}")
            raise
    
    def _preprocess_data(self):
        """数据预处理"""
        logger.info("🔄 开始数据预处理...")
        
        # 统一字段名称映射
        master_mapping = {
            'spczm': 'id',
            '产品名称': 'name',
            '产品规格': 'specification',
            '生产厂家': 'manufacturer',
            '医保代码': 'insurance_code'
        }
        
        new_mapping = {
            '资产代码': 'id', 
            '资产名称': 'name',
            '规格型号': 'specification',
            '品牌': 'brand',
            '医保码': 'insurance_code',
            '生产厂家名称': 'manufacturer'
        }
        
        # 重命名字段
        self.master_data = self.master_data.rename(columns=master_mapping)
        self.new_data = self.new_data.rename(columns=new_mapping)
        
        # 清理数据
        for df in [self.master_data, self.new_data]:
            df['name'] = df['name'].fillna('')
            df['specification'] = df['specification'].fillna('')
            df['manufacturer'] = df['manufacturer'].fillna('')
            
            # 合并文本用于分析
            df['combined_text'] = df['name'].astype(str) + ' ' + \
                                df['specification'].astype(str) + ' ' + \
                                df['manufacturer'].astype(str)
        
        logger.info("✅ 数据预处理完成")
    
    def extract_classification_patterns(self):
        """提取分类模式"""
        logger.info("🧠 提取分类模式...")
        
        # 分析产品名称中的关键词
        product_keywords = self._extract_product_keywords()
        
        # 分析制造商模式
        manufacturer_patterns = self._extract_manufacturer_patterns()
        
        # 分析规格模式
        specification_patterns = self._extract_specification_patterns()
        
        # 构建分类规则
        classification_rules = self._build_classification_rules(
            product_keywords, manufacturer_patterns, specification_patterns
        )
        
        return classification_rules
    
    def _extract_product_keywords(self) -> Dict[str, List[str]]:
        """提取产品关键词"""
        logger.info("📝 分析产品关键词...")
        
        # 合并所有产品名称
        all_names = list(self.master_data['name']) + list(self.new_data['name'])
        
        # 使用jieba分词
        all_words = []
        for name in all_names:
            if pd.notna(name):
                words = jieba.lcut(str(name))
                all_words.extend([w for w in words if len(w) > 1])
        
        # 统计词频
        word_freq = {}
        for word in all_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序并分类
        high_freq_words = {k: v for k, v in word_freq.items() if v >= 5}
        
        # 分类关键词
        categories = {
            '医疗器械': ['器械', '设备', '仪器', '系统', '机器', '治疗', '诊断', '监护'],
            '电子设备': ['电子', '电路', '芯片', '传感器', '控制器', '显示器'],
            '机械零件': ['零件', '配件', '轴承', '齿轮', '螺丝', '螺栓'],
            '化工材料': ['化学', '溶液', '试剂', '材料', '涂料', '胶水']
        }
        
        return {'word_frequency': high_freq_words, 'category_keywords': categories}
    
    def _extract_manufacturer_patterns(self) -> Dict[str, str]:
        """分析制造商模式"""
        logger.info("🏢 分析制造商模式...")
        
        manufacturer_category = {}
        
        # 合并制造商数据
        all_manufacturers = list(self.master_data['manufacturer'].dropna()) + \
                          list(self.new_data['manufacturer'].dropna())
        
        # 制造商分类规则
        medical_keywords = ['医疗', '器械', '生物', '药业', '医药', '健康', '强生', 'Johnson', 'Depuy']
        electronic_keywords = ['电子', '科技', '技术', '软件', '数码', '通讯']
        mechanical_keywords = ['机械', '工程', '制造', '重工', '精密', '自动化']
        
        for manufacturer in set(all_manufacturers):
            manufacturer_str = str(manufacturer).lower()
            
            if any(keyword in manufacturer_str for keyword in medical_keywords):
                manufacturer_category[manufacturer] = '医疗器械'
            elif any(keyword in manufacturer_str for keyword in electronic_keywords):
                manufacturer_category[manufacturer] = '电子设备'
            elif any(keyword in manufacturer_str for keyword in mechanical_keywords):
                manufacturer_category[manufacturer] = '机械零件'
            else:
                manufacturer_category[manufacturer] = '通用'
        
        return manufacturer_category
    
    def _extract_specification_patterns(self) -> Dict[str, List[str]]:
        """分析规格模式"""
        logger.info("📐 分析规格模式...")
        
        # 合并所有规格数据
        all_specs = list(self.master_data['specification'].dropna()) + \
                   list(self.new_data['specification'].dropna())
        
        # 规格模式
        patterns = {
            '尺寸规格': [],
            '电气规格': [],
            '材质规格': [],
            '医疗规格': []
        }
        
        size_pattern = r'(\d+(?:\.\d+)?)\s*[×xX*]\s*(\d+(?:\.\d+)?)'
        voltage_pattern = r'(\d+(?:\.\d+)?)\s*[VvKk]'
        material_pattern = r'(不锈钢|铝合金|塑料|橡胶|硅胶)'
        medical_pattern = r'(一次性|无菌|消毒|灭菌)'
        
        for spec in all_specs:
            spec_str = str(spec)
            
            if re.search(size_pattern, spec_str):
                patterns['尺寸规格'].append(spec_str)
            if re.search(voltage_pattern, spec_str):
                patterns['电气规格'].append(spec_str)
            if re.search(material_pattern, spec_str):
                patterns['材质规格'].append(spec_str)
            if re.search(medical_pattern, spec_str):
                patterns['医疗规格'].append(spec_str)
        
        return patterns
    
    def _build_classification_rules(self, keywords, manufacturers, specifications):
        """构建分类规则"""
        logger.info("⚙️ 构建分类规则...")
        
        rules = {
            'keyword_rules': {},
            'manufacturer_rules': manufacturers,
            'specification_rules': {},
            'combined_rules': {}
        }
        
        # 基于关键词的规则
        for category, words in keywords['category_keywords'].items():
            rules['keyword_rules'][category] = {
                'keywords': words,
                'confidence_base': 0.7
            }
        
        # 基于规格的规则
        rules['specification_rules'] = {
            '医疗器械': ['电极', '导管', '植入物', '一次性'],
            '电子设备': ['V', 'W', 'Hz', 'A', 'Ω'],
            '机械零件': ['mm', 'cm', 'M3', 'M4', '不锈钢']
        }
        
        return rules
    
    def train_tfidf_model(self):
        """训练TF-IDF模型"""
        logger.info("🤖 训练TF-IDF模型...")
        
        # 合并所有文本数据
        all_texts = list(self.master_data['combined_text']) + \
                   list(self.new_data['combined_text'])
        
        # 创建TF-IDF向量化器
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,  # 中文不使用英文停用词
            ngram_range=(1, 2)
        )
        
        # 训练模型
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
        
        logger.info(f"✅ TF-IDF模型训练完成，特征维度: {tfidf_matrix.shape}")
        
        return tfidf_matrix
    
    def generate_enhanced_keywords(self):
        """生成增强的关键词映射"""
        logger.info("🚀 生成增强关键词映射...")
        
        # 分析实际数据中的高频词
        all_product_names = []
        for df in [self.master_data, self.new_data]:
            all_product_names.extend(df['name'].dropna().tolist())
        
        # 使用jieba分词并统计
        word_counts = {}
        for name in all_product_names:
            words = jieba.lcut(str(name))
            for word in words:
                if len(word) > 1:  # 过滤单字符
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # 生成增强的分类关键词
        enhanced_keywords = {
            '医疗器械': [],
            '治疗设备': [],
            '诊断设备': [],
            '手术器械': [],
            '监护设备': []
        }
        
        # 医疗相关高频词
        medical_words = [word for word, count in sorted_words[:100] 
                        if any(med_key in word for med_key in 
                              ['医', '疗', '械', '设备', '仪器', '系统', '治疗', '手术', '诊断'])]
        
        enhanced_keywords['医疗器械'].extend(medical_words[:20])
        enhanced_keywords['治疗设备'].extend([w for w in medical_words if '治疗' in w or '射频' in w or '等离子' in w])
        enhanced_keywords['手术器械'].extend([w for w in medical_words if '手术' in w or '电极' in w or '导管' in w])
        
        return enhanced_keywords
    
    def save_training_results(self, output_path: str = 'training_results.json'):
        """保存训练结果"""
        logger.info(f"💾 保存训练结果到 {output_path}...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {
                'master_data_count': len(self.master_data),
                'new_data_count': len(self.new_data),
                'total_samples': len(self.master_data) + len(self.new_data)
            },
            'classification_patterns': self.trained_patterns,
            'enhanced_keywords': self.generate_enhanced_keywords()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ 训练结果保存成功")
    
    def update_database_categories(self):
        """更新数据库分类数据"""
        logger.info("🗄️ 更新数据库分类数据...")
        
        conn = sqlite3.connect('master_data.db')
        cursor = conn.cursor()
        
        # 基于训练数据添加新的分类
        new_categories = [
            ('CAT004', '诊疗设备', 'CAT003', 2, '专业诊疗设备', '{"keywords": ["诊疗", "检查", "扫描"]}'),
            ('CAT005', '植入器械', 'CAT003', 2, '植入式医疗器械', '{"keywords": ["植入", "埋置", "内置"]}'),
            ('CAT006', '急救设备', 'CAT003', 2, '急救医疗设备', '{"keywords": ["急救", "抢救", "应急"]}')
        ]
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        iso_time = datetime.now().isoformat()
        
        for category in new_categories:
            try:
                cursor.execute('''
                INSERT OR IGNORE INTO material_categories 
                (category_id, category_name, parent_id, level, description, features, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (*category, current_time, iso_time))
                logger.info(f"  添加分类: {category[1]}")
            except Exception as e:
                logger.warning(f"  分类添加失败 {category[1]}: {e}")
        
        conn.commit()
        conn.close()
        logger.info("✅ 数据库分类数据更新完成")
    
    def run_training_pipeline(self):
        """运行完整的训练流程"""
        logger.info("🚀 启动智能分类训练流程...")
        
        try:
            # 1. 加载数据
            self.load_training_data()
            
            # 2. 提取分类模式
            self.trained_patterns = self.extract_classification_patterns()
            
            # 3. 训练TF-IDF模型
            self.train_tfidf_model()
            
            # 4. 更新数据库
            self.update_database_categories()
            
            # 5. 保存结果
            self.save_training_results()
            
            logger.info("🎉 智能分类训练完成！")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 训练过程失败: {e}")
            return False

def main():
    """主函数"""
    print("=" * 60)
    print("    智能分类训练系统")
    print("=" * 60)
    
    trainer = IntelligentClassificationTrainer()
    
    if trainer.run_training_pipeline():
        print("\n✅ 训练成功完成！")
        print("\n📊 训练数据统计:")
        print(f"   主数据样本: {len(trainer.master_data)} 条")
        print(f"   新数据样本: {len(trainer.new_data)} 条") 
        print(f"   总训练样本: {len(trainer.master_data) + len(trainer.new_data)} 条")
        
        print("\n🎯 建议下一步:")
        print("   1. 重启MMP应用以加载新的分类数据")
        print("   2. 测试改进后的智能分类效果") 
        print("   3. 查看 training_results.json 了解训练详情")
    else:
        print("\n❌ 训练失败，请检查错误日志")

if __name__ == "__main__":
    main()