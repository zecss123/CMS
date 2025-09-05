#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实机组问题测试 - 生成反映实际故障的CMS振动分析报告
"""

import os
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import base64
import io

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from report.generator import CMSReportGenerator

def create_realistic_problem_data():
    """
    创建反映真实机组问题的测试数据
    包含多种典型故障模式：不平衡、轴承磨损、齿轮箱问题等
    """
    
    # 基础信息 - 匹配CMSReportGenerator格式
    basic_info = {
        "wind_farm": "华能新能源风场",
        "turbine_id": "WT-2023-015", 
        "measurement_date": "2024-09-04",
        "report_date": "2024-09-04",
        "operator": "张工程师",
        "equipment_status": "运行中(存在故障)",
        "wind_speed": "12.5 m/s",
        "power": "1850 kW",
        "rotation_speed": "1485 rpm",
        "temperature": "45°C",
        "humidity": "65%",
        "detection_equipment": "CMS-Pro 3000"
    }
    
    # 测量结果 - 匹配CMSReportGenerator格式
    measurement_results = [
        {
            "measurement_point": "主轴承DE端",
            "rms_value": 8.5,  # 偏高，提示轴承问题
            "peak_value": 25.2,
            "main_frequency": 25.0,
            "alarm_level": "warning",
            "status": "异常",
            "frequency_feature": "1×转频突出"
        },
        {
            "measurement_point": "主轴承NDE端", 
            "rms_value": 6.8,
            "peak_value": 18.9,
            "main_frequency": 156.3,
            "alarm_level": "attention",
            "status": "轻微异常",
            "frequency_feature": "轴承故障频率"
        },
        {
            "measurement_point": "齿轮箱高速轴",
            "rms_value": 12.3,  # 明显偏高
            "peak_value": 38.7,
            "main_frequency": 350.0,
            "alarm_level": "alarm",
            "status": "异常",
            "frequency_feature": "齿轮啮合频率异常"
        },
        {
            "measurement_point": "齿轮箱中速轴",
            "rms_value": 9.2,
            "peak_value": 28.1,
            "main_frequency": 116.7,
            "alarm_level": "warning",
            "status": "异常",
            "frequency_feature": "边频带明显"
        },
        {
            "measurement_point": "发电机DE端",
            "rms_value": 7.1,
            "peak_value": 21.5,
            "main_frequency": 50.0,
            "alarm_level": "attention",
            "status": "轻微异常",
            "frequency_feature": "电磁频率"
        },
        {
            "measurement_point": "塔顶振动",
            "rms_value": 4.2,
            "peak_value": 12.8,
            "main_frequency": 0.5,
            "alarm_level": "normal",
            "status": "正常",
            "frequency_feature": "1P频率"
        }
    ]
    
    # 分析结论 - 反映实际故障诊断
    analysis_conclusions = [
        "主轴承DE端振动水平偏高，RMS值达到8.5mm/s，超出正常范围(≤6.0mm/s)，提示轴承可能存在磨损或润滑不良",
        "主轴承NDE端检测到轴承故障特征频率，建议进一步检查轴承内圈是否存在点蚀或剥落现象",
        "齿轮箱高速轴振动严重超标，RMS值12.3mm/s远超报警值(≤8.0mm/s)，齿轮啮合频率异常突出",
        "齿轮箱中速轴频谱出现明显边频带，提示齿轮可能存在局部磨损或齿面损伤",
        "发电机DE端振动水平轻微偏高，电磁频率成分明显，可能与转子偏心或气隙不均有关",
        "塔顶振动在正常范围内，1P频率成分正常，整机动平衡状态良好",
        "整体振动趋势分析显示，齿轮箱系统存在较严重问题，需要立即安排停机检修",
        "主轴承系统振动水平持续上升，建议加强润滑维护并制定更换计划",
        "根据频谱分析结果，齿轮箱内部齿轮损伤程度较重，继续运行存在安全风险",
        "建议立即降载运行，将功率控制在额定功率的70%以下，减少设备负荷"
    ]
    
    # 建议措施 - 针对实际问题的维护建议
    recommendations = [
        "立即安排齿轮箱停机检修，重点检查高速轴齿轮磨损情况",
        "更换主轴承DE端轴承，检查润滑系统是否正常",
        "对齿轮箱进行内窥镜检查，确认齿轮损伤程度",
        "加强主轴承润滑维护，缩短润滑油更换周期",
        "检查发电机转子动平衡，必要时进行重新校正",
        "建立设备振动趋势监测档案，每周进行一次振动检测",
        "制定应急预案，准备备件和检修工具",
        "联系设备厂家技术支持，获取专业维修指导"
    ]
    
    return {
        "basic_info": basic_info,
        "measurement_results": measurement_results,
        "analysis_conclusions": analysis_conclusions,
        "recommendations": recommendations,
        "charts": {}  # 将在后面生成为字典格式
    }

def generate_realistic_charts():
    """
    生成反映实际问题的振动图表，返回base64编码的图片数据
    """
    charts = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 设置中文字体 - 直接指定字体文件路径
    import matplotlib.font_manager as fm
    from matplotlib import font_manager
    import os
    
    # 直接添加中文字体文件
    font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
    if os.path.exists(font_path):
        try:
            # 添加字体到matplotlib
            font_manager.fontManager.addfont(font_path)
            # 获取字体属性
            font_prop = fm.FontProperties(fname=font_path)
            font_name = font_prop.get_name()
            
            # 设置matplotlib参数
            plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['font.size'] = 12
            # 强制使用指定字体
            plt.rcParams['font.family'] = 'sans-serif'
            # 解决负号显示问题
            plt.rcParams['mathtext.fontset'] = 'custom'
            plt.rcParams['mathtext.rm'] = font_name
            plt.rcParams['mathtext.it'] = font_name
            
            print(f"成功加载中文字体: {font_name}")
        except Exception as e:
            print(f"字体加载失败: {e}")
            # 回退到默认配置
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
    else:
        # 使用系统字体配置
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def save_chart_as_base64(fig, chart_name):
        """将matplotlib图表转换为base64编码"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return image_base64
    
    # 1. 主轴承DE端振动趋势图 - 显示异常趋势
    fig, ax = plt.subplots(figsize=(10, 6))
    days = np.arange(1, 31)
    # 模拟振动水平逐渐上升的趋势
    rms_trend = 4.5 + 0.13 * days + 0.5 * np.sin(days * 0.3) + np.random.normal(0, 0.2, 30)
    ax.plot(days, rms_trend, 'b-', linewidth=2, label='RMS振动值')
    ax.axhline(y=6.0, color='orange', linestyle='--', label='注意阈值')
    ax.axhline(y=8.0, color='red', linestyle='--', label='报警阈值')
    ax.fill_between(days, 0, 6.0, alpha=0.2, color='green', label='正常区域')
    ax.fill_between(days, 6.0, 8.0, alpha=0.2, color='orange', label='注意区域')
    ax.fill_between(days, 8.0, 12, alpha=0.2, color='red', label='报警区域')
    ax.set_xlabel('天数')
    ax.set_ylabel('RMS值 (mm/s)')
    ax.set_title('主轴承DE端振动趋势 - 30天监测')
    ax.legend()
    ax.grid(True, alpha=0.3)
    charts["30天振动趋势分析"] = save_chart_as_base64(fig, "bearing_trend")
    plt.close()
    
    # 2. 齿轮箱高速轴频谱图 - 显示齿轮故障特征
    fig, ax = plt.subplots(figsize=(12, 6))
    freq = np.linspace(0, 1000, 1000)
    # 基础噪声
    spectrum = np.random.exponential(0.1, 1000)
    # 齿轮啮合频率及其谐波 (假设为350Hz)
    gmf = 350
    for i in range(1, 4):
        idx = int(gmf * i)
        if idx < 1000:
            spectrum[idx-5:idx+5] += 2.5 * (4-i) * np.exp(-np.linspace(-2, 2, 10)**2)
    # 边频带 - 故障特征
    for i in range(1, 4):
        for side in [-1, 1]:
            idx = int(gmf * i + side * 15)  # ±15Hz边频
            if 0 < idx < 1000:
                spectrum[idx-2:idx+3] += 1.2 * (4-i) * np.exp(-np.linspace(-1, 1, 5)**2)
    
    ax.semilogy(freq, spectrum, 'b-', linewidth=1)
    ax.set_xlabel('频率 (Hz)')
    ax.set_ylabel('振动幅值 (mm/s)')
    ax.set_title('齿轮箱高速轴频谱分析 - 齿轮故障特征明显')
    ax.grid(True, alpha=0.3)
    ax.axvline(x=gmf, color='red', linestyle='--', alpha=0.7, label=f'齿轮啮合频率 {gmf}Hz')
    ax.axvline(x=gmf*2, color='red', linestyle='--', alpha=0.5, label=f'2倍频 {gmf*2}Hz')
    ax.legend()
    charts["齿轮箱频谱分析"] = save_chart_as_base64(fig, "gearbox_spectrum")
    plt.close()
    
    # 3. 各测点振动对比图
    fig, ax = plt.subplots(figsize=(12, 8))
    test_points = ['主轴承DE', '主轴承NDE', '齿轮箱高速轴', '齿轮箱中速轴', '发电机DE', '塔顶']
    rms_values = [8.5, 6.8, 12.3, 9.2, 7.1, 4.2]
    colors = ['red' if x > 8.0 else 'orange' if x > 6.0 else 'green' for x in rms_values]
    
    bars = ax.bar(test_points, rms_values, color=colors, alpha=0.7, edgecolor='black')
    ax.axhline(y=6.0, color='orange', linestyle='--', alpha=0.8, label='注意阈值 6.0mm/s')
    ax.axhline(y=8.0, color='red', linestyle='--', alpha=0.8, label='报警阈值 8.0mm/s')
    
    # 添加数值标签
    for bar, value in zip(bars, rms_values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, 
                f'{value}', ha='center', va='bottom', fontweight='bold')
    
    ax.set_ylabel('RMS振动值 (mm/s)')
    ax.set_title('各测点振动水平对比 - 故障点突出显示')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    charts["各测点振动对比分析"] = save_chart_as_base64(fig, "comparison")
    plt.close()
    
    # 4. 轴承故障频率分析图
    fig, ax = plt.subplots(figsize=(10, 6))
    freq = np.linspace(0, 500, 500)
    spectrum = np.random.exponential(0.05, 500)
    
    # 轴承故障特征频率
    bpfi = 156.3  # 内圈故障频率
    bpfo = 103.7  # 外圈故障频率
    bsf = 67.2    # 滚动体故障频率
    
    # 添加故障特征频率及其谐波
    for freq_val, label in [(bpfi, 'BPFI'), (bpfo, 'BPFO'), (bsf, 'BSF')]:
        for i in range(1, 3):
            idx = int(freq_val * i)
            if idx < 500:
                spectrum[idx-3:idx+4] += 0.8 * (3-i) * np.exp(-np.linspace(-1.5, 1.5, 7)**2)
    
    ax.semilogy(freq, spectrum, 'b-', linewidth=1)
    ax.axvline(x=bpfi, color='red', linestyle='--', alpha=0.7, label=f'BPFI {bpfi:.1f}Hz')
    ax.axvline(x=bpfo, color='orange', linestyle='--', alpha=0.7, label=f'BPFO {bpfo:.1f}Hz')
    ax.axvline(x=bsf, color='purple', linestyle='--', alpha=0.7, label=f'BSF {bsf:.1f}Hz')
    ax.set_xlabel('频率 (Hz)')
    ax.set_ylabel('振动幅值 (mm/s)')
    ax.set_title('主轴承故障特征频率分析')
    ax.legend()
    ax.grid(True, alpha=0.3)
    charts["轴承故障频率分析"] = save_chart_as_base64(fig, "bearing_fault")
    plt.close()
    
    # 5. 振动烈度等级评估图
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # ISO 10816标准等级
    levels = ['优秀\n(<2.8)', '良好\n(2.8-4.5)', '可接受\n(4.5-7.1)', '不可接受\n(>7.1)']
    level_ranges = [(0, 2.8), (2.8, 4.5), (4.5, 7.1), (7.1, 15)]
    colors_level = ['green', 'yellow', 'orange', 'red']
    
    # 绘制等级区域
    for i, ((low, high), color, level) in enumerate(zip(level_ranges, colors_level, levels)):
        ax.barh(i, high-low, left=low, color=color, alpha=0.3, edgecolor='black')
        ax.text(low + (high-low)/2, i, level, ha='center', va='center', fontweight='bold')
    
    # 标记各测点位置
    test_points_short = ['主轴DE', '主轴NDE', '齿轮高速', '齿轮中速', '发电机', '塔顶']
    for j, (point, value) in enumerate(zip(test_points_short, rms_values)):
        ax.scatter(value, 3.5 - j*0.1, s=100, c='black', marker='o', zorder=5)
        ax.text(value + 0.3, 3.5 - j*0.1, f'{point}: {value}', va='center', fontsize=9)
    
    ax.set_xlim(0, 15)
    ax.set_ylim(-0.5, 4.5)
    ax.set_xlabel('RMS振动值 (mm/s)')
    ax.set_title('振动烈度等级评估 (ISO 10816标准)')
    ax.set_yticks(range(4))
    ax.set_yticklabels(['不可接受', '可接受', '良好', '优秀'])
    ax.grid(True, alpha=0.3, axis='x')
    charts["ISO 10816振动等级评估"] = save_chart_as_base64(fig, "iso_levels")
    plt.close()
    
    return charts

