# -*- coding: utf-8 -*-
"""
图表生成工具模块
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import base64
import io
from loguru import logger

# 设置中文字体
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei', 'DejaVu Sans', 'Arial Unicode MS']
except:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class VibrationChartGenerator:
    """振动分析图表生成器"""
    
    def __init__(self, style: str = "seaborn-v0_8"):
        self.style = style
        self.colors = {
            "normal": "#2E8B57",
            "warning": "#FF8C00",
            "alarm": "#DC143C",
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "accent": "#2ca02c"
        }
        
        # 设置seaborn样式
        try:
            plt.style.use(self.style)
        except:
            plt.style.use('default')
        
        sns.set_palette("husl")
    
    def create_time_series_chart(self, signal: np.ndarray, sampling_rate: float = 2048, 
                               title: str = "时域波形", save_path: Optional[str] = None) -> str:
        """创建时域波形图"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 生成时间轴
            time = np.arange(len(signal)) / sampling_rate
            
            # 绘制波形
            ax.plot(time, signal, color=self.colors["primary"], linewidth=0.8)
            ax.set_xlabel("时间 (s)")
            ax.set_ylabel("振幅")
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            # 添加统计信息
            rms_value = np.sqrt(np.mean(signal**2))
            peak_value = np.max(np.abs(signal))
            ax.text(0.02, 0.98, f"RMS: {rms_value:.3f}\nPeak: {peak_value:.3f}", 
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # 转换为base64字符串
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"创建时域波形图失败: {e}")
            plt.close()
            return ""
    
    def create_frequency_spectrum(self, frequencies: np.ndarray, magnitudes: np.ndarray,
                                title: str = "频谱图", save_path: Optional[str] = None) -> str:
        """创建频谱图"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 绘制频谱
            ax.plot(frequencies, magnitudes, color=self.colors["secondary"], linewidth=1.2)
            ax.set_xlabel("频率 (Hz)")
            ax.set_ylabel("幅值")
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            # 标记主频率
            main_freq_idx = np.argmax(magnitudes)
            main_freq = frequencies[main_freq_idx]
            main_amp = magnitudes[main_freq_idx]
            
            ax.plot(main_freq, main_amp, 'ro', markersize=8, label=f'主频率: {main_freq:.1f} Hz')
            ax.legend()
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # 转换为base64字符串
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"创建频谱图失败: {e}")
            plt.close()
            return ""
    
    def create_waterfall_chart(self, time_freq_data: Dict[str, Any], 
                             title: str = "瀑布图", save_path: Optional[str] = None) -> str:
        """创建瀑布图（时频分析）"""
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 假设数据格式：{"timestamps": [...], "frequencies": [...], "magnitudes": [...]}
            timestamps = time_freq_data.get("timestamps", [])
            frequencies = time_freq_data.get("frequencies", [])
            magnitudes = time_freq_data.get("magnitudes", [])
            
            if len(timestamps) == 0 or len(frequencies) == 0:
                logger.warning("瀑布图数据不足")
                plt.close()
                return ""
            
            # 创建网格
            X, Y = np.meshgrid(frequencies, range(len(timestamps)))
            Z = np.array(magnitudes)
            
            # 绘制瀑布图
            contour = ax.contourf(X, Y, Z, levels=50, cmap='viridis')
            ax.set_xlabel("频率 (Hz)")
            ax.set_ylabel("时间序列")
            ax.set_title(title)
            
            # 添加颜色条
            cbar = plt.colorbar(contour)
            cbar.set_label("幅值")
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # 转换为base64字符串
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"创建瀑布图失败: {e}")
            plt.close()
            return ""
    
    def create_trend_chart(self, trend_data: List[Dict[str, Any]], 
                         feature_name: str = "rms_value",
                         title: str = "趋势图", save_path: Optional[str] = None) -> str:
        """创建趋势图"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 提取数据
            timestamps = []
            values = []
            alarm_levels = []
            
            for data_point in trend_data:
                if "timestamp" in data_point and feature_name in data_point:
                    try:
                        timestamp = datetime.fromisoformat(data_point["timestamp"])
                        timestamps.append(timestamp)
                        values.append(data_point[feature_name])
                        alarm_levels.append(data_point.get("alarm_level", "normal"))
                    except:
                        continue
            
            if len(timestamps) == 0:
                logger.warning("趋势图数据不足")
                plt.close()
                return ""
            
            # 绘制趋势线
            ax.plot(timestamps, values, color=self.colors["primary"], 
                   linewidth=2, marker='o', markersize=4)
            
            # 根据报警级别着色
            for i, level in enumerate(alarm_levels):
                color = self.colors.get(level, self.colors["normal"])
                ax.plot(timestamps[i], values[i], 'o', color=color, markersize=6)
            
            # 设置坐标轴
            ax.set_xlabel("时间")
            ax.set_ylabel(feature_name.replace("_", " ").title())
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            # 格式化时间轴
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            plt.xticks(rotation=45)
            
            # 添加报警线
            if len(values) > 0:
                mean_val = float(np.mean(values))
                std_val = float(np.std(values))
                ax.axhline(y=mean_val + 2*std_val, color=self.colors["warning"], 
                          linestyle='--', alpha=0.7, label='警告线')
                ax.axhline(y=mean_val + 3*std_val, color=self.colors["alarm"], 
                          linestyle='--', alpha=0.7, label='报警线')
                ax.legend()
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # 转换为base64字符串
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"创建趋势图失败: {e}")
            plt.close()
            return ""
    
    def create_bearing_analysis_chart(self, analysis_result: Dict[str, Any],
                                    title: str = "轴承分析图", save_path: Optional[str] = None) -> str:
        """创建轴承分析图"""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # 1. 时域波形
            if "time_domain" in analysis_result:
                time_data = analysis_result["time_domain"]
                signal_length = time_data.get("length", 1000)
                sampling_rate = time_data.get("sampling_rate", 2048)
                
                # 生成示例信号用于显示
                t = np.linspace(0, signal_length/sampling_rate, signal_length)
                example_signal = np.random.randn(signal_length) * 0.1
                
                ax1.plot(t, example_signal, color=self.colors["primary"], linewidth=0.8)
                ax1.set_title("时域波形")
                ax1.set_xlabel("时间 (s)")
                ax1.set_ylabel("振幅")
                ax1.grid(True, alpha=0.3)
            
            # 2. 频谱图
            if "frequency_domain" in analysis_result:
                freq_data = analysis_result["frequency_domain"]
                frequencies = freq_data.get("frequencies", np.linspace(0, 1000, 500))
                magnitudes = freq_data.get("magnitudes", np.random.exponential(0.1, len(frequencies)))
                
                ax2.plot(frequencies, magnitudes, color=self.colors["secondary"], linewidth=1.2)
                ax2.set_title("频谱图")
                ax2.set_xlabel("频率 (Hz)")
                ax2.set_ylabel("幅值")
                ax2.grid(True, alpha=0.3)
                
                # 标记轴承特征频率
                if "bearing_frequencies" in analysis_result:
                    bearing_freqs = analysis_result["bearing_frequencies"]
                    for freq_name, freq_value in bearing_freqs.items():
                        if freq_name != "rotation_frequency" and freq_value < max(frequencies):
                            ax2.axvline(x=freq_value, color=self.colors["alarm"], 
                                      linestyle='--', alpha=0.7, label=freq_name)
                    ax2.legend()
            
            # 3. 包络谱
            if "envelope_analysis" in analysis_result:
                envelope_data = analysis_result["envelope_analysis"]
                envelope_freqs = envelope_data.get("envelope_frequencies", np.linspace(0, 500, 250))
                envelope_mags = envelope_data.get("envelope_magnitudes", np.random.exponential(0.05, len(envelope_freqs)))
                
                ax3.plot(envelope_freqs, envelope_mags, color=self.colors["accent"], linewidth=1.2)
                ax3.set_title("包络谱")
                ax3.set_xlabel("频率 (Hz)")
                ax3.set_ylabel("包络幅值")
                ax3.grid(True, alpha=0.3)
            
            # 4. 阶次分析
            if "order_analysis" in analysis_result:
                order_data = analysis_result["order_analysis"]
                main_orders = order_data.get("main_orders", [])
                
                if main_orders:
                    orders = [order["order"] for order in main_orders]
                    amplitudes = [order["amplitude"] for order in main_orders]
                    
                    ax4.bar(orders, amplitudes, color=self.colors["primary"], alpha=0.7)
                    ax4.set_title("阶次分析")
                    ax4.set_xlabel("阶次")
                    ax4.set_ylabel("幅值")
                    ax4.grid(True, alpha=0.3)
                else:
                    ax4.text(0.5, 0.5, "无阶次数据", ha='center', va='center', transform=ax4.transAxes)
                    ax4.set_title("阶次分析")
            
            plt.suptitle(title, fontsize=16)
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # 转换为base64字符串
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"创建轴承分析图失败: {e}")
            plt.close()
            return ""
    
    def create_turbine_overview_chart(self, turbine_data: Dict[str, Any],
                                    title: str = "风机总览图", save_path: Optional[str] = None) -> str:
        """创建风机总览图"""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # 1. 各测点RMS值对比
            measurement_points = turbine_data.get("measurement_points", {})
            if measurement_points:
                points = list(measurement_points.keys())
                rms_values = [point_data.get("rms_value", 0) for point_data in measurement_points.values()]
                alarm_levels = [point_data.get("alarm_level", "normal") for point_data in measurement_points.values()]
                
                colors = [self.colors.get(level, self.colors["normal"]) for level in alarm_levels]
                bars = ax1.bar(points, rms_values, color=colors, alpha=0.7)
                ax1.set_title("各测点RMS值")
                ax1.set_ylabel("RMS值")
                ax1.tick_params(axis='x', rotation=45)
                ax1.grid(True, alpha=0.3)
                
                # 添加数值标签
                for bar, value in zip(bars, rms_values):
                    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                            f'{value:.3f}', ha='center', va='bottom')
            
            # 2. 报警级别分布
            if measurement_points:
                alarm_counts = {"normal": 0, "warning": 0, "alarm": 0}
                for point_data in measurement_points.values():
                    level = point_data.get("alarm_level", "normal")
                    alarm_counts[level] += 1
                
                labels = list(alarm_counts.keys())
                sizes = list(alarm_counts.values())
                colors_pie = [self.colors[label] for label in labels]
                
                ax2.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
                ax2.set_title("报警级别分布")
            
            # 3. 主频率分布
            if measurement_points:
                main_freqs = []
                for point_data in measurement_points.values():
                    freq = point_data.get("main_frequency", 0)
                    if freq > 0:
                        main_freqs.append(freq)
                
                if main_freqs:
                    ax3.hist(main_freqs, bins=10, color=self.colors["primary"], alpha=0.7, edgecolor='black')
                    ax3.set_title("主频率分布")
                    ax3.set_xlabel("频率 (Hz)")
                    ax3.set_ylabel("数量")
                    ax3.grid(True, alpha=0.3)
            
            # 4. 健康度评分
            health_score = turbine_data.get("health_score", 85)
            
            # 创建仪表盘样式的健康度显示
            theta = np.linspace(0, np.pi, 100)
            r = np.ones_like(theta)
            
            # 背景扇形
            ax4.fill_between(theta, 0, r, color='lightgray', alpha=0.3)
            
            # 健康度扇形
            health_theta = np.linspace(0, np.pi * health_score / 100, int(health_score))
            health_r = np.ones_like(health_theta)
            
            if health_score >= 80:
                color = self.colors["normal"]
            elif health_score >= 60:
                color = self.colors["warning"]
            else:
                color = self.colors["alarm"]
            
            ax4.fill_between(health_theta, 0, health_r, color=color, alpha=0.7)
            
            # 添加文字
            ax4.text(np.pi/2, 0.5, f'{health_score}%', ha='center', va='center', 
                    fontsize=20, fontweight='bold')
            ax4.text(np.pi/2, 0.2, '健康度', ha='center', va='center', fontsize=12)
            
            ax4.set_xlim(0, np.pi)
            ax4.set_ylim(0, 1.2)
            ax4.set_aspect('equal')
            ax4.axis('off')
            ax4.set_title("设备健康度")
            
            plt.suptitle(title, fontsize=16)
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # 转换为base64字符串
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"创建风机总览图失败: {e}")
            plt.close()
            return ""
    
    def create_interactive_plotly_chart(self, data: Dict[str, Any], chart_type: str = "time_series") -> str:
        """创建交互式Plotly图表"""
        try:
            fig = go.Figure()  # 初始化fig变量
            
            if chart_type == "time_series":
                # 添加时域信号
                if "signal" in data and "time" in data:
                    fig.add_trace(go.Scatter(
                        x=data["time"],
                        y=data["signal"],
                        mode='lines',
                        name='振动信号',
                        line=dict(color='blue', width=1)
                    ))
                
                fig.update_layout(
                    title="交互式时域波形",
                    xaxis_title="时间 (s)",
                    yaxis_title="振幅",
                    hovermode='x unified'
                )
            
            elif chart_type == "frequency":
                if "frequencies" in data and "magnitudes" in data:
                    fig.add_trace(go.Scatter(
                        x=data["frequencies"],
                        y=data["magnitudes"],
                        mode='lines',
                        name='频谱',
                        line=dict(color='orange', width=2)
                    ))
                
                fig.update_layout(
                    title="交互式频谱图",
                    xaxis_title="频率 (Hz)",
                    yaxis_title="幅值",
                    hovermode='x unified'
                )
            
            # 转换为HTML字符串
            html_str = fig.to_html(include_plotlyjs='cdn')
            return html_str
            
        except Exception as e:
            logger.error(f"创建交互式图表失败: {e}")
            return ""
    
    def create_chart_with_text_annotation(self, chart_data: Dict[str, Any], 
                                        polished_text: str,
                                        chart_type: str = "time_series",
                                        title: str = "图文组合分析",
                                        save_path: Optional[str] = None) -> str:
        """创建带文本注释的图表组合"""
        try:
            # 创建图表和文本的组合布局
            fig, (ax_chart, ax_text) = plt.subplots(2, 1, figsize=(12, 10), 
                                                   gridspec_kw={'height_ratios': [3, 1]})
            
            # 根据图表类型生成相应图表
            if chart_type == "time_series" and "signal" in chart_data:
                signal = chart_data["signal"]
                sampling_rate = chart_data.get("sampling_rate", 2048)
                time = np.arange(len(signal)) / sampling_rate
                
                ax_chart.plot(time, signal, color=self.colors["primary"], linewidth=0.8)
                ax_chart.set_xlabel("时间 (s)")
                ax_chart.set_ylabel("振幅")
                ax_chart.set_title(f"{title} - 时域波形")
                ax_chart.grid(True, alpha=0.3)
                
            elif chart_type == "frequency" and "frequencies" in chart_data:
                frequencies = chart_data["frequencies"]
                magnitudes = chart_data["magnitudes"]
                
                ax_chart.plot(frequencies, magnitudes, color=self.colors["secondary"], linewidth=1.2)
                ax_chart.set_xlabel("频率 (Hz)")
                ax_chart.set_ylabel("幅值")
                ax_chart.set_title(f"{title} - 频谱图")
                ax_chart.grid(True, alpha=0.3)
                
            elif chart_type == "trend" and "trend_data" in chart_data:
                trend_data = chart_data["trend_data"]
                timestamps = []
                values = []
                
                for data_point in trend_data:
                    if "timestamp" in data_point and "value" in data_point:
                        try:
                            timestamp = datetime.fromisoformat(data_point["timestamp"])
                            timestamps.append(timestamp)
                            values.append(data_point["value"])
                        except:
                            continue
                
                if timestamps and values:
                    ax_chart.plot(timestamps, values, color=self.colors["primary"], 
                                linewidth=2, marker='o', markersize=4)
                    ax_chart.set_xlabel("时间")
                    ax_chart.set_ylabel("数值")
                    ax_chart.set_title(f"{title} - 趋势图")
                    ax_chart.grid(True, alpha=0.3)
                    
                    # 格式化时间轴
                    ax_chart.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                    plt.setp(ax_chart.xaxis.get_majorticklabels(), rotation=45)
            
            # 添加文本注释区域
            ax_text.axis('off')  # 隐藏坐标轴
            
            # 处理长文本，自动换行
            import textwrap
            wrapped_text = textwrap.fill(polished_text, width=80)
            
            ax_text.text(0.05, 0.95, "分析结论:", transform=ax_text.transAxes, 
                        fontsize=12, fontweight='bold', verticalalignment='top')
            ax_text.text(0.05, 0.85, wrapped_text, transform=ax_text.transAxes, 
                        fontsize=10, verticalalignment='top', wrap=True,
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.3))
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # 转换为base64字符串
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"创建图文组合失败: {e}")
            plt.close()
            return ""
    
    def create_multi_chart_report(self, charts_data: List[Dict[str, Any]], 
                                polished_texts: List[str],
                                report_title: str = "振动分析报告",
                                save_path: Optional[str] = None) -> str:
        """创建多图表报告，每个图表配对相应的润色文本"""
        try:
            num_charts = len(charts_data)
            if num_charts == 0:
                logger.warning("没有图表数据")
                return ""
            
            # 确保文本数量与图表数量匹配
            if len(polished_texts) < num_charts:
                polished_texts.extend(["暂无分析结论"] * (num_charts - len(polished_texts)))
            
            # 计算子图布局
            cols = 1
            rows = num_charts * 2  # 每个图表占用两行（图表+文本）
            
            fig = plt.figure(figsize=(12, 6 * num_charts))
            
            for i, (chart_data, text) in enumerate(zip(charts_data, polished_texts)):
                # 图表子图
                ax_chart = plt.subplot(rows, cols, i * 2 + 1)
                
                chart_type = chart_data.get("type", "time_series")
                chart_title = chart_data.get("title", f"图表 {i+1}")
                
                if chart_type == "time_series" and "signal" in chart_data:
                    signal = chart_data["signal"]
                    sampling_rate = chart_data.get("sampling_rate", 2048)
                    time = np.arange(len(signal)) / sampling_rate
                    
                    ax_chart.plot(time, signal, color=self.colors["primary"], linewidth=0.8)
                    ax_chart.set_xlabel("时间 (s)")
                    ax_chart.set_ylabel("振幅")
                    ax_chart.set_title(chart_title)
                    ax_chart.grid(True, alpha=0.3)
                    
                elif chart_type == "frequency" and "frequencies" in chart_data:
                    frequencies = chart_data["frequencies"]
                    magnitudes = chart_data["magnitudes"]
                    
                    ax_chart.plot(frequencies, magnitudes, color=self.colors["secondary"], linewidth=1.2)
                    ax_chart.set_xlabel("频率 (Hz)")
                    ax_chart.set_ylabel("幅值")
                    ax_chart.set_title(chart_title)
                    ax_chart.grid(True, alpha=0.3)
                
                # 文本子图
                ax_text = plt.subplot(rows, cols, i * 2 + 2)
                ax_text.axis('off')
                
                # 处理长文本
                import textwrap
                wrapped_text = textwrap.fill(text, width=80)
                
                ax_text.text(0.05, 0.95, f"分析结论 {i+1}:", transform=ax_text.transAxes, 
                            fontsize=11, fontweight='bold', verticalalignment='top')
                ax_text.text(0.05, 0.80, wrapped_text, transform=ax_text.transAxes, 
                            fontsize=9, verticalalignment='top',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.3))
            
            plt.suptitle(report_title, fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # 转换为base64字符串
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"创建多图表报告失败: {e}")
            plt.close()
            return ""
    
    def combine_chart_and_conclusion(self, chart_base64: str, conclusion_text: str, 
                                   chart_title: str = "分析图表") -> Dict[str, Any]:
        """组合图表和结论文本，返回结构化数据"""
        try:
            # 创建图文组合的结构化数据
            combined_data = {
                "chart_image": chart_base64,
                "conclusion_text": conclusion_text,
                "chart_title": chart_title,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "image_format": "base64_png",
                    "text_length": len(conclusion_text),
                    "has_chart": bool(chart_base64),
                    "has_text": bool(conclusion_text.strip())
                }
            }
            
            # 提取文本关键信息
            if conclusion_text:
                # 简单的关键词提取
                keywords = []
                key_terms = ["频率", "振幅", "RMS", "峰值", "趋势", "异常", "正常", "报警", "轴承", "齿轮"]
                for term in key_terms:
                    if term in conclusion_text:
                        keywords.append(term)
                
                combined_data["keywords"] = keywords
                combined_data["summary"] = conclusion_text[:100] + "..." if len(conclusion_text) > 100 else conclusion_text
            
            logger.info(f"成功组合图表和结论: {chart_title}")
            return combined_data
            
        except Exception as e:
            logger.error(f"组合图表和结论失败: {e}")
            return {}
    
    def generate_chart_text_pairs(self, analysis_results: Dict[str, Any], 
                                conclusions: Dict[str, str]) -> List[Dict[str, Any]]:
        """生成图表-文本配对列表"""
        try:
            pairs = []
            
            # 时域分析配对
            if "time_domain" in analysis_results and "time_domain" in conclusions:
                time_chart = self.create_time_series_chart(
                    analysis_results["time_domain"].get("signal", np.random.randn(1000)),
                    analysis_results["time_domain"].get("sampling_rate", 2048),
                    "时域波形分析"
                )
                if time_chart:
                    pair = self.combine_chart_and_conclusion(
                        time_chart, conclusions["time_domain"], "时域波形分析"
                    )
                    pairs.append(pair)
            
            # 频域分析配对
            if "frequency_domain" in analysis_results and "frequency_domain" in conclusions:
                freq_data = analysis_results["frequency_domain"]
                freq_chart = self.create_frequency_spectrum(
                    freq_data.get("frequencies", np.linspace(0, 1000, 500)),
                    freq_data.get("magnitudes", np.random.exponential(0.1, 500)),
                    "频谱分析"
                )
                if freq_chart:
                    pair = self.combine_chart_and_conclusion(
                        freq_chart, conclusions["frequency_domain"], "频谱分析"
                    )
                    pairs.append(pair)
            
            # 轴承分析配对
            if "bearing_analysis" in analysis_results and "bearing_analysis" in conclusions:
                bearing_chart = self.create_bearing_analysis_chart(
                    analysis_results["bearing_analysis"], "轴承分析"
                )
                if bearing_chart:
                    pair = self.combine_chart_and_conclusion(
                        bearing_chart, conclusions["bearing_analysis"], "轴承分析"
                    )
                    pairs.append(pair)
            
            logger.info(f"生成了 {len(pairs)} 个图表-文本配对")
            return pairs
            
        except Exception as e:
            logger.error(f"生成图表-文本配对失败: {e}")
            return []

