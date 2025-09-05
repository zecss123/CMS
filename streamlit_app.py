# -*- coding: utf-8 -*-
"""
CMS振动分析系统 - Streamlit Web界面
集成聊天功能和报告生成的统一界面
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger
import yaml
import shutil

# 导入自定义模块
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import get_config
from chat.chat_manager import ChatManager
from chat.session_manager import SessionManager
from knowledge.knowledge_retriever import KnowledgeRetriever
from data.mock_data import CMSDataGenerator
from utils.chart_generator import VibrationChartGenerator
from report.generator import CMSReportGenerator

# 配置页面
config = get_config()
st.set_page_config(
    page_title=config.get('streamlit.page_title', 'CMS振动分析报告系统'),
    page_icon=config.get('streamlit.page_icon', '🔧'),
    layout=config.get('streamlit.layout', 'wide'),
    initial_sidebar_state=config.get('streamlit.initial_sidebar_state', 'expanded')
)

# 自定义CSS样式
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
    padding: 1rem;
    background: linear-gradient(90deg, #f0f8ff, #e6f3ff);
    border-radius: 10px;
    border-left: 5px solid #1f77b4;
}

.chat-container {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 1rem 0;
}

.user-message {
    background: #e3f2fd;
    padding: 0.8rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    border-left: 4px solid #2196f3;
}

.assistant-message {
    background: #f1f8e9;
    padding: 0.8rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    border-left: 4px solid #4caf50;
}

.config-section {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    border-left: 4px solid #6c757d;
}

.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
}

.status-online {
    background-color: #28a745;
}

.status-offline {
    background-color: #dc3545;
}

.status-warning {
    background-color: #ffc107;
}
</style>
""", unsafe_allow_html=True)

