# -*- coding: utf-8 -*-
"""
会话管理器 - 管理用户对话状态和上下文
"""

import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger
import json


@dataclass
class ChatMessage:
    """聊天消息数据类"""
    id: str
    user_id: str
    content: str
    message_type: str  # 'user' or 'assistant'
    timestamp: datetime
    intent: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatSession:
    """聊天会话数据类"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    messages: List[ChatMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = 'active'  # active, inactive, expired


class SessionManager:
    """会话管理器"""
    
    def __init__(self, session_timeout: int = 3600):
        """初始化会话管理器
        
        Args:
            session_timeout: 会话超时时间（秒），默认1小时
        """
        self.sessions: Dict[str, ChatSession] = {}
        self.session_timeout = session_timeout
        self.max_messages_per_session = 100  # 每个会话最大消息数
        
    def create_session(self, user_id: Optional[str] = None) -> str:
        """创建新会话
        
        Args:
            user_id: 用户ID，如果为None则生成随机ID
            
        Returns:
            会话ID
        """
        session_id = str(uuid.uuid4())
        if user_id is None:
            user_id = f"user_{uuid.uuid4().hex[:8]}"
            
        now = datetime.now()
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now
        )
        
        self.sessions[session_id] = session
        logger.info(f"创建新会话: {session_id}, 用户: {user_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象，如果不存在或已过期则返回None
        """
        if session_id not in self.sessions:
            return None
            
        session = self.sessions[session_id]
        
        # 检查会话是否过期
        if self._is_session_expired(session):
            self._expire_session(session_id)
            return None
            
        return session
    
    def add_message(self, session_id: str, content: str, message_type: str, 
                   intent: Optional[Dict[str, Any]] = None, 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """添加消息到会话
        
        Args:
            session_id: 会话ID
            content: 消息内容
            message_type: 消息类型 ('user' 或 'assistant')
            intent: 意图信息（可选）
            metadata: 元数据（可选）
            
        Returns:
            消息ID，如果失败则返回None
        """
        session = self.get_session(session_id)
        if session is None:
            logger.warning(f"会话不存在或已过期: {session_id}")
            return None
            
        # 检查消息数量限制
        if len(session.messages) >= self.max_messages_per_session:
            # 删除最旧的消息
            session.messages.pop(0)
            logger.info(f"会话 {session_id} 消息数量达到上限，删除最旧消息")
        
        message_id = str(uuid.uuid4())
        message = ChatMessage(
            id=message_id,
            user_id=session.user_id,
            content=content,
            message_type=message_type,
            timestamp=datetime.now(),
            intent=intent,
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        session.last_activity = datetime.now()
        
        logger.debug(f"添加消息到会话 {session_id}: {message_type} - {content[:50]}...")
        
        return message_id
    
    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """获取会话消息
        
        Args:
            session_id: 会话ID
            limit: 消息数量限制
            
        Returns:
            消息列表
        """
        session = self.get_session(session_id)
        if session is None:
            return []
            
        messages = session.messages
        if limit is not None:
            messages = messages[-limit:]
            
        return messages
    
    def update_context(self, session_id: str, context_updates: Dict[str, Any]) -> bool:
        """更新会话上下文
        
        Args:
            session_id: 会话ID
            context_updates: 上下文更新数据
            
        Returns:
            是否更新成功
        """
        session = self.get_session(session_id)
        if session is None:
            return False
            
        session.context.update(context_updates)
        session.last_activity = datetime.now()
        
        logger.debug(f"更新会话 {session_id} 上下文: {context_updates}")
        
        return True
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """获取会话上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            上下文字典
        """
        session = self.get_session(session_id)
        if session is None:
            return {}
            
        return session.context.copy()
    
    def clear_context(self, session_id: str, keys: Optional[List[str]] = None) -> bool:
        """清除会话上下文
        
        Args:
            session_id: 会话ID
            keys: 要清除的键列表，如果为None则清除所有
            
        Returns:
            是否清除成功
        """
        session = self.get_session(session_id)
        if session is None:
            return False
            
        if keys is None:
            session.context.clear()
        else:
            for key in keys:
                session.context.pop(key, None)
                
        session.last_activity = datetime.now()
        
        logger.debug(f"清除会话 {session_id} 上下文: {keys or 'all'}")
        
        return True
    
    def end_session(self, session_id: str) -> bool:
        """结束会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否结束成功
        """
        if session_id in self.sessions:
            self.sessions[session_id].status = 'inactive'
            logger.info(f"结束会话: {session_id}")
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"删除会话: {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话
        
        Returns:
            清理的会话数量
        """
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
            
        if expired_sessions:
            logger.info(f"清理过期会话: {len(expired_sessions)} 个")
            
        return len(expired_sessions)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息
        
        Returns:
            统计信息字典
        """
        total_sessions = len(self.sessions)
        active_sessions = sum(1 for s in self.sessions.values() if s.status == 'active')
        total_messages = sum(len(s.messages) for s in self.sessions.values())
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'inactive_sessions': total_sessions - active_sessions,
            'total_messages': total_messages,
            'average_messages_per_session': total_messages / total_sessions if total_sessions > 0 else 0
        }
    
    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """导出会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据字典
        """
        session = self.get_session(session_id)
        if session is None:
            return None
            
        return {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'status': session.status,
            'context': session.context,
            'messages': [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'message_type': msg.message_type,
                    'timestamp': msg.timestamp.isoformat(),
                    'intent': msg.intent,
                    'metadata': msg.metadata
                }
                for msg in session.messages
            ]
        }
    
    def _is_session_expired(self, session: ChatSession) -> bool:
        """检查会话是否过期"""
        if session.status != 'active':
            return True
            
        time_since_last_activity = datetime.now() - session.last_activity
        return time_since_last_activity.total_seconds() > self.session_timeout
    
    def _expire_session(self, session_id: str) -> None:
        """标记会话为过期"""
        if session_id in self.sessions:
            self.sessions[session_id].status = 'expired'
            logger.info(f"会话过期: {session_id}")