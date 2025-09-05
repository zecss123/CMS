# -*- coding: utf-8 -*-
"""
数据库管理器 - 处理数据库连接、初始化和基本操作
"""

import os
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from loguru import logger

from .models import Base


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: Optional[str] = None):
        """初始化数据库管理器
        
        Args:
            database_url: 数据库连接URL，如果为None则使用SQLite
        """
        self.database_url = database_url or self._get_default_database_url()
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._initialized = False
    
    def _get_default_database_url(self) -> str:
        """获取默认数据库URL"""
        # 使用项目根目录下的SQLite数据库
        db_path = os.path.join(os.getcwd(), 'data', 'cms_vibration.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f"sqlite:///{db_path}"
    
    def initialize(self) -> bool:
        """初始化数据库连接和表结构
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 创建数据库引擎
            if self.database_url.startswith('sqlite'):
                # SQLite特殊配置
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={
                        'check_same_thread': False,
                        'timeout': 20
                    },
                    echo=False  # 设置为True可以看到SQL语句
                )
            else:
                # 其他数据库
                self.engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            
            self._initialized = True
            logger.info(f"数据库初始化成功: {self.database_url}")
            return True
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            return False
    
    def get_session(self) -> Optional[Session]:
        """获取数据库会话
        
        Returns:
            Session: 数据库会话对象，失败时返回None
        """
        if not self._initialized:
            logger.warning("数据库未初始化，尝试自动初始化")
            if not self.initialize():
                return None
        
        try:
            if self.SessionLocal is not None:
                return self.SessionLocal()
            else:
                logger.error("SessionLocal未初始化")
                return None
        except Exception as e:
            logger.error(f"创建数据库会话失败: {e}")
            return None
    
    def close_session(self, session: Session) -> None:
        """关闭数据库会话
        
        Args:
            session: 要关闭的会话
        """
        try:
            if session:
                session.close()
        except Exception as e:
            logger.error(f"关闭数据库会话失败: {e}")
    
    def execute_raw_sql(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行原始SQL语句
        
        Args:
            sql: SQL语句
            params: 参数字典
            
        Returns:
            执行结果
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            result = session.execute(text(sql), params or {})
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"执行SQL失败: {sql}, 错误: {e}")
            return None
        finally:
            self.close_session(session)
    
    def test_connection(self) -> bool:
        """测试数据库连接
        
        Returns:
            bool: 连接是否正常
        """
        session = self.get_session()
        if not session:
            return False
        
        try:
            # 执行简单查询测试连接
            session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
        finally:
            self.close_session(session)
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息
        
        Returns:
            Dict: 数据库信息字典
        """
        info = {
            'database_url': self.database_url,
            'initialized': self._initialized,
            'engine_info': None,
            'connection_status': False
        }
        
        if self.engine:
            info['engine_info'] = {
                'name': self.engine.name,
                'driver': self.engine.driver,
                'url': str(self.engine.url)
            }
        
        info['connection_status'] = self.test_connection()
        
        return info
    
    def backup_database(self, backup_path: str) -> bool:
        """备份数据库（仅支持SQLite）
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 备份是否成功
        """
        if not self.database_url.startswith('sqlite'):
            logger.warning("当前仅支持SQLite数据库备份")
            return False
        
        try:
            import shutil
            
            # 提取SQLite文件路径
            db_file = self.database_url.replace('sqlite:///', '')
            
            if os.path.exists(db_file):
                # 确保备份目录存在
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                
                # 复制数据库文件
                shutil.copy2(db_file, backup_path)
                logger.info(f"数据库备份成功: {backup_path}")
                return True
            else:
                logger.error(f"数据库文件不存在: {db_file}")
                return False
                
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """恢复数据库（仅支持SQLite）
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 恢复是否成功
        """
        if not self.database_url.startswith('sqlite'):
            logger.warning("当前仅支持SQLite数据库恢复")
            return False
        
        try:
            import shutil
            
            if not os.path.exists(backup_path):
                logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            # 提取SQLite文件路径
            db_file = self.database_url.replace('sqlite:///', '')
            
            # 关闭现有连接
            if self.engine:
                self.engine.dispose()
            
            # 恢复数据库文件
            shutil.copy2(backup_path, db_file)
            
            # 重新初始化
            self._initialized = False
            success = self.initialize()
            
            if success:
                logger.info(f"数据库恢复成功: {backup_path}")
            else:
                logger.error("数据库恢复后初始化失败")
            
            return success
            
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            return False
    
    def clear_all_data(self) -> bool:
        """清空所有数据（保留表结构）
        
        Returns:
            bool: 清空是否成功
        """
        session = self.get_session()
        if not session:
            return False
        
        try:
            # 获取所有表名
            tables = Base.metadata.tables.keys()
            
            # 删除所有表的数据
            for table_name in tables:
                session.execute(text(f"DELETE FROM {table_name}"))
            
            session.commit()
            logger.info("所有数据清空成功")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"清空数据失败: {e}")
            return False
        finally:
            self.close_session(session)
    
    def __del__(self):
        """析构函数，清理资源"""
        try:
            if self.engine:
                self.engine.dispose()
        except Exception:
            pass


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """获取全局数据库管理器实例
    
    Returns:
        DatabaseManager: 数据库管理器实例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_database(database_url: Optional[str] = None) -> bool:
    """初始化全局数据库
    
    Args:
        database_url: 数据库连接URL
        
    Returns:
        bool: 初始化是否成功
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url)
    return _db_manager.initialize()


def get_db_session() -> Optional[Session]:
    """获取数据库会话的便捷函数
    
    Returns:
        Session: 数据库会话
    """
    return get_database_manager().get_session()