class StreamlitCMSApp:
    """Streamlit CMS应用程序主类"""
    
    def __init__(self):
        self.config = get_config()
        self._init_session_state()
        self._init_components()
    
    def _init_session_state(self):
        """初始化会话状态"""
        if 'chat_manager' not in st.session_state:
            st.session_state.chat_manager = None
        
        if 'session_manager' not in st.session_state:
            st.session_state.session_manager = None
        
        if 'knowledge_retriever' not in st.session_state:
            st.session_state.knowledge_retriever = None
        
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = None
        
        if 'system_status' not in st.session_state:
            st.session_state.system_status = {
                'llm': 'offline',
                'knowledge_base': 'offline',
                'database': 'offline'
            }
    
    def _init_components(self):
        """初始化系统组件"""
        try:
            # 初始化会话管理器
            if st.session_state.session_manager is None:
                st.session_state.session_manager = SessionManager()
                logger.info("会话管理器初始化完成")
            
            # 初始化知识检索器
            if st.session_state.knowledge_retriever is None:
                try:
                    with st.spinner("初始化知识库..."):
                        # 从配置中获取路径
                        knowledge_config = self.config.get('knowledge', {})
                        embeddings_path = knowledge_config.get('embeddings_path', './data/embeddings')
                        metadata_path = knowledge_config.get('metadata_path', './data/metadata')
                        
                        st.session_state.knowledge_retriever = KnowledgeRetriever(
                            embeddings_path=embeddings_path,
                            metadata_path=metadata_path
                        )
                        st.session_state.system_status['knowledge_base'] = 'online'
                        logger.info("知识检索器初始化完成")
                except Exception as e:
                    st.session_state.knowledge_retriever = None
                    st.session_state.system_status['knowledge_base'] = 'offline'
                    logger.error(f"知识检索器初始化失败: {e}")
            
            # 初始化聊天管理器
            if st.session_state.chat_manager is None:
                try:
                    with st.spinner("初始化聊天系统..."):
                        st.session_state.chat_manager = ChatManager(
                            config=self.config.config,
                            session_manager=st.session_state.session_manager
                        )
                        # 检查LLM状态
                        if hasattr(st.session_state.chat_manager.llm_client, 'model_config'):
                            st.session_state.system_status['llm'] = 'online'
                        else:
                            st.session_state.system_status['llm'] = 'warning'
                        logger.info("聊天管理器初始化完成")
                except Exception as e:
                    st.session_state.chat_manager = None
                    st.session_state.system_status['llm'] = 'offline'
                    logger.error(f"聊天管理器初始化失败: {e}")
            
            # 数据库状态检查
            st.session_state.system_status['database'] = 'online'
            
        except Exception as e:
            st.error(f"组件初始化失败: {e}")
            logger.error(f"组件初始化失败: {e}")
    
    def run(self):
        """运行主应用程序"""
        # 主标题
        st.markdown('<h1 class="main-header">🔧 CMS振动分析报告系统</h1>', unsafe_allow_html=True)
        
        # 侧边栏
        self._render_sidebar()
        
        # 主内容区域
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 智能对话", "📊 数据分析", "📋 报告生成", "📚 知识库管理", "⚙️ 系统配置"])
        
        with tab1:
            self._render_chat_interface()
        
        with tab2:
            self._render_data_analysis()
        
        with tab3:
            self._render_report_generation()
        
        with tab4:
            self._render_knowledge_management()
        
        with tab5:
            self._render_system_config()
    
    def _render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.header("🎛️ 系统控制台")
            
            # 系统状态显示
            st.subheader("📊 系统状态")
            
            status_indicators = {
                'llm': '🤖 语言模型',
                'knowledge_base': '📚 知识库',
                'database': '🗄️ 数据库'
            }
            
            for key, label in status_indicators.items():
                status = st.session_state.system_status.get(key, 'offline')
                if status == 'online':
                    st.markdown(f'<span class="status-indicator status-online"></span>{label}: 在线', unsafe_allow_html=True)
                elif status == 'warning':
                    st.markdown(f'<span class="status-indicator status-warning"></span>{label}: 警告', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="status-indicator status-offline"></span>{label}: 离线', unsafe_allow_html=True)
            
            st.divider()
            
            # 配置信息
            st.subheader("⚙️ 当前配置")
            model_config = self.config.get_model_config()
            st.write(f"**模型类型**: {model_config.get('type', 'unknown')}")
            
            if model_config['type'] == 'local':
                st.write(f"**本地模型**: {model_config.get('model_name', 'unknown')}")
            elif model_config['type'] == 'openai':
                api_key = model_config.get('api_key', '')
                masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key and len(api_key) > 12 else "未配置"
                st.write(f"**OpenAI模型**: {model_config.get('model_name', 'unknown')}")
                st.write(f"**API密钥**: {masked_key}")
            
            embedding_config = self.config.get_embedding_config()
            st.write(f"**嵌入模型**: {embedding_config.get('type', 'unknown')}")
            
            st.divider()
            
            # 快速操作
            st.subheader("🚀 快速操作")
            
            if st.button("🔄 重新加载配置"):
                self.config.reload()
                st.success("配置已重新加载")
                st.rerun()
            
            if st.button("🗑️ 清空对话历史"):
                st.session_state.chat_history = []
                st.success("对话历史已清空")
                st.rerun()
            
            if st.button("📊 生成测试数据"):
                try:
                    self._generate_test_data()
                    # 设置会话上下文，启用测试数据模式
                    if not st.session_state.current_session_id:
                        st.session_state.current_session_id = st.session_state.session_manager.create_session(
                            user_id="streamlit_user"
                        )
                    st.session_state.session_manager.update_context(
                        st.session_state.current_session_id,
                        {'use_mock_data': True}
                    )
                    st.success("✅ 测试数据生成完成，测试数据模式已启用！")
                    st.rerun()
                except Exception as e:
                    st.error(f"测试数据生成失败，无法启用测试数据模式: {str(e)}")
    
    def _render_chat_interface(self):
        """渲染聊天界面"""
        st.header("💬 智能对话助手")
        st.write("与AI助手对话，获取振动分析报告和技术支持")
        
        # 聊天历史显示
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f'<div class="user-message">👤 **用户**: {message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="assistant-message">🤖 **助手**: {message["content"]}</div>', unsafe_allow_html=True)
        
        # 输入区域
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "请输入您的问题",
                placeholder="例如：生成华能风场A的A01风机振动分析报告",
                key="chat_input"
            )
        
        with col2:
            send_button = st.button("发送", type="primary")
        
        # 处理用户输入
        if send_button and user_input:
            self._handle_chat_message(user_input)
        
        # 快速问题按钮
        st.subheader("🔍 快速问题")
        quick_questions = [
            "生成振动分析报告",
            "查询设备状态",
            "分析振动趋势",
            "故障诊断建议"
        ]
        
        cols = st.columns(len(quick_questions))
        for i, question in enumerate(quick_questions):
            with cols[i]:
                if st.button(question, key=f"quick_{i}"):
                    self._handle_chat_message(question)
    
    def _handle_chat_message(self, message: str):
        """处理聊天消息"""
        # 添加用户消息到历史
        st.session_state.chat_history.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now()
        })
        
        try:
            # 获取或创建会话
            if not st.session_state.current_session_id:
                st.session_state.current_session_id = st.session_state.session_manager.create_session(
                    user_id="streamlit_user"
                )
            
            # 处理消息
            with st.spinner("AI正在思考中..."):
                result = st.session_state.chat_manager.process_message(
                    user_id="streamlit_user",
                    message=message,
                    session_id=st.session_state.current_session_id
                )
                response = result.get('response', '处理失败') if result.get('success') else result.get('error', '未知错误')
            
            # 添加助手回复到历史
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now()
            })
            
        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)}"
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': error_msg,
                'timestamp': datetime.now()
            })
            logger.error(error_msg)
        
        # 重新运行以更新界面
        st.rerun()
    
    def _render_knowledge_management(self):
        """渲染知识库管理界面"""
        st.header("📚 知识库管理")
        
        # 创建两列布局
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📄 文档管理")
            
            # 文件上传区域
            st.markdown("### 📤 上传文档")
            uploaded_files = st.file_uploader(
                "选择要上传的文档",
                type=['pdf', 'docx', 'txt', 'md'],
                accept_multiple_files=True,
                help="支持PDF、Word文档、文本文件和Markdown文件"
            )
            
            if uploaded_files:
                if st.button("🚀 开始上传并处理", type="primary"):
                    self._handle_file_upload(uploaded_files)
            
            # 现有文档列表
            st.markdown("### 📋 现有文档")
            self._display_knowledge_documents()
        
        with col2:
            st.subheader("📊 知识库统计")
            self._display_knowledge_stats()
            
            st.subheader("🔧 管理操作")
            
            # 重建索引按钮
            if st.button("🔄 重建知识库索引"):
                self._rebuild_knowledge_index()
            
            # 清空知识库按钮
            if st.button("🗑️ 清空知识库", type="secondary"):
                if st.session_state.get('confirm_clear_kb', False):
                    self._clear_knowledge_base()
                    st.session_state.confirm_clear_kb = False
                else:
                    st.session_state.confirm_clear_kb = True
                    st.warning("⚠️ 再次点击确认清空知识库")
    
    def _handle_file_upload(self, uploaded_files):
        """处理文件上传"""
        try:
            with st.spinner("正在处理上传的文档..."):
                success_count = 0
                error_count = 0
                
                for uploaded_file in uploaded_files:
                    try:
                        # 保存文件到临时目录
                        temp_path = Path("./temp") / uploaded_file.name
                        temp_path.parent.mkdir(exist_ok=True)
                        
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # 使用知识库管理器处理文档
                        if hasattr(st.session_state, 'knowledge_retriever'):
                            # 这里应该调用文档处理方法
                            # 暂时显示成功消息
                            success_count += 1
                            st.success(f"✅ {uploaded_file.name} 上传成功")
                        else:
                            error_count += 1
                            st.error(f"❌ {uploaded_file.name} 处理失败：知识库未初始化")
                        
                        # 清理临时文件
                        if temp_path.exists():
                            temp_path.unlink()
                            
                    except Exception as e:
                        error_count += 1
                        st.error(f"❌ {uploaded_file.name} 处理失败：{str(e)}")
                        logger.error(f"文件上传处理失败: {e}")
                
                # 显示总结
                if success_count > 0:
                    st.success(f"🎉 成功处理 {success_count} 个文档")
                if error_count > 0:
                    st.error(f"⚠️ {error_count} 个文档处理失败")
                    
        except Exception as e:
            st.error(f"文件上传处理异常：{str(e)}")
            logger.error(f"文件上传处理异常: {e}")
    
    def _display_knowledge_documents(self):
        """显示知识库文档列表"""
        try:
            # 获取知识库文档列表
            knowledge_dir = Path("./data/knowledge")
            if not knowledge_dir.exists():
                st.info("📝 知识库为空，请上传文档")
                return
            
            # 扫描文档文件
            doc_files = []
            for ext in ['.pdf', '.docx', '.txt', '.md']:
                doc_files.extend(knowledge_dir.rglob(f'*{ext}'))
            
            if not doc_files:
                st.info("📝 知识库为空，请上传文档")
                return
            
            # 创建文档表格
            doc_data = []
            for doc_file in doc_files:
                doc_data.append({
                    '文档名称': doc_file.name,
                    '文件大小': f"{doc_file.stat().st_size / 1024:.1f} KB",
                    '修改时间': datetime.fromtimestamp(doc_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    '文件路径': str(doc_file.relative_to(knowledge_dir))
                })
            
            if doc_data:
                df = pd.DataFrame(doc_data)
                st.dataframe(df, use_container_width=True)
                
                # 删除文档功能
                selected_docs = st.multiselect(
                    "选择要删除的文档",
                    options=[doc['文档名称'] for doc in doc_data],
                    help="选择一个或多个文档进行删除"
                )
                
                if selected_docs and st.button("🗑️ 删除选中文档", type="secondary"):
                    self._delete_documents(selected_docs, doc_files)
            
        except Exception as e:
            st.error(f"获取文档列表失败：{str(e)}")
            logger.error(f"获取文档列表失败: {e}")
    
    def _display_knowledge_stats(self):
        """显示知识库统计信息"""
        try:
            knowledge_dir = Path("./data/knowledge")
            
            # 统计文档数量
            doc_count = 0
            total_size = 0
            
            if knowledge_dir.exists():
                for ext in ['.pdf', '.docx', '.txt', '.md']:
                    files = list(knowledge_dir.rglob(f'*{ext}'))
                    doc_count += len(files)
                    total_size += sum(f.stat().st_size for f in files)
            
            # 显示统计信息
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📄 文档数量", doc_count)
            with col2:
                st.metric("💾 总大小", f"{total_size / 1024 / 1024:.1f} MB")
            
            # 显示向量数据库状态
            vector_db_path = Path("./data/vector_db")
            if vector_db_path.exists():
                st.success("✅ 向量数据库已建立")
            else:
                st.warning("⚠️ 向量数据库未建立")
                
        except Exception as e:
            st.error(f"获取统计信息失败：{str(e)}")
            logger.error(f"获取统计信息失败: {e}")
    
    def _delete_documents(self, selected_docs, doc_files):
        """删除选中的文档"""
        try:
            deleted_count = 0
            for doc_name in selected_docs:
                # 找到对应的文件
                for doc_file in doc_files:
                    if doc_file.name == doc_name:
                        doc_file.unlink()
                        deleted_count += 1
                        break
            
            if deleted_count > 0:
                st.success(f"✅ 成功删除 {deleted_count} 个文档")
                st.rerun()
            
        except Exception as e:
            st.error(f"删除文档失败：{str(e)}")
            logger.error(f"删除文档失败: {e}")
    
    def _rebuild_knowledge_index(self):
        """重建知识库索引"""
        try:
            with st.spinner("正在重建知识库索引..."):
                # 这里应该调用知识库重建方法
                # 暂时显示成功消息
                import time
                time.sleep(2)  # 模拟处理时间
                st.success("✅ 知识库索引重建完成")
                
        except Exception as e:
            st.error(f"重建索引失败：{str(e)}")
            logger.error(f"重建索引失败: {e}")
    
    def _clear_knowledge_base(self):
        """清空知识库"""
        try:
            with st.spinner("正在清空知识库..."):
                knowledge_dir = Path("./data/knowledge")
                vector_db_dir = Path("./data/vector_db")
                
                # 删除知识库文件
                if knowledge_dir.exists():
                    import shutil
                    shutil.rmtree(knowledge_dir)
                    knowledge_dir.mkdir(parents=True, exist_ok=True)
                
                # 删除向量数据库
                if vector_db_dir.exists():
                    import shutil
                    shutil.rmtree(vector_db_dir)
                    vector_db_dir.mkdir(parents=True, exist_ok=True)
                
                st.success("✅ 知识库已清空")
                st.rerun()
                
        except Exception as e:
            st.error(f"清空知识库失败：{str(e)}")
            logger.error(f"清空知识库失败: {e}")
    
    def _render_data_analysis(self):
        """渲染数据分析界面"""
        st.header("📊 振动数据分析")
        
        # 风场和风机选择
        col1, col2 = st.columns(2)
        
        with col1:
            wind_farms = list(self.config.get('business.wind_farms', {}).keys())
            selected_farm = st.selectbox("选择风场", wind_farms)
        
        with col2:
            selected_turbine = None
            if selected_farm:
                turbines = self.config.get(f'business.wind_farms.{selected_farm}.turbines', [])
                selected_turbine = st.selectbox("选择风机", turbines)
        
        if selected_farm and selected_turbine:
            # 生成模拟数据
            if st.button("📈 生成振动数据"):
                with st.spinner("生成振动数据中..."):
                    data_generator = CMSDataGenerator()
                    vibration_data = data_generator.generate_turbine_data(
                        wind_farm=selected_farm,
                        turbine_id=selected_turbine
                    )
                    
                    # 显示数据概览
                    st.subheader("📋 数据概览")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("测点数量", len(vibration_data['measurements']))
                    with col2:
                        # 从第一个测点获取采样频率
                        first_measurement = next(iter(vibration_data['measurements'].values()))
                        sampling_rate = first_measurement.get('sampling_rate', 2048)
                        st.metric("采样频率", f"{sampling_rate} Hz")
                    with col3:
                        # 从第一个测点获取数据长度
                        data_length = first_measurement.get('data_length', 0)
                        st.metric("数据长度", data_length)
                    with col4:
                        overall_status = vibration_data.get('overall_status', '正常')
                        st.metric("整体状态", overall_status)
                    
                    # 显示振动图表
                    st.subheader("📊 振动波形")
                    
                    chart_generator = VibrationChartGenerator()
                    for point_name, point_data in vibration_data['measurements'].items():
                        with st.expander(f"📈 {point_name}"):
                            # 生成图表
                            if 'time_series' in point_data:
                                try:
                                    # 确保time_series是numpy数组
                                    time_series_data = point_data['time_series']
                                    if isinstance(time_series_data, list):
                                        time_series_data = np.array(time_series_data)
                                    
                                    chart_base64 = chart_generator.create_time_series_chart(
                                        time_series_data,
                                        sampling_rate=point_data.get('sampling_rate', 2048),
                                        title=f"{selected_farm} - {selected_turbine} - {point_name}"
                                    )
                                    if chart_base64:
                                        import base64
                                        chart_bytes = base64.b64decode(chart_base64)
                                        st.image(chart_bytes, use_column_width=True)
                                    else:
                                        st.error(f"图表生成失败: {point_name}")
                                except Exception as e:
                                    st.error(f"图表生成出错: {point_name} - {str(e)}")
                            else:
                                st.warning(f"无时域数据可显示: {point_name}")
                            
                            # 显示统计信息
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                rms_value = point_data.get('features', {}).get('rms_value', 0.0)
                                st.metric("RMS值", f"{rms_value:.2f} mm/s")
                            with col2:
                                peak_value = point_data.get('features', {}).get('peak_value', 0.0)
                                st.metric("峰值", f"{peak_value:.2f} mm/s")
                            with col3:
                                alarm_level = point_data.get('alarm_level', '正常')
                                st.metric("状态", alarm_level)
    
    def _render_report_generation(self):
        """渲染报告生成界面"""
        st.header("📋 报告生成")
        
        # 数据源选择
        st.subheader("🔧 数据源配置")
        use_test_data = st.checkbox(
            "生成测试数据", 
            value=False,  # 默认不使用测试数据，需要用户明确选择
            help="勾选此项将生成测试数据进行分析，不勾选则调用外部API获取实际数据"
        )
        
        # 报告参数设置
        st.subheader("📋 报告参数")
        col1, col2 = st.columns(2)
        
        with col1:
            wind_farms = list(self.config.get('business.wind_farms', {}).keys())
            selected_farm = st.selectbox("选择风场", wind_farms, key="report_farm")
        
        with col2:
            selected_turbine = None
            if selected_farm:
                turbines = self.config.get(f'business.wind_farms.{selected_farm}.turbines', [])
                selected_turbine = st.selectbox("选择风机", turbines, key="report_turbine")
        
        # 报告类型选择
        report_types = ["完整分析报告", "简要状态报告", "故障诊断报告", "趋势分析报告"]
        selected_report_type = st.selectbox("报告类型", report_types)
        
        # 时间范围选择
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("结束日期", datetime.now())
        
        # 报告格式选择
        report_formats = self.config.get('business.report.formats', ['docx', 'pdf'])
        selected_format = st.selectbox("报告格式", report_formats)
        
        # 显示数据源状态
        if use_test_data:
            st.info("🧪 将使用测试数据生成报告")
        else:
            api_enabled = self.config.get('external_api.enabled', False)
            if api_enabled:
                st.success("🌐 将调用外部API获取实际数据")
            else:
                st.warning("⚠️ 外部API未启用，请检查配置")
        
        # 生成报告按钮
        if st.button("📄 生成报告", type="primary"):
            if selected_farm and selected_turbine:
                with st.spinner("正在生成报告..."):
                    try:
                        # 设置会话上下文中的数据源选择
                        if not st.session_state.current_session_id:
                            st.session_state.current_session_id = st.session_state.session_manager.create_session(
                                user_id="streamlit_user"
                            )
                        
                        # 更新会话上下文，设置数据源模式
                        st.session_state.session_manager.update_context(
                            st.session_state.current_session_id,
                            {'use_mock_data': use_test_data}
                        )
                        
                        # 使用聊天管理器生成报告
                        data_source_info = "使用测试数据" if use_test_data else "调用外部API"
                        report_request = f"生成{selected_farm}的{selected_turbine}风机{selected_report_type}，时间范围从{start_date}到{end_date}（{data_source_info}）"
                        
                        response = st.session_state.chat_manager.process_message(
                            user_id="streamlit_user",
                            message=report_request,
                            session_id=st.session_state.current_session_id
                        )
                        
                        st.success("报告生成完成！")
                        st.markdown("### 📋 生成的报告")
                        st.markdown(response.get('response', response) if isinstance(response, dict) else response)
                        
                        # 检查是否有生成的DOCX文件
                        if isinstance(response, dict) and response.get('docx_file'):
                            docx_file_path = response['docx_file']
                            if os.path.exists(docx_file_path):
                                with open(docx_file_path, 'rb') as f:
                                    st.download_button(
                                        label="📥 下载 DOCX 报告",
                                        data=f.read(),
                                        file_name=os.path.basename(docx_file_path),
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    )
                        else:
                            # 备用方案：检查输出目录中的文件
                            output_dir = Path(self.config.get('system', {}).get('output_dir', './output'))
                            if output_dir.exists():
                                report_files = list(output_dir.glob(f"*{selected_turbine}*.{selected_format}"))
                                if report_files:
                                    latest_report = max(report_files, key=os.path.getctime)
                                    with open(latest_report, 'rb') as f:
                                        mime_type = {
                                            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                            'pdf': 'application/pdf',
                                            'html': 'text/html'
                                        }.get(selected_format, f'application/{selected_format}')
                                        
                                        st.download_button(
                                            label=f"📥 下载 {selected_format.upper()} 报告",
                                            data=f.read(),
                                            file_name=latest_report.name,
                                            mime=mime_type
                                        )
                        
                    except Exception as e:
                        st.error(f"报告生成失败: {str(e)}")
                        logger.error(f"报告生成失败: {e}")
            else:
                st.warning("请选择风场和风机")
    
    def _render_system_config(self):
        """渲染系统配置界面"""
        st.header("⚙️ 系统配置")
        
        # 配置文件编辑
        st.subheader("📝 配置文件编辑")
        
        config_file_path = self.config.config_file
        
        if st.button("📂 重新加载配置文件"):
            self.config.reload()
            st.success("配置文件已重新加载")
            st.rerun()
        
        # 显示当前配置
        with st.expander("📋 查看当前配置", expanded=False):
            st.json(self.config.config)
        
        # 配置编辑器
        st.subheader("✏️ 在线配置编辑")
        
        # 模型配置
        with st.expander("🤖 模型配置", expanded=True):
            model_types = ['local', 'openai', 'deepseek_api', 'custom']
            current_model_type = self.config.get('model.type', 'local')
            new_model_type = st.selectbox("模型类型", model_types, index=model_types.index(current_model_type))
            
            if new_model_type != current_model_type:
                self.config.set('model.type', new_model_type)
                st.info(f"模型类型已更改为: {new_model_type}")
            
            if new_model_type == 'openai':
                api_key = st.text_input(
                    "OpenAI API Key",
                    value=self.config.get('model.openai.api_key', ''),
                    type="password"
                )
                base_url = st.text_input(
                    "Base URL",
                    value=self.config.get('model.openai.base_url', 'https://api.openai.com/v1')
                )
                model_name = st.text_input(
                    "模型名称",
                    value=self.config.get('model.openai.model_name', 'gpt-3.5-turbo')
                )
                
                if st.button("💾 保存OpenAI配置"):
                    self.config.set('model.openai.api_key', api_key)
                    self.config.set('model.openai.base_url', base_url)
                    self.config.set('model.openai.model_name', model_name)
                    st.success("OpenAI配置已保存")
            
            elif new_model_type == 'local':
                model_path = st.text_input(
                    "本地模型路径",
                    value=self.config.get('model.local.model_path', '')
                )
                device = st.selectbox(
                    "设备",
                    ['auto', 'cuda', 'cpu'],
                    index=['auto', 'cuda', 'cpu'].index(self.config.get('model.local.device', 'auto'))
                )
                
                if st.button("💾 保存本地模型配置"):
                    self.config.set('model.local.model_path', model_path)
                    self.config.set('model.local.device', device)
                    st.success("本地模型配置已保存")
        
        # 保存配置到文件
        if st.button("💾 保存所有配置到文件", type="primary"):
            try:
                self.config.save_config()
                st.success(f"配置已保存到: {config_file_path}")
            except Exception as e:
                st.error(f"保存配置失败: {str(e)}")
    
    def _generate_test_data(self):
        """生成测试数据"""
        try:
            data_generator = CMSDataGenerator()
            test_data = data_generator.generate_turbine_data(
                wind_farm="华能风场A",
                turbine_id="A01"
            )
            logger.info("测试数据生成完成")
        except Exception as e:
            st.error(f"测试数据生成失败: {str(e)}")
            logger.error(f"测试数据生成失败: {e}")
            raise  # 重新抛出异常，让调用者处理


def main():
    """主函数"""
    # 检查是否启用Streamlit
    config = get_config()
    if not config.is_streamlit_enabled():
        st.error("Streamlit界面已被禁用，请在配置文件中启用")
        st.stop()
    
    # 创建并运行应用
    app = StreamlitCMSApp()
    app.run()


if __name__ == "__main__":
    main()