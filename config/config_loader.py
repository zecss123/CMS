# -*- coding: utf-8 -*-
"""
CMS振动分析系统配置加载器
统一管理所有配置项，支持YAML配置文件和环境变量覆盖
支持.env文件加载
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from loguru import logger

# 环境变量加载器
class FallbackEnvLoader:
    """备用环境变量加载器"""
    def __init__(self, env_file=None):
        pass
    def update_config_from_env(self, config):
        return config

try:
    from .env_loader import EnvLoader
    EnvLoaderClass = EnvLoader
except ImportError:
    EnvLoaderClass = FallbackEnvLoader

class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, config_file: Optional[str] = None, env_file: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_file: 配置文件路径，默认为项目根目录下的config.yaml
            env_file: 环境变量文件路径，默认为项目根目录下的.env
        """
        self.project_root = Path(__file__).parent.parent
        self.config_file = config_file or self.project_root / "config.yaml"
        self.env_file = env_file or self.project_root / ".env"
        self._config = None
        self.env_loader = EnvLoaderClass(str(self.env_file))
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if not Path(self.config_file).exists():
                logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
                self._config = self._get_default_config()
            else:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
                logger.info(f"配置文件加载成功: {self.config_file}")
            
            # 使用环境变量加载器更新配置
            self._config = self.env_loader.update_config_from_env(self._config)
            
            # 应用传统环境变量覆盖（向后兼容）
            self._apply_env_overrides()
            
            # 处理路径
            self._resolve_paths()
            
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            self._config = self._get_default_config()
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖配置"""
        env_mappings = {
            # 模型配置
            'CMS_MODEL_TYPE': 'model.type',
            'CMS_OPENAI_API_KEY': 'model.openai.api_key',
            'CMS_OPENAI_BASE_URL': 'model.openai.base_url',
            'CMS_LOCAL_MODEL_PATH': 'model.local.model_path',
            'CMS_DEEPSEEK_API_KEY': 'model.deepseek_api.api_key',
            'CMS_CUSTOM_API_KEY': 'model.custom.api_key',
            'CMS_CUSTOM_BASE_URL': 'model.custom.base_url',
            
            # 嵌入模型配置
            'CMS_EMBEDDING_TYPE': 'embedding.type',
            'CMS_EMBEDDING_MODEL': 'embedding.huggingface.model_name',
            'CMS_EMBEDDING_CACHE_DIR': 'embedding.huggingface.cache_dir',
            
            # 数据库配置
            'CMS_DB_TYPE': 'database.type',
            'CMS_DB_PATH': 'database.sqlite.path',
            'CMS_DB_HOST': 'database.postgresql.host',
            'CMS_DB_PASSWORD': 'database.postgresql.password',
            
            # 外部API配置
            'CMS_EXTERNAL_API_ENABLED': 'external_api.enabled',
            'CMS_CMS_API_KEY': 'external_api.cms_api.api_key',
            'CMS_CMS_API_URL': 'external_api.cms_api.base_url',
            
            # Streamlit配置
            'CMS_STREAMLIT_ENABLED': 'streamlit.enabled',
            'CMS_STREAMLIT_PORT': 'streamlit.server.port',
            'CMS_STREAMLIT_HOST': 'streamlit.server.host',
            
            # 系统配置
            'CMS_LOG_LEVEL': 'system.logging.level',
            'CMS_DEBUG': 'development.debug',
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config_path, env_value)
                logger.info(f"环境变量覆盖配置: {env_var} -> {config_path}")
    
    def _set_nested_value(self, path: str, value: Any):
        """设置嵌套字典的值"""
        if self._config is None:
            return
            
        keys = path.split('.')
        current = self._config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 转换值类型
        final_key = keys[-1]
        if isinstance(value, str):
            # 尝试转换布尔值
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            # 尝试转换数字
            elif value.isdigit():
                value = int(value)
            elif '.' in value and value.replace('.', '').isdigit():
                value = float(value)
        
        current[final_key] = value
    
    def _resolve_paths(self):
        """解析相对路径为绝对路径"""
        path_configs = [
            'model.local.model_path',
            'embedding.huggingface.cache_dir',
            'vector_db.persist_directory',
            'database.sqlite.path',
            'system.data_dir',
            'system.output_dir',
            'system.logging.log_file',
            'business.report.template_dir',
        ]
        
        for path_config in path_configs:
            value = self.get(path_config)
            if value and isinstance(value, str) and not os.path.isabs(value):
                absolute_path = self.project_root / value
                self._set_nested_value(path_config, str(absolute_path))
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'model': {
                'type': 'local',
                'local': {
                    'model_name': 'deepseek-7b',
                    'model_path': str(self.project_root / 'models' / 'deepseek-7b'),
                    'temperature': 0.7,
                    'device': 'auto'
                }
            },
            'embedding': {
                'type': 'huggingface',
                'huggingface': {
                    'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
                    'device': 'auto'
                }
            },
            'vector_db': {
                'persist_directory': str(self.project_root / 'data' / 'vector_db'),
                'collection_name': 'cms_vibration_knowledge'
            },
            'database': {
                'type': 'sqlite',
                'sqlite': {
                    'path': str(self.project_root / 'data' / 'cms_data.db')
                }
            },
            'streamlit': {
                'enabled': True,
                'server': {
                    'port': 8501,
                    'host': '0.0.0.0'
                }
            },
            'system': {
                'logging': {
                    'level': 'INFO'
                }
            },
            'development': {
                'debug': True,
                'use_mock_data': True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的嵌套键
        
        Args:
            key: 配置键，支持嵌套如 'model.openai.api_key'
            default: 默认值
        
        Returns:
            配置值
        """
        if self._config is None:
            return default
            
        keys = key.split('.')
        current = self._config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self._set_nested_value(key, value)
    
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        if self._config is None:
            return {}
            
        model_type = self.get('model.type', 'local')
        base_config = {
            'type': model_type,
            'temperature': self.get(f'model.{model_type}.temperature', 0.7),
            'max_tokens': self.get(f'model.{model_type}.max_tokens', 4096)
        }
        
        if model_type == 'openai':
            base_config.update({
                'api_key': self.get('model.openai.api_key'),
                'base_url': self.get('model.openai.base_url', 'https://api.openai.com/v1'),
                'model_name': self.get('model.openai.model_name', 'gpt-3.5-turbo')
            })
        elif model_type == 'local':
            base_config.update({
                'model_name': self.get('model.local.model_name', 'deepseek-7b'),
                'model_path': self.get('model.local.model_path'),
                'device': self.get('model.local.device', 'auto'),
                'load_in_8bit': self.get('model.local.load_in_8bit', False),
                'load_in_4bit': self.get('model.local.load_in_4bit', False)
            })
        elif model_type == 'deepseek_api':
            base_config.update({
                'api_key': self.get('model.deepseek_api.api_key'),
                'base_url': self.get('model.deepseek_api.base_url', 'https://api.deepseek.com/v1'),
                'model_name': self.get('model.deepseek_api.model_name', 'deepseek-chat')
            })
        elif model_type == 'custom':
            base_config.update({
                'api_key': self.get('model.custom.api_key'),
                'base_url': self.get('model.custom.base_url'),
                'model_name': self.get('model.custom.model_name'),
                'headers': self.get('model.custom.headers', {})
            })
        
        return base_config
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """获取嵌入模型配置"""
        embedding_type = self.get('embedding.type', 'huggingface')
        return {
            'type': embedding_type,
            **self.get(f'embedding.{embedding_type}', {})
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        if self._config is None:
            return {}
            
        db_type = self.get('database.type', 'sqlite')
        return {
            'type': db_type,
            **self.get(f'database.{db_type}', {})
        }
    
    def is_streamlit_enabled(self) -> bool:
        """检查是否启用Streamlit界面"""
        return self.get('streamlit.enabled', True)
    
    def is_external_api_enabled(self) -> bool:
        """检查是否启用外部API"""
        return self.get('external_api.enabled', False)
    
    def is_debug_mode(self) -> bool:
        """检查是否为调试模式"""
        return self.get('development.debug', False)
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.get('system.data_dir', './data'),
            self.get('system.output_dir', './output'),
            self.get('vector_db.persist_directory'),
            os.path.dirname(self.get('system.logging.log_file', './logs/cms_rag.log')),
            self.get('business.report.template_dir', './data/templates'),
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
                logger.debug(f"确保目录存在: {directory}")
    
    def save_config(self, file_path: Optional[str] = None):
        """保存配置到文件"""
        save_path = file_path or self.config_file
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置已保存到: {save_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def reload(self):
        """重新加载配置"""
        self._load_config()
        logger.info("配置已重新加载")
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        if self._config is None:
            return {}
        return self._config.copy()


# 全局配置实例
_config_loader = None

def get_config() -> ConfigLoader:
    """获取全局配置实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
        _config_loader.ensure_directories()
    return _config_loader

def reload_config():
    """重新加载全局配置"""
    global _config_loader
    if _config_loader is not None:
        _config_loader.reload()


if __name__ == "__main__":
    # 测试配置加载器
    config = get_config()
    print("模型配置:", config.get_model_config())
    print("嵌入配置:", config.get_embedding_config())
    print("数据库配置:", config.get_database_config())
    print("Streamlit启用:", config.is_streamlit_enabled())
    print("调试模式:", config.is_debug_mode())