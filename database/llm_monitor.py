# -*- coding: utf-8 -*-
"""
LLM调用监控装饰器
用于自动记录每次LLM调用的详细信息，包括token消耗、等待时间等
"""
import uuid
import time
import logging
import functools
from typing import Dict, Any, Optional, Callable
from .db_config import default_llm_logger, LLMCallLogger


class LLMMonitor:
    """LLM调用监控器"""
    
    def __init__(self, logger: Optional[LLMCallLogger] = None, enabled: bool = True):
        self.logger = logger or default_llm_logger
        self.enabled = enabled
        
    def set_enabled(self, enabled: bool):
        """设置监控开启状态"""
        self.enabled = enabled
        logging.info(f"LLM调用监控{'已开启' if enabled else '已关闭'}")
    
    def _parse_usage_from_response(self, response) -> Dict[str, int]:
        """从响应中解析usage信息"""
        usage_info = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'cached_tokens': 0
        }
        
        try:
            if hasattr(response, 'usage'):
                usage = response.usage
                usage_info['prompt_tokens'] = getattr(usage, 'prompt_tokens', 0)
                usage_info['completion_tokens'] = getattr(usage, 'completion_tokens', 0)
                usage_info['total_tokens'] = getattr(usage, 'total_tokens', 0)
                
                # 检查是否有缓存token信息
                if hasattr(usage, 'prompt_tokens_details'):
                    details = usage.prompt_tokens_details
                    usage_info['cached_tokens'] = getattr(details, 'cached_tokens', 0)
        except Exception as e:
            logging.warning(f"解析usage信息失败: {e}")
            
        return usage_info


# 全局监控器实例
global_llm_monitor = LLMMonitor()
