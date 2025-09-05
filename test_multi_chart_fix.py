#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from report.generator import CMSReportGenerator
from datetime import datetime
import base64
import io
import matplotlib.pyplot as plt
import numpy as np

def create_test_chart(title):
    """创建测试图表"""
    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.linspace(0, 10, 100)
    y = np.sin(x) + np.random.normal(0, 0.1, 100)
    ax.plot(x, y)
    ax.set_title(title)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Amplitude')
    
    # 转换为base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return image_base64

def test_multi_chart_fix():
    """测试多图表修复逻辑"""
    print("🔧 测试多图表配对修复逻辑")
    print("=" * 40)
    
    # 创建测试数据：5个分析结论，但只有2个图表
    test_data = {
        "title": "多图表配对测试报告",
        "basic_info": {
            "wind_farm": "测试风场",
            "turbine_id": "WT-TEST-001",
            "measurement_date": "2024-09-04",
            "operator": "测试员",
            "equipment_status": "运行中"
        },
        "executive_summary": "测试多个分析结论与少量图表的配对显示。",
        "measurement_results": [
            {
                "measurement_point": "测点1",
                "rms_value": 2.5,
                "peak_value": 8.2,
                "main_frequency": 25.5,
                "alarm_level": "normal"
            },
            {
                "measurement_point": "测点2",
                "rms_value": 4.1,
                "peak_value": 12.8,
                "main_frequency": 1250.0,
                "alarm_level": "warning"
            }
        ],
        # 5个分析结论
        "analysis_conclusion": "1)转子严重不平衡；2)联轴器对中不良；3)齿轮箱内部磨损严重；4)轴承可能存在缺陷；5)整体温度异常升高。建议立即停机进行全面检修。",
        # 只有2个图表
        "charts": {
            "RMS分布图": create_test_chart("RMS Distribution"),
            "峰值分布图": create_test_chart("Peak Distribution")
        },
        "recommendations": [
            "立即停机，避免设备进一步损坏",
            "检查并重新平衡转子",
            "重新校正联轴器对中",
            "更换磨损的齿轮",
            "检查轴承状态",
            "监测温度变化"
        ]
    }
    
    # 生成报告
    generator = CMSReportGenerator()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"multi_chart_test_{timestamp}.html"
    
    success = generator.generate_html_report(test_data, filename)
    
    if success:
        print(f"✅ 测试报告生成成功: {filename}")
        
        # 读取并分析报告内容
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计分析要点数量
        analysis_points = content.count('<h3>分析要点')
        chart_images = content.count('<img src="data:image/png;base64,')
        
        print(f"📊 报告分析:")
        print(f"  - 分析要点数量: {analysis_points}")
        print(f"  - 图表数量: {chart_images}")
        print(f"  - 预期结果: 前2个要点有图表，后3个要点无图表")
        
        # 检查具体结构
        if "分析要点 1" in content and "分析要点 5" in content:
            print("✅ 所有5个分析要点都已显示")
        else:
            print("❌ 分析要点显示不完整")
            
        if chart_images == 2:
            print("✅ 图表数量正确（2个）")
        else:
            print(f"❌ 图表数量错误，期望2个，实际{chart_images}个")
            
        return filename
    else:
        print("❌ 报告生成失败")
        return None

if __name__ == "__main__":
    test_multi_chart_fix()