# 需求配置文件
# enhanced_config.py

# 基础配置（保持兼容）
MASTER_DATA_PATH = 'data/e4p9.xlsx - Sheet1.csv'
NEW_DATA_PATH = 'data/e4.xlsx - Sheet1.csv'
OUTPUT_RESULT_PATH = 'data/batch_matching_results.csv'

# 基础匹配规则 - 修正为实际数据库字段
MATCH_RULES = {
    'master_fields': {
        'id': 'material_code',
        'exact': ['brand', 'model'],  # 使用实际存在的字段
        'fuzzy': ['material_name', 'specification']  # 使用实际存在的字段
    },
    'new_item_fields': {
        'id': '资产代码',
        'exact': ['生产厂家名称', '型号'],  # 映射到实际字段
        'fuzzy': ['资产名称', '规格型号']
    }
}

# ===== 新增功能配置 =====

# 1. 数据源配置
DATA_SOURCES = {
    'file': {
        'enabled': True,
        'supported_formats': ['.xlsx', '.xls', '.csv', '.json', '.parquet'],
        'encoding': 'utf-8-sig',
        'default_separator': ',',
        'max_file_size': '100MB'
    },
    'database': {
        'enabled': True,
        'supported_types': ['mysql', 'postgresql', 'sqlite', 'oracle', 'mongodb'],
        'connection_pool_size': 10,
        'connection_timeout': 30,
        'query_timeout': 300
    },
    'ocr': {
        'enabled': False,  # 需要安装PaddleOCR
        'supported_formats': ['.jpg', '.png', '.pdf'],
        'confidence_threshold': 0.8
    },
    'api': {
        'enabled': True,
        'timeout': 30,
        'retry_count': 3,
        'rate_limit': 100  # 每分钟请求数
    }
}

# 2. 数据库连接配置
DATABASE_CONNECTIONS = {
    # 主数据库配置
    'master_db': {
        'type': 'postgresql',  # mysql, postgresql, sqlite, oracle, mongodb
        'host': 'localhost',
        'port': 5432,
        'database': 'material_master_db',
        'username': 'material_user',
        'password': 'your_password',
        'driver': 'psycopg2',  # mysql: pymysql, postgresql: psycopg2
        'params': {
            'sslmode': 'prefer',
            'connect_timeout': 10
        },
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'echo': False  # 是否显示SQL日志
    },
    
    # 业务数据库配置（用于新数据）
    'business_db': {
        'type': 'mysql',
        'host': 'localhost',
        'port': 3306,
        'database': 'business_system_db',
        'username': 'business_user',
        'password': 'your_password',
        'driver': 'pymysql',
        'params': {
            'charset': 'utf8mb4',
            'autocommit': True
        },
        'pool_size': 5,
        'max_overflow': 10
    },
    
    # 结果存储数据库
    'result_db': {
        'type': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'database': 'matching_results_db',
        'username': 'result_user',
        'password': 'your_password',
        'driver': 'psycopg2'
    },
    
    # MongoDB配置示例（用于存储非结构化数据）
    'mongo_db': {
        'type': 'mongodb',
        'host': 'localhost',
        'port': 27017,
        'database': 'material_documents',
        'username': 'mongo_user',
        'password': 'your_password',
        'timeout': 5000
    }
}

# 3. 数据加载配置
DATA_LOADING_CONFIGS = {
    # 主数据加载配置
    'master_data': {
        'source_type': 'database',  # file, database, api
        'connection': 'master_db',  # 引用DATABASE_CONNECTIONS中的配置
        'query': {
            'type': 'table',  # table, custom_query
            'table_name': 'material_master',
            'conditions': {
                'status': 'active',
                'deleted_at': None
            }
        },
        'filters': {
            'columns': ['id', 'product_name', 'specification', 'manufacturer', 'approval_number'],
            'drop_duplicates': True,
            'sort_by': {'column': 'updated_at', 'ascending': False}
        },
        'cache': {
            'enabled': True,
            'ttl': 3600,  # 缓存1小时
            'key_prefix': 'master_data'
        }
    },
    
    # 新数据加载配置
    'new_data': {
        'source_type': 'database',
        'connection': 'business_db',
        'query': {
            'type': 'custom_query',
            'query': """
                SELECT 
                    asset_code,
                    asset_name,
                    specification,
                    manufacturer_name,
                    medical_code,
                    created_at
                FROM pending_materials 
                WHERE status = 'pending' 
                AND created_at >= :start_date
                ORDER BY created_at DESC
            """,
            'params': {
                'start_date': '2024-01-01'
            }
        },
        'filters': {
            'limit': 10000  # 限制处理数量
        }
    },
    
    # 文件数据源配置示例
    'file_data': {
        'source_type': 'file',
        'path': 'data/materials.xlsx',
        'type': 'excel',
        'sheet_name': 'Materials',
        'encoding': 'utf-8',
        'filters': {
            'columns': ['name', 'spec', 'brand', 'code'],
            'conditions': [
                {'column': 'status', 'operator': '==', 'value': 'active'}
            ],
            'drop_duplicates': True
        }
    },
    
    # API数据源配置示例
    'api_data': {
        'source_type': 'api',
        'url': 'https://api.material-system.com/materials',
        'method': 'GET',
        'headers': {
            'Authorization': 'Bearer your_api_token',
            'Content-Type': 'application/json'
        },
        'params': {
            'status': 'active',
            'limit': 1000
        },
        'data_key': 'data',  # 响应数据中的数据字段
        'timeout': 30
    }
}