# 便捷函数
def generate_vibration_charts(analysis_data: Dict[str, Any], output_dir: str = "./charts") -> Dict[str, str]:
    """生成振动分析图表的便捷函数"""
    generator = VibrationChartGenerator()
    charts = {}
    
    try:
        # 时域波形图
        if "time_domain" in analysis_data:
            # 生成示例信号
            signal_length = analysis_data["time_domain"].get("length", 1000)
            sampling_rate = analysis_data["time_domain"].get("sampling_rate", 2048)
            example_signal = np.random.randn(signal_length) * 0.1
            
            charts["time_series"] = generator.create_time_series_chart(
                example_signal, sampling_rate, "时域波形图")
        
        # 频谱图
        if "frequency_domain" in analysis_data:
            freq_data = analysis_data["frequency_domain"]
            frequencies = freq_data.get("frequencies", np.linspace(0, 1000, 500))
            magnitudes = freq_data.get("magnitudes", np.random.exponential(0.1, len(frequencies)))
            
            charts["frequency"] = generator.create_frequency_spectrum(
                frequencies, magnitudes, "频谱图")
        
        # 轴承分析图
        if "bearing_analysis" in analysis_data:
            charts["bearing"] = generator.create_bearing_analysis_chart(
                analysis_data["bearing_analysis"], "轴承分析图")
        
        return charts
        
    except Exception as e:
        logger.error(f"生成振动分析图表失败: {e}")
        return {}

if __name__ == "__main__":
    # 测试代码
    generator = VibrationChartGenerator()
    
    # 生成测试信号
    t = np.linspace(0, 1, 2048)
    signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100 * t) + 0.1 * np.random.randn(len(t))
    
    # 创建时域图
    time_chart = generator.create_time_series_chart(signal, 2048, "测试时域波形")
    print(f"时域图表生成完成，长度: {len(time_chart)}")
    
    # 创建频谱图
    fft_result = np.fft.fft(signal)
    frequencies = np.fft.fftfreq(len(signal), 1/2048)[:len(signal)//2]
    magnitudes = np.abs(fft_result)[:len(signal)//2] / len(signal) * 2
    
    freq_chart = generator.create_frequency_spectrum(frequencies, magnitudes, "测试频谱图")
    print(f"频谱图表生成完成，长度: {len(freq_chart)}")