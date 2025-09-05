#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析系统 - 离线演示版本
无需网络连接，使用模拟数据演示完整功能
"""

import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入现有模块
try:
    from api.embedding_client import EmbeddingClient, get_embedding_client
    from api.real_cms_client import RealCMSAPIClient
except ImportError as e:
    logger.warning(f"模块导入失败: {e}，使用基础功能")
    RealCMSAPIClient = None

class MockCMSAPIClient:
    """模拟CMS API客户端，生成测试数据"""
    
    def __init__(self):
        self.base_url = "http://mock-api/services"
        np.random.seed(42)  # 固定随机种子，确保结果可重现
    
    def fetch_vibration_data(self, region: str, station: str, position: str, 
                           point: str, features: str, start_time: str, end_time: str) -> pd.DataFrame:
        """生成模拟振动数据"""
        logger.info(f"生成模拟振动数据: {region}-{station}-{position}-{point}")
        
        # 解析时间范围
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        
        # 生成时间序列（每10分钟一个数据点）
        time_range = pd.date_range(start=start_dt, end=end_dt, freq='10T')
        n_points = len(time_range)
        
        # 生成模拟数据
        data = {
            'Time': time_range,
            'Sample_Rate': np.full(n_points, 25600.0),  # 固定采样率
            'Speed': np.random.normal(1500, 50, n_points),  # 转速，均值1500rpm，标准差50
            'Time_Domain_RMS_Value': self._generate_rms_values(n_points),
            'Time_Domain_10_5000Hz_Acceleration_RMS': self._generate_acceleration_rms(n_points)
        }
        
        df = pd.DataFrame(data)
        logger.info(f"生成了{len(df)}条模拟振动数据")
        return df
    
    def _generate_rms_values(self, n_points: int) -> np.ndarray:
        """生成RMS值，模拟真实的振动模式"""
        # 基础RMS值，正常范围0.3-0.8
        base_rms = np.random.normal(0.5, 0.1, n_points)
        
        # 添加一些异常值模拟故障
        anomaly_indices = np.random.choice(n_points, size=max(1, n_points//20), replace=False)
        base_rms[anomaly_indices] += np.random.normal(0.3, 0.1, len(anomaly_indices))
        
        # 确保值为正数
        base_rms = np.abs(base_rms)
        
        return base_rms
    
    def _generate_acceleration_rms(self, n_points: int) -> np.ndarray:
        """生成加速度RMS值"""
        # 加速度RMS通常比位移RMS大
        acc_rms = np.random.normal(2.0, 0.5, n_points)
        return np.abs(acc_rms)
    
    def run_analysis_model(self, model_id: str, wfid: str, run_date: str = "0") -> str:
        """模拟模型分析结果"""
        logger.info(f"运行模拟分析模型: {model_id}")
        
        # 模拟分析结果
        results = [
            "✅ 设备运行状态正常",
            "📊 振动水平在正常范围内",
            "🔧 建议继续监控，无需立即维护",
            "📈 趋势分析显示设备性能稳定"
        ]
        
        # 随机选择一些结果
        selected_results = np.random.choice(results, size=2, replace=False)
        return "\n".join(selected_results)
    
    def generate_chart(self, region: str, station: str, position: str, 
                      point: str, features: str, start_time: str, end_time: str, 
                      output_path: Optional[str] = None) -> str:
        """模拟生成图表"""
        if output_path is None:
            output_path = f"mock_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib import font_manager
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 生成模拟时间序列数据
            time_points = pd.date_range(start=start_time, end=end_time, periods=100)
            
            # 生成模拟振动数据（RMS值）
            base_value = 0.5
            noise = np.random.normal(0, 0.1, 100)
            trend = np.sin(np.linspace(0, 4*np.pi, 100)) * 0.2
            rms_values = base_value + trend + noise
            rms_values = np.abs(rms_values)  # 确保为正值
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 绘制RMS趋势线
            ax.plot(time_points, rms_values, 'b-', linewidth=2, label='RMS值')
            ax.fill_between(time_points, rms_values, alpha=0.3)
            
            # 添加报警线
            ax.axhline(y=1.0, color='orange', linestyle='--', alpha=0.7, label='警告线')
            ax.axhline(y=1.5, color='red', linestyle='--', alpha=0.7, label='报警线')
            
            # 设置标题和标签
            ax.set_title(f'振动分析图表 - {region}-{station}-{position}-{point}', fontsize=14, fontweight='bold')
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('RMS值', fontsize=12)
            
            # 格式化时间轴
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            plt.xticks(rotation=45)
            
            # 添加网格和图例
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # 添加统计信息文本框
            stats_text = f'特征: {features}\n平均值: {np.mean(rms_values):.3f}\n最大值: {np.max(rms_values):.3f}\n最小值: {np.min(rms_values):.3f}'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            
            # 保存图表
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"模拟图表已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成模拟图表失败: {e}")
            # 如果matplotlib不可用，创建一个简单的占位图片
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                # 创建一个简单的图片
                img = Image.new('RGB', (800, 400), color='white')
                draw = ImageDraw.Draw(img)
                
                # 绘制简单的图表框架
                draw.rectangle([50, 50, 750, 350], outline='black', width=2)
                
                # 添加标题文字
                try:
                    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
                except:
                    font = ImageFont.load_default()
                
                title = f'Mock Chart - {region}-{station}-{position}-{point}'
                draw.text((60, 60), title, fill='black', font=font)
                draw.text((60, 90), f'Features: {features}', fill='black', font=font)
                draw.text((60, 120), f'Time: {start_time} ~ {end_time}', fill='black', font=font)
                draw.text((60, 300), 'This is a mock chart for demonstration', fill='gray', font=font)
                
                # 绘制简单的趋势线
                for i in range(10):
                    x1 = 100 + i * 60
                    y1 = 200 + np.sin(i * 0.5) * 50
                    x2 = 100 + (i + 1) * 60
                    y2 = 200 + np.sin((i + 1) * 0.5) * 50
                    draw.line([(x1, y1), (x2, y2)], fill='blue', width=2)
                
                img.save(output_path)
                logger.info(f"简单模拟图表已保存到: {output_path}")
                return output_path
                
            except Exception as e2:
                logger.error(f"创建简单图表也失败: {e2}")
                return output_path
    
    def test_connection(self) -> bool:
        """测试连接（模拟客户端总是返回True）"""
        logger.info("模拟API客户端连接测试")
        return True

class CMSOfflineDemo:
    """CMS离线演示应用"""
    
    def __init__(self, use_real_api: bool = False):
        # 根据配置选择API客户端
        if use_real_api and RealCMSAPIClient is not None:
            try:
                self.api_client = RealCMSAPIClient()
                logger.info("使用真实API客户端")
            except Exception as e:
                logger.warning(f"真实API客户端初始化失败: {e}，回退到模拟客户端")
                self.api_client = MockCMSAPIClient()
        else:
            self.api_client = MockCMSAPIClient()
            if use_real_api and RealCMSAPIClient is None:
                logger.warning("真实API客户端不可用，使用模拟客户端")
            else:
                logger.info("使用模拟API客户端")
        
        # 初始化Embedding客户端
        try:
            embedding_client_func = globals().get('get_embedding_client')
            if embedding_client_func:
                self.embedding_client = embedding_client_func()
                logger.info("Embedding客户端初始化成功")
            else:
                self.embedding_client = None
        except Exception as e:
            logger.warning(f"Embedding客户端初始化失败: {e}")
            self.embedding_client = None
        
        # 模拟配置
        self.config = {
            "default_region": "A08",
            "default_station": "1003", 
            "default_position": "8",
            "default_features": "Sample_Rate,Speed,Time_Domain_RMS_Value,Time_Domain_10_5000Hz_Acceleration_RMS",
            "default_model_id": "906"
        }
    
    def analyze_vibration_data(self, region: str, station: str, position: str, 
                             point: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """分析振动数据（离线模式）"""
        logger.info(f"开始离线分析振动数据: {region}-{station}-{position}-{point}")
        
        try:
            # 1. 获取模拟振动数据
            features = self.config.get("default_features", "Time_Domain_RMS_Value")
            df = self.api_client.fetch_vibration_data(
                region, station, position, point, features, start_time, end_time
            )
            
            # 2. 运行模拟分析模型
            model_id = self.config.get("default_model_id", "906")
            model_result = self.api_client.run_analysis_model(model_id, station)
            
            # 3. 生成模拟可视化图表
            chart_path = self.api_client.generate_chart(
                region, station, position, point, "Time_Domain_RMS_Value", 
                start_time, end_time
            )
            
            # 4. 数据统计分析
            stats = self._calculate_statistics(df)
            
            # 5. 生成分析报告
            report = self._generate_analysis_report(df, stats, model_result, chart_path)
            
            # 6. 准备HTML报告数据
            report_data = self._prepare_report_data(df, stats, model_result, chart_path)
            
            return {
                "success": True,
                "data": df,
                "statistics": stats,
                "model_result": model_result,
                "chart_path": chart_path,
                "report": report,
                "report_data": report_data
            }
            
        except Exception as e:
            logger.error(f"振动数据分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算统计信息"""
        stats = {}
        
        # 基础统计
        stats["record_count"] = len(df)
        stats["time_range"] = {
            "start": df['Time'].min().strftime('%Y-%m-%d %H:%M:%S') if 'Time' in df.columns else None,
            "end": df['Time'].max().strftime('%Y-%m-%d %H:%M:%S') if 'Time' in df.columns else None
        }
        
        # 振动数据统计
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_columns:
            if 'RMS' in col or 'Speed' in col:
                stats[col] = {
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "median": float(df[col].median())
                }
        
        return stats
    
    def _generate_analysis_report(self, df: pd.DataFrame, stats: Dict[str, Any], 
                                model_result: str, chart_path: str) -> str:
        """生成分析报告 - 使用标准模板格式"""
        try:
            # 尝试导入报告生成器
            from report.generator import CMSReportGenerator
            
            # 准备报告数据
            report_data = self._prepare_report_data(df, stats, model_result, chart_path)
            
            # 使用标准报告生成器生成HTML报告
            generator = CMSReportGenerator()
            
            # 生成临时HTML文件
            temp_html_path = f"temp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            if generator.generate_html_report(report_data, temp_html_path):
                # 读取生成的HTML内容
                with open(temp_html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # 删除临时文件
                try:
                    os.remove(temp_html_path)
                except:
                    pass
                
                return html_content
            else:
                # 如果HTML生成失败，回退到简化版本
                return self._generate_fallback_report(df, stats, model_result, chart_path)
                
        except ImportError:
            # 如果无法导入报告生成器，使用简化版本
            logger.warning("无法导入报告生成器，使用简化报告格式")
            return self._generate_fallback_report(df, stats, model_result, chart_path)
        except Exception as e:
            logger.error(f"生成标准报告失败: {e}，使用简化版本")
            return self._generate_fallback_report(df, stats, model_result, chart_path)
    
    def _prepare_report_data(self, df: pd.DataFrame, stats: Dict[str, Any], 
                           model_result: str, chart_path: str) -> Dict[str, Any]:
        """准备报告数据"""
        # 基于RMS值确定设备状态
        rms_columns = [col for col in stats.keys() if 'RMS' in str(col) and isinstance(stats[col], dict)]
        health_status = "良好"
        risk_level = "低"
        recommendations = []
        
        if rms_columns:
            rms_col = rms_columns[0]
            rms_mean = stats[rms_col]['mean']
            rms_max = stats[rms_col]['max']
            
            if rms_mean < 0.6:
                health_status = "良好"
                risk_level = "低"
                recommendations = ["继续按计划进行常规维护", "保持当前监测频率"]
            elif rms_mean < 1.0:
                health_status = "警告"
                risk_level = "中等"
                recommendations = ["增加监测频率", "检查设备紧固件", "关注振动趋势变化"]
            else:
                health_status = "危险"
                risk_level = "高"
                recommendations = ["立即停机检查", "联系维护人员", "进行详细故障诊断"]
            
            if rms_max > 1.5:
                recommendations.append("检测到振动峰值异常，可能存在间歇性故障")
        
        # 构建报告数据
        report_data = {
            "title": "CMS振动分析报告 (离线演示版)",
            "report_title": "CMS振动分析报告 (离线演示版)",
            "turbine_id": "DEMO-001",
            "equipment_name": "演示风机设备",
            "equipment_model": "模拟型号",
            "location": "离线演示环境",
            "measurement_point": "主轴承",
            "analysis_date": datetime.now().strftime('%Y-%m-%d'),
            "generation_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "analyst_name": "CMS离线演示系统",
            "health_status": health_status,
            "executive_summary": f"本次振动分析基于模拟数据进行演示。设备当前状态为{health_status}，风险等级为{risk_level}。{model_result}",
            "basic_info": {
                "wind_farm": "离线演示风场",
                "turbine_id": "DEMO-001",
                "equipment_name": "演示风机设备",
                "equipment_model": "模拟型号",
                "measurement_date": datetime.now().strftime('%Y-%m-%d'),
                "report_date": datetime.now().strftime('%Y-%m-%d'),
                "operator": "CMS离线演示系统",
                "equipment_status": "运行中",
                "measurement_point": "主轴承",
                "record_count": stats.get('record_count', 0),
                "time_range": f"{stats.get('time_range', {}).get('start', 'N/A')} ~ {stats.get('time_range', {}).get('end', 'N/A')}"
            },
            "measurement_results": self._format_measurement_results(stats),
            "charts": self._prepare_chart_data(chart_path),
            "analysis_conclusion": model_result,
            "recommendations": recommendations,
            "risk_assessment": {
                "风险等级": risk_level,
                "主要风险": "基于模拟数据的演示分析" if risk_level == "低" else "需要关注振动水平变化"
            },
            "next_inspection_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            "report_version": "离线演示版 v1.0"
        }
        
        return report_data
    
    def _prepare_chart_data(self, chart_path: str) -> Dict[str, str]:
        """准备图表数据，将图片文件转换为base64格式"""
        import base64
        charts = {}
        
        try:
            if chart_path and os.path.exists(chart_path):
                with open(chart_path, 'rb') as f:
                    chart_data = base64.b64encode(f.read()).decode('utf-8')
                    charts["振动趋势图"] = chart_data
            else:
                # 如果图片文件不存在，使用空字符串
                charts["振动趋势图"] = ""
        except Exception as e:
            logger.warning(f"图表数据准备失败: {e}")
            charts["振动趋势图"] = ""
        
        return charts
    
    def _format_measurement_results(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化测量结果为HTML模板所需的列表格式"""
        results = []
        for col, col_stats in stats.items():
            if isinstance(col_stats, dict) and 'mean' in col_stats:
                # 根据RMS值判断报警级别
                rms_value = col_stats['mean']
                if rms_value < 0.6:
                    alarm_level = "normal"
                elif rms_value < 1.0:
                    alarm_level = "warning"
                else:
                    alarm_level = "critical"
                
                results.append({
                    "measurement_point": col,
                    "rms_value": col_stats['mean'],
                    "peak_value": col_stats['max'],
                    "main_frequency": 25.0,  # 模拟主频率
                    "alarm_level": alarm_level
                })
        return results
    
    def _generate_fallback_report(self, df: pd.DataFrame, stats: Dict[str, Any], 
                                model_result: str, chart_path: str) -> str:
        """生成简化版报告（回退方案）"""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("CMS振动分析报告 (离线演示版)")
        report_lines.append("=" * 60)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"模式: 离线演示 (使用模拟数据)")
        report_lines.append("")
        
        # 数据概览
        report_lines.append("📊 数据概览")
        report_lines.append("-" * 30)
        report_lines.append(f"数据记录数: {stats['record_count']}")
        if stats['time_range']['start']:
            report_lines.append(f"时间范围: {stats['time_range']['start']} ~ {stats['time_range']['end']}")
        report_lines.append("")
        
        # 振动数据统计
        report_lines.append("🔧 振动数据统计")
        report_lines.append("-" * 30)
        for col, col_stats in stats.items():
            if isinstance(col_stats, dict) and 'mean' in col_stats:
                report_lines.append(f"{col}:")
                report_lines.append(f"  平均值: {col_stats['mean']:.4f}")
                report_lines.append(f"  标准差: {col_stats['std']:.4f}")
                report_lines.append(f"  最小值: {col_stats['min']:.4f}")
                report_lines.append(f"  最大值: {col_stats['max']:.4f}")
                report_lines.append(f"  中位数: {col_stats['median']:.4f}")
                report_lines.append("")
        
        # 模型分析结果
        report_lines.append("🤖 模型分析结果")
        report_lines.append("-" * 30)
        report_lines.append(model_result)
        report_lines.append("")
        
        # 可视化图表
        report_lines.append("📈 可视化图表")
        report_lines.append("-" * 30)
        report_lines.append(f"图表文件: {chart_path}")
        report_lines.append("")
        
        # 结论和建议
        report_lines.append("💡 结论和建议")
        report_lines.append("-" * 30)
        
        # 基于RMS值给出建议
        rms_columns = [col for col in stats.keys() if 'RMS' in str(col) and isinstance(stats[col], dict)]
        if rms_columns:
            rms_col = rms_columns[0]
            rms_mean = stats[rms_col]['mean']
            rms_max = stats[rms_col]['max']
            
            if rms_mean < 0.6:
                report_lines.append("✅ 振动水平正常，设备运行状态良好")
                report_lines.append("📋 建议: 继续按计划进行常规维护")
            elif rms_mean < 1.0:
                report_lines.append("⚠️ 振动水平略高，建议加强监控")
                report_lines.append("📋 建议: 增加监测频率，检查设备紧固件")
            else:
                report_lines.append("🚨 振动水平异常，建议立即检查设备")
                report_lines.append("📋 建议: 立即停机检查，联系维护人员")
            
            if rms_max > 1.5:
                report_lines.append("⚠️ 检测到振动峰值异常，可能存在间歇性故障")
        
        report_lines.append("")
        report_lines.append("📝 备注")
        report_lines.append("-" * 30)
        report_lines.append("本报告基于模拟数据生成，仅用于演示系统功能。")
        report_lines.append("实际使用时将连接真实的CMS数据源和分析模型。")
        report_lines.append("")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def get_embedding(self, text: str, use_test_data: bool = True) -> Optional[List[float]]:
        """获取文本的embedding向量"""
        if self.embedding_client:
            try:
                if hasattr(self.embedding_client, 'get_single_embedding'):
                    return self.embedding_client.get_single_embedding(text, use_test_data=use_test_data)
                elif hasattr(self.embedding_client, 'get_embeddings'):
                    result = self.embedding_client.get_embeddings([text], use_test_data=use_test_data)
                    return result[0] if result else None
                else:
                    logger.warning("Embedding客户端没有预期的方法")
                    return None
            except Exception as e:
                logger.error(f"获取embedding失败: {e}")
                return None
        else:
            logger.warning("Embedding客户端不可用")
            return None
    
    def chat(self, message: str) -> str:
        """模拟智能对话"""
        # 简单的规则基础对话系统
        message_lower = message.lower()
        
        if "振动" in message or "vibration" in message_lower:
            return "振动分析是通过监测设备运行时的振动信号来评估设备健康状态的技术。主要包括时域分析、频域分析和时频分析等方法。"
        elif "rms" in message_lower or "均方根" in message:
            return "RMS（均方根值）是振动分析中的重要指标，反映振动信号的能量大小。正常情况下RMS值应保持在设备规定的安全范围内。"
        elif "故障" in message or "fault" in message_lower:
            return "常见的设备故障类型包括：不平衡、不对中、轴承故障、齿轮故障等。每种故障都有其特征频率和振动模式。"
        elif "维护" in message or "maintenance" in message_lower:
            return "预测性维护基于设备状态监测数据，在故障发生前进行维护，可以有效降低维护成本并提高设备可靠性。"
        elif "帮助" in message or "help" in message_lower:
            return "我可以帮助您了解振动分析、故障诊断、设备维护等相关知识。请告诉我您想了解的具体内容。"
        else:
            return f"收到您的消息：{message}。这是离线演示模式，我可以回答关于振动分析、故障诊断、设备维护等方面的问题。"

# 全局应用实例
_demo_app_instance = None

def get_demo_app(use_real_api: bool = False) -> CMSOfflineDemo:
    """获取演示应用实例（单例模式）"""
    global _demo_app_instance
    if _demo_app_instance is None:
        _demo_app_instance = CMSOfflineDemo(use_real_api=use_real_api)
    return _demo_app_instance

# 便捷函数
def demo_analyze_vibration(region: str = "A08", station: str = "1003", position: str = "8", 
                          point: str = "AI_CMS024", hours: int = 24, use_real_api: bool = False) -> Dict[str, Any]:
    """演示振动数据分析的便捷函数"""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    app = get_demo_app(use_real_api=use_real_api)
    return app.analyze_vibration_data(
        region, station, position, point, 
        start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time.strftime("%Y-%m-%d %H:%M:%S")
    )

def demo_get_embedding(text: str, use_real_api: bool = False) -> Optional[List[float]]:
    """演示获取文本embedding的便捷函数"""
    app = get_demo_app(use_real_api=use_real_api)
    return app.get_embedding(text, use_test_data=not use_real_api)

def demo_chat(message: str, use_real_api: bool = False) -> str:
    """演示对话功能的便捷函数"""
    app = get_demo_app(use_real_api=use_real_api)
    return app.chat(message)

# 主程序
if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='CMS振动分析离线演示')
    parser.add_argument('--use-real-api', action='store_true', 
                       help='使用真实API而不是模拟数据')
    parser.add_argument('--region', default='A08', help='区域代码')
    parser.add_argument('--station', default='1003', help='站点编号')
    parser.add_argument('--position', default='8', help='位置编号')
    parser.add_argument('--point', default='AI_CMS024', help='测点编号')
    parser.add_argument('--hours', type=int, default=1, help='分析时间范围（小时）')
    
    args = parser.parse_args()
    
    # 配置日志
    logger.add("cms_offline_demo.log", rotation="10 MB", level="INFO")
    
    print("🔧 CMS振动分析系统 - 离线演示版本")
    print("=" * 50)
    print(f"API模式: {'真实API' if args.use_real_api else '模拟数据'}")
    print("本版本可选择使用模拟数据或真实API进行演示")
    print("")
    
    # 演示1: 振动数据分析
    print("📊 演示1: 振动数据分析")
    print("-" * 30)
    print(f"分析参数: {args.region}-{args.station}-{args.position}-{args.point}")
    print(f"时间范围: 最近{args.hours}小时")
    
    result = demo_analyze_vibration(
        region=args.region,
        station=args.station,
        position=args.position,
        point=args.point,
        hours=args.hours,
        use_real_api=args.use_real_api
    )
    
    if result["success"]:
        print("✅ 分析完成！")
        print("\n" + result["report"])
        
        # 保存报告
        filename = f"demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result["report"])
        print(f"\n📄 报告已保存到: {filename}")
    else:
        print(f"❌ 分析失败: {result['error']}")
    
    # 演示2: 文本嵌入向量
    print("\n\n🔤 演示2: 文本嵌入向量生成")
    print("-" * 30)
    embedding = demo_get_embedding("CMS振动分析系统演示", use_real_api=args.use_real_api)
    if embedding:
        print(f"✅ 向量生成成功，维度: {len(embedding)}")
        print(f"前10个值: {embedding[:10]}")
        print(f"向量范数: {sum(x*x for x in embedding)**0.5:.6f}")
    else:
        print("❌ 向量生成失败")
    
    # 演示3: 智能对话
    print("\n\n💬 演示3: 智能对话")
    print("-" * 30)
    questions = [
        "什么是振动分析？",
        "RMS值的意义是什么？",
        "常见的设备故障有哪些？",
        "如何进行预测性维护？"
    ]
    
    for question in questions:
        response = demo_chat(question, use_real_api=args.use_real_api)
        print(f"❓ {question}")
        print(f"🤖 {response}")
        print()
    
    print("=" * 50)
    print("🎉 离线演示完成！")
    print("\n💡 提示:")
    print("- 可以直接调用 demo_analyze_vibration() 函数进行分析")
    print("- 可以直接调用 demo_get_embedding(text) 生成向量")
    print("- 可以直接调用 demo_chat(message) 进行对话")
    print(f"- 当前使用{'真实API' if args.use_real_api else '模拟数据'}模式")
    print("\n🚀 使用方法:")
    print("  python cms_offline_demo.py                    # 使用模拟数据")
    print("  python cms_offline_demo.py --use-real-api     # 使用真实API")
    print("  python cms_offline_demo.py --hours 24         # 分析24小时数据")
    print("  python cms_offline_demo.py --region A09       # 指定区域")