# 4. 数据保存配置
DATA_SAVING_CONFIGS = {
    # 匹配结果保存到数据库
    'database_results': {
        'type': 'database',
        'connection': 'result_db',
        'save': {
            'table_name': 'matching_results',
            'if_exists': 'append'  # append, replace, fail
        }
    },
    
    # 保存到文件
    'file_results': {
        'type': 'file',
        'path': 'data/results/matching_results_{timestamp}.csv',
        'format': 'csv',
        'encoding': 'utf-8-sig'
    },
    
    # 保存到Excel
    'excel_results': {
        'type': 'file',
        'path': 'data/results/matching_results_{timestamp}.xlsx',
        'format': 'excel',
        'sheet_name': 'MatchingResults'
    }
}

# 2. 文本处理配置
TEXT_PROCESSING = {
    'chinese_segmentation': {
        'enabled': True,
        'tool': 'jieba',  # 可选: jieba, pkuseg, thulac
        'custom_dict': 'data/custom_dict.txt'
    },
    'parameter_extraction': {
        'enabled': True,
        'extract_brand': True,
        'extract_specification': True,
        'extract_model': True,
        'extract_material': True,
        'extract_usage': True
    },
    'normalization': {
        'enabled': True,
        'standardize_units': True,
        'remove_stopwords': True,
        'convert_traditional': True  # 繁体转简体
    }
}

# 3. 分类推荐配置
CATEGORY_RECOMMENDATION = {
    'api_endpoint': 'http://data-platform-api/categories',
    'recommendation_strategy': 'hybrid',  # rule_based, ml_based, hybrid
    'confidence_threshold': 0.6,
    'max_recommendations': 5,
    'fallback_to_parent': True,
    
    # 规则推荐配置
    'rule_based': {
        'medical_keywords': {
            '药品-注射剂': ['注射液', '注射用', '静脉注射'],
            '药品-口服剂': ['胶囊', '片剂', '颗粒', '口服液'],
            '医疗器械-监护设备': ['监护仪', '心电图', '血压计'],
            '医疗器械-治疗设备': ['呼吸机', '除颤器', '输液泵'],
            '检验试剂': ['试剂盒', '检测卡', '标准品'],
            '医用耗材': ['导管', '导丝', '缝合线', '敷料']
        },
        'industrial_keywords': {
            '电气设备-低压电器': ['开关', '接触器', '断路器'],
            '电气设备-电机': ['电机', '马达', '发电机'],
            '机械设备-泵阀': ['水泵', '油泵', '阀门', '调节阀'],
            '仪器仪表-检测仪表': ['压力表', '温度计', '流量计'],
            '五金工具-紧固件': ['螺丝', '螺母', '垫片', '弹簧']
        }
    },
    
    # 机器学习推荐配置
    'ml_based': {
        'model_type': 'naive_bayes',  # naive_bayes, svm, bert
        'training_data_path': 'data/category_training.csv',
        'model_save_path': 'models/category_classifier.pkl',
        'retrain_interval': 30  # 天
    }
}

# 4. 特征模型配置
FEATURE_MODELS = {
    'storage_type': 'database',  # file, database, api
    'database_config': {
        'host': 'localhost',
        'port': 5432,
        'database': 'material_db',
        'username': 'material_user',
        'password': 'material_pass'
    },
    
    # 示例特征模型
    'models': {
        '药品-注射剂': {
            'fields': [
                {'name': 'generic_name', 'type': 'text', 'required': True, 'label': '通用名'},
                {'name': 'strength', 'type': 'text', 'required': True, 'label': '规格'},
                {'name': 'dosage_form', 'type': 'enum', 'required': True, 'label': '剂型',
                 'options': ['注射液', '冻干粉针', '注射用无菌粉末']},
                {'name': 'manufacturer', 'type': 'text', 'required': True, 'label': '生产厂家'},
                {'name': 'approval_number', 'type': 'text', 'required': True, 'label': '批准文号'},
                {'name': 'package_spec', 'type': 'text', 'required': False, 'label': '包装规格'}
            ],
            'strict_fields': ['manufacturer', 'approval_number'],
            'fuzzy_fields': ['generic_name', 'strength'],
            'field_weights': {
                'generic_name': 0.4,
                'strength': 0.3,
                'manufacturer': 0.2,
                'approval_number': 0.1
            }
        },
        '医疗器械-监护设备': {
            'fields': [
                {'name': 'product_name', 'type': 'text', 'required': True, 'label': '产品名称'},
                {'name': 'model', 'type': 'text', 'required': True, 'label': '型号'},
                {'name': 'manufacturer', 'type': 'text', 'required': True, 'label': '制造商'},
                {'name': 'registration_number', 'type': 'text', 'required': True, 'label': '注册证号'},
                {'name': 'technical_specs', 'type': 'text', 'required': False, 'label': '技术参数'}
            ],
            'strict_fields': ['manufacturer', 'registration_number'],
            'fuzzy_fields': ['product_name', 'model', 'technical_specs'],
            'field_weights': {
                'product_name': 0.35,
                'model': 0.25,
                'manufacturer': 0.25,
                'technical_specs': 0.15
            }
        }
    }
}

