#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析报告系统 - Gradio前端（简化版）
作者: Assistant
版本: 1.0.0
"""

import gradio as gr
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from config.config_loader import ConfigLoader
from chat.session_manager import SessionManager
from knowledge.knowledge_retriever import KnowledgeRetriever
from chat.chat_manager import ChatManager

class SimpleCMSApp:
    """简化的CMS应用类"""
    
    def __init__(self):
        """初始化应用"""
        self.config = ConfigLoader()
        self.session_manager = None
        self.knowledge_retriever = None
        self.chat_manager = None
        self.current_session_id = None
        
        # 初始化组件
        self._init_components()
    
    def _init_components(self):
        """初始化核心组件"""
        try:
            # 初始化会话管理器
            self.session_manager = SessionManager()
            logger.info("会话管理器初始化完成")
            
            # 初始化知识检索器
            try:
                # 确保config_dict正确获取
                if hasattr(self.config, 'config'):
                    config_dict = self.config.config
                else:
                    config_dict = self.config
                
                knowledge_config = config_dict.get('knowledge', {})
                self.knowledge_retriever = KnowledgeRetriever(
                    embeddings_path=knowledge_config.get('embeddings_path', 'data/knowledge/embeddings'),
                    metadata_path=knowledge_config.get('metadata_path', 'data/knowledge/metadata')
                )
                logger.info("知识检索器初始化完成")
            except Exception as e:
                logger.warning(f"知识检索器初始化失败: {e}")
                self.knowledge_retriever = None
                config_dict = {}
            
            # 初始化聊天管理器
            try:
                self.chat_manager = ChatManager(
                    config=config_dict,
                    session_manager=self.session_manager
                )
                logger.info("聊天管理器初始化完成")
            except Exception as e:
                logger.warning(f"聊天管理器初始化失败: {e}")
                self.chat_manager = None
                
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
    
    def chat_interface(self, message: str, history: List[List[str]]) -> Tuple[str, List[List[str]]]:
        """聊天界面处理函数"""
        if not message.strip():
            return "", history
        
        try:
            # 检查聊天管理器是否可用
            if not self.chat_manager:
                response = "❌ 系统未完全初始化，请稍后重试"
                history.append([message, response])
                return "", history
            
            # 获取或创建会话
            if not self.current_session_id:
                if self.session_manager and hasattr(self.session_manager, 'create_session'):
                    session_result = self.session_manager.create_session(user_id="gradio_user")
                    self.current_session_id = session_result.get('session_id') if session_result else None
                else:
                    self.current_session_id = None
            
            # 处理消息
            result = self.chat_manager.process_message(
                user_id="gradio_user",
                message=message,
                session_id=self.current_session_id
            )
            
            if isinstance(result, dict) and result.get('success'):
                response = result.get('response', '处理完成')
            else:
                response = result.get('error', '处理失败') if isinstance(result, dict) else str(result)
            
            # 更新历史记录
            history.append([message, response])
            
        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)}"
            history.append([message, error_msg])
            logger.error(error_msg)
        
        return "", history
    
    def get_system_status(self) -> str:
        """获取系统状态"""
        status_info = []
        status_info.append("## 系统状态")
        status_info.append(f"- 配置加载: ✅ 成功")
        status_info.append(f"- 会话管理器: {'✅ 正常' if self.session_manager else '❌ 未初始化'}")
        status_info.append(f"- 知识检索器: {'✅ 正常' if self.knowledge_retriever else '❌ 未初始化'}")
        status_info.append(f"- 聊天管理器: {'✅ 正常' if self.chat_manager else '❌ 未初始化'}")
        
        if self.current_session_id:
            status_info.append(f"- 当前会话: {self.current_session_id}")
        
        return "\n".join(status_info)
    
    def handle_chat_message(self, message: str) -> str:
        """处理聊天消息"""
        if not self.chat_manager:
            return "系统初始化失败，请重启应用"
        
        try:
            # 获取或创建会话
            if not self.current_session_id:
                if self.session_manager and hasattr(self.session_manager, 'create_session'):
                    session_result = self.session_manager.create_session(user_id="gradio_user")
                    self.current_session_id = session_result.get('session_id') if session_result else None
                else:
                    self.current_session_id = None
            
            result = self.chat_manager.process_message(
                user_id="gradio_user",
                message=message,
                session_id=self.current_session_id
            )
            
            if isinstance(result, dict) and result.get('success'):
                response = result.get('response', '处理完成')
            else:
                response = result.get('error', '处理失败') if isinstance(result, dict) else str(result)
            
            return response
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return f"处理失败: {str(e)}"
    
    def create_interface(self):
        """创建Gradio界面"""
        interface = gr.Interface(
            fn=self.handle_chat_message,
            inputs=gr.Textbox(label="输入消息", placeholder="请输入您的问题或需求...", lines=2),
            outputs=gr.Textbox(label="回复", lines=5),
            title="CMS振动分析报告系统",
            description="基于Gradio的智能对话界面",
            examples=[
                "请显示系统状态",
                "请生成振动分析报告",
                "帮我分析设备振动数据"
            ]
        )
        
        return interface

def main():
    """主函数"""
    try:
        # 创建应用实例
        app = SimpleCMSApp()
        
        # 创建界面
        interface = app.create_interface()
        
        # 启动服务
        logger.info("启动Gradio服务...")
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=True,
            debug=False
        )
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise

if __name__ == "__main__":
    main()