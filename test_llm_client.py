#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试LLM客户端
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat.llm_client import LLMClient

def test_llm_client():
    """测试LLM客户端"""
    try:
        # 配置
        config = {
            'type': 'local',
            'model_name': 'test-model',
            'max_tokens': 1000,
            'temperature': 0.7
        }
        
        # 创建客户端
        print("1. 创建LLM客户端...")
        client = LLMClient(config)
        print("✅ LLM客户端创建成功")
        
        # 测试对话
        print("\n2. 测试对话...")
        test_messages = [
            "你好",
            "什么是振动分析？",
            "生成一个报告"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n2.{i} 测试消息: {message}")
            try:
                result = client.chat(message)
                if result.get('success'):
                    print(f"✅ 响应: {result['response'][:100]}...")
                else:
                    print(f"❌ 错误: {result.get('error')}")
            except Exception as e:
                print(f"❌ 异常: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n=== 测试完成 ===")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_client()
    if success:
        print("\n🎉 LLM客户端测试成功！")
    else:
        print("\n💥 LLM客户端测试失败")
        sys.exit(1)