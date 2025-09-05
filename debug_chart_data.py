#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from cms_offline_demo import CMSOfflineDemo
from datetime import datetime, timedelta

def debug_chart_data():
    """调试图表数据准备过程"""
    print("🔍 调试图表数据准备过程")
    print("=" * 40)
    
    # 创建演示实例
    demo = CMSOfflineDemo()
    
    # 查找最新的图表文件
    chart_files = [f for f in os.listdir('.') if f.startswith('mock_chart_') and f.endswith('.png')]
    if chart_files:
        latest_chart = sorted(chart_files)[-1]
        print(f"📊 最新图表文件: {latest_chart}")
        print(f"📏 文件大小: {os.path.getsize(latest_chart)} 字节")
        
        # 测试_prepare_chart_data方法
        chart_data = demo._prepare_chart_data(latest_chart)
        print(f"\n📋 图表数据结构:")
        for name, data in chart_data.items():
            if data:
                print(f"  ✅ {name}: {len(data)} 字符")
                print(f"     前50字符: {data[:50]}...")
            else:
                print(f"  ❌ {name}: 空数据")
        
        # 直接测试base64编码
        import base64
        try:
            with open(latest_chart, 'rb') as f:
                image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            print(f"\n🔧 直接base64编码测试:")
            print(f"  ✅ 编码成功: {len(base64_data)} 字符")
            print(f"     前50字符: {base64_data[:50]}...")
        except Exception as e:
            print(f"  ❌ 编码失败: {e}")
    else:
        print("❌ 没有找到图表文件")
    
    # 测试完整的分析流程
    print("\n🔄 测试完整分析流程")
    print("-" * 30)
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    result = demo.analyze_vibration_data(
        region="A08",
        station="1003", 
        position="8",
        point="AI_CMS024",
        start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
        end_time=end_time.strftime('%Y-%m-%d %H:%M:%S')
    )
    
    if result["success"] and "report_data" in result:
        report_data = result["report_data"]
        if "charts" in report_data:
            charts = report_data["charts"]
            print(f"✅ 分析结果中的图表数据:")
            for name, data in charts.items():
                if data:
                    print(f"  ✅ {name}: {len(data)} 字符")
                else:
                    print(f"  ❌ {name}: 空数据")
        else:
            print("❌ 分析结果中没有charts字段")
    else:
        print("❌ 分析失败或没有report_data字段")

if __name__ == "__main__":
    debug_chart_data()