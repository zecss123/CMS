# -*- coding: utf-8 -*-
"""
数据处理工具模块
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import json
from loguru import logger

class VibrationDataProcessor:
    """振动数据处理器"""
    
    def __init__(self):
        self.sampling_rate = 2048  # Hz
        self.frequency_range = (0, 1000)  # Hz
    
    def process_time_series(self, signal: np.ndarray, sampling_rate: Optional[float] = None) -> Dict[str, Any]:
        """处理时域信号"""
        if sampling_rate is None:
            sampling_rate = float(self.sampling_rate)
        
        # 基本统计特征
        features = {
            "length": len(signal),
            "duration": len(signal) / sampling_rate,
            "sampling_rate": sampling_rate,
            "mean": np.mean(signal),
            "std": np.std(signal),
            "rms": np.sqrt(np.mean(signal**2)),
            "peak": np.max(np.abs(signal)),
            "peak_to_peak": np.max(signal) - np.min(signal),
            "crest_factor": np.max(np.abs(signal)) / np.sqrt(np.mean(signal**2)),
            "kurtosis": self._calculate_kurtosis(signal),
            "skewness": self._calculate_skewness(signal)
        }
        
        return features
    
    def _calculate_kurtosis(self, signal: np.ndarray) -> float:
        """计算峭度"""
        mean = np.mean(signal)
        std = np.std(signal)
        if std == 0:
            return 0.0
        normalized = (signal - mean) / std
        return float(np.mean(normalized**4) - 3)
    
    def _calculate_skewness(self, signal: np.ndarray) -> float:
        """计算偏度"""
        mean = np.mean(signal)
        std = np.std(signal)
        if std == 0:
            return 0.0
        normalized = (signal - mean) / std
        return float(np.mean(normalized**3))
    
    def fft_analysis(self, signal: np.ndarray, sampling_rate: Optional[float] = None) -> Dict[str, Any]:
        """FFT频域分析"""
        if sampling_rate is None:
            sampling_rate = float(self.sampling_rate)
        
        # 执行FFT
        fft_result = np.fft.fft(signal)
        frequencies = np.fft.fftfreq(len(signal), 1/sampling_rate)
        
        # 只取正频率部分
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        magnitudes = np.abs(fft_result[positive_freq_idx])
        
        # 转换为实际幅值
        magnitudes = magnitudes / len(signal) * 2
        
        # 找到主频率
        main_freq_idx = np.argmax(magnitudes)
        main_frequency = frequencies[main_freq_idx]
        main_amplitude = magnitudes[main_freq_idx]
        
        # 频域特征
        features = {
            "frequencies": frequencies,
            "magnitudes": magnitudes,
            "main_frequency": main_frequency,
            "main_amplitude": main_amplitude,
            "frequency_resolution": sampling_rate / len(signal),
            "spectral_centroid": np.sum(frequencies * magnitudes) / np.sum(magnitudes),
            "spectral_rolloff": self._calculate_spectral_rolloff(frequencies, magnitudes),
            "spectral_bandwidth": self._calculate_spectral_bandwidth(frequencies, magnitudes)
        }
        
        return features
    
    def _calculate_spectral_rolloff(self, frequencies: np.ndarray, magnitudes: np.ndarray, 
                                  rolloff_percent: float = 0.85) -> float:
        """计算频谱滚降点"""
        cumulative_sum = np.cumsum(magnitudes)
        total_sum = cumulative_sum[-1]
        rolloff_threshold = rolloff_percent * total_sum
        
        rolloff_idx = np.where(cumulative_sum >= rolloff_threshold)[0]
        if len(rolloff_idx) > 0:
            return float(frequencies[rolloff_idx[0]])
        return float(frequencies[-1])
    
    def _calculate_spectral_bandwidth(self, frequencies: np.ndarray, magnitudes: np.ndarray) -> float:
        """计算频谱带宽"""
        centroid = np.sum(frequencies * magnitudes) / np.sum(magnitudes)
        bandwidth = np.sqrt(np.sum(((frequencies - centroid) ** 2) * magnitudes) / np.sum(magnitudes))
        return bandwidth
    
    def envelope_analysis(self, signal: np.ndarray, sampling_rate: Optional[float] = None) -> Dict[str, Any]:
        """包络分析（用于轴承故障诊断）"""
        if sampling_rate is None:
            sampling_rate = float(self.sampling_rate)
        
        # 希尔伯特变换获取包络
        analytic_signal = np.abs(np.fft.ifft(np.fft.fft(signal) * 
                                           (1 + np.sign(np.fft.fftfreq(len(signal))))))
        envelope = np.abs(analytic_signal)
        
        # 包络频谱
        envelope_fft = np.fft.fft(envelope - np.mean(envelope))
        envelope_freqs = np.fft.fftfreq(len(envelope), 1/sampling_rate)
        
        positive_idx = envelope_freqs > 0
        envelope_freqs = envelope_freqs[positive_idx]
        envelope_magnitudes = np.abs(envelope_fft[positive_idx]) / len(envelope) * 2
        
        return {
            "envelope": envelope,
            "envelope_frequencies": envelope_freqs,
            "envelope_magnitudes": envelope_magnitudes,
            "envelope_rms": np.sqrt(np.mean(envelope**2))
        }
    
    def order_analysis(self, signal: np.ndarray, rpm: float, sampling_rate: Optional[float] = None) -> Dict[str, Any]:
        """阶次分析"""
        if sampling_rate is None:
            sampling_rate = float(self.sampling_rate)
        
        # 转频
        rotation_freq = rpm / 60
        
        # FFT分析
        fft_result = self.fft_analysis(signal, sampling_rate)
        frequencies = fft_result["frequencies"]
        magnitudes = fft_result["magnitudes"]
        
        # 计算阶次
        orders = frequencies / rotation_freq
        
        # 找到主要阶次成分
        main_orders = []
        for order in [1, 2, 3, 4, 5, 6]:  # 1X到6X
            target_freq = order * rotation_freq
            # 找到最接近的频率
            closest_idx = np.argmin(np.abs(frequencies - target_freq))
            if np.abs(frequencies[closest_idx] - target_freq) < rotation_freq * 0.1:  # 10%容差
                main_orders.append({
                    "order": order,
                    "frequency": frequencies[closest_idx],
                    "amplitude": magnitudes[closest_idx]
                })
        
        return {
            "rotation_frequency": rotation_freq,
            "orders": orders,
            "order_magnitudes": magnitudes,
            "main_orders": main_orders
        }
    
    def trend_analysis(self, time_series_data: List[Dict[str, Any]], 
                      feature_name: str = "rms_value") -> Dict[str, Any]:
        """趋势分析"""
        if len(time_series_data) < 2:
            return {"trend": "insufficient_data", "slope": 0, "correlation": 0}
        
        # 提取时间和特征值
        timestamps = []
        values = []
        
        for data_point in time_series_data:
            if "timestamp" in data_point and feature_name in data_point:
                try:
                    timestamp = datetime.fromisoformat(data_point["timestamp"])
                    timestamps.append(timestamp)
                    values.append(data_point[feature_name])
                except:
                    continue
        
        if len(values) < 2:
            return {"trend": "insufficient_data", "slope": 0, "correlation": 0}
        
        # 转换为数值
        time_numeric = [(t - timestamps[0]).total_seconds() for t in timestamps]
        
        # 线性回归
        slope, intercept, correlation = self._linear_regression(time_numeric, values)
        
        # 判断趋势
        if abs(correlation) < 0.3:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        return {
            "trend": trend,
            "slope": slope,
            "correlation": correlation,
            "intercept": intercept,
            "data_points": len(values)
        }
    
    def _linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float, float]:
        """简单线性回归"""
        n = len(x)
        if n < 2:
            return 0, 0, 0
        
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        # 计算斜率和截距
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0, float(y_mean), 0.0
        
        slope = float(numerator / denominator)
        intercept = float(y_mean - slope * x_mean)
        
        # 计算相关系数
        y_var = sum((y[i] - y_mean) ** 2 for i in range(n))
        if y_var == 0:
            correlation = 0.0
        else:
            correlation = float(numerator / np.sqrt(denominator * y_var))
        
        return slope, intercept, correlation
    
    def detect_anomalies(self, values: List[float], method: str = "iqr", 
                        threshold: float = 1.5) -> Dict[str, Any]:
        """异常检测"""
        if len(values) < 4:
            return {"anomalies": [], "method": method, "threshold": threshold}
        
        values_array = np.array(values)
        anomaly_indices = []
        
        if method == "iqr":
            # 四分位距方法
            q1 = np.percentile(values_array, 25)
            q3 = np.percentile(values_array, 75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            anomaly_indices = np.where((values_array < lower_bound) | 
                                     (values_array > upper_bound))[0].tolist()
        
        elif method == "zscore":
            # Z-score方法
            mean = np.mean(values_array)
            std = np.std(values_array)
            if std > 0:
                z_scores = np.abs((values_array - mean) / std)
                anomaly_indices = np.where(z_scores > threshold)[0].tolist()
        
        return {
            "anomalies": anomaly_indices,
            "method": method,
            "threshold": threshold,
            "anomaly_count": len(anomaly_indices),
            "anomaly_rate": len(anomaly_indices) / len(values)
        }
    
    def calculate_bearing_frequencies(self, rpm: float, bearing_params: Dict[str, float]) -> Dict[str, float]:
        """计算轴承特征频率"""
        rotation_freq = rpm / 60  # Hz
        
        # 轴承参数
        ball_count = bearing_params.get("ball_count", 8)
        pitch_diameter = bearing_params.get("pitch_diameter", 50)  # mm
        ball_diameter = bearing_params.get("ball_diameter", 8)  # mm
        contact_angle = bearing_params.get("contact_angle", 0)  # degrees
        
        # 转换角度为弧度
        contact_angle_rad = np.radians(contact_angle)
        
        # 计算特征频率
        bpfo = (ball_count / 2) * rotation_freq * (1 - (ball_diameter / pitch_diameter) * np.cos(contact_angle_rad))
        bpfi = (ball_count / 2) * rotation_freq * (1 + (ball_diameter / pitch_diameter) * np.cos(contact_angle_rad))
        bsf = (pitch_diameter / (2 * ball_diameter)) * rotation_freq * (1 - ((ball_diameter / pitch_diameter) * np.cos(contact_angle_rad))**2)
        ftf = (rotation_freq / 2) * (1 - (ball_diameter / pitch_diameter) * np.cos(contact_angle_rad))
        
        return {
            "rotation_frequency": rotation_freq,
            "bpfo": bpfo,  # 外圈故障频率
            "bpfi": bpfi,  # 内圈故障频率
            "bsf": bsf,    # 滚动体故障频率
            "ftf": ftf     # 保持架故障频率
        }

# 便捷函数
def process_vibration_signal(signal: np.ndarray, sampling_rate: float = 2048) -> Dict[str, Any]:
    """处理振动信号的便捷函数"""
    processor = VibrationDataProcessor()
    
    # 时域分析
    time_features = processor.process_time_series(signal, sampling_rate)
    
    # 频域分析
    freq_features = processor.fft_analysis(signal, sampling_rate)
    
    return {
        "time_domain": time_features,
        "frequency_domain": freq_features
    }

def analyze_bearing_signal(signal: np.ndarray, rpm: float, bearing_params: Dict[str, float], 
                          sampling_rate: float = 2048) -> Dict[str, Any]:
    """轴承信号分析的便捷函数"""
    processor = VibrationDataProcessor()
    
    # 基础分析
    basic_analysis = process_vibration_signal(signal, sampling_rate)
    
    # 包络分析
    envelope_analysis = processor.envelope_analysis(signal, sampling_rate)
    
    # 轴承特征频率
    bearing_freqs = processor.calculate_bearing_frequencies(rpm, bearing_params)
    
    # 阶次分析
    order_analysis = processor.order_analysis(signal, rpm, sampling_rate)
    
    return {
        **basic_analysis,
        "envelope_analysis": envelope_analysis,
        "bearing_frequencies": bearing_freqs,
        "order_analysis": order_analysis
    }

if __name__ == "__main__":
    # 测试代码
    processor = VibrationDataProcessor()
    
    # 生成测试信号
    t = np.linspace(0, 1, 2048)
    signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100 * t) + 0.1 * np.random.randn(len(t))
    
    # 处理信号
    result = process_vibration_signal(signal)
    print(f"主频率: {result['frequency_domain']['main_frequency']:.1f} Hz")
    print(f"RMS值: {result['time_domain']['rms']:.3f}")