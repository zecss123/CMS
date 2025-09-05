# -*- coding: utf-8 -*-
"""
CMS振动数据模拟生成模块
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple, Any, Optional
import json

from config.settings import CMS_CONFIG, WIND_FARM_CONFIG

class CMSDataGenerator:
    """CMS振动数据生成器"""
    
    def __init__(self):
        self.measurement_points = CMS_CONFIG["measurement_points"]
        self.frequency_range = CMS_CONFIG["frequency_range"]
        self.sampling_rate = CMS_CONFIG["sampling_rate"]
        self.data_length = CMS_CONFIG["data_length"]
        self.alarm_levels = CMS_CONFIG["alarm_levels"]
        
        # 故障模式定义
        self.fault_patterns = {
            "正常": {
                "base_rms": (0.5, 2.0),
                "main_freq": (20, 50),
                "harmonics": [],
                "noise_level": 0.1
            },
            "不平衡": {
                "base_rms": (2.5, 5.0),
                "main_freq": (16.7, 25),  # 1X转频
                "harmonics": [2, 3],  # 2X, 3X谐波
                "noise_level": 0.15
            },
            "不对中": {
                "base_rms": (3.0, 6.0),
                "main_freq": (33.3, 50),  # 2X转频
                "harmonics": [1, 3, 4],
                "noise_level": 0.2
            },
            "轴承故障": {
                "base_rms": (4.0, 8.0),
                "main_freq": (100, 300),  # 高频特征
                "harmonics": [2, 3, 4, 5],
                "noise_level": 0.25
            },
            "齿轮箱故障": {
                "base_rms": (5.0, 10.0),
                "main_freq": (200, 800),  # 齿轮啮合频率
                "harmonics": [2, 3, 4],
                "noise_level": 0.3
            },
            "松动": {
                "base_rms": (3.0, 7.0),
                "main_freq": (16.7, 33.3),  # 1X, 2X
                "harmonics": [2, 3, 4, 5, 6],  # 多次谐波
                "noise_level": 0.35
            }
        }
    
    def generate_time_series(self, fault_type: str = "正常", duration: float = 4.0) -> np.ndarray:
        """生成时域振动信号"""
        pattern = self.fault_patterns[fault_type]
        
        # 时间轴
        t = np.linspace(0, duration, int(self.sampling_rate * duration))
        
        # 基础信号
        base_freq = random.uniform(*pattern["main_freq"])
        base_amplitude = random.uniform(*pattern["base_rms"]) / np.sqrt(2)  # RMS转幅值
        
        signal = base_amplitude * np.sin(2 * np.pi * base_freq * t)
        
        # 添加谐波
        for harmonic in pattern["harmonics"]:
            harm_freq = base_freq * harmonic
            if harm_freq < self.frequency_range[1]:
                harm_amp = base_amplitude * random.uniform(0.1, 0.5) / harmonic
                signal += harm_amp * np.sin(2 * np.pi * harm_freq * t + random.uniform(0, 2*np.pi))
        
        # 添加噪声
        noise = np.random.normal(0, pattern["noise_level"] * base_amplitude, len(t))
        signal += noise
        
        # 添加随机调制（模拟实际工况）
        modulation = 1 + 0.1 * np.sin(2 * np.pi * random.uniform(0.1, 2) * t)
        signal *= modulation
        
        return signal
    
    def calculate_features(self, signal: np.ndarray) -> Dict[str, float]:
        """计算振动特征参数"""
        # 时域特征
        rms = float(np.sqrt(np.mean(signal**2)))
        peak = float(np.max(np.abs(signal)))
        pp = float(np.max(signal) - np.min(signal))
        
        # 频域分析
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/self.sampling_rate)
        
        # 只取正频率部分
        positive_freqs = freqs[:len(freqs)//2]
        magnitude = np.abs(fft[:len(fft)//2])
        
        # 主频率和幅值
        main_freq_idx = np.argmax(magnitude[1:]) + 1  # 排除直流分量
        main_frequency = float(positive_freqs[main_freq_idx])
        main_amplitude = float(magnitude[main_freq_idx] / len(signal) * 2)  # 转换为实际幅值
        
        return {
            "rms_value": rms,
            "peak_value": peak,
            "peak_to_peak": pp,
            "main_frequency": main_frequency,
            "main_amplitude": main_amplitude,
            "dominant_freq": main_frequency,
            "amplitude": main_amplitude,
            "harmonic_ratio": float(np.random.uniform(0.1, 0.3))
        }
    
    def get_alarm_level(self, rms_value: float) -> str:
        """根据RMS值确定报警等级"""
        for level, (min_val, max_val) in self.alarm_levels.items():
            if min_val <= rms_value < max_val:
                return level
        return "危险"
    
    def generate_measurement_data(self, wind_farm: str, turbine_id: str, 
                                measurement_point: str, fault_type: Optional[str] = None) -> Dict[str, Any]:
        """生成单个测点的完整数据"""
        # 随机选择故障类型（如果未指定）
        if fault_type is None:
            fault_type = random.choices(
                list(self.fault_patterns.keys()),
                weights=[0.6, 0.1, 0.1, 0.08, 0.07, 0.05],  # 正常状态概率更高
                k=1
            )[0]
        
        # 生成时域信号
        signal = self.generate_time_series(fault_type)
        
        # 计算特征参数
        features = self.calculate_features(signal)
        
        # 确定报警等级
        alarm_level = self.get_alarm_level(features["rms_value"])
        alarm_threshold = float(self.alarm_levels[alarm_level][1] if alarm_level != "危险" else 10.0)
        
        # 生成频谱特征描述
        frequency_features = self._generate_frequency_description(features, fault_type)
        
        # 生成趋势分析
        trend_analysis = self._generate_trend_analysis(features["rms_value"], alarm_level)
        
        return {
            "wind_farm": wind_farm,
            "turbine_id": turbine_id,
            "measurement_point": measurement_point,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fault_type": fault_type,
            "alarm_level": alarm_level,
            "alarm_threshold": alarm_threshold,
            "features": features,
            "frequency_features": frequency_features,
            "trend_analysis": trend_analysis,
            "time_series": signal.tolist()[:1000],  # 只保存部分时域数据
            "sampling_rate": self.sampling_rate,  # 添加采样率
        }
    
    def _generate_frequency_description(self, features: Dict, fault_type: str) -> str:
        """生成频谱特征描述"""
        main_freq = features["main_frequency"]
        main_amp = features["main_amplitude"]
        
        descriptions = {
            "正常": f"频谱相对平坦，主频率{main_freq:.1f}Hz，幅值{main_amp:.3f}mm/s，无明显异常峰值。",
            "不平衡": f"1X转频{main_freq:.1f}Hz处有明显峰值{main_amp:.3f}mm/s，存在2X、3X谐波成分。",
            "不对中": f"2X转频{main_freq:.1f}Hz处峰值突出{main_amp:.3f}mm/s，伴有1X和3X谐波。",
            "轴承故障": f"高频段{main_freq:.1f}Hz处出现特征频率{main_amp:.3f}mm/s，频谱较宽。",
            "齿轮箱故障": f"齿轮啮合频率{main_freq:.1f}Hz及其边频带明显，幅值{main_amp:.3f}mm/s。",
            "松动": f"多次谐波成分丰富，{main_freq:.1f}Hz处幅值{main_amp:.3f}mm/s，频谱复杂。"
        }
        
        return descriptions.get(fault_type, f"主频率{main_freq:.1f}Hz，幅值{main_amp:.3f}mm/s。")
    
    def _generate_trend_analysis(self, current_rms: float, alarm_level: str) -> str:
        """生成趋势分析描述"""
        # 模拟历史数据趋势
        trend_types = ["稳定", "上升", "下降", "波动"]
        trend = random.choice(trend_types)
        
        base_descriptions = {
            "稳定": f"近期振动水平保持稳定，RMS值在{current_rms*0.9:.2f}-{current_rms*1.1:.2f}mm/s范围内波动。",
            "上升": f"振动水平呈上升趋势，从{current_rms*0.7:.2f}mm/s增长至当前{current_rms:.2f}mm/s。",
            "下降": f"振动水平有所下降，从{current_rms*1.3:.2f}mm/s降至当前{current_rms:.2f}mm/s。",
            "波动": f"振动水平存在波动，在{current_rms*0.8:.2f}-{current_rms*1.2:.2f}mm/s之间变化。"
        }
        
        return base_descriptions[trend]
    
    def generate_turbine_data(self, wind_farm: str, turbine_id: str) -> Dict[str, Any]:
        """生成单台机组所有测点的数据"""
        turbine_data = {
            "wind_farm": wind_farm,
            "turbine_id": turbine_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "measurements": {}
        }
        
        # 为每个测点生成数据
        for point in self.measurement_points:
            measurement_data = self.generate_measurement_data(wind_farm, turbine_id, point)
            turbine_data["measurements"][point] = measurement_data
        
        return turbine_data
    
    def generate_farm_data(self, wind_farm: str, turbine_count: Optional[int] = None) -> Dict[str, Any]:
        """生成整个风场的数据"""
        if wind_farm not in WIND_FARM_CONFIG["farms"]:
            raise ValueError(f"未知风场: {wind_farm}")
        
        farm_config = WIND_FARM_CONFIG["farms"][wind_farm]
        turbines = farm_config["turbines"]
        
        if turbine_count:
            turbines = turbines[:turbine_count]
        
        farm_data = {
            "wind_farm": wind_farm,
            "location": farm_config["location"],
            "capacity": farm_config["capacity"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "turbines": {}
        }
        
        for turbine_id in turbines:
            farm_data["turbines"][turbine_id] = self.generate_turbine_data(wind_farm, turbine_id)
        
        return farm_data

# 便捷函数
def get_mock_data(wind_farm: str, turbine_id: str, measurement_point: str) -> Dict[str, Any]:
    """获取单个测点的模拟数据"""
    generator = CMSDataGenerator()
    return generator.generate_measurement_data(wind_farm, turbine_id, measurement_point)

def get_turbine_mock_data(wind_farm: str, turbine_id: str) -> Dict[str, Any]:
    """获取单台机组的模拟数据"""
    generator = CMSDataGenerator()
    return generator.generate_turbine_data(wind_farm, turbine_id)

def get_available_farms() -> List[str]:
    """获取可用的风场列表"""
    return list(WIND_FARM_CONFIG["farms"].keys())

def get_farm_turbines(wind_farm: str) -> List[str]:
    """获取指定风场的机组列表"""
    if wind_farm in WIND_FARM_CONFIG["farms"]:
        return WIND_FARM_CONFIG["farms"][wind_farm]["turbines"]
    return []

if __name__ == "__main__":
    # 测试代码
    generator = CMSDataGenerator()
    
    # 生成测试数据
    test_data = generator.generate_measurement_data("华能风场A", "A01", "1X水平振动")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))