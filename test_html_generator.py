#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import base64
from report.generator import CMSReportGenerator
from cms_offline_demo import CMSOfflineDemo
from datetime import datetime, timedelta

def test_html_generator():
    """测试HTML生成器的图表嵌入功能"""
    print("🔍 测试HTML生成器的图表嵌入功能")
    print("=" * 50)
    
    # 1. 获取真实的分析数据
    demo = CMSOfflineDemo()
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
    
    if not result["success"] or "report_data" not in result:
        print("❌ 无法获取分析数据")
        return
    
    report_data = result["report_data"]
    print(f"✅ 获取到分析数据")
    print(f"📊 图表数据: {'存在' if 'charts' in report_data else '缺失'}")
    
    if 'charts' in report_data:
        for name, data in report_data['charts'].items():
            print(f"  - {name}: {len(data) if data else 0} 字符")
    
    # 2. 使用HTML生成器生成报告
    generator = CMSReportGenerator()
    output_path = f"test_html_generator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    try:
        success = generator.generate_html_report(report_data, output_path)
        print(f"\n📄 HTML报告生成: {'成功' if success else '失败'}")
        print(f"📁 输出文件: {output_path}")
        
        if success and os.path.exists(output_path):
            # 检查生成的HTML文件
            with open(output_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            print(f"\n🔍 HTML文件分析:")
            print(f"  - 文件大小: {len(html_content)} 字符")
            print(f"  - 包含图表标题: {'分析图表' in html_content}")
            print(f"  - 包含img标签: {'<img src="data:image' in html_content}")
            print(f"  - 包含base64数据: {'base64,' in html_content}")
            
            # 查找图表部分
            chart_start = html_content.find('<h2>分析图表</h2>')
            if chart_start != -1:
                chart_section = html_content[chart_start:chart_start+500]
                print(f"\n📊 图表部分预览:")
                print(chart_section)
            else:
                print(f"\n❌ 未找到图表部分")
                
        else:
            print(f"❌ HTML文件不存在或生成失败")
            
    except Exception as e:
        print(f"❌ HTML生成过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 创建一个简化的测试数据来验证
    print(f"\n🧪 使用简化测试数据验证")
    print("-" * 30)
    
    # 找到最新的图表文件
    chart_files = [f for f in os.listdir('.') if f.startswith('mock_chart_') and f.endswith('.png')]
    if chart_files:
        latest_chart = sorted(chart_files)[-1]
        
        # 读取并编码图表
        with open(latest_chart, 'rb') as f:
            image_data = f.read()
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        test_data = {
            "title": "简化测试报告",
            "basic_info": {
                "wind_farm": "测试风场",
                "turbine_id": "TEST-001",
                "measurement_date": "2025-09-03",
                "operator": "测试员",
                "equipment_status": "运行中"
            },
            "executive_summary": "这是一个简化的测试报告。",
            "measurement_results": [
                {
                    "measurement_point": "测试点",
                    "rms_value": 1.0,
                    "peak_value": 2.0,
                    "main_frequency": 50.0,
                    "alarm_level": "normal"
                }
            ],
            "charts": {
                "测试图表": base64_data
            },
            "analysis_conclusion": "测试结论",
            "recommendations": ["测试建议1", "测试建议2"]
        }
        
        test_output = f"simplified_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        try:
            success = generator.generate_html_report(test_data, test_output)
            print(f"✅ 简化测试报告生成: {'成功' if success else '失败'}")
            print(f"📁 输出文件: {test_output}")
            
            if success and os.path.exists(test_output):
                with open(test_output, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"  - 包含img标签: {'<img src="data:image' in content}")
                print(f"  - 包含base64数据: {'base64,' in content}")
            
        except Exception as e:
            print(f"❌ 简化测试失败: {e}")
    else:
        print("❌ 没有找到图表文件进行测试")

if __name__ == "__main__":
    test_html_generator()