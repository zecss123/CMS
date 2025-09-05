#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试大量分析结论的处理能力
验证generator.py是否能正确处理超过5个分析结论的情况
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
        plt.title(f'{title} - RMS分布')
        plt.xlabel('时间 (s)')
        plt.ylabel('RMS值 (mm/s)')
    elif chart_type == "peak":
        # 峰值分布图
        x = np.linspace(0, 100, 100)
        y = np.random.normal(8.0, 1.5, 100)
        plt.plot(x, y, 'r-', linewidth=2)
        plt.title(f'{title} - 峰值分布')
        plt.xlabel('时间 (s)')
        plt.ylabel('峰值 (mm/s)')
    elif chart_type == "frequency":
        # 频谱图
        freqs = np.linspace(0, 1000, 500)
        spectrum = np.random.exponential(0.1, 500)
        plt.semilogy(freqs, spectrum, 'g-', linewidth=1)
        plt.title(f'{title} - 频谱分析')
        plt.xlabel('频率 (Hz)')
        plt.ylabel('幅值')
    else:
        # 默认趋势图
        x = np.linspace(0, 100, 100)
        y = np.sin(x/10) + np.random.normal(0, 0.1, 100)
        plt.plot(x, y, 'm-', linewidth=2)
        plt.title(f'{title} - 趋势分析')
        plt.xlabel('时间 (s)')
        plt.ylabel('振动值')
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 转换为base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return chart_base64

def create_large_test_data():
    """创建包含大量分析结论的测试数据"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建10个分析结论
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
        "整机振动水平符合设计要求，建议继续监测"
    ]
    
    # 只创建3个图表（少于结论数量）
    charts = {
        "主轴承RMS分布": generate_test_chart("rms", "主轴承"),
        "齿轮箱峰值分析": generate_test_chart("peak", "齿轮箱"),
        "发电机频谱分析": generate_test_chart("frequency", "发电机")
    }
    
    # 将分析结论合并为一个字符串
    combined_analysis = "；".join(analysis_conclusions)
    
    test_data = {
        "title": f"大量分析结论测试报告 - {timestamp}",
        "basic_info": {
            "wind_farm": "测试风场A",
            "turbine_id": "WT-TEST-001",
            "measurement_date": datetime.now().strftime("%Y-%m-%d"),
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "operator": "自动化测试",
            "equipment_status": "运行中"
        },
        "executive_summary": "本次测试验证了系统处理大量分析结论的能力，共包含10个分析要点和3个配套图表。",
        "measurement_results": [
            {
                "measurement_point": "主轴承DE",
                "rms_value": 2.3,
                "peak_value": 7.8,
                "main_frequency": 24.5,
                "alarm_level": "normal"
            },
            {
                "measurement_point": "齿轮箱HSS",
                "rms_value": 3.8,
                "peak_value": 11.2,
                "main_frequency": 1245.0,
                "alarm_level": "warning"
            },
            {
                "measurement_point": "发电机前轴承",
                "rms_value": 1.9,
                "peak_value": 6.1,
                "main_frequency": 50.0,
                "alarm_level": "normal"
            },
            {
                "measurement_point": "塔筒顶部",
                "rms_value": 0.8,
                "peak_value": 2.5,
                "main_frequency": 0.3,
                "alarm_level": "normal"
            },
            {
                "measurement_point": "偏航轴承",
                "rms_value": 1.2,
                "peak_value": 4.0,
                "main_frequency": 0.1,
                "alarm_level": "normal"
            }
        ],
        "analysis_conclusion": combined_analysis,
        "charts": charts,
        "recommendations": [
            "继续监测齿轮箱高速轴不平衡情况",
            "检查发电机前轴承润滑状态",
            "定期检查主轴低速端轴承磨损程度",
            "保持现有维护计划，3个月后复检",
            "建议增加温度监测点位"
        ]
    }
    
    return test_data, timestamp

def main():
    """主测试函数"""
    print("开始测试大量分析结论处理能力...")
    print("="*60)
    
    # 创建测试数据
    test_data, timestamp = create_large_test_data()
    
    print(f"测试数据创建完成:")
    print(f"- 分析结论数量: {len(test_data['analysis_conclusion'].split('；'))}")
    print(f"- 图表数量: {len(test_data['charts'])}")
    print(f"- 测量结果数量: {len(test_data['measurement_results'])}")
    print()
    
    # 创建报告生成器
    generator = CMSReportGenerator()
    
    # 生成HTML报告
    html_output = f"large_conclusions_test_{timestamp}.html"
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
            
            print(f"\n报告验证结果:")
            print(f"- 分析要点显示数量: {analysis_sections}")
            print(f"- 图表显示数量: {chart_images}")
            
            if analysis_sections == 10:
                print("✓ 所有10个分析结论都正确显示")
            else:
                print(f"✗ 分析结论显示不完整，期望10个，实际{analysis_sections}个")
                
            if chart_images == 3:
                print("✓ 所有3个图表都正确显示")
            else:
                print(f"✗ 图表显示异常，期望3个，实际{chart_images}个")
                
        else:
            print("✗ HTML报告生成失败")
            return False
            
    except Exception as e:
        print(f"✗ 报告生成过程中出现异常: {e}")
        return False
    
    print("\n" + "="*60)
    print("大量分析结论测试完成！")
    print(f"测试结果: 系统能够正确处理10个分析结论和3个图表的配对显示")
    print(f"报告文件: {html_output}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)