# 5. 高级匹配配置
ADVANCED_MATCHING = {
    'similarity_threshold': 0.3,
    'max_candidates': 1000,  # 精确匹配后的最大候选数
    'top_n_results': 5,
    
    # 字段权重配置
    'field_weights': {
        'exact_match': 1.0,      # 精确匹配字段权重
        'fuzzy_match': 0.8,      # 模糊匹配字段权重
        'description_match': 0.6  # 描述匹配权重
    },
    
    # 描述拼接模板
    'description_templates': {
        'default': '{name} {specification} {manufacturer}',
        '药品': '{generic_name} {strength} {manufacturer}',
        '医疗器械': '{product_name} {model} {manufacturer}',
        '工业品': '{product_name} {specification} {brand}'
    },
    
    # 相似度计算配置
    'similarity_config': {
        'algorithm': 'cosine',  # cosine, jaccard, edit_distance
        'tfidf_config': {
            'max_features': 1000,
            'ngram_range': [1, 2],
            'min_df': 1,
            'max_df': 0.8
        },
        'custom_similarity_functions': {
            'specification': 'spec_similarity',
            'model': 'model_similarity'
        }
    },
    
    # 匹配策略配置
    'matching_strategy': {
        'multi_field_matching': True,
        'weighted_combination': True,
        'attribute_level_matching': True,
        'description_fallback': True
    }
}

# 6. 决策支持配置
DECISION_SUPPORT = {
    'confidence_thresholds': {
        'auto_update': 0.95,      # 自动更新阈值
        'manual_review': 0.7,     # 人工审核阈值
        'create_new': 0.3         # 创建新物料阈值
    },
    
    'decision_rules': {
        'prefer_exact_match': True,
        'consider_business_rules': True,
        'enable_user_feedback': True
    },
    
    'review_workflow': {
        'enabled': True,
        'api_endpoint': 'http://workflow-api/approvals',
        'default_reviewers': ['material_admin'],
        'auto_approve_threshold': 0.98
    }
}

# 7. 批量清洗配置
BATCH_CLEANING = {
    'enabled': True,
    'chunk_size': 1000,  # 分批处理大小
    'parallel_processing': True,
    'max_workers': 4,
    
    'cleaning_rules': {
        'remove_duplicates': True,
        'fix_encoding_issues': True,
        'standardize_formats': True,
        'validate_required_fields': True,
        'normalize_values': True
    },
    
    'quality_checks': {
        'completeness_check': True,
        'consistency_check': True,
        'validity_check': True,
        'accuracy_check': False  # 需要外部标准库
    },
    
    'external_validation': {
        'enabled': False,  # 长期功能
        'drug_authority_api': 'http://nmpa-api/drugs',
        'supplier_database': 'http://supplier-api/validate'
    }
}

# 8. 性能监控配置
PERFORMANCE_MONITORING = {
    'enabled': True,
    'metrics_collection': {
        'processing_time': True,
        'accuracy_metrics': True,
        'user_satisfaction': True,
        'system_resource_usage': True
    },
    
    'alert_thresholds': {
        'processing_time': 5.0,  # 秒
        'accuracy_drop': 0.1,    # 准确率下降阈值
        'memory_usage': 0.8      # 内存使用率
    },
    
    'reporting': {
        'daily_summary': True,
        'weekly_analysis': True,
        'export_format': 'excel'
    }
}

# 9. API配置增强
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False,
    'threaded': True,
    
    'rate_limiting': {
        'enabled': True,
        'requests_per_minute': 100,
        'burst_limit': 200
    },
    
    'authentication': {
        'enabled': False,  # 生产环境建议启用
        'method': 'api_key',  # api_key, jwt, oauth2
        'api_key_header': 'X-API-Key'
    },
    
    'cors': {
        'enabled': True,
        'origins': ['*'],  # 生产环境应限制具体域名
        'methods': ['GET', 'POST', 'PUT', 'DELETE']
    },
    
    'response_format': {
        'include_metadata': True,
        'include_debug_info': False,
        'max_response_size': '10MB'
    }
}

# 10. 日志配置增强
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': {
        'console': {
            'enabled': True,
            'level': 'INFO'
        },
        'file': {
            'enabled': True,
            'level': 'DEBUG',
            'filename': 'logs/mmp.log',
            'max_bytes': 10485760,  # 10MB
            'backup_count': 5,
            'rotation': 'time'  # time, size
        },
        'elasticsearch': {
            'enabled': False,
            'host': 'localhost:9200',
            'index': 'mmp-logs'
        }
    }
}

# 应用配置
LOG_LEVEL = LOGGING_CONFIG['level']
