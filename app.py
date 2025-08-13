# -*- coding: utf-8 -*-
"""
CMS振动分析报告系统主应用程序
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

# 导入自定义模块
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import (
    MODEL_CONFIG, VECTOR_DB_CONFIG, CMS_CONFIG, 
    WIND_FARM_CONFIG, REPORT_CONFIG
)
from data.mock_data import CMSDataGenerator
from rag.llm_handler import DeepSeekLLMHandler
from rag.vector_store import KnowledgeBase
from rag.chain import CMSAnalysisChain
from utils.data_processor import VibrationDataProcessor, process_vibration_signal
from utils.chart_generator import VibrationChartGenerator, generate_vibration_charts
from report.generator import CMSReportGenerator, generate_cms_report

# 配置页面
st.set_page_config(
    page_title="CMS振动分析报告系统",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
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

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid #1f77b4;
    margin: 0.5rem 0;
}

.status-normal {
    color: #28a745;
    font-weight: bold;
}

.status-warning {
    color: #ffc107;
    font-weight: bold;
}

.status-attention {
    color: #ff9800;
    font-weight: bold;
}

.status-alarm {
    color: #dc3545;
    font-weight: bold;
}

.sidebar-section {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

class CMSApp:
    """CMS振动分析应用程序主类"""
    
    def __init__(self):
        self.data_generator = CMSDataGenerator()
        self.chart_generator = VibrationChartGenerator()
        self.report_generator = CMSReportGenerator()
        self.data_processor = VibrationDataProcessor()
        
        # 初始化会话状态
        self._init_session_state()
        
        # 初始化组件
        self._init_components()
    
    def _init_session_state(self):
        """初始化会话状态"""
        if 'llm_initialized' not in st.session_state:
            st.session_state.llm_initialized = False
        
        if 'knowledge_base_initialized' not in st.session_state:
            st.session_state.knowledge_base_initialized = False
        
        if 'current_data' not in st.session_state:
            st.session_state.current_data = None
        
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        
        if 'generated_charts' not in st.session_state:
            st.session_state.generated_charts = {}
    
    def _init_components(self):
        """初始化系统组件"""
        try:
            # 初始化知识库
            if not st.session_state.knowledge_base_initialized:
                with st.spinner("初始化知识库..."):
                    self.knowledge_base = KnowledgeBase()
                    st.session_state.knowledge_base_initialized = True
                    logger.info("知识库初始化完成")
            
            # 初始化LLM（延迟加载）
            if not st.session_state.llm_initialized:
                self.llm_handler = None
            else:
                self.llm_handler = DeepSeekLLMHandler()
                self.llm_handler.load_model()
            
            # 初始化分析链
            try:
                self.analysis_chain = CMSAnalysisChain()
                if not self.analysis_chain.initialized:
                    logger.warning("分析链初始化不完整，部分功能可能受限")
            except Exception as e:
                logger.error(f"分析链初始化失败: {e}")
                # 创建一个基础的分析链实例
                self.analysis_chain = CMSAnalysisChain()
            
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
        self._render_main_content()
    
    def _render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.header("⚙️ 系统控制")
            
            # LLM初始化控制
            if st.button("🚀 初始化LLM模型", disabled=st.session_state.llm_initialized):
                self._initialize_llm()
            
            # 显示系统状态
            st.subheader("📊 系统状态")
            
            llm_status = "✅ 已就绪" if st.session_state.llm_initialized else "❌ 未初始化"
            kb_status = "✅ 已就绪" if st.session_state.knowledge_base_initialized else "❌ 未初始化"
            
            st.write(f"**LLM模型**: {llm_status}")
            st.write(f"**知识库**: {kb_status}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 数据生成控制
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.header("📈 数据生成")
            
            # 风场选择
            wind_farm_options = list(WIND_FARM_CONFIG["farms"].keys())
            selected_farm = st.selectbox("选择风场", wind_farm_options)
            
            # 风机选择
            selected_turbine = None
            if selected_farm:
                turbine_options = WIND_FARM_CONFIG["farms"][selected_farm]["turbines"]
                selected_turbine = st.selectbox("选择风机", turbine_options)
            
            # 故障模式选择
            fault_patterns = ["normal", "imbalance", "misalignment", "bearing_fault", "gearbox_fault", "looseness"]
            selected_pattern = st.selectbox("故障模式", fault_patterns)
            
            # 生成数据按钮
            if st.button("🎲 生成测试数据") and selected_turbine:
                self._generate_test_data(selected_farm, selected_turbine, selected_pattern)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def _initialize_llm(self):
        """初始化LLM模型"""
        try:
            with st.spinner("正在初始化LLM模型，请稍候..."):
                self.llm_handler = DeepSeekLLMHandler()
                if self.llm_handler.load_model():
                    st.session_state.llm_initialized = True
                    st.success("✅ LLM模型初始化成功！")
                    logger.info("LLM模型初始化完成")
                else:
                    st.error("❌ LLM模型加载失败")
                    logger.error("LLM模型加载失败")
        except Exception as e:
            st.error(f"❌ LLM模型初始化失败: {e}")
            logger.error(f"LLM模型初始化失败: {e}")
    
    def _generate_test_data(self, wind_farm: str, turbine_id: str, fault_pattern: str):
        """生成测试数据"""
        try:
            with st.spinner("正在生成测试数据..."):
                # 生成风机数据
                turbine_data = self.data_generator.generate_turbine_data(
                    wind_farm=wind_farm,
                    turbine_id=turbine_id
                )
                
                st.session_state.current_data = turbine_data
                st.success(f"✅ 已生成 {wind_farm}-{turbine_id} 的测试数据（故障模式: {fault_pattern}）")
                logger.info(f"生成测试数据: {wind_farm}-{turbine_id}-{fault_pattern}")
        
        except Exception as e:
            st.error(f"❌ 数据生成失败: {e}")
            logger.error(f"数据生成失败: {e}")
    
    def _render_main_content(self):
        """渲染主内容区域"""
        # 创建标签页
        tab1, tab2, tab3, tab4 = st.tabs(["📊 数据概览", "🔍 智能分析", "📈 图表展示", "📄 报告生成"])
        
        with tab1:
            self._render_data_overview()
        
        with tab2:
            self._render_intelligent_analysis()
        
        with tab3:
            self._render_chart_display()
        
        with tab4:
            self._render_report_generation()
    
    def _render_data_overview(self):
        """渲染数据概览页面"""
        st.header("📊 振动数据概览")
        
        if st.session_state.current_data is None:
            st.info("📝 请先在侧边栏生成测试数据")
            return
        
        data = st.session_state.current_data
        
        # 基本信息
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("风场", data.get("wind_farm", "-"))
        
        with col2:
            st.metric("风机编号", data.get("turbine_id", "-"))
        
        with col3:
            st.metric("测量时间", data.get("timestamp", "-")[:16] if data.get("timestamp") else "-")
        
        with col4:
            health_score = data.get("health_score", 0)
            st.metric("健康度评分", f"{health_score}%")
        
        # 测点数据表格
        st.subheader("📍 各测点数据")
        
        measurement_points = data.get("measurements", {})
        if measurement_points:
            # 构建数据表格
            table_data = []
            for point_name, point_data in measurement_points.items():
                features = point_data.get('features', {})
                table_data.append({
                    "测点": point_name,
                    "RMS值": f"{features.get('rms_value', 0):.3f}",
                    "峰值": f"{features.get('peak_value', 0):.3f}",
                    "主频率(Hz)": f"{features.get('main_frequency', 0):.1f}",
                    "报警级别": point_data.get("alarm_level", "normal")
                })
            
            df = pd.DataFrame(table_data)
            
            # 根据报警级别着色
            def color_alarm_level(val):
                if val == "alarm":
                    return 'background-color: #ffebee'
                elif val == "warning":
                    return 'background-color: #fff3e0'
                elif val == "注意":
                    return 'background-color: #fff8e1'
                elif val == "normal":
                    return 'background-color: #e8f5e8'
                return ''
            
            styled_df = df.style.applymap(color_alarm_level, subset=['报警级别'])
            st.dataframe(styled_df, use_container_width=True)
        
        # 统计信息
        if measurement_points:
            st.subheader("📈 统计信息")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # 计算统计数据
            alarm_counts = {"normal": 0, "注意": 0, "warning": 0, "alarm": 0}
            rms_values = []
            
            for point_data in measurement_points.values():
                level = point_data.get("alarm_level", "normal")
                if level in alarm_counts:
                    alarm_counts[level] += 1
                else:
                    # 处理未知状态，归类到注意
                    alarm_counts["注意"] += 1
                features = point_data.get('features', {})
                rms_values.append(features.get("rms_value", 0))
            
            with col1:
                st.metric("正常测点", alarm_counts["normal"], delta=None)
            
            with col2:
                st.metric("注意测点", alarm_counts["注意"], delta=None)
            
            with col3:
                st.metric("警告测点", alarm_counts["warning"], delta=None)
            
            with col4:
                st.metric("报警测点", alarm_counts["alarm"], delta=None)
            
            # RMS值分布
            if rms_values:
                st.subheader("📊 RMS值分布")
                chart_data = pd.DataFrame({
                    "测点": list(measurement_points.keys()),
                    "RMS值": rms_values
                })
                st.bar_chart(chart_data.set_index("测点"))
    
    def _render_intelligent_analysis(self):
        """渲染智能分析页面"""
        st.header("🔍 智能振动分析")
        
        if not st.session_state.llm_initialized:
            st.warning("⚠️ 请先在侧边栏初始化LLM模型")
            return
        
        if st.session_state.current_data is None:
            st.info("📝 请先生成测试数据")
            return
        
        # 分析控制
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("🎯 分析选项")
        
        with col2:
            if st.button("🚀 开始分析", type="primary"):
                self._perform_intelligent_analysis()
        
        # 显示分析结果
        if st.session_state.analysis_results:
            self._display_analysis_results()
    
    def _perform_intelligent_analysis(self):
        """执行智能分析"""
        try:
            with st.spinner("🤖 正在进行智能分析，请稍候..."):
                data = st.session_state.current_data
                
                # 使用分析链进行分析
                analysis_results = self.analysis_chain.analyze_turbine_all_points(
                    data.get("wind_farm", ""), 
                    data.get("turbine_id", "")
                )
                
                st.session_state.analysis_results = analysis_results
                st.success("✅ 智能分析完成！")
                logger.info("智能分析完成")
        
        except Exception as e:
            st.error(f"❌ 智能分析失败: {e}")
            logger.error(f"智能分析失败: {e}")
    
    def _display_analysis_results(self):
        """显示分析结果"""
        results = st.session_state.analysis_results
        
        if not results:
            return
        
        st.subheader("🎯 分析结果")
        
        # 总体评估
        if "overall_assessment" in results:
            st.markdown("### 📋 总体评估")
            st.write(results["overall_assessment"])
        
        # 各测点分析
        if "point_analyses" in results:
            st.markdown("### 📍 各测点详细分析")
            
            for point_name, analysis in results["point_analyses"].items():
                with st.expander(f"📊 {point_name} 分析结果"):
                    st.write(analysis)
        
        # 故障诊断
        if "fault_diagnosis" in results:
            st.markdown("### 🔧 故障诊断")
            st.write(results["fault_diagnosis"])
        
        # 建议措施
        if "recommendations" in results:
            st.markdown("### 💡 建议措施")
            recommendations = results["recommendations"]
            if isinstance(recommendations, list):
                for i, rec in enumerate(recommendations, 1):
                    st.write(f"{i}. {rec}")
            else:
                st.write(recommendations)
    
    def _render_chart_display(self):
        """渲染图表展示页面"""
        st.header("📈 振动分析图表")
        
        if st.session_state.current_data is None:
            st.info("📝 请先生成测试数据")
            return
        
        # 图表生成控制
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("🎨 图表选项")
            chart_types = st.multiselect(
                "选择要生成的图表类型",
                ["时域波形", "频谱图", "趋势图", "设备总览"],
                default=["时域波形", "频谱图"]
            )
        
        with col2:
            if st.button("📊 生成图表", type="primary"):
                self._generate_charts(chart_types)
        
        # 显示生成的图表
        self._display_charts()
    
    def _generate_charts(self, chart_types: List[str]):
        """生成图表"""
        try:
            with st.spinner("🎨 正在生成图表..."):
                data = st.session_state.current_data
                charts = {}
                
                # 生成各种类型的图表
                for chart_type in chart_types:
                    if chart_type == "时域波形":
                        # 为第一个测点生成时域波形
                        measurement_points = data.get("measurements", {})
                        if measurement_points:
                            first_point = list(measurement_points.keys())[0]
                            # 生成示例信号
                            signal = self.data_generator.generate_time_series(
                                fault_type=data.get("fault_pattern", "正常")
                            )
                            chart_data = self.chart_generator.create_time_series_chart(
                                signal, title=f"{first_point} 时域波形"
                            )
                            charts["时域波形"] = chart_data
                    
                    elif chart_type == "频谱图":
                        # 生成频谱图
                        signal = self.data_generator.generate_time_series(
                            fault_type=data.get("fault_pattern", "正常")
                        )
                        # 进行FFT分析
                        fft_result = np.fft.fft(signal)
                        frequencies = np.fft.fftfreq(len(signal), 1/2048)[:len(signal)//2]
                        magnitudes = np.abs(fft_result)[:len(signal)//2] / len(signal) * 2
                        
                        chart_data = self.chart_generator.create_frequency_spectrum(
                            frequencies, magnitudes, title="频谱分析"
                        )
                        charts["频谱图"] = chart_data
                    
                    elif chart_type == "设备总览":
                        chart_data = self.chart_generator.create_turbine_overview_chart(
                            data, title=f"{data.get('turbine_id', 'Unknown')} 设备总览"
                        )
                        charts["设备总览"] = chart_data
                
                st.session_state.generated_charts = charts
                st.success(f"✅ 已生成 {len(charts)} 个图表！")
                logger.info(f"生成图表: {list(charts.keys())}")
        
        except Exception as e:
            st.error(f"❌ 图表生成失败: {e}")
            logger.error(f"图表生成失败: {e}")
    
    def _display_charts(self):
        """显示图表"""
        charts = st.session_state.generated_charts
        
        if not charts:
            st.info("📊 暂无图表，请先生成图表")
            return
        
        st.subheader("📊 生成的图表")
        
        for chart_name, chart_data in charts.items():
            if chart_data:
                st.markdown(f"### {chart_name}")
                # 解码并显示图表
                import base64
                image_data = base64.b64decode(chart_data)
                st.image(image_data, use_column_width=True)
    
    def _render_report_generation(self):
        """渲染报告生成页面"""
        st.header("📄 分析报告生成")
        
        if st.session_state.current_data is None:
            st.info("📝 请先生成测试数据")
            return
        
        # 报告配置
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚙️ 报告配置")
            
            report_title = st.text_input("报告标题", value="CMS振动分析报告")
            report_format = st.selectbox("报告格式", ["PDF", "HTML", "Word"])
            
            # 基本信息
            st.subheader("📋 基本信息")
            operator = st.text_input("测量人员", value="系统自动")
            equipment_status = st.text_input("设备状态", value="运行中")
        
        with col2:
            st.subheader("📊 报告内容")
            
            include_summary = st.checkbox("包含执行摘要", value=True)
            include_charts = st.checkbox("包含分析图表", value=True)
            include_analysis = st.checkbox("包含智能分析", value=True)
            include_recommendations = st.checkbox("包含建议措施", value=True)
        
        # 生成报告按钮
        if st.button("📄 生成报告", type="primary"):
            self._generate_report(
                report_title, report_format, operator, equipment_status,
                include_summary, include_charts, include_analysis, include_recommendations
            )
    
    def _generate_report(self, title: str, format_type: str, operator: str, 
                        equipment_status: str, include_summary: bool, 
                        include_charts: bool, include_analysis: bool, 
                        include_recommendations: bool):
        """生成报告"""
        try:
            with st.spinner(f"📄 正在生成{format_type}报告..."):
                data = st.session_state.current_data
                
                # 构建报告数据
                report_data = {
                    "title": title,
                    "basic_info": {
                        "wind_farm": data.get("wind_farm", "-"),
                        "turbine_id": data.get("turbine_id", "-"),
                        "measurement_date": data.get("timestamp", "-")[:10] if data.get("timestamp") else "-",
                        "report_date": datetime.now().strftime("%Y-%m-%d"),
                        "operator": operator,
                        "equipment_status": equipment_status
                    }
                }
                
                # 添加执行摘要
                if include_summary:
                    health_score = data.get("health_score", 85)
                    if health_score >= 80:
                        summary = "设备运行状态良好，各项振动指标均在正常范围内。"
                    elif health_score >= 60:
                        summary = "设备运行状态一般，部分振动指标需要关注。"
                    else:
                        summary = "设备运行状态较差，存在明显的振动异常，需要立即处理。"
                    
                    report_data["executive_summary"] = summary
                
                # 添加测量结果
                measurement_points = data.get("measurements", {})
                if measurement_points:
                    results = []
                    for point_name, point_data in measurement_points.items():
                        features = point_data.get('features', {})
                        results.append({
                            "measurement_point": point_name,
                            "rms_value": features.get("rms_value", 0),
                            "peak_value": features.get("peak_value", 0),
                            "main_frequency": features.get("main_frequency", 0),
                            "alarm_level": point_data.get("alarm_level", "normal")
                        })
                    report_data["measurement_results"] = results
                
                # 添加图表
                if include_charts and st.session_state.generated_charts:
                    report_data["charts"] = st.session_state.generated_charts
                
                # 添加分析结果
                if include_analysis and st.session_state.analysis_results:
                    analysis = st.session_state.analysis_results
                    report_data["analysis_conclusion"] = analysis.get("overall_assessment", "分析完成")
                
                # 添加建议措施
                if include_recommendations:
                    recommendations = [
                        "定期监测设备振动状态",
                        "及时更换磨损部件",
                        "保持设备良好润滑",
                        "建议下次检测时间：3个月后"
                    ]
                    report_data["recommendations"] = recommendations
                
                # 生成报告文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_ext = "docx" if format_type.lower() == "word" else format_type.lower()
                filename = f"cms_report_{timestamp}.{file_ext}"
                
                success = generate_cms_report(report_data, filename, format_type.lower())
                
                if success:
                    st.success(f"✅ {format_type}报告生成成功！文件名: {filename}")
                    
                    # 提供下载链接
                    if os.path.exists(filename):
                        with open(filename, "rb") as file:
                            st.download_button(
                                label=f"📥 下载{format_type}报告",
                                data=file.read(),
                                file_name=filename,
                                mime=self._get_mime_type(format_type)
                            )
                else:
                    st.error(f"❌ {format_type}报告生成失败")
        
        except Exception as e:
            st.error(f"❌ 报告生成失败: {e}")
            logger.error(f"报告生成失败: {e}")
    
    def _get_mime_type(self, format_type: str) -> str:
        """获取MIME类型"""
        mime_types = {
            "PDF": "application/pdf",
            "HTML": "text/html",
            "Word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        return mime_types.get(format_type, "application/octet-stream")

def main():
    """主函数"""
    try:
        # 配置日志
        logger.add("logs/cms_app.log", rotation="1 day", retention="7 days")
        
        # 创建并运行应用
        app = CMSApp()
        app.run()
        
    except Exception as e:
        st.error(f"应用程序启动失败: {e}")
        logger.error(f"应用程序启动失败: {e}")

if __name__ == "__main__":
    main()