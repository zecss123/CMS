#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import os
from cms_offline_demo import CMSOfflineDemo

def test_chart_embedding():
    """测试图表嵌入功能"""
    print("🔍 测试图表嵌入功能")
    print("=" * 40)
    
    # 检查最新的图片文件
    chart_files = [f for f in os.listdir('.') if f.startswith('mock_chart_') and f.endswith('.png')]
    if not chart_files:
        print("❌ 没有找到图片文件")
        return
    
    latest_chart = sorted(chart_files)[-1]
    print(f"📊 使用图片文件: {latest_chart}")
    print(f"📏 文件大小: {os.path.getsize(latest_chart)} bytes")
    
    # 测试base64编码
    try:
        with open(latest_chart, 'rb') as f:
            chart_data = base64.b64encode(f.read()).decode('utf-8')
        print(f"✅ Base64编码成功，长度: {len(chart_data)}")
        print(f"🔤 Base64前缀: {chart_data[:50]}...")
    except Exception as e:
        print(f"❌ Base64编码失败: {e}")
        return
    
    # 测试CMSOfflineDemo的_prepare_chart_data方法
    demo = CMSOfflineDemo()
    charts = demo._prepare_chart_data(latest_chart)
    print(f"\n📋 图表数据准备结果:")
    for name, data in charts.items():
        if data:
            print(f"  ✅ {name}: {len(data)} 字符")
        else:
            print(f"  ❌ {name}: 空数据")
    
    # 创建简单的HTML测试
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>图表测试</title>
</head>
<body>
    <h1>图表嵌入测试</h1>
    <div class="chart">
        <h3>振动趋势图</h3>
        <img src="data:image/png;base64,{chart_data}" alt="振动趋势图" style="max-width: 100%; border: 1px solid #ddd;">
    </div>
</body>
</html>
"""
    
    test_html_file = "test_chart_embedding.html"
    with open(test_html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 测试HTML文件已生成: {test_html_file}")
    print(f"📏 HTML文件大小: {os.path.getsize(test_html_file)} bytes")
    
if __name__ == "__main__":
    test_chart_embedding()