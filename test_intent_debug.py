#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Intent分析调试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import get_config
from chat.intent_analyzer import IntentAnalyzer

def test_intent_analysis():
    """测试意图分析"""
    print("=== Intent分析调试测试 ===")
    
    # 初始化配置
    config = get_config()
    print(f"配置加载成功: {type(config)}")
    
    # 初始化Intent分析器
    intent_analyzer = IntentAnalyzer()
    print("Intent分析器初始化完成")
    
    # 测试消息
    test_messages = [
        "华能风场A的A01风机",
        "生成华能风场A的A01风机振动分析报告",
        "你好",
        "查询系统状态"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- 测试消息 {i}: {message} ---")
        try:
            result = intent_analyzer.analyze_intent(message)
            print(f"意图类型: {result.get('intent', 'unknown')}")
            print(f"置信度: {result.get('confidence', 0)}")
            print(f"实体: {result.get('entities', {})}")
            if result.get('error'):
                print(f"错误: {result.get('error')}")
        except Exception as e:
            print(f"分析失败: {e}")

if __name__ == "__main__":
    test_intent_analysis()