def main():
    print("开始生成真实机组问题分析报告...")
    print("=" * 60)
    
    # 创建测试数据
    test_data = create_realistic_problem_data()
    print(f"真实问题测试数据创建完成:")
    print(f"- 分析结论数量: {len(test_data['analysis_conclusions'])}")
    print(f"- 测量结果数量: {len(test_data['measurement_results'])}")
    print(f"- 建议措施数量: {len(test_data['recommendations'])}")
    print(f"- 问题严重程度: 齿轮箱严重故障 + 主轴承磨损")
    print()
    
    # 生成图表
    print("正在生成问题分析图表...")
    charts = generate_realistic_charts()
    test_data['charts'] = charts
    print(f"✓ 生成了 {len(charts)} 个分析图表")
    print()
    
    # 生成报告
    generator = CMSReportGenerator()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"realistic_problems_report_{timestamp}.html"
    
    print(f"正在生成HTML报告: {report_filename}")
    
    # 转换数据格式以匹配CMSReportGenerator
    report_data = {
        "title": "风电机组振动分析报告 - 真实故障案例",
        "basic_info": test_data['basic_info'],
        "executive_summary": "本次检测发现机组存在多项严重问题，齿轮箱高速轴振动严重超标，主轴承磨损明显，需要立即安排停机检修。",
        "measurement_results": test_data['measurement_results'],
        "analysis_conclusion": "；".join(test_data['analysis_conclusions']),
        "recommendations": test_data['recommendations'],
        "charts": test_data['charts']
    }
    
    generator.generate_html_report(report_data, report_filename)
    print(f"✓ HTML报告生成成功: {report_filename}")
    print()
    
    # 验证报告内容
    if os.path.exists(report_filename):
        file_size = os.path.getsize(report_filename) / 1024  # KB
        print("真实问题报告验证结果:")
        print(f"- 报告文件大小: {file_size:.1f} KB")
        print(f"- 包含故障类型: 齿轮箱齿轮损伤、主轴承磨损、发电机偏心")
        print(f"- 严重程度评估: 齿轮箱需立即停机检修")
        print(f"- 维护建议: {len(test_data['recommendations'])} 项具体措施")
        print()
        
        print("主要故障特征:")
        print("- 齿轮箱高速轴振动12.3mm/s (严重超标)")
        print("- 主轴承DE端振动8.5mm/s (超出正常范围)")
        print("- 齿轮啮合频率异常，边频带明显")
        print("- 轴承故障特征频率突出")
        print()
        
    print("=" * 60)
    print("真实机组问题分析报告生成完成！")
    print(f"报告文件: {report_filename}")
    print("该报告反映了风电机组的典型故障模式和诊断结果")

if __name__ == "__main__":
    main()