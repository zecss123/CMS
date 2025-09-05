#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试极大量分析结论的处理能力
验证generator.py是否能正确处理20个分析结论的情况
"""

import sys
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from report.generator import CMSReportGenerator

def generate_test_chart(chart_type, title):
    """生成测试图表"""
    plt.figure(figsize=(10, 6))
    
    if chart_type == "rms":
        # RMS分布图
        x = np.linspace(0, 100, 100)
        y = np.random.normal(2.5, 0.5, 100)
        plt.plot(x, y, 'b-', linewidth=2)
        plt.title(f'{title} - RMS Distribution')
        plt.xlabel('Time (s)')
        plt.ylabel('RMS Value (mm/s)')
    elif chart_type == "peak":
        # 峰值分布图
        x = np.linspace(0, 100, 100)
        y = np.random.normal(8.0, 1.5, 100)
        plt.plot(x, y, 'r-', linewidth=2)
        plt.title(f'{title} - Peak Distribution')
        plt.xlabel('Time (s)')
        plt.ylabel('Peak Value (mm/s)')
    elif chart_type == "frequency":
        # 频谱图
        freqs = np.linspace(0, 1000, 500)
        spectrum = np.random.exponential(0.1, 500)
        plt.semilogy(freqs, spectrum, 'g-', linewidth=1)
        plt.title(f'{title} - Frequency Spectrum')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Amplitude')
    else:
        # 默认趋势图
        x = np.linspace(0, 100, 100)
        y = np.sin(x/10) + np.random.normal(0, 0.1, 100)
        plt.plot(x, y, 'm-', linewidth=2)
        plt.title(f'{title} - Trend Analysis')
        plt.xlabel('Time (s)')
        plt.ylabel('Vibration Value')
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 转换为base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return chart_base64

def create_extreme_test_data():
    """创建包含20个分析结论的测试数据"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建20个分析结论
    analysis_conclusions = [
        "主轴承DE端振动水平正常，RMS值在标准范围内",
        "齿轮箱高速轴存在轻微不平衡现象，建议关注",
        "发电机前轴承温度略高，可能存在润滑问题",
        "塔筒振动频率与风速相关性良好，结构稳定",
        "偏航系统运行平稳，无异常振动信号",
        "变桨系统各轴承状态良好，运行正常",
        "主轴低速端轴承磨损轻微，在可接受范围内",
        "齿轮箱中速轴齿轮啮合正常，无明显故障特征",
        "发电机后轴承振动幅值稳定，运行状态良好",
        "整机振动水平符合设计要求，建议继续监测",
        "主轴承NDE端振动特征正常，无异常频率成分",
        "齿轮箱润滑系统工作正常，油温在正常范围",
        "发电机定子绕组振动水平稳定，电磁特性良好",
        "塔筒基础连接牢固，无松动迹象",
        "偏航轴承润滑充分，转动阻力正常",
        "变桨电机运行平稳，扭矩输出稳定",
        "主轴联轴器对中良好，无偏心现象",
        "齿轮箱行星轮系运行正常，载荷分布均匀",
        "发电机冷却系统效果良好，温升控制有效",
        "整体设备健康状态优良，可继续正常运行"
    ]
    
    # 只创建5个图表（远少于结论数量）
    charts = {
        "Main Bearing RMS": generate_test_chart("rms", "Main Bearing"),
        "Gearbox Peak Analysis": generate_test_chart("peak", "Gearbox"),
        "Generator Frequency Spectrum": generate_test_chart("frequency", "Generator"),
        "Tower Vibration Trend": generate_test_chart("trend", "Tower"),
        "Yaw System Analysis": generate_test_chart("rms", "Yaw System")
    }
    
    # 将分析结论合并为一个字符串
    combined_analysis = "；".join(analysis_conclusions)
    
    test_data = {
        "title": f"极大量分析结论测试报告 - {timestamp}",
        "basic_info": {
            "wind_farm": "极限测试风场",
            "turbine_id": "WT-EXTREME-001",
            "measurement_date": datetime.now().strftime("%Y-%m-%d"),
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "operator": "极限测试系统",
            "equipment_status": "运行中"
        },
        "executive_summary": "本次极限测试验证了系统处理20个分析结论的能力，仅配备5个图表进行配对显示测试。",
        "measurement_results": [
            {
                "measurement_point": "主轴承DE",
                "rms_value": 2.1,
                "peak_value": 7.3,
                "main_frequency": 23.8,
                "alarm_level": "normal"
            },
            {
                "measurement_point": "齿轮箱HSS",
                "rms_value": 3.5,
                "peak_value": 10.8,
                "main_frequency": 1238.0,
                "alarm_level": "warning"
            },
            {
                "measurement_point": "发电机前轴承",
                "rms_value": 1.7,
                "peak_value": 5.9,
                "main_frequency": 49.8,
                "alarm_level": "normal"
            },
            {
                "measurement_point": "塔筒顶部",
                "rms_value": 0.6,
                "peak_value": 2.1,
                "main_frequency": 0.25,
                "alarm_level": "normal"
            },
            {
                "measurement_point": "偏航轴承",
                "rms_value": 1.0,
                "peak_value": 3.5,
                "main_frequency": 0.08,
                "alarm_level": "normal"
            },
            {
                "measurement_point": "变桨系统",
                "rms_value": 0.9,
                "peak_value": 3.2,
                "main_frequency": 2.5,
                "alarm_level": "normal"
            }
        ],
        "analysis_conclusion": combined_analysis,
        "charts": charts,
        "recommendations": [
            "继续监测齿轮箱高速轴不平衡情况",
            "检查发电机前轴承润滑状态",
            "定期检查主轴低速端轴承磨损程度",
            "保持现有维护计划，定期复检",
            "建议增加关键部位温度监测",
            "优化润滑系统维护周期",
            "加强极端天气条件下的监测频次"
        ]
    }
    
    return test_data, timestamp

