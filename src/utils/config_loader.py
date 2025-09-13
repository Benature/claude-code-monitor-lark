#!/usr/bin/env python3
"""
配置加载工具模块
仅支持YAML格式的配置文件
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union


class ConfigLoader:
    """配置加载器，仅支持YAML格式"""
    
    @staticmethod
    def load_config(config_file: Union[str, Path]) -> Dict[str, Any]:
        """
        加载YAML配置文件
        
        Args:
            config_file: YAML配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置文件格式错误
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        # 检查文件扩展名
        if config_path.suffix.lower() not in ['.yaml', '.yml']:
            raise ValueError(f"配置文件必须是YAML格式 (.yaml 或 .yml): {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            return yaml.safe_load(content)
                        
        except yaml.YAMLError as e:
            raise ValueError(f"YAML配置文件格式错误: {e}")
        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            raise ValueError(f"读取配置文件时发生错误: {e}")
    
    @staticmethod
    def get_nested_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        获取嵌套配置值，支持点号分隔的键路径
        
        Args:
            config: 配置字典
            key_path: 键路径，如 'api.claude.bearer_token'
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key_path.split('.')
        current = config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    


class ConfigManager:
    """配置管理器，提供统一的配置访问接口"""
    
    def __init__(self, config_file: Union[str, Path]):
        """
        初始化配置管理器
        
        Args:
            config_file: YAML配置文件路径
        """
        self.config_file = Path(config_file)
        self._config = None
        self.load()
    
    def load(self):
        """加载YAML配置"""
        self._config = ConfigLoader.load_config(self.config_file)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径
            default: 默认值
            
        Returns:
            配置值
        """
        return ConfigLoader.get_nested_value(self._config, key_path, default)
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self._config.get('api', {})
    
    def get_notification_config(self) -> Dict[str, Any]:
        """获取通知配置"""
        return self._config.get('notification', {})
    
    def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return self._config.get('server', {})
    


def create_config_manager(config_file: str = 'config.yaml') -> ConfigManager:
    """
    创建配置管理器的便捷函数
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        ConfigManager实例
    """
    return ConfigManager(config_file)