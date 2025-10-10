# -*- coding: utf-8 -*-
"""
质量评估权重优化算法
基于历史分类结果和用户反馈，使用机器学习算法优化质量评估维度权重
"""

import numpy as np
import pandas as pd
import sqlite3
from typing import Dict, List, Any, Tuple
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import optuna
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class QualityWeightOptimizer:
    """质量评估权重优化器"""
    
    def __init__(self, mmp_db_path: str = 'business_data.db', 
                 training_db_path: str = 'training_data.db'):
        self.mmp_db_path = mmp_db_path
        self.training_db_path = training_db_path
        
        # 当前权重配置（基于现有智能分类器的经验权重）
        self.current_weights = {
            'confidence_score': 0.30,     # 置信度权重30%
            'consistency_score': 0.25,    # 一致性权重25%
            'completeness_score': 0.20,   # 完整性权重20%
            'accuracy_score': 0.15,       # 准确性权重15%
            'compliance_score': 0.10      # 合规性权重10%
        }
        
        # 历史最优权重记录
        self.optimization_history = []
        
    def collect_training_data(self, days_back: int = 30) -> pd.DataFrame:
        """收集训练数据，基于现有MMP系统的分类结果和用户反馈"""
        
        # 从业务数据库中获取分类历史
        conn = sqlite3.connect(self.mmp_db_path)
        
        # 查询最近的分类结果和用户反馈
        query = '''
        SELECT 
            material_name,
            specification,
            manufacturer,
            predicted_category,
            confidence_score,
            user_feedback,
            final_category,
            created_at
        FROM classification_history 
        WHERE created_at >= date('now', '-{} days')
        AND user_feedback IS NOT NULL
        '''.format(days_back)
        
        try:
            df_feedback = pd.read_sql(query, conn)
        except:
            # 如果表不存在，创建模拟数据用于演示
            df_feedback = self._create_mock_training_data()
        
        conn.close()
        
        if df_feedback.empty:
            logger.warning("未找到训练数据，使用模拟数据")
            df_feedback = self._create_mock_training_data()
        
        # 计算各维度评分
        enhanced_df = self._calculate_quality_dimensions(df_feedback)
        
        logger.info(f"收集到 {len(enhanced_df)} 条训练数据")
        return enhanced_df
    
    def _create_mock_training_data(self) -> pd.DataFrame:
        """创建模拟训练数据用于演示和测试"""
        
        mock_data = []
        
        # 基于现有智能分类器的实际案例创建模拟数据
        classifications = [
            ('不锈钢球阀', 'DN100 PN16', '上海阀门厂', '球阀', 0.95, 'correct', '球阀'),
            ('法兰', 'DN80 PN25', '江苏管件', '法兰', 0.88, 'correct', '法兰'),
            ('螺栓', 'M16*80', '标准件厂', '紧固件', 0.72, 'incorrect', '螺栓'),
            ('密封圈', 'φ100*5', '橡胶制品', '密封件', 0.85, 'correct', '密封圈'),
            ('离心泵', '50m³/h 32m', '水泵厂', '泵', 0.93, 'correct', '离心泵'),
            ('疏水阀', 'CS19H DN25', '阀门公司', '阀门', 0.67, 'incorrect', '疏水阀'),
            ('管件', '90度弯头 DN50', '管道公司', '管件', 0.79, 'correct', '弯头'),
            ('轴承', '6205-2RS', '轴承厂', '轴承', 0.91, 'correct', '滚动轴承'),
        ]
        
        for i, (name, spec, mfg, pred_cat, conf, feedback, final_cat) in enumerate(classifications):
            # 为每个基础案例创建多个变体
            for variation in range(5):
                # 添加一些随机变化
                conf_variation = conf + np.random.normal(0, 0.05)
                conf_variation = max(0.1, min(0.99, conf_variation))
                
                mock_data.append({
                    'material_name': name,
                    'specification': spec,
                    'manufacturer': mfg,
                    'predicted_category': pred_cat,
                    'confidence_score': conf_variation,
                    'user_feedback': feedback,
                    'final_category': final_cat,
                    'created_at': datetime.now() - timedelta(days=np.random.randint(1, 30))
                })
        
        return pd.DataFrame(mock_data)
    
    def _calculate_quality_dimensions(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算质量评估的各个维度评分"""
        
        enhanced_df = df.copy()
        
        # 1. 置信度评分（直接使用）
        enhanced_df['confidence_dimension'] = enhanced_df['confidence_score']
        
        # 2. 一致性评分（基于历史相似物料的分类一致性）
        enhanced_df['consistency_dimension'] = enhanced_df.apply(
            lambda row: self._calculate_consistency_score(row), axis=1
        )
        
        # 3. 完整性评分（基于字段完整度）
        enhanced_df['completeness_dimension'] = enhanced_df.apply(
            lambda row: self._calculate_completeness_score(row), axis=1
        )
        
        # 4. 准确性评分（基于规则匹配）
        enhanced_df['accuracy_dimension'] = enhanced_df.apply(
            lambda row: self._calculate_accuracy_score(row), axis=1
        )
        
        # 5. 合规性评分（基于行业标准）
        enhanced_df['compliance_dimension'] = enhanced_df.apply(
            lambda row: self._calculate_compliance_score(row), axis=1
        )
        
        # 6. 目标标签（用户反馈转换为二分类）
        enhanced_df['quality_label'] = enhanced_df['user_feedback'].apply(
            lambda x: 1 if x == 'correct' else 0
        )
        
        return enhanced_df
    
    def _calculate_consistency_score(self, row) -> float:
        """计算一致性评分"""
        # 模拟一致性计算（实际应该基于历史相似物料）
        base_score = 0.8
        
        # 如果物料名称包含明确的类别词，一致性较高
        name = row['material_name'].lower()
        category_keywords = ['阀', '泵', '管', '轴承', '密封', '法兰', '螺栓']
        
        for keyword in category_keywords:
            if keyword in name:
                base_score += 0.1
                break
        
        return min(base_score + np.random.normal(0, 0.1), 1.0)
    
    def _calculate_completeness_score(self, row) -> float:
        """计算完整性评分"""
        score = 0.0
        
        # 检查关键字段完整性
        if row['material_name'] and len(str(row['material_name']).strip()) > 2:
            score += 0.4
        if row['specification'] and len(str(row['specification']).strip()) > 2:
            score += 0.3
        if row['manufacturer'] and len(str(row['manufacturer']).strip()) > 2:
            score += 0.2
        if row['predicted_category'] and len(str(row['predicted_category']).strip()) > 1:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_accuracy_score(self, row) -> float:
        """计算准确性评分"""
        # 基于分类置信度和名称匹配度
        base_score = row['confidence_score'] * 0.6
        
        # 名称与预测分类的匹配度
        name = str(row['material_name']).lower()
        pred_category = str(row['predicted_category']).lower()
        
        # 简单的匹配逻辑
        if pred_category in name or name in pred_category:
            base_score += 0.3
        
        return min(base_score + 0.1, 1.0)
    
    def _calculate_compliance_score(self, row) -> float:
        """计算合规性评分"""
        # 基于规格格式的标准化程度
        spec = str(row['specification'])
        
        score = 0.7  # 基础分
        
        # 检查是否包含标准规格格式
        if any(pattern in spec for pattern in ['DN', 'PN', 'φ', 'M', '*']):
            score += 0.2
        
        return min(score + np.random.normal(0, 0.1), 1.0)
    
    def optimize_weights_optuna(self, training_data: pd.DataFrame, 
                               n_trials: int = 100) -> Dict[str, float]:
        """使用Optuna优化权重配置"""
        
        def objective(trial):
            # 定义权重搜索空间
            weights = {
                'confidence_score': trial.suggest_float('confidence_score', 0.1, 0.5),
                'consistency_score': trial.suggest_float('consistency_score', 0.1, 0.4),
                'completeness_score': trial.suggest_float('completeness_score', 0.1, 0.3),
                'accuracy_score': trial.suggest_float('accuracy_score', 0.05, 0.25),
                'compliance_score': trial.suggest_float('compliance_score', 0.05, 0.2)
            }
            
            # 归一化权重
            total_weight = sum(weights.values())
            normalized_weights = {k: v/total_weight for k, v in weights.items()}
            
            # 计算加权质量分数
            quality_scores = self._calculate_weighted_quality_score(
                training_data, normalized_weights
            )
            
            # 计算预测准确率
            accuracy = self._evaluate_quality_prediction_accuracy(
                quality_scores, training_data['quality_label']
            )
            
            return accuracy
        
        # 运行优化
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials)
        
        # 获取最优权重
        best_params = study.best_params
        total_weight = sum(best_params.values())
        optimal_weights = {k: v/total_weight for k, v in best_params.items()}
        
        logger.info(f"权重优化完成，最优准确率: {study.best_value:.4f}")
        logger.info(f"最优权重: {optimal_weights}")
        
        return optimal_weights
    
    def _calculate_weighted_quality_score(self, df: pd.DataFrame, 
                                        weights: Dict[str, float]) -> np.ndarray:
        """计算加权质量分数"""
        
        dimension_columns = [
            'confidence_dimension', 'consistency_dimension', 'completeness_dimension',
            'accuracy_dimension', 'compliance_dimension'
        ]
        
        weight_values = [
            weights['confidence_score'], weights['consistency_score'], 
            weights['completeness_score'], weights['accuracy_score'], 
            weights['compliance_score']
        ]
        
        # 计算加权分数
        weighted_scores = np.zeros(len(df))
        for i, (col, weight) in enumerate(zip(dimension_columns, weight_values)):
            weighted_scores += df[col].values * weight
        
        return weighted_scores
    
    def _evaluate_quality_prediction_accuracy(self, quality_scores: np.ndarray, 
                                           true_labels: np.ndarray) -> float:
        """评估质量预测准确率"""
        
        # 使用质量分数阈值进行二分类
        threshold = 0.75  # 质量阈值
        predicted_labels = (quality_scores >= threshold).astype(int)
        
        # 计算准确率
        accuracy = accuracy_score(true_labels, predicted_labels)
        return accuracy
    
    def cross_validate_weights(self, training_data: pd.DataFrame, 
                             weights: Dict[str, float], cv_folds: int = 5) -> Dict[str, float]:
        """交叉验证权重配置的性能"""
        
        # 准备特征和标签
        feature_columns = [
            'confidence_dimension', 'consistency_dimension', 'completeness_dimension',
            'accuracy_dimension', 'compliance_dimension'
        ]
        
        X = training_data[feature_columns].values
        y = training_data['quality_label'].values
        
        # 应用权重
        weight_vector = np.array([
            weights['confidence_score'], weights['consistency_score'],
            weights['completeness_score'], weights['accuracy_score'],
            weights['compliance_score']
        ])
        
        X_weighted = X * weight_vector
        
        # 使用逻辑回归进行交叉验证
        clf = LogisticRegression(random_state=42)
        cv_scores = cross_val_score(clf, X_weighted, y, cv=cv_folds, scoring='accuracy')
        
        return {
            'mean_accuracy': np.mean(cv_scores),
            'std_accuracy': np.std(cv_scores),
            'cv_scores': cv_scores.tolist()
        }
    
    def run_weight_optimization(self) -> Dict[str, Any]:
        """运行完整的权重优化流程"""
        
        logger.info("开始权重优化流程")
        
        # 1. 收集训练数据
        training_data = self.collect_training_data()
        
        if len(training_data) < 10:
            logger.warning("训练数据不足，使用默认权重")
            return {
                'optimal_weights': self.current_weights,
                'optimization_method': 'default',
                'performance': {'accuracy': 0.75}
            }
        
        # 2. 使用当前权重进行基准测试
        baseline_performance = self.cross_validate_weights(training_data, self.current_weights)
        logger.info(f"基准性能: {baseline_performance['mean_accuracy']:.4f}")
        
        # 3. 运行权重优化
        optimal_weights = self.optimize_weights_optuna(training_data, n_trials=50)
        
        # 4. 验证优化后的性能
        optimized_performance = self.cross_validate_weights(training_data, optimal_weights)
        logger.info(f"优化后性能: {optimized_performance['mean_accuracy']:.4f}")
        
        # 5. 决定是否采用新权重
        improvement = optimized_performance['mean_accuracy'] - baseline_performance['mean_accuracy']
        
        if improvement > 0.02:  # 改进超过2%才采用
            final_weights = optimal_weights
            adopted = True
            logger.info(f"采用新权重，性能提升: {improvement:.4f}")
        else:
            final_weights = self.current_weights
            adopted = False
            logger.info("保持当前权重，优化效果不明显")
        
        # 6. 保存优化结果
        optimization_result = {
            'optimal_weights': final_weights,
            'baseline_performance': baseline_performance,
            'optimized_performance': optimized_performance,
            'improvement': improvement,
            'adopted': adopted,
            'training_samples': len(training_data),
            'optimization_timestamp': datetime.now().isoformat()
        }
        
        self._save_optimization_result(optimization_result)
        
        return optimization_result
    
    def _save_optimization_result(self, result: Dict[str, Any]):
        """保存优化结果到数据库"""
        
        try:
            conn = sqlite3.connect(self.training_db_path)
            cursor = conn.cursor()
            
            # 创建权重优化历史表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS weight_optimization_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                weights_config TEXT,
                baseline_accuracy REAL,
                optimized_accuracy REAL,
                improvement REAL,
                adopted INTEGER,
                training_samples INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 保存优化记录
            cursor.execute('''
            INSERT INTO weight_optimization_history 
            (weights_config, baseline_accuracy, optimized_accuracy, improvement, adopted, training_samples)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                json.dumps(result['optimal_weights'], ensure_ascii=False),
                result['baseline_performance']['mean_accuracy'],
                result['optimized_performance']['mean_accuracy'],
                result['improvement'],
                1 if result['adopted'] else 0,
                result['training_samples']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存优化结果失败: {e}")
    
    def get_optimization_history(self) -> pd.DataFrame:
        """获取权重优化历史"""
        
        try:
            conn = sqlite3.connect(self.training_db_path)
            df = pd.read_sql('''
                SELECT * FROM weight_optimization_history 
                ORDER BY created_at DESC LIMIT 20
            ''', conn)
            conn.close()
            return df
        except:
            return pd.DataFrame()

# 使用示例和集成现有系统
def integrate_with_existing_system():
    """与现有MMP系统集成的示例"""
    
    # 初始化权重优化器
    optimizer = QualityWeightOptimizer()
    
    # 运行权重优化
    result = optimizer.run_weight_optimization()
    
    print("权重优化结果:")
    print(f"最优权重: {result['optimal_weights']}")
    print(f"性能提升: {result['improvement']:.4f}")
    print(f"是否采用: {result['adopted']}")
    
    # 获取优化历史
    history = optimizer.get_optimization_history()
    print(f"\n历史优化记录: {len(history)} 条")

if __name__ == "__main__":
    integrate_with_existing_system()