# app/workflow_service.py
import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime

# 导入基础模块
import config
from app.data_loader import load_csv_data, load_data_from_config, save_data_to_config
from app.preprocessor import recommend_category, extract_parameters
from app.matcher import MaterialMatcher

# 尝试导入增强功能
try:
    from app.advanced_preprocessor import AdvancedPreprocessor
    ADVANCED_PREPROCESSOR_AVAILABLE = True
except ImportError:
    ADVANCED_PREPROCESSOR_AVAILABLE = False
    logging.warning("高级预处理器不可用")

try:
    from app.advanced_matcher import AdvancedMaterialMatcher
    ADVANCED_MATCHER_AVAILABLE = True
except ImportError:
    ADVANCED_MATCHER_AVAILABLE = False
    logging.warning("高级匹配器不可用")

class MaterialWorkflowService:
    def __init__(self, service_config: Dict[str, Any] = None):
        """
        初始化服务，支持灵活的配置
        
        Args:
            service_config: 服务配置，如果为None则使用默认配置
        """
        self.service_config = service_config or self._get_default_config()
        self.rules = self.service_config.get('match_rules', config.MATCH_RULES)
        
        # 初始化数据和匹配器
        self._initialize_data()
        self._initialize_matcher()
        self._initialize_preprocessor()
        
        logging.info("物料工作流服务已初始化")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'match_rules': config.MATCH_RULES,
            'data_source': {
                'master_data': {
                    'source_type': 'file',
                    'path': config.MASTER_DATA_PATH
                },
                'use_enhanced_features': False,
                'use_database': False
            },
            'processing': {
                'use_advanced_preprocessor': ADVANCED_PREPROCESSOR_AVAILABLE,
                'use_advanced_matcher': ADVANCED_MATCHER_AVAILABLE,
                'batch_size': 1000,
                'enable_caching': True
            }
        }

    def _initialize_data(self):
        """初始化数据"""
        data_config = self.service_config.get('data_source', {})
        master_config = data_config.get('master_data', {})
        
        try:
            if master_config.get('source_type') == 'database':
                # 从数据库加载主数据
                self.df_master = load_data_from_config(master_config)
                logging.info("已从数据库加载主数据")
            else:
                # 从文件加载主数据（保持向后兼容）
                file_path = master_config.get('path', config.MASTER_DATA_PATH)
                self.df_master = load_csv_data(file_path)
                logging.info("已从文件加载主数据")
                
        except Exception as e:
            logging.error(f"主数据加载失败: {e}")
            self.df_master = pd.DataFrame()

    def _initialize_matcher(self):
        """初始化匹配器"""
        processing_config = self.service_config.get('processing', {})
        
        if processing_config.get('use_advanced_matcher', False) and ADVANCED_MATCHER_AVAILABLE:
            # 使用高级匹配器
            try:
                # 从配置获取高级匹配参数
                match_config = self.service_config.get('advanced_matching', {})
                self.matcher = AdvancedMaterialMatcher(self.df_master, self.rules, match_config)
                self.use_advanced_matcher = True
                logging.info("已启用高级匹配器")
            except Exception as e:
                logging.error(f"高级匹配器初始化失败，回退到基础匹配器: {e}")
                self.matcher = MaterialMatcher(self.df_master, self.rules)
                self.use_advanced_matcher = False
        else:
            # 使用基础匹配器
            self.matcher = MaterialMatcher(self.df_master, self.rules)
            self.use_advanced_matcher = False
            logging.info("已启用基础匹配器")

    def _initialize_preprocessor(self):
        """初始化预处理器"""
        processing_config = self.service_config.get('processing', {})
        
        if processing_config.get('use_advanced_preprocessor', False) and ADVANCED_PREPROCESSOR_AVAILABLE:
            try:
                self.preprocessor = AdvancedPreprocessor()
                self.use_advanced_preprocessor = True
                logging.info("已启用高级预处理器")
            except Exception as e:
                logging.error(f"高级预处理器初始化失败: {e}")
                self.preprocessor = None
                self.use_advanced_preprocessor = False
        else:
            self.preprocessor = None
            self.use_advanced_preprocessor = False

    def process_single_item(self, item_data: Union[Dict, pd.Series]) -> Dict[str, Any]:
        """
        处理单条物料数据的完整流程（用于API）
        
        Args:
            item_data: 物料数据
            
        Returns:
            处理结果字典
        """
        # 转换数据格式
        if isinstance(item_data, pd.Series):
            item_dict = item_data.to_dict()
        else:
            item_dict = dict(item_data)
        
        try:
            # 1. 预处理步骤
            if self.use_advanced_preprocessor:
                # 使用高级预处理器
                text_parts = []
                for field in self.rules['new_item_fields']['fuzzy']:
                    if field in item_dict:
                        text_parts.append(str(item_dict[field]))
                
                full_text = ' '.join(text_parts)
                extracted_params = self.preprocessor.extract_comprehensive_parameters(full_text)
                category_recommendations = self.preprocessor.recommend_category_advanced(full_text, extracted_params)
                
                category = category_recommendations[0][0] if category_recommendations else "未识别分类"
                params = {
                    'extracted_params': extracted_params,
                    'category_recommendations': category_recommendations
                }
            else:
                # 使用基础预处理器
                category = recommend_category(item_dict, self.rules['new_item_fields'])
                params = extract_parameters(item_dict)
            
            # 2. 核心匹配步骤
            if self.use_advanced_matcher:
                matches = self.matcher.find_matches_advanced(item_dict)
            else:
                matches = self.matcher.find_matches(item_dict)
            
            # 3. 组装结果
            result = {
                'input_data': item_dict,
                'recommended_category': category,
                'extracted_params': params,
                'matches': matches.to_dict('records') if not matches.empty else [],
                'processing_info': {
                    'timestamp': datetime.now().isoformat(),
                    'advanced_preprocessor': self.use_advanced_preprocessor,
                    'advanced_matcher': self.use_advanced_matcher,
                    'match_count': len(matches) if not matches.empty else 0
                }
            }
            
            return result
            
        except Exception as e:
            logging.error(f"处理单条物料数据失败: {e}")
            return {
                'input_data': item_dict,
                'error': str(e),
                'processing_info': {
                    'timestamp': datetime.now().isoformat(),
                    'status': 'failed'
                }
            }

    def process_batch(self, data_source: Union[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理批量的物料数据（支持多种数据源）
        
        Args:
            data_source: 数据源，可以是文件路径或数据配置字典
            
        Returns:
            处理结果列表
        """
        # 加载数据
        if isinstance(data_source, str):
            # 文件路径（保持向后兼容）
            df_new = load_csv_data(data_source)
        elif isinstance(data_source, dict):
            # 配置字典
            df_new = load_data_from_config(data_source)
        else:
            raise ValueError("数据源类型无效")
        
        if df_new.empty:
            logging.warning("没有数据需要处理")
            return []
        
        # 批量处理配置
        batch_size = self.service_config.get('processing', {}).get('batch_size', 1000)
        all_results = []
        
        # 分批处理
        for start_idx in range(0, len(df_new), batch_size):
            end_idx = min(start_idx + batch_size, len(df_new))
            batch_df = df_new.iloc[start_idx:end_idx]
            
            logging.info(f"处理批次 {start_idx//batch_size + 1}：第 {start_idx+1}-{end_idx} 条记录")
            
            batch_results = []
            for index, row in batch_df.iterrows():
                item_result = self.process_single_item(row.to_dict())
                batch_results.append(item_result)
            
            all_results.extend(batch_results)
        
        logging.info(f"批量处理完成，共处理 {len(all_results)} 条记录")
        return all_results

    def process_batch_from_database(self, db_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从数据库批量处理数据
        
        Args:
            db_config: 数据库配置
            
        Returns:
            处理结果列表
        """
        # 构建数据源配置
        data_source_config = {
            'source_type': 'database',
            'connection': db_config.get('connection'),
            'query': db_config.get('query'),
            'filters': db_config.get('filters', {})
        }
        
        return self.process_batch(data_source_config)

    def save_results(self, results: List[Dict[str, Any]], 
                    save_config: Dict[str, Any]) -> bool:
        """
        保存处理结果
        
        Args:
            results: 处理结果列表
            save_config: 保存配置
            
        Returns:
            是否保存成功
        """
        if not results:
            logging.warning("没有结果需要保存")
            return False
        
        try:
            # 转换结果为DataFrame
            results_df = self._convert_results_to_dataframe(results)
            
            # 添加时间戳到文件路径
            if save_config.get('type') == 'file' and '{timestamp}' in save_config.get('path', ''):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                save_config['path'] = save_config['path'].format(timestamp=timestamp)
            
            # 保存数据
            success = save_data_to_config(results_df, save_config)
            
            if success:
                logging.info(f"成功保存 {len(results)} 条结果")
            
            return success
            
        except Exception as e:
            logging.error(f"保存结果失败: {e}")
            return False

    def _convert_results_to_dataframe(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """将结果转换为DataFrame"""
        flattened_results = []
        
        for result in results:
            # 展平结果结构
            flat_result = {}
            
            # 输入数据
            input_data = result.get('input_data', {})
            for key, value in input_data.items():
                flat_result[f'input_{key}'] = value
            
            # 推荐分类
            flat_result['recommended_category'] = result.get('recommended_category')
            
            # 匹配结果
            matches = result.get('matches', [])
            if matches:
                best_match = matches[0]
                flat_result['best_match_similarity'] = best_match.get('similarity', 0)
                flat_result['best_match_id'] = best_match.get('id')
                flat_result['match_count'] = len(matches)
                
                # 最佳匹配的详细信息
                for key, value in best_match.items():
                    if key not in ['similarity', 'id']:
                        flat_result[f'best_match_{key}'] = value
            else:
                flat_result['best_match_similarity'] = 0
                flat_result['best_match_id'] = None
                flat_result['match_count'] = 0
            
            # 处理信息
            processing_info = result.get('processing_info', {})
            flat_result['processing_timestamp'] = processing_info.get('timestamp')
            flat_result['processing_status'] = 'success' if 'error' not in result else 'failed'
            flat_result['error_message'] = result.get('error')
            
            flattened_results.append(flat_result)
        
        return pd.DataFrame(flattened_results)

    def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            'master_data_count': len(self.df_master),
            'advanced_preprocessor_enabled': self.use_advanced_preprocessor,
            'advanced_matcher_enabled': self.use_advanced_matcher,
            'match_rules': self.rules,
            'service_config': self.service_config
        }

    def reload_master_data(self) -> bool:
        """重新加载主数据"""
        try:
            self._initialize_data()
            self._initialize_matcher()
            logging.info("主数据重新加载成功")
            return True
        except Exception as e:
            logging.error(f"主数据重新加载失败: {e}")
            return False