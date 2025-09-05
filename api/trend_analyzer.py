# -*- coding: utf-8 -*-
"""
趋势分析器 - 处理振动数据的趋势分析和可视化
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from loguru import logger
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans


class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self, output_dir: str = "analysis_output"):
        """初始化趋势分析器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 设置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置seaborn样式
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    def analyze_single_point_trend(self, data: Dict[str, Any], 
                                   point_id: str) -> Dict[str, Any]:
        """分析单个测点的趋势
        
        Args:
            data: 测点数据
            point_id: 测点ID
            
        Returns:
            Dict: 趋势分析结果
        """
        try:
            # 提取时间序列数据
            if 'time_series' not in data or not data['time_series']:
                logger.warning(f"测点 {point_id} 无时间序列数据")
                return {'status': 'no_data', 'point_id': point_id}
            
            time_series = data['time_series']
            timestamps = [datetime.fromisoformat(item['timestamp']) for item in time_series]
            values = [float(item['value']) for item in time_series]
            
            if len(values) < 3:
                logger.warning(f"测点 {point_id} 数据点不足")
                return {'status': 'insufficient_data', 'point_id': point_id}
            
            # 创建DataFrame
            df = pd.DataFrame({
                'timestamp': timestamps,
                'value': values
            })
            df = df.sort_values('timestamp')
            
            # 基础统计分析
            values_series = pd.Series(df['value'])
            basic_stats = self._calculate_basic_statistics(values_series)
            
            # 趋势分析
            trend_analysis = self._analyze_trend(df)
            
            # 异常检测
            anomaly_detection = self._detect_anomalies(values_series)
            
            # 周期性分析
            periodicity_analysis = self._analyze_periodicity(df)
            
            # 报警级别评估
            alarm_level = self._assess_alarm_level(basic_stats, trend_analysis, anomaly_detection)
            
            # 生成趋势图
            chart_path = self._generate_trend_chart(df, point_id, alarm_level)
            
            result = {
                'status': 'success',
                'point_id': point_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_points': len(values),
                'time_range': {
                    'start': timestamps[0].isoformat(),
                    'end': timestamps[-1].isoformat()
                },
                'basic_statistics': basic_stats,
                'trend_analysis': trend_analysis,
                'anomaly_detection': anomaly_detection,
                'periodicity_analysis': periodicity_analysis,
                'alarm_level': alarm_level,
                'chart_path': str(chart_path) if chart_path else None,
                'recommendations': self._generate_recommendations(alarm_level, trend_analysis)
            }
            
            logger.info(f"测点 {point_id} 趋势分析完成，报警级别: {alarm_level}")
            return result
            
        except Exception as e:
            logger.error(f"测点 {point_id} 趋势分析失败: {e}")
            return {
                'status': 'error',
                'point_id': point_id,
                'error': str(e)
            }
    
    def _calculate_basic_statistics(self, values: pd.Series) -> Dict[str, float]:
        """计算基础统计信息
        
        Args:
            values: 数值序列
            
        Returns:
            Dict: 统计信息
        """
        return {
            'mean': float(values.mean()),
            'median': float(values.median()),
            'std': float(values.std()),
            'min': float(values.min()),
            'max': float(values.max()),
            'q25': float(values.quantile(0.25)),
            'q75': float(values.quantile(0.75)),
            'skewness': float(values.skew()),
            'kurtosis': float(values.kurtosis()),
            'cv': float(values.std() / values.mean()) if values.mean() != 0 else 0
        }
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析趋势
        
        Args:
            df: 数据框
            
        Returns:
            Dict: 趋势分析结果
        """
        # 线性回归分析趋势
        x = np.arange(len(df))
        y = df['value'].values
        
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # 趋势方向判断
            if abs(slope) < std_err:
                trend_direction = 'stable'
            elif slope > 0:
                trend_direction = 'increasing'
            else:
                trend_direction = 'decreasing'
            
            # 趋势强度
            trend_strength = abs(r_value)
            
            # 变化率分析
            if len(df) > 1:
                first_val = float(df['value'].iloc[0])
                last_val = float(df['value'].iloc[-1])
                if first_val != 0:
                    recent_change_rate = (last_val - first_val) / first_val * 100
                else:
                    recent_change_rate = 0
            else:
                recent_change_rate = 0
            
            return {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'trend_direction': trend_direction,
                'trend_strength': float(trend_strength),
                'recent_change_rate_percent': float(recent_change_rate),
                'is_significant': bool(p_value < 0.05)
            }
        except Exception as e:
            logger.warning(f"趋势分析计算失败: {e}")
            return {
                'slope': 0.0,
                'intercept': 0.0,
                'r_squared': 0.0,
                'p_value': 1.0,
                'trend_direction': 'stable',
                'trend_strength': 0.0,
                'recent_change_rate_percent': 0.0,
                'is_significant': False
            }
    
    def _detect_anomalies(self, values: pd.Series) -> Dict[str, Any]:
        """检测异常值
        
        Args:
            values: 数值序列
            
        Returns:
            Dict: 异常检测结果
        """
        # IQR方法检测异常值
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers_iqr = values[(values < lower_bound) | (values > upper_bound)]
        
        # Z-score方法检测异常值
        try:
            z_scores = np.abs(stats.zscore(values.values))
            outliers_zscore = values[z_scores > 3]
        except Exception:
            outliers_zscore = pd.Series([], dtype=float)
        
        # 移动平均偏差检测
        window_size = min(10, len(values) // 4) if len(values) > 4 else 1
        rolling_mean = values.rolling(window=window_size, center=True).mean()
        rolling_std = values.rolling(window=window_size, center=True).std()
        
        deviation_threshold = 2
        outliers_rolling = values[
            np.abs(values - rolling_mean) > deviation_threshold * rolling_std
        ]
        
        return {
            'iqr_outliers_count': len(outliers_iqr),
            'iqr_outlier_rate': len(outliers_iqr) / len(values) * 100,
            'zscore_outliers_count': len(outliers_zscore),
            'zscore_outlier_rate': len(outliers_zscore) / len(values) * 100,
            'rolling_outliers_count': len(outliers_rolling),
            'rolling_outlier_rate': len(outliers_rolling) / len(values) * 100,
            'bounds': {
                'iqr_lower': float(lower_bound),
                'iqr_upper': float(upper_bound)
            }
        }
    
    def _analyze_periodicity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析周期性
        
        Args:
            df: 数据框
            
        Returns:
            Dict: 周期性分析结果
        """
        try:
            values = df['value'].values
            
            # 简单的自相关分析
            if len(values) > 10:
                # 计算不同滞后的自相关系数
                max_lag = min(len(values) // 4, 50)
                autocorr = []
                
                for lag in range(1, max_lag + 1):
                    if len(values) > lag:
                        try:
                            val1 = values[:-lag]
                            val2 = values[lag:]
                            corr = np.corrcoef(val1, val2)[0, 1]
                            if not np.isnan(corr):
                                autocorr.append((lag, float(corr)))
                        except Exception:
                            continue
                
                # 找到最强的周期性
                if autocorr:
                    best_lag, best_corr = max(autocorr, key=lambda x: abs(x[1]))
                    has_periodicity = abs(best_corr) > 0.3
                else:
                    best_lag, best_corr = 0, 0
                    has_periodicity = False
            else:
                best_lag, best_corr = 0, 0
                has_periodicity = False
            
            return {
                'has_periodicity': has_periodicity,
                'best_period': int(best_lag) if has_periodicity else None,
                'periodicity_strength': float(abs(best_corr)) if best_corr else 0,
                'analysis_method': 'autocorrelation'
            }
            
        except Exception as e:
            logger.warning(f"周期性分析失败: {e}")
            return {
                'has_periodicity': False,
                'analysis_method': 'failed',
                'error': str(e)
            }
    
    def _assess_alarm_level(self, basic_stats: Dict[str, float],
                           trend_analysis: Dict[str, Any],
                           anomaly_detection: Dict[str, Any]) -> str:
        """评估报警级别
        
        Args:
            basic_stats: 基础统计信息
            trend_analysis: 趋势分析结果
            anomaly_detection: 异常检测结果
            
        Returns:
            str: 报警级别 (normal, warning, alarm, critical)
        """
        # 异常值比例阈值
        if anomaly_detection['iqr_outlier_rate'] > 20:
            return 'critical'
        elif anomaly_detection['iqr_outlier_rate'] > 10:
            return 'alarm'
        elif anomaly_detection['iqr_outlier_rate'] > 5:
            return 'warning'
        
        # 趋势变化率阈值
        change_rate = abs(trend_analysis['recent_change_rate_percent'])
        if change_rate > 50:
            return 'critical'
        elif change_rate > 30:
            return 'alarm'
        elif change_rate > 15:
            return 'warning'
        
        # 变异系数阈值
        cv = basic_stats['cv']
        if cv > 1.0:
            return 'alarm'
        elif cv > 0.5:
            return 'warning'
        
        return 'normal'
    
    def _generate_trend_chart(self, df: pd.DataFrame, point_id: str, 
                             alarm_level: str) -> Optional[Path]:
        """生成趋势图
        
        Args:
            df: 数据框
            point_id: 测点ID
            alarm_level: 报警级别
            
        Returns:
            Path: 图表文件路径
        """
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # 颜色映射
            color_map = {
                'normal': 'green',
                'warning': 'orange',
                'alarm': 'red',
                'critical': 'darkred'
            }
            color = color_map.get(alarm_level, 'blue')
            
            # 主趋势图
            ax1.plot(df['timestamp'], df['value'], color=color, linewidth=2, alpha=0.8)
            ax1.fill_between(df['timestamp'], df['value'], alpha=0.3, color=color)
            ax1.set_title(f'测点 {point_id} 振动趋势 (报警级别: {alarm_level})', fontsize=14, fontweight='bold')
            ax1.set_ylabel('振动值', fontsize=12)
            ax1.grid(True, alpha=0.3)
            
            # 添加趋势线
            x_numeric = np.arange(len(df))
            z = np.polyfit(x_numeric, df['value'], 1)
            p = np.poly1d(z)
            ax1.plot(df['timestamp'], p(x_numeric), "--", color='black', alpha=0.8, linewidth=1)
            
            # 分布直方图
            ax2.hist(df['value'], bins=20, color=color, alpha=0.7, edgecolor='black')
            ax2.axvline(df['value'].mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {df["value"].mean():.2f}')
            ax2.axvline(df['value'].median(), color='blue', linestyle='--', linewidth=2, label=f'中位数: {df["value"].median():.2f}')
            ax2.set_title('数值分布', fontsize=12)
            ax2.set_xlabel('振动值', fontsize=10)
            ax2.set_ylabel('频次', fontsize=10)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表
            chart_filename = f"trend_{point_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            chart_path = self.output_dir / chart_filename
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"趋势图已保存: {chart_path}")
            return chart_path
            
        except Exception as e:
            logger.error(f"生成趋势图失败: {e}")
            plt.close()
            return None
    
    def _generate_recommendations(self, alarm_level: str, 
                                trend_analysis: Dict[str, Any]) -> List[str]:
        """生成建议
        
        Args:
            alarm_level: 报警级别
            trend_analysis: 趋势分析结果
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        if alarm_level == 'critical':
            recommendations.extend([
                "立即停机检查，存在严重振动异常",
                "联系专业技术人员进行现场诊断",
                "检查轴承、齿轮箱等关键部件"
            ])
        elif alarm_level == 'alarm':
            recommendations.extend([
                "安排近期维护检查",
                "增加监测频率",
                "检查润滑系统和紧固件"
            ])
        elif alarm_level == 'warning':
            recommendations.extend([
                "持续关注振动变化趋势",
                "按计划进行常规维护",
                "记录异常时间和工况条件"
            ])
        else:
            recommendations.append("设备运行正常，继续按计划维护")
        
        # 基于趋势的建议
        if trend_analysis['trend_direction'] == 'increasing' and trend_analysis['is_significant']:
            recommendations.append("振动呈上升趋势，建议提前安排检查")
        elif trend_analysis['trend_direction'] == 'decreasing' and trend_analysis['is_significant']:
            recommendations.append("振动呈下降趋势，设备状态改善")
        
        return recommendations
    
    def batch_analyze_trends(self, data_dict: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """批量分析趋势
        
        Args:
            data_dict: 测点数据字典，键为测点ID
            
        Returns:
            Dict: 批量分析结果
        """
        results = {}
        
        for point_id, data in data_dict.items():
            try:
                result = self.analyze_single_point_trend(data, point_id)
                results[point_id] = result
            except Exception as e:
                logger.error(f"批量分析失败 - 测点 {point_id}: {e}")
                results[point_id] = {
                    'status': 'error',
                    'point_id': point_id,
                    'error': str(e)
                }
        
        logger.info(f"批量趋势分析完成，处理测点数: {len(results)}")
        return results
    
    def generate_summary_report(self, analysis_results: Dict[str, Dict[str, Any]],
                               wind_farm_name: str = "未知风场") -> Dict[str, Any]:
        """生成汇总报告
        
        Args:
            analysis_results: 分析结果字典
            wind_farm_name: 风场名称
            
        Returns:
            Dict: 汇总报告
        """
        # 统计各报警级别数量
        alarm_counts = {'normal': 0, 'warning': 0, 'alarm': 0, 'critical': 0, 'error': 0}
        successful_analyses = 0
        
        for point_id, result in analysis_results.items():
            if result['status'] == 'success':
                successful_analyses += 1
                alarm_level = result.get('alarm_level', 'normal')
                if alarm_level in alarm_counts:
                    alarm_counts[alarm_level] += 1
            else:
                alarm_counts['error'] += 1
        
        # 计算健康度评分
        total_points = successful_analyses
        if total_points > 0:
            health_score = (
                alarm_counts['normal'] * 100 +
                alarm_counts['warning'] * 70 +
                alarm_counts['alarm'] * 40 +
                alarm_counts['critical'] * 10
            ) / total_points
        else:
            health_score = 0
        
        # 确定整体状态
        if alarm_counts['critical'] > 0:
            overall_status = 'critical'
        elif alarm_counts['alarm'] > 0:
            overall_status = 'alarm'
        elif alarm_counts['warning'] > 0:
            overall_status = 'warning'
        else:
            overall_status = 'normal'
        
        summary_report = {
            'wind_farm_name': wind_farm_name,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_measurement_points': len(analysis_results),
            'successful_analyses': successful_analyses,
            'failed_analyses': alarm_counts['error'],
            'alarm_distribution': alarm_counts,
            'health_score': round(health_score, 2),
            'overall_status': overall_status,
            'critical_points': [
                point_id for point_id, result in analysis_results.items()
                if result.get('alarm_level') == 'critical'
            ],
            'alarm_points': [
                point_id for point_id, result in analysis_results.items()
                if result.get('alarm_level') == 'alarm'
            ],
            'recommendations': self._generate_summary_recommendations(overall_status, alarm_counts)
        }
        
        return summary_report
    
    def _generate_summary_recommendations(self, overall_status: str, 
                                        alarm_counts: Dict[str, int]) -> List[str]:
        """生成汇总建议
        
        Args:
            overall_status: 整体状态
            alarm_counts: 报警级别统计
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        if overall_status == 'critical':
            recommendations.extend([
                f"发现 {alarm_counts['critical']} 个严重报警测点，需要立即处理",
                "建议暂停相关机组运行，进行全面检查",
                "联系设备制造商或专业维修团队"
            ])
        elif overall_status == 'alarm':
            recommendations.extend([
                f"发现 {alarm_counts['alarm']} 个报警测点，需要及时关注",
                "安排专业人员进行详细检查",
                "制定针对性维护计划"
            ])
        elif overall_status == 'warning':
            recommendations.extend([
                f"发现 {alarm_counts['warning']} 个预警测点，建议加强监控",
                "按计划进行预防性维护",
                "记录设备运行参数变化"
            ])
        else:
            recommendations.append("整体设备状态良好，继续正常运行")
        
        return recommendations
    
    def save_analysis_results(self, results: Dict[str, Any], 
                             filename: Optional[str] = None) -> Path:
        """保存分析结果
        
        Args:
            results: 分析结果
            filename: 文件名，None时自动生成
            
        Returns:
            Path: 保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"trend_analysis_{timestamp}.json"
        
        file_path = self.output_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"分析结果已保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            raise
    
    def clear_output_directory(self) -> None:
        """清空输出目录"""
        try:
            for file_path in self.output_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            logger.info("输出目录已清空")
        except Exception as e:
            logger.error(f"清空输出目录失败: {e}")