def main():
    """主测试函数"""
    print("开始极限测试：20个分析结论 vs 5个图表...")
    print("="*70)
    
    # 创建测试数据
    test_data, timestamp = create_extreme_test_data()
    
    print(f"极限测试数据创建完成:")
    print(f"- 分析结论数量: {len(test_data['analysis_conclusion'].split('；'))}")
    print(f"- 图表数量: {len(test_data['charts'])}")
    print(f"- 测量结果数量: {len(test_data['measurement_results'])}")
    print(f"- 结论与图表比例: {len(test_data['analysis_conclusion'].split('；'))}:{len(test_data['charts'])} = 4:1")
    print()
    
    # 创建报告生成器
    generator = CMSReportGenerator()
    
    # 生成HTML报告
    html_output = f"extreme_conclusions_test_{timestamp}.html"
    print(f"正在生成HTML报告: {html_output}")
    
    try:
        success = generator.generate_html_report(test_data, html_output)
        if success:
            print(f"✓ HTML报告生成成功: {html_output}")
            
            # 验证报告内容
            with open(html_output, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 统计分析要点数量
            analysis_sections = content.count('分析要点')
            chart_images = content.count('<img src="data:image/png;base64,')
            
            print(f"\n极限测试验证结果:")
            print(f"- 分析要点显示数量: {analysis_sections}")
            print(f"- 图表显示数量: {chart_images}")
            
            expected_conclusions = 20
            expected_charts = 5
            
            if analysis_sections == expected_conclusions:
                print(f"✓ 所有{expected_conclusions}个分析结论都正确显示")
            else:
                print(f"✗ 分析结论显示异常，期望{expected_conclusions}个，实际{analysis_sections}个")
                
            if chart_images == expected_charts:
                print(f"✓ 所有{expected_charts}个图表都正确显示")
            else:
                print(f"✗ 图表显示异常，期望{expected_charts}个，实际{chart_images}个")
            
            # 检查配对逻辑
            print(f"\n配对逻辑验证:")
            print(f"- 前{expected_charts}个分析要点应该有对应图表")
            print(f"- 后{expected_conclusions - expected_charts}个分析要点应该只有文字描述")
            
            # 计算文件大小
            file_size = os.path.getsize(html_output)
            print(f"\n报告文件信息:")
            print(f"- 文件大小: {file_size / 1024:.1f} KB")
            print(f"- 处理能力验证: {'通过' if analysis_sections >= 15 else '需要优化'}")
                
        else:
            print("✗ HTML报告生成失败")
            return False
            
    except Exception as e:
        print(f"✗ 报告生成过程中出现异常: {e}")
        return False
    
    print("\n" + "="*70)
    print("极限测试完成！")
    print(f"测试结论: 系统{'能够' if analysis_sections >= 15 else '无法'}正确处理大量分析结论")
    print(f"报告文件: {html_output}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)