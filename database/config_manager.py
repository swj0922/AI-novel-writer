# -*- coding: utf-8 -*-
"""
配置管理模块
用于管理LLM监控功能和数据库连接等配置
"""
import os
import json
import logging
from typing import Dict, Any, Optional


class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = "llm_monitor_config.json"):
        self.config_file = config_file
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "llm_monitoring": {
                "enabled": True,
                "log_detailed_response": False
            },
            "database": {
                "host": "localhost",
                "port": 3306,
                "user": "root", 
                "password": "",
                "database": "novel_generator",
                "charset": "utf8mb4"
            },
            "logging": {
                "level": "INFO",
                "file": "llm_monitor.log"
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # 合并默认配置和加载的配置
                self._merge_config(default_config, loaded_config)
                return default_config
            except Exception as e:
                logging.warning(f"加载配置文件失败，使用默认配置: {e}")
                return default_config
        else:
            # 如果配置文件不存在，创建一个
            self._save_config(default_config)
            return default_config
    
    def _merge_config(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> None:
        """递归合并配置，如果llm_monitor_config.json中的配置与默认配置不同，
            则使用llm_monitor_config.json中的配置"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value
    
    def _save_config(self, config: Dict[str, Any] = None) -> None:
        """保存配置到文件"""
        config = config or self.config_data
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取config_data中的配置值，支持点分割的路径，如 'llm_monitoring.enabled'则返回True，
        如果配置文件中没有该配置项，则返回默认值default"""
        keys = key_path.split('.')
        value = self.config_data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """设置配置值，支持点分割的路径"""
        keys = key_path.split('.')
        config = self.config_data
        
        # 导航到最后一级的父字典
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置最后一级的值
        config[keys[-1]] = value
        self._save_config()
    
    def get_monitoring_enabled(self) -> bool:
        """获取监控开启状态"""
        return self.get('llm_monitoring.enabled', True)
    
    def set_monitoring_enabled(self, enabled: bool) -> None:
        """设置监控开启状态"""
        self.set('llm_monitoring.enabled', enabled)
        logging.info(f"LLM监控功能{'已开启' if enabled else '已关闭'}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.get('database', {})
    


# 全局配置实例
global_config = Config()


def set_monitoring_enabled(enabled: bool) -> None:
    """全局设置监控开启状态"""
    global_config.set_monitoring_enabled(enabled)
    
    # 同时更新监控器状态
    try:
        from database.llm_monitor import global_llm_monitor
        global_llm_monitor.set_enabled(enabled)
    except ImportError:
        logging.warning("无法导入llm_monitor模块")

