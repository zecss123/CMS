# -*- coding: utf-8 -*-
"""
环境变量加载器 - 支持从.env文件加载配置
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class EnvLoader:
    """
    环境变量加载器
    支持从.env文件和系统环境变量加载配置
    """
    
    def __init__(self, env_file: str = ".env"):
        """
        初始化环境变量加载器
        
        Args:
            env_file: .env文件路径
        """
        self.env_file = Path(env_file)
        self.env_vars = {}
        
        # 加载.env文件
        if self.env_file.exists():
            self._load_env_file()
            logger.info(f"已加载环境变量文件: {self.env_file}")
        else:
            logger.info(f"环境变量文件不存在: {self.env_file}，将使用系统环境变量")
    
    def _load_env_file(self) -> None:
        """
        从.env文件加载环境变量
        """
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析键值对
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 移除引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        self.env_vars[key] = value
                        # 同时设置到系统环境变量
                        os.environ[key] = value
                    else:
                        logger.warning(f"环境变量文件第{line_num}行格式错误: {line}")
        
        except Exception as e:
            logger.error(f"加载环境变量文件失败: {e}")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取环境变量值
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            环境变量值
        """
        # 优先从系统环境变量获取
        value = os.environ.get(key)
        if value is not None:
            return value
        
        # 然后从.env文件获取
        value = self.env_vars.get(key)
        if value is not None:
            return value
        
        return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        获取布尔类型环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            布尔值
        """
        value = self.get(key)
        if value is None:
            return default
        
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        获取整数类型环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            整数值
        """
        value = self.get(key)
        if value is None:
            return default
        
        try:
            return int(value)
        except ValueError:
            logger.warning(f"环境变量 {key} 不是有效的整数: {value}，使用默认值: {default}")
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        获取浮点数类型环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            浮点数值
        """
        value = self.get(key)
        if value is None:
            return default
        
        try:
            return float(value)
        except ValueError:
            logger.warning(f"环境变量 {key} 不是有效的浮点数: {value}，使用默认值: {default}")
            return default
    
    def update_config_from_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用环境变量更新配置字典
        
        Args:
            config: 原始配置字典
            
        Returns:
            更新后的配置字典
        """
        updated_config = config.copy()
        
        # LLM配置更新
        if 'model' in updated_config:
            model_config = updated_config['model']
            
            # OpenAI配置
            if 'openai' in model_config:
                openai_config = model_config['openai']
                openai_config['api_key'] = self.get('OPENAI_API_KEY', openai_config.get('api_key'))
                openai_config['base_url'] = self.get('OPENAI_BASE_URL', openai_config.get('base_url'))
                openai_config['model_name'] = self.get('OPENAI_MODEL', openai_config.get('model_name'))
            
            # DeepSeek配置
            if 'deepseek_api' in model_config:
                deepseek_config = model_config['deepseek_api']
                deepseek_config['api_key'] = self.get('DEEPSEEK_API_KEY', deepseek_config.get('api_key'))
                deepseek_config['base_url'] = self.get('DEEPSEEK_BASE_URL', deepseek_config.get('base_url'))
                deepseek_config['model_name'] = self.get('DEEPSEEK_MODEL', deepseek_config.get('model_name'))
            
            # 本地模型配置
            if 'local' in model_config:
                local_config = model_config['local']
                local_config['model_path'] = self.get('LOCAL_MODEL_PATH', local_config.get('model_path'))
                local_config['device'] = self.get('LOCAL_MODEL_DEVICE', local_config.get('device'))
        
        # 数据库配置更新
        if 'database' in updated_config:
            db_config = updated_config['database']
            
            # PostgreSQL配置
            if 'postgresql' in db_config:
                pg_config = db_config['postgresql']
                pg_config['host'] = self.get('POSTGRES_HOST', pg_config.get('host'))
                pg_config['port'] = self.get_int('POSTGRES_PORT', pg_config.get('port', 5432))
                pg_config['database'] = self.get('POSTGRES_DB', pg_config.get('database'))
                pg_config['username'] = self.get('POSTGRES_USER', pg_config.get('username'))
                pg_config['password'] = self.get('POSTGRES_PASSWORD', pg_config.get('password'))
            
            # SQLite配置
            if 'sqlite' in db_config:
                sqlite_config = db_config['sqlite']
                sqlite_config['path'] = self.get('SQLITE_PATH', sqlite_config.get('path'))
        
        # 外部API配置更新
        if 'external_api' in updated_config:
            api_config = updated_config['external_api']
            
            # CMS API配置
            if 'cms_api' in api_config:
                cms_config = api_config['cms_api']
                cms_config['base_url'] = self.get('CMS_API_BASE_URL', cms_config.get('base_url'))
                cms_config['api_key'] = self.get('CMS_API_KEY', cms_config.get('api_key'))
                cms_config['timeout'] = self.get_int('CMS_API_TIMEOUT', cms_config.get('timeout', 30))
        
        # 系统配置更新
        if 'system' in updated_config:
            sys_config = updated_config['system']
            sys_config['project_root'] = self.get('PROJECT_ROOT', sys_config.get('project_root'))
            sys_config['data_dir'] = self.get('DATA_DIR', sys_config.get('data_dir'))
            sys_config['output_dir'] = self.get('OUTPUT_DIR', sys_config.get('output_dir'))
            
            # 日志配置
            if 'logging' in sys_config:
                log_config = sys_config['logging']
                log_config['level'] = self.get('LOG_LEVEL', log_config.get('level'))
            
            # 缓存配置
            if 'cache' in sys_config:
                cache_config = sys_config['cache']
                cache_config['type'] = self.get('CACHE_TYPE', cache_config.get('type'))
                cache_config['ttl'] = self.get_int('CACHE_TTL', cache_config.get('ttl', 3600))
            
            # Redis配置
            if 'redis' in sys_config:
                redis_config = sys_config['redis']
                redis_config['host'] = self.get('REDIS_HOST', redis_config.get('host'))
                redis_config['port'] = self.get_int('REDIS_PORT', redis_config.get('port', 6379))
                redis_config['db'] = self.get_int('REDIS_DB', redis_config.get('db', 0))
                redis_config['password'] = self.get('REDIS_PASSWORD', redis_config.get('password'))
        
        # Streamlit配置更新
        if 'streamlit' in updated_config:
            st_config = updated_config['streamlit']
            if 'server' in st_config:
                server_config = st_config['server']
                server_config['port'] = self.get_int('STREAMLIT_PORT', server_config.get('port', 8501))
                server_config['host'] = self.get('STREAMLIT_HOST', server_config.get('host'))
        
        # 开发配置更新
        if 'development' in updated_config:
            dev_config = updated_config['development']
            dev_config['debug'] = self.get_bool('DEBUG', dev_config.get('debug', False))
            dev_config['use_mock_data'] = self.get_bool('USE_MOCK_DATA', dev_config.get('use_mock_data', False))
        
        return updated_config
    
    def list_env_vars(self) -> Dict[str, str]:
        """
        列出所有已加载的环境变量
        
        Returns:
            环境变量字典
        """
        return self.env_vars.copy()


# 全局环境变量加载器实例
env_loader = EnvLoader()


def load_env_config(config: Dict[str, Any], env_file: str = ".env") -> Dict[str, Any]:
    """
    便捷函数：使用环境变量更新配置
    
    Args:
        config: 原始配置字典
        env_file: .env文件路径
        
    Returns:
        更新后的配置字典
    """
    loader = EnvLoader(env_file)
    return loader.update_config_from_env(config)


if __name__ == "__main__":
    # 测试环境变量加载器
    print("=== 环境变量加载器测试 ===")
    
    loader = EnvLoader(".env.example")
    
    # 测试获取环境变量
    print(f"OPENAI_API_KEY: {loader.get('OPENAI_API_KEY', 'Not found')}")
    print(f"DEBUG: {loader.get_bool('DEBUG')}")
    print(f"STREAMLIT_PORT: {loader.get_int('STREAMLIT_PORT', 8501)}")
    
    # 测试配置更新
    test_config = {
        'model': {
            'openai': {
                'api_key': 'old-key',
                'model_name': 'gpt-3.5-turbo'
            }
        },
        'development': {
            'debug': False
        }
    }
    
    updated_config = loader.update_config_from_env(test_config)
    print(f"\n更新后的配置: {updated_config}")