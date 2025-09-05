# -*- coding: utf-8 -*-
"""
对话界面 - 基于Streamlit的自然语言交互界面
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

from .intent_parser import IntentParser, Intent
from .session_manager import SessionManager, ChatMessage


class ChatInterface:
    """对话界面类"""
    
    def __init__(self):
        """初始化对话界面"""
        self.intent_parser = IntentParser()
        self.session_manager = SessionManager()
        
        # 初始化会话状态
        if 'chat_session_id' not in st.session_state:
            st.session_state.chat_session_id = self.session_manager.create_session()
            
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
            
        if 'waiting_for_info' not in st.session_state:
            st.session_state.waiting_for_info = False
            
        if 'missing_entities' not in st.session_state:
            st.session_state.missing_entities = []
    
    def render(self) -> None:
        """渲染对话界面"""
        st.header("💬 智能对话助手")
        
        # 显示会话信息
        self._render_session_info()
        
        # 显示聊天历史
        self._render_chat_history()
        
        # 输入区域
        self._render_input_area()
        
        # 侧边栏功能
        self._render_sidebar_functions()
    
    def _render_session_info(self) -> None:
        """渲染会话信息"""
        with st.expander("📊 会话信息", expanded=False):
            session = self.session_manager.get_session(st.session_state.chat_session_id)
            if session:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("会话ID", session.session_id[:8] + "...")
                with col2:
                    st.metric("消息数量", len(session.messages))
                with col3:
                    st.metric("会话状态", session.status)
                    
                # 显示上下文信息
                if session.context:
                    st.subheader("🔍 当前上下文")
                    for key, value in session.context.items():
                        st.write(f"**{key}**: {value}")
    
    def _render_chat_history(self) -> None:
        """渲染聊天历史"""
        messages = self.session_manager.get_messages(st.session_state.chat_session_id)
        
        # 创建聊天容器
        chat_container = st.container()
        
        with chat_container:
            for message in messages:
                if message.message_type == "user":
                    with st.chat_message("user"):
                        st.write(message.content)
                        
                        # 显示意图信息（调试模式）
                        if message.intent and st.session_state.get('debug_mode', False):
                            with st.expander("🔍 意图分析", expanded=False):
                                st.json(message.intent)
                                
                elif message.message_type == "assistant":
                    with st.chat_message("assistant"):
                        st.write(message.content)
                        
                        # 显示元数据（如果有）
                        if message.metadata:
                            if 'action_buttons' in message.metadata:
                                self._render_action_buttons(message.metadata['action_buttons'])
    
    def _render_input_area(self) -> None:
        """渲染输入区域"""
        # 用户输入
        user_input = st.chat_input("请输入您的问题或需求...")
        
        if user_input:
            self._process_user_input(user_input)
    
    def _render_action_buttons(self, buttons: List[Dict[str, Any]]) -> None:
        """渲染操作按钮"""
        cols = st.columns(len(buttons))
        
        for i, button in enumerate(buttons):
            with cols[i]:
                if st.button(button['label'], key=f"action_btn_{button['action']}_{datetime.now().timestamp()}"):
                    self._handle_action(button['action'], button.get('params', {}))
    
    def _render_sidebar_functions(self) -> None:
        """渲染侧边栏功能"""
        with st.sidebar:
            st.markdown("---")
            st.subheader("💬 对话功能")
            
            # 清除对话历史
            if st.button("🗑️ 清除对话历史"):
                self._clear_chat_history()
            
            # 新建会话
            if st.button("🆕 新建会话"):
                self._create_new_session()
            
            # 调试模式
            debug_mode = st.checkbox("🐛 调试模式", value=st.session_state.get('debug_mode', False))
            st.session_state.debug_mode = debug_mode
            
            # 会话统计
            stats = self.session_manager.get_session_stats()
            st.subheader("📈 会话统计")
            st.metric("活跃会话", stats['active_sessions'])
            st.metric("总消息数", stats['total_messages'])
            
            # 导出会话
            if st.button("📤 导出当前会话"):
                self._export_current_session()
    
    def _process_user_input(self, user_input: str) -> None:
        """处理用户输入"""
        try:
            # 添加用户消息到会话
            self.session_manager.add_message(
                st.session_state.chat_session_id,
                user_input,
                "user"
            )
            
            # 解析用户意图
            intent = self.intent_parser.parse(user_input)
            
            # 更新消息的意图信息
            session = self.session_manager.get_session(st.session_state.chat_session_id)
            if session and session.messages:
                session.messages[-1].intent = {
                    'type': intent.type,
                    'confidence': intent.confidence,
                    'entities': intent.entities
                }
            
            # 处理意图
            response = self._handle_intent(intent)
            
            # 添加助手回复
            self.session_manager.add_message(
                st.session_state.chat_session_id,
                response['content'],
                "assistant",
                metadata=response.get('metadata', {})
            )
            
            # 更新上下文
            if 'context_updates' in response:
                self.session_manager.update_context(
                    st.session_state.chat_session_id,
                    response['context_updates']
                )
            
            # 刷新页面以显示新消息
            st.rerun()
            
        except Exception as e:
            logger.error(f"处理用户输入失败: {e}")
            st.error(f"处理您的输入时出现错误: {e}")
    
    def _handle_intent(self, intent: Intent) -> Dict[str, Any]:
        """处理用户意图"""
        if intent.type == 'report_request':
            return self._handle_report_request(intent)
        elif intent.type == 'data_query':
            return self._handle_data_query(intent)
        elif intent.type == 'knowledge_query':
            return self._handle_knowledge_query(intent)
        elif intent.type == 'system_status':
            return self._handle_system_status(intent)
        else:
            return self._handle_unknown_intent(intent)
    
    def _handle_report_request(self, intent: Intent) -> Dict[str, Any]:
        """处理报告生成请求"""
        # 验证必需的实体
        missing_entities = self.intent_parser.validate_entities(intent)
        
        if missing_entities:
            return {
                'content': f"为了生成报告，我还需要以下信息：{', '.join(missing_entities)}。请提供这些信息。",
                'metadata': {
                    'waiting_for_entities': missing_entities,
                    'intent_type': 'report_request'
                }
            }
        
        # 提取实体信息
        wind_farm = intent.entities.get('wind_farm', '未指定')
        turbine_id = intent.entities.get('turbine_id', '未指定')
        time_range = intent.entities.get('time_range', {})
        
        # 构建响应
        response_content = f"我将为您生成 {wind_farm} 的 {turbine_id} 机组的振动分析报告。"
        
        if time_range:
            response_content += f"\n时间范围：{time_range.get('start_time', '')} 至 {time_range.get('end_time', '')}"
        
        response_content += "\n\n请选择您需要的操作："
        
        action_buttons = [
            {
                'label': '🚀 开始生成报告',
                'action': 'generate_report',
                'params': {
                    'wind_farm': wind_farm,
                    'turbine_id': turbine_id,
                    'time_range': time_range
                }
            },
            {
                'label': '📊 查看数据概览',
                'action': 'show_data_overview',
                'params': {
                    'wind_farm': wind_farm,
                    'turbine_id': turbine_id
                }
            }
        ]
        
        return {
            'content': response_content,
            'metadata': {
                'action_buttons': action_buttons
            },
            'context_updates': {
                'current_wind_farm': wind_farm,
                'current_turbine_id': turbine_id,
                'current_time_range': time_range
            }
        }
    
    def _handle_data_query(self, intent: Intent) -> Dict[str, Any]:
        """处理数据查询请求"""
        wind_farm = intent.entities.get('wind_farm', '未指定')
        turbine_id = intent.entities.get('turbine_id', '未指定')
        measurement_point = intent.entities.get('measurement_point', '')
        
        response_content = f"我将为您查询 {wind_farm} 的 {turbine_id} 机组的数据。"
        
        if measurement_point:
            response_content += f"\n重点关注测点：{measurement_point}"
        
        action_buttons = [
            {
                'label': '📈 查看实时数据',
                'action': 'show_realtime_data',
                'params': {
                    'wind_farm': wind_farm,
                    'turbine_id': turbine_id,
                    'measurement_point': measurement_point
                }
            },
            {
                'label': '📊 历史趋势分析',
                'action': 'show_trend_analysis',
                'params': {
                    'wind_farm': wind_farm,
                    'turbine_id': turbine_id
                }
            }
        ]
        
        return {
            'content': response_content,
            'metadata': {
                'action_buttons': action_buttons
            }
        }
    
    def _handle_knowledge_query(self, intent: Intent) -> Dict[str, Any]:
        """处理知识库查询"""
        query_text = intent.raw_text
        
        # 这里可以集成RAG系统进行知识查询
        response_content = f"我正在为您查询相关知识：{query_text}\n\n"
        response_content += "基于我的知识库，我可以为您提供以下信息：\n"
        response_content += "• 振动分析的基本原理和方法\n"
        response_content += "• 常见故障模式的识别和诊断\n"
        response_content += "• 设备维护和保养建议\n\n"
        response_content += "如需更详细的信息，请告诉我您具体想了解哪个方面。"
        
        return {
            'content': response_content
        }
    
    def _handle_system_status(self, intent: Intent) -> Dict[str, Any]:
        """处理系统状态查询"""
        # 获取系统状态信息
        llm_status = "✅ 已就绪" if st.session_state.get('llm_initialized', False) else "❌ 未初始化"
        kb_status = "✅ 已就绪" if st.session_state.get('knowledge_base_initialized', False) else "❌ 未初始化"
        
        response_content = f"📊 **系统状态报告**\n\n"
        response_content += f"• **LLM模型**: {llm_status}\n"
        response_content += f"• **知识库**: {kb_status}\n"
        response_content += f"• **对话系统**: ✅ 运行正常\n"
        response_content += f"• **数据处理**: ✅ 运行正常\n\n"
        
        if not st.session_state.get('llm_initialized', False):
            response_content += "💡 建议：请先在侧边栏初始化LLM模型以获得完整功能。"
        
        return {
            'content': response_content
        }
    
    def _handle_unknown_intent(self, intent: Intent) -> Dict[str, Any]:
        """处理未知意图"""
        response_content = "抱歉，我没有完全理解您的需求。\n\n"
        response_content += "我可以帮助您：\n"
        response_content += "• 🔍 生成振动分析报告\n"
        response_content += "• 📊 查询设备数据和状态\n"
        response_content += "• 💡 回答振动分析相关问题\n"
        response_content += "• ⚙️ 查看系统运行状态\n\n"
        response_content += "请尝试重新描述您的需求，或选择上述功能之一。"
        
        return {
            'content': response_content
        }
    
    def _handle_action(self, action: str, params: Dict[str, Any]) -> None:
        """处理操作按钮点击"""
        try:
            if action == 'generate_report':
                self._trigger_report_generation(params)
            elif action == 'show_data_overview':
                self._show_data_overview(params)
            elif action == 'show_realtime_data':
                self._show_realtime_data(params)
            elif action == 'show_trend_analysis':
                self._show_trend_analysis(params)
            else:
                st.warning(f"未知操作: {action}")
                
        except Exception as e:
            logger.error(f"处理操作失败: {action}, {e}")
            st.error(f"执行操作时出现错误: {e}")
    
    def _trigger_report_generation(self, params: Dict[str, Any]) -> None:
        """触发报告生成"""
        wind_farm = params.get('wind_farm', '')
        turbine_id = params.get('turbine_id', '')
        
        # 添加系统消息
        self.session_manager.add_message(
            st.session_state.chat_session_id,
            f"正在为 {wind_farm} 的 {turbine_id} 机组生成分析报告，请稍候...",
            "assistant"
        )
        
        # 设置标志，让主应用知道需要生成报告
        st.session_state.trigger_report_generation = True
        st.session_state.report_params = params
        
        st.success("报告生成请求已提交，请切换到报告生成页面查看进度。")
        st.rerun()
    
    def _show_data_overview(self, params: Dict[str, Any]) -> None:
        """显示数据概览"""
        # 设置标志，让主应用切换到数据概览页面
        st.session_state.switch_to_data_overview = True
        st.session_state.data_overview_params = params
        
        st.info("正在切换到数据概览页面...")
        st.rerun()
    
    def _show_realtime_data(self, params: Dict[str, Any]) -> None:
        """显示实时数据"""
        st.info("实时数据功能正在开发中，敬请期待！")
    
    def _show_trend_analysis(self, params: Dict[str, Any]) -> None:
        """显示趋势分析"""
        st.info("趋势分析功能正在开发中，敬请期待！")
    
    def _clear_chat_history(self) -> None:
        """清除对话历史"""
        if st.session_state.chat_session_id:
            session = self.session_manager.get_session(st.session_state.chat_session_id)
            if session:
                session.messages.clear()
                session.context.clear()
                
        st.success("对话历史已清除")
        st.rerun()
    
    def _create_new_session(self) -> None:
        """创建新会话"""
        old_session_id = st.session_state.chat_session_id
        new_session_id = self.session_manager.create_session()
        
        st.session_state.chat_session_id = new_session_id
        st.session_state.chat_messages = []
        
        # 结束旧会话
        if old_session_id:
            self.session_manager.end_session(old_session_id)
        
        st.success(f"新会话已创建: {new_session_id[:8]}...")
        st.rerun()
    
    def _export_current_session(self) -> None:
        """导出当前会话"""
        session_data = self.session_manager.export_session(st.session_state.chat_session_id)
        
        if session_data:
            import json
            json_str = json.dumps(session_data, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="📥 下载会话数据",
                data=json_str,
                file_name=f"chat_session_{session_data['session_id'][:8]}.json",
                mime="application/json"
            )
        else:
            st.error("导出会话数据失败")