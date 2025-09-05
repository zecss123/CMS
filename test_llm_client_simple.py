#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试LLM客户端
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import get_config
from chat.llm_client import LLMClient

def test_llm_client():
    """测试LLM客户端"""
    print("=== LLM客户端测试 ===")
    
    # 加载配置
    config = get_config()
    model_config = config.config.get('model', {})
    print(f"模型配置: {model_config}")
    
    # 初始化LLM客户端
    try:
        llm_client = LLMClient(model_config)
        print(f"LLM客户端初始化成功")
        print(f"模型类型: {llm_client.model_type}")
        print(f"模型名称: {llm_client.model_name}")
        
        # 测试简单对话
        test_message = "请生成一个简短的测试响应"
        print(f"\n测试消息: {test_message}")
        
        result = llm_client.chat(test_message, stream=False)
        print(f"\n对话结果: {result}")
        
        if result.get('success'):
            print(f"✅ LLM客户端工作正常")
            print(f"响应: {result.get('response', '无响应')}")
        else:
            print(f"❌ LLM客户端调用失败")
            print(f"错误: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ LLM客户端初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm_client()