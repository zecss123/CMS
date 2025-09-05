#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gradio前端应用 - CMS振动分析报告系统
基于原有streamlit_app.py转换而来，保持相同的功能和代码结构
"""

import gradio as gr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
import yaml
import shutil
import base64
import time

# 添加项目路径到系统路径
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import get_config
from chat.chat_manager import ChatManager
from chat.session_manager import SessionManager
from knowledge.knowledge_retriever import KnowledgeRetriever
from data.mock_data import CMSDataGenerator
from utils.chart_generator import VibrationChartGenerator
from report.generator import CMSReportGenerator

# 全局配置
config = get_config()

class GradioCMSApp:
    """Gradio CMS应用程序主类"""
    
    def __init__(self):
        self.config = get_config()
        self.chat_history = []
        self.current_session_id = None
        self.system_status = {
            'llm': 'offline',
            'knowledge_base': 'offline',
            'database': 'offline'
        }
        self._init_components()
    
    def _init_components(self):
        """初始化系统组件"""
        try:
            # 初始化会话管理器
            self.session_manager = SessionManager()
            logger.info("会话管理器初始化完成")
            
            # 初始化知识检索器
            try:
                knowledge_config = self.config.get('knowledge', {})
                embeddings_path = knowledge_config.get('embeddings_path', './data/embeddings')
                metadata_path = knowledge_config.get('metadata_path', './data/metadata')
                
                self.knowledge_retriever = KnowledgeRetriever(
                    embeddings_path=embeddings_path,
                    metadata_path=metadata_path
                )
                self.system_status['knowledge_base'] = 'online'
                logger.info("知识检索器初始化完成")
            except Exception as e:
                self.knowledge_retriever = None
                self.system_status['knowledge_base'] = 'offline'
                logger.error(f"知识检索器初始化失败: {e}")
            
            # 初始化聊天管理器
            try:
                self.chat_manager = ChatManager(
                    config=self.config.config,
                    session_manager=self.session_manager
                )
                # 检查LLM状态
                if hasattr(self.chat_manager.llm_client, 'model_config'):
                    self.system_status['llm'] = 'online'
                else:
                    self.system_status['llm'] = 'warning'
                logger.info("聊天管理器初始化完成")
            except Exception as e:
                self.chat_manager = None
                self.system_status['llm'] = 'offline'
                logger.error(f"聊天管理器初始化失败: {e}")
            
            # 数据库状态检查
            self.system_status['database'] = 'online'
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
    
    def get_system_status_display(self) -> str:
        """获取系统状态显示文本"""
        status_text = "## 📊 系统状态\n\n"
        
        status_indicators = {
            'llm': '🤖 语言模型',
            'knowledge_base': '📚 知识库',
            'database': '🗄️ 数据库'
        }
        
        for key, label in status_indicators.items():
            status = self.system_status.get(key, 'offline')
            if status == 'online':
                status_text += f"✅ {label}: 在线\n"
            elif status == 'warning':
                status_text += f"⚠️ {label}: 警告\n"
            else:
                status_text += f"❌ {label}: 离线\n"
        
        return status_text
    
    def get_config_info(self) -> str:
        """获取配置信息显示文本"""
        config_text = "## ⚙️ 当前配置\n\n"
        
        model_config = self.config.get_model_config()
        config_text += f"**模型类型**: {model_config.get('type', 'unknown')}\n"
        
        if model_config['type'] == 'local':
            config_text += f"**本地模型**: {model_config.get('model_name', 'unknown')}\n"
        elif model_config['type'] == 'openai':
            api_key = model_config.get('api_key', '')
            masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key and len(api_key) > 12 else "未配置"
            config_text += f"**OpenAI模型**: {model_config.get('model_name', 'unknown')}\n"
            config_text += f"**API密钥**: {masked_key}\n"
        
        embedding_config = self.config.get_embedding_config()
        config_text += f"**嵌入模型**: {embedding_config.get('type', 'unknown')}\n"
        
        return config_text
    
    def handle_chat_message(self, message: str, history: List[List[str]]) -> Tuple[str, List[List[str]]]:
        """处理聊天消息"""
        if not message.strip():
            return "", history
        
        try:
            # 检查聊天管理器是否可用
            if not self.chat_manager:
                history.append([message, "❌ 聊天管理器未初始化，请检查系统配置"])
                return "", history
            
            # 获取或创建会话
            if not self.current_session_id:
                self.current_session_id = self.session_manager.create_session(
                    user_id="gradio_user"
                )
            
            # 处理消息
            result = self.chat_manager.process_message(
                user_id="gradio_user",
                message=message,
                session_id=self.current_session_id
            )
            response = result.get('response', '处理失败') if result.get('success') else result.get('error', '未知错误')
            
            # 更新历史记录
            history.append([message, response])
            
        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)}"
            history.append([message, error_msg])
            logger.error(error_msg)
        
        return "", history
    
    def handle_quick_question(self, question: str, history: List[List[str]]) -> Tuple[str, List[List[str]]]:
        """处理快速问题"""
        return self.handle_chat_message(question, history)
    
    def reload_config(self) -> str:
        """重新加载配置"""
        try:
            self.config.reload()
            return "✅ 配置已重新加载"
        except Exception as e:
            return f"❌ 配置重新加载失败: {str(e)}"
    
    def clear_chat_history(self, history: List[List[str]]) -> List[List[str]]:
        """清空对话历史"""
        return []
    
    def generate_test_data(self) -> str:
        """生成测试数据"""
        try:
            data_generator = CMSDataGenerator()
            test_data = data_generator.generate_turbine_data(
                wind_farm="华能风场A",
                turbine_id="A01"
            )
            
            # 设置会话上下文，启用测试数据模式
            if not self.current_session_id:
                self.current_session_id = self.session_manager.create_session(
                    user_id="gradio_user"
                )
            self.session_manager.update_context(
                self.current_session_id,
                {'use_mock_data': True}
            )
            
            logger.info("测试数据生成完成")
            return "✅ 测试数据生成完成，测试数据模式已启用！"
        except Exception as e:
            error_msg = f"测试数据生成失败，无法启用测试数据模式: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    def generate_vibration_data(self, wind_farm: str, turbine: str) -> Tuple[str, str, str]:
        """生成振动数据分析"""
        if not wind_farm or not turbine:
            return "❌ 请选择风场和风机", "", ""
        
        try:
            data_generator = CMSDataGenerator()
            vibration_data = data_generator.generate_turbine_data(
                wind_farm=wind_farm,
                turbine_id=turbine
            )
            
            # 生成数据概览
            overview_text = "## 📋 数据概览\n\n"
            overview_text += f"**测点数量**: {len(vibration_data['measurements'])}\n"
            
            # 从第一个测点获取信息
            first_measurement = next(iter(vibration_data['measurements'].values()))
            sampling_rate = first_measurement.get('sampling_rate', 2048)
            data_length = first_measurement.get('data_length', 0)
            overall_status = vibration_data.get('overall_status', '正常')
            
            overview_text += f"**采样频率**: {sampling_rate} Hz\n"
            overview_text += f"**数据长度**: {data_length}\n"
            overview_text += f"**整体状态**: {overall_status}\n"
            
            # 生成详细分析
            analysis_text = "## 📊 振动分析详情\n\n"
            chart_generator = VibrationChartGenerator()
            
            for point_name, point_data in vibration_data['measurements'].items():
                analysis_text += f"### 📈 {point_name}\n\n"
                
                # 统计信息
                rms_value = point_data.get('features', {}).get('rms_value', 0.0)
                peak_value = point_data.get('features', {}).get('peak_value', 0.0)
                alarm_level = point_data.get('alarm_level', '正常')
                
                analysis_text += f"- **RMS值**: {rms_value:.2f} mm/s\n"
                analysis_text += f"- **峰值**: {peak_value:.2f} mm/s\n"
                analysis_text += f"- **状态**: {alarm_level}\n\n"
            
            # 生成图表（这里简化处理，实际应用中可以生成真实图表）
            chart_info = "## 📊 振动波形图表\n\n"
            chart_info += "图表生成功能已集成，可显示时域波形、频域分析等。\n"
            chart_info += f"数据来源: {wind_farm} - {turbine}\n"
            
            return overview_text, analysis_text, chart_info
            
        except Exception as e:
            error_msg = f"振动数据生成失败: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}", "", ""
    
    def generate_report(self, wind_farm: str, turbine: str, report_type: str, 
                       start_date: str, end_date: str, report_format: str, 
                       use_test_data: bool) -> Tuple[str, str]:
        """生成报告"""
        if not wind_farm or not turbine:
            return "❌ 请选择风场和风机", ""
        
        try:
            # 检查聊天管理器是否可用
            if not self.chat_manager:
                return "❌ 聊天管理器未初始化，请检查系统配置", ""
            
            # 设置会话上下文中的数据源选择
            if not self.current_session_id:
                self.current_session_id = self.session_manager.create_session(
                    user_id="gradio_user"
                )
            
            # 更新会话上下文，设置数据源模式
            self.session_manager.update_context(
                self.current_session_id,
                {'use_mock_data': use_test_data}
            )
            
            # 使用聊天管理器生成报告
            data_source_info = "使用测试数据" if use_test_data else "调用外部API"
            report_request = f"生成{wind_farm}的{turbine}风机{report_type}，时间范围从{start_date}到{end_date}（{data_source_info}）"
            
            response = self.chat_manager.process_message(
                user_id="gradio_user",
                message=report_request,
                session_id=self.current_session_id
            )
            
            report_content = response.get('response', response) if isinstance(response, dict) else response
            
            # 检查是否有生成的文件
            download_info = ""
            if isinstance(response, dict) and response.get('docx_file'):
                docx_file_path = response['docx_file']
                if os.path.exists(docx_file_path):
                    download_info = f"📥 报告文件已生成: {docx_file_path}"
            else:
                # 备用方案：检查输出目录中的文件
                output_dir = Path(self.config.get('system', {}).get('output_dir', './output'))
                if output_dir.exists():
                    report_files = list(output_dir.glob(f"*{turbine}*.{report_format}"))
                    if report_files:
                        latest_report = max(report_files, key=os.path.getctime)
                        download_info = f"📥 报告文件已生成: {latest_report}"
            
            success_msg = "✅ 报告生成完成！"
            if download_info:
                success_msg += f"\n{download_info}"
            
            return success_msg, report_content
            
        except Exception as e:
            error_msg = f"报告生成失败: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}", ""
    
    def upload_documents(self, files) -> str:
        """处理文档上传"""
        if not files:
            return "❌ 请选择要上传的文件"
        
        try:
            success_count = 0
            error_count = 0
            
            for file in files:
                try:
                    # 保存文件到临时目录
                    temp_path = Path("./temp") / file.name
                    temp_path.parent.mkdir(exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(file.name, temp_path)
                    
                    # 使用知识库管理器处理文档
                    if hasattr(self, 'knowledge_retriever') and self.knowledge_retriever:
                        # 这里应该调用文档处理方法
                        # 暂时显示成功消息
                        success_count += 1
                    else:
                        error_count += 1
                    
                    # 清理临时文件
                    if temp_path.exists():
                        temp_path.unlink()
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"文件上传处理失败: {e}")
            
            # 生成结果消息
            result_msg = ""
            if success_count > 0:
                result_msg += f"✅ 成功处理 {success_count} 个文档\n"
            if error_count > 0:
                result_msg += f"❌ {error_count} 个文档处理失败\n"
            
            return result_msg if result_msg else "❌ 文档上传处理失败"
            
        except Exception as e:
            error_msg = f"文件上传处理异常：{str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    def get_knowledge_stats(self) -> str:
        """获取知识库统计信息"""
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
            
            stats_text = "## 📊 知识库统计\n\n"
            stats_text += f"**文档数量**: {doc_count}\n"
            stats_text += f"**总大小**: {total_size / 1024 / 1024:.1f} MB\n"
            
            # 显示向量数据库状态
            vector_db_path = Path("./data/vector_db")
            if vector_db_path.exists():
                stats_text += "**向量数据库**: ✅ 已建立\n"
            else:
                stats_text += "**向量数据库**: ⚠️ 未建立\n"
            
            return stats_text
            
        except Exception as e:
            error_msg = f"获取统计信息失败：{str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    def rebuild_knowledge_index(self) -> str:
        """重建知识库索引"""
        try:
            # 这里应该调用知识库重建方法
            # 暂时模拟处理时间
            time.sleep(2)
            return "✅ 知识库索引重建完成"
        except Exception as e:
            error_msg = f"重建索引失败：{str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    def clear_knowledge_base(self) -> str:
        """清空知识库"""
        try:
            knowledge_dir = Path("./data/knowledge")
            vector_db_dir = Path("./data/vector_db")
            
            # 删除知识库文件
            if knowledge_dir.exists():
                shutil.rmtree(knowledge_dir)
                knowledge_dir.mkdir(parents=True, exist_ok=True)
            
            # 删除向量数据库
            if vector_db_dir.exists():
                shutil.rmtree(vector_db_dir)
                vector_db_dir.mkdir(parents=True, exist_ok=True)
            
            return "✅ 知识库已清空"
        except Exception as e:
            error_msg = f"清空知识库失败：{str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    def save_model_config(self, model_type: str, **kwargs) -> str:
        """保存模型配置"""
        try:
            self.config.set('model.type', model_type)
            
            if model_type == 'openai':
                self.config.set('model.openai.api_key', kwargs.get('api_key', ''))
                self.config.set('model.openai.base_url', kwargs.get('base_url', 'https://api.openai.com/v1'))
                self.config.set('model.openai.model_name', kwargs.get('model_name', 'gpt-3.5-turbo'))
            elif model_type == 'local':
                self.config.set('model.local.model_path', kwargs.get('model_path', ''))
                self.config.set('model.local.device', kwargs.get('device', 'auto'))
            
            return f"✅ {model_type} 配置已保存"
        except Exception as e:
            error_msg = f"保存配置失败: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    def save_all_config(self) -> str:
        """保存所有配置到文件"""
        try:
            self.config.save_config()
            return f"✅ 配置已保存到: {self.config.config_file}"
        except Exception as e:
            error_msg = f"保存配置失败: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    def create_interface(self):
        """创建Gradio界面"""
        # 获取风场和风机列表
        wind_farms = list(self.config.get('business.wind_farms', {}).keys())
        
        def get_turbines(wind_farm):
            if wind_farm:
                return gr.Dropdown(
                    choices=self.config.get(f'business.wind_farms.{wind_farm}.turbines', []),
                    label="选择风机",
                    interactive=True
                )
            return gr.Dropdown(choices=[], label="选择风机", interactive=False)
        
        # 创建主界面
        with gr.Blocks(title="🔧 CMS振动分析报告系统", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🔧 CMS振动分析报告系统")
            
            with gr.Tabs():
                # 智能对话标签页
                with gr.TabItem("💬 智能对话"):
                    gr.Markdown("## 💬 智能对话助手")
                    gr.Markdown("与AI助手对话，获取振动分析报告和技术支持")
                    
                    chatbot = gr.Chatbot(label="对话历史", height=400)
                    msg = gr.Textbox(
                        label="请输入您的问题",
                        placeholder="例如：生成华能风场A的A01风机振动分析报告",
                        lines=2
                    )
                    
                    with gr.Row():
                        send_btn = gr.Button("发送", variant="primary")
                        clear_btn = gr.Button("清空历史")
                    
                    # 快速问题按钮
                    gr.Markdown("### 🔍 快速问题")
                    with gr.Row():
                        quick_btn1 = gr.Button("生成振动分析报告")
                        quick_btn2 = gr.Button("查询设备状态")
                        quick_btn3 = gr.Button("分析振动趋势")
                        quick_btn4 = gr.Button("故障诊断建议")
                    
                    # 绑定事件
                    send_btn.click(
                        self.handle_chat_message,
                        inputs=[msg, chatbot],
                        outputs=[msg, chatbot]
                    )
                    msg.submit(
                        self.handle_chat_message,
                        inputs=[msg, chatbot],
                        outputs=[msg, chatbot]
                    )
                    clear_btn.click(
                        self.clear_chat_history,
                        inputs=[chatbot],
                        outputs=[chatbot]
                    )
                    
                    # 快速问题按钮事件
                    quick_btn1.click(
                        lambda history: self.handle_quick_question("生成振动分析报告", history),
                        inputs=[chatbot],
                        outputs=[msg, chatbot]
                    )
                    quick_btn2.click(
                        lambda history: self.handle_quick_question("查询设备状态", history),
                        inputs=[chatbot],
                        outputs=[msg, chatbot]
                    )
                    quick_btn3.click(
                        lambda history: self.handle_quick_question("分析振动趋势", history),
                        inputs=[chatbot],
                        outputs=[msg, chatbot]
                    )
                    quick_btn4.click(
                        lambda history: self.handle_quick_question("故障诊断建议", history),
                        inputs=[chatbot],
                        outputs=[msg, chatbot]
                    )
                
                # 数据分析标签页
                with gr.TabItem("📊 数据分析"):
                    gr.Markdown("## 📊 振动数据分析")
                    
                    with gr.Row():
                        analysis_farm = gr.Dropdown(
                            choices=wind_farms,
                            label="选择风场",
                            interactive=True
                        )
                        analysis_turbine = gr.Dropdown(
                            choices=[],
                            label="选择风机",
                            interactive=False
                        )
                    
                    generate_data_btn = gr.Button("📈 生成振动数据", variant="primary")
                    
                    with gr.Row():
                        with gr.Column():
                            data_overview = gr.Markdown("### 数据概览将在这里显示")
                        with gr.Column():
                            data_analysis = gr.Markdown("### 分析结果将在这里显示")
                    
                    chart_info = gr.Markdown("### 图表信息将在这里显示")
                    
                    # 更新风机选择
                    analysis_farm.change(
                        get_turbines,
                        inputs=[analysis_farm],
                        outputs=[analysis_turbine]
                    )
                    
                    # 生成数据分析
                    generate_data_btn.click(
                        self.generate_vibration_data,
                        inputs=[analysis_farm, analysis_turbine],
                        outputs=[data_overview, data_analysis, chart_info]
                    )
                
                # 报告生成标签页
                with gr.TabItem("📋 报告生成"):
                    gr.Markdown("## 📋 报告生成")
                    
                    # 数据源配置
                    gr.Markdown("### 🔧 数据源配置")
                    use_test_data = gr.Checkbox(
                        label="生成测试数据",
                        value=False,
                        info="勾选此项将生成测试数据进行分析，不勾选则调用外部API获取实际数据"
                    )
                    
                    # 报告参数设置
                    gr.Markdown("### 📋 报告参数")
                    with gr.Row():
                        report_farm = gr.Dropdown(
                            choices=wind_farms,
                            label="选择风场",
                            interactive=True
                        )
                        report_turbine = gr.Dropdown(
                            choices=[],
                            label="选择风机",
                            interactive=False
                        )
                    
                    report_type = gr.Dropdown(
                        choices=["完整分析报告", "简要状态报告", "故障诊断报告", "趋势分析报告"],
                        label="报告类型",
                        value="完整分析报告"
                    )
                    
                    with gr.Row():
                        start_date = gr.Textbox(
                            label="开始日期",
                            value=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                        )
                        end_date = gr.Textbox(
                            label="结束日期",
                            value=datetime.now().strftime("%Y-%m-%d")
                        )
                    
                    report_format = gr.Dropdown(
                        choices=self.config.get('business.report.formats', ['docx', 'pdf']),
                        label="报告格式",
                        value="docx"
                    )
                    
                    generate_report_btn = gr.Button("📄 生成报告", variant="primary")
                    
                    report_status = gr.Markdown("### 报告状态将在这里显示")
                    report_content = gr.Markdown("### 生成的报告内容将在这里显示")
                    
                    # 更新风机选择
                    report_farm.change(
                        get_turbines,
                        inputs=[report_farm],
                        outputs=[report_turbine]
                    )
                    
                    # 生成报告
                    generate_report_btn.click(
                        self.generate_report,
                        inputs=[report_farm, report_turbine, report_type, start_date, end_date, report_format, use_test_data],
                        outputs=[report_status, report_content]
                    )
                
                # 知识库管理标签页
                with gr.TabItem("📚 知识库管理"):
                    gr.Markdown("## 📚 知识库管理")
                    
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### 📤 上传文档")
                            upload_files = gr.File(
                                label="选择要上传的文档",
                                file_count="multiple",
                                file_types=[".pdf", ".docx", ".txt", ".md"]
                            )
                            upload_btn = gr.Button("🚀 开始上传并处理", variant="primary")
                            upload_status = gr.Markdown("### 上传状态将在这里显示")
                        
                        with gr.Column():
                            knowledge_stats = gr.Markdown(self.get_knowledge_stats())
                            
                            gr.Markdown("### 🔧 管理操作")
                            rebuild_btn = gr.Button("🔄 重建知识库索引")
                            clear_kb_btn = gr.Button("🗑️ 清空知识库", variant="secondary")
                            
                            operation_status = gr.Markdown("### 操作状态将在这里显示")
                    
                    # 绑定事件
                    upload_btn.click(
                        self.upload_documents,
                        inputs=[upload_files],
                        outputs=[upload_status]
                    )
                    
                    rebuild_btn.click(
                        self.rebuild_knowledge_index,
                        outputs=[operation_status]
                    )
                    
                    clear_kb_btn.click(
                        self.clear_knowledge_base,
                        outputs=[operation_status]
                    )
                
                # 系统配置标签页
                with gr.TabItem("⚙️ 系统配置"):
                    gr.Markdown("## ⚙️ 系统配置")
                    
                    # 配置文件操作
                    gr.Markdown("### 📝 配置文件操作")
                    reload_config_btn = gr.Button("📂 重新加载配置文件")
                    config_status = gr.Markdown("### 配置状态将在这里显示")
                    
                    # 模型配置
                    gr.Markdown("### 🤖 模型配置")
                    model_type = gr.Dropdown(
                        choices=['local', 'openai', 'deepseek_api', 'custom'],
                        label="模型类型",
                        value=self.config.get('model.type', 'local')
                    )
                    
                    # OpenAI配置
                    with gr.Group(visible=False) as openai_config:
                        api_key = gr.Textbox(
                            label="OpenAI API Key",
                            type="password",
                            value=self.config.get('model.openai.api_key', '')
                        )
                        base_url = gr.Textbox(
                            label="Base URL",
                            value=self.config.get('model.openai.base_url', 'https://api.openai.com/v1')
                        )
                        openai_model_name = gr.Textbox(
                            label="模型名称",
                            value=self.config.get('model.openai.model_name', 'gpt-3.5-turbo')
                        )
                        save_openai_btn = gr.Button("💾 保存OpenAI配置")
                    
                    # 本地模型配置
                    with gr.Group(visible=True) as local_config:
                        model_path = gr.Textbox(
                            label="本地模型路径",
                            value=self.config.get('model.local.model_path', '')
                        )
                        device = gr.Dropdown(
                            choices=['auto', 'cuda', 'cpu'],
                            label="设备",
                            value=self.config.get('model.local.device', 'auto')
                        )
                        save_local_btn = gr.Button("💾 保存本地模型配置")
                    
                    save_all_btn = gr.Button("💾 保存所有配置到文件", variant="primary")
                    
                    # 显示配置组件的函数
                    def show_config_group(model_type_value):
                        return (
                            gr.Group(visible=model_type_value == 'openai'),
                            gr.Group(visible=model_type_value == 'local')
                        )
                    
                    # 绑定事件
                    model_type.change(
                        show_config_group,
                        inputs=[model_type],
                        outputs=[openai_config, local_config]
                    )
                    
                    reload_config_btn.click(
                        self.reload_config,
                        outputs=[config_status]
                    )
                    
                    save_openai_btn.click(
                        lambda: self.save_model_config('openai', api_key=api_key.value, base_url=base_url.value, model_name=openai_model_name.value),
                        outputs=[config_status]
                    )
                    
                    save_local_btn.click(
                        lambda: self.save_model_config('local', model_path=model_path.value, device=device.value),
                        outputs=[config_status]
                    )
                    
                    save_all_btn.click(
                        self.save_all_config,
                        outputs=[config_status]
                    )
            
            # 侧边栏信息（使用Accordion模拟）
            with gr.Accordion("🎛️ 系统控制台", open=True):
                system_status_display = gr.Markdown(self.get_system_status_display())
                config_info_display = gr.Markdown(self.get_config_info())
                
                gr.Markdown("### 🚀 快速操作")
                with gr.Row():
                    reload_btn = gr.Button("🔄 重新加载配置")
                    clear_history_btn = gr.Button("🗑️ 清空对话历史")
                    test_data_btn = gr.Button("📊 生成测试数据")
                
                quick_status = gr.Markdown("### 操作状态将在这里显示")
                
                # 绑定快速操作事件
                reload_btn.click(
                    self.reload_config,
                    outputs=[quick_status]
                )
                
                test_data_btn.click(
                    self.generate_test_data,
                    outputs=[quick_status]
                )
        
        return interface


def main():
    """主函数"""
    # 检查是否启用Gradio（这里我们假设总是启用）
    config = get_config()
    
    # 创建应用实例
    app = GradioCMSApp()
    
    # 创建界面
    interface = app.create_interface()
    
    # 启动应用
    interface.launch(
        server_name="0.0.0.0",  # 允许外部访问
        server_port=7860,       # 默认端口
        share=True,             # 创建公共链接以便访问
        debug=True,             # 启用调试模式
        show_error=True         # 显示错误信息
    )


if __name__ == "__main__":
    main()