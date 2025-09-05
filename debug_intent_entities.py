#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试意图分析器实体提取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat.intent_analyzer import IntentAnalyzer

def debug_intent_analysis():
    """调试意图分析"""
    print("=== 意图分析器实体提取调试 ===")
    
    analyzer = IntentAnalyzer()
    
    test_messages = [
        "华能风场A的A01风机",
        "生成华能风场A的A01风机振动分析报告",
        "查询华能风场A的A01风机状态"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- 测试消息 {i}: {message} ---")
        
        result = analyzer.analyze_intent(message)
        
        print(f"意图: {result.get('intent')}")
        print(f"置信度: {result.get('confidence')}")
        print(f"实体: {result.get('entities')}")
        
        # 详细检查实体
        entities = result.get('entities', {})
        print(f"风场实体: '{entities.get('wind_farm')}'")
        print(f"机组实体: '{entities.get('turbine')}'")
        print(f"时间范围: '{entities.get('time_range')}'")
        
        # 检查实体是否为空
        wind_farm_empty = not entities.get('wind_farm')
        turbine_empty = not entities.get('turbine')
        print(f"风场为空: {wind_farm_empty}")
        print(f"机组为空: {turbine_empty}")
        
        # 模拟ChatManager的检查逻辑
        if wind_farm_empty or turbine_empty:
            print("❌ ChatManager会返回'请提供风场和机组信息'")
        else:
            print("✅ ChatManager会继续处理报告生成")

if __name__ == "__main__":
    debug_intent_analysis()