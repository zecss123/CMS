#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from cms_offline_demo import CMSOfflineDemo
from datetime import datetime, timedelta

def debug_report_data():
    """调试报告数据结构"""
    print("🔍 调试报告数据结构")
    print("=" * 40)
    
    # 创建演示实例
    demo = CMSOfflineDemo()
    
    # 模拟分析过程
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
    
    if result["success"]:
        print("✅ 分析成功")
        
        # 检查报告数据结构
        report_data = result.get("report_data")
        if report_data:
            print("\n📋 报告数据结构:")
            print(f"  - title: {report_data.get('title', 'N/A')}")
            print(f"  - basic_info: {'存在' if 'basic_info' in report_data else '缺失'}")
            print(f"  - measurement_results: {'存在' if 'measurement_results' in report_data else '缺失'}")
            print(f"  - charts: {'存在' if 'charts' in report_data else '缺失'}")
            
            if 'charts' in report_data:
                charts = report_data['charts']
                print(f"\n📊 图表数据:")
                for name, data in charts.items():
                    if data:
                        print(f"  ✅ {name}: {len(data)} 字符")
                    else:
                        print(f"  ❌ {name}: 空数据")
            else:
                print("\n❌ 报告数据中没有charts字段")
            
            # 保存完整的报告数据到JSON文件
            with open('debug_report_data.json', 'w', encoding='utf-8') as f:
                # 为了避免JSON文件过大，截断base64数据
                debug_data = report_data.copy()
                if 'charts' in debug_data:
                    for name, data in debug_data['charts'].items():
                        if data and len(data) > 100:
                            debug_data['charts'][name] = data[:100] + "...[截断]"
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            print("\n📄 调试数据已保存到: debug_report_data.json")
            
        else:
            print("❌ 结果中没有report_data字段")
            print(f"结果键: {list(result.keys())}")
    else:
        print(f"❌ 分析失败: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    debug_report_data()