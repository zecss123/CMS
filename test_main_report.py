#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试主程序的报告生成功能
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from cms_offline_demo import CMSOfflineDemo
from report.generator import CMSReportGenerator

def test_main_report_generation():
    """测试主程序的报告生成逻辑"""
    print("🧪 测试主程序报告生成功能...")
    
    # 初始化应用
    demo_app = CMSOfflineDemo(use_real_api=False)
    
    # 设置测试参数
    region = "A08"
    station = "S001"
    position = "P001"
    point = "PT001"
    hours = 1
    
    # 计算时间范围
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    print(f"📊 生成分析数据...")
    print(f"区域: {region}, 站点: {station}, 位置: {position}, 测点: {point}")
    print(f"时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 生成分析报告
    result = demo_app.analyze_vibration_data(
        region=region,
        station=station,
        position=position,
        point=point,
        start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
        end_time=end_time.strftime('%Y-%m-%d %H:%M:%S')
    )
    
    if result["success"]:
        print("✅ 分析数据生成成功")
        print(f"包含report_data: {'report_data' in result}")
        
        if "report_data" in result:
            print(f"report_data包含charts: {'charts' in result['report_data']}")
            if 'charts' in result['report_data']:
                charts = result['report_data']['charts']
                print(f"图表数量: {len(charts)}")
                for i, chart in enumerate(charts):
                    if isinstance(chart, dict):
                        print(f"  图表{i+1}: {chart.get('title', 'Unknown')} - 数据长度: {len(chart.get('data', ''))}")
                    else:
                        print(f"  图表{i+1}: 数据类型: {type(chart)} - 数据长度: {len(str(chart))}")
                        print(f"  图表{i+1}内容预览: {str(chart)[:100]}...")
        
        # 测试HTML报告生成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"test_main_report_{timestamp}.html"
        
        print(f"\n📄 生成HTML报告: {report_filename}")
        
        # 使用HTML报告生成器
        generator = CMSReportGenerator()
        success = generator.generate_html_report(result["report_data"], report_filename)
        
        if success:
            print(f"✅ HTML报告生成成功: {report_filename}")
            
            # 检查文件内容
            with open(report_filename, 'r', encoding='utf-8') as f:
                content = f.read()
                
            print(f"文件大小: {len(content)} 字符")
            print(f"包含img标签: {'<img src="data:image' in content}")
            print(f"包含base64数据: {'base64,' in content}")
            
            # 查找图表部分
            if '分析图表' in content:
                print("✅ 找到图表部分")
                chart_start = content.find('分析图表')
                chart_section = content[chart_start:chart_start+500]
                print(f"图表部分预览: {chart_section[:200]}...")
            else:
                print("❌ 未找到图表部分")
                
        else:
            print("❌ HTML报告生成失败")
            
    else:
        print("❌ 分析数据生成失败")
        print(f"错误信息: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_main_report_generation()