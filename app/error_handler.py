# -*- coding: utf-8 -*-
"""
错误处理包装器 - 增强系统稳定性
"""

import logging
import traceback
from functools import wraps
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self):
        self.error_counts = {}
        self.max_retries = 3
        
    def safe_execute(self, func: Callable, *args, fallback=None, **kwargs) -> Any:
        """安全执行函数，带降级处理"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_key = f"{func.__name__}_{type(e).__name__}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            logger.error(f"函数执行失败: {func.__name__}, 错误: {e}")
            logger.debug(f"错误详情: {traceback.format_exc()}")
            
            if fallback is not None:
                logger.info(f"使用降级处理: {fallback}")
                if callable(fallback):
                    return fallback(*args, **kwargs)
                else:
                    return fallback
            
            raise

def safe_api(fallback_response=None):
    """API安全装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"API错误 {func.__name__}: {e}")
                if fallback_response:
                    return fallback_response
                else:
                    return {"error": f"操作失败: {str(e)}", "success": False}, 500
        return wrapper
    return decorator

def safe_length(obj, default=0):
    """安全获取对象长度"""
    try:
        if hasattr(obj, '__len__'):
            return len(obj)
        elif obj is not None:
            return 1
        else:
            return default
    except:
        return default

# 全局错误处理实例
error_handler = ErrorHandler()
