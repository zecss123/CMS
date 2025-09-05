#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM响应
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import get_config
from chat.llm_client import LLMClient

def test_llm_report_generation():
    """测试LLM报告生成"""
    print("=== 测试LLM报告生成 ===")
    
    # 初始化配置和LLM客户端
    config = get_config()
    llm_client = LLMClient(config.config)
    
    # 构建测试提示
    prompt = """请生成一份专业的风电机组振动分析报告，包含以下信息：

风场：华能风场A
机组：A01

振动数据概况：
- data_source: mock_data
- timestamp: 2025-08-14T16:43:07.019107
- data: [大量振动数据点]

请确保报告包含：
1. 执行摘要
2. 数据分析结果
3. 异常识别和诊断
4. 维护建议
5. 结论和建议"""
    
    print(f"\n发送给LLM的提示:")
    print(f"提示长度: {len(prompt)}")
    print(f"提示内容: {prompt[:500]}...")
    
    # 构建上下文
    context = {
        'knowledge_results': {'success': True, 'query': '华能风场A A01 振动分析', 'results': [], 'total_found': 0},
        'data_context': {
            'data_source': 'mock_data',
            'timestamp': '2025-08-14T16:43:07.019107',
            'data': [1.0, 2.0, 3.0]  # 简化的数据
        }
    }
    
    print(f"\n上下文信息:")
    print(f"知识检索结果: {context['knowledge_results']}")
    print(f"数据上下文: {context['data_context']}")
    
    try:
        # 调用LLM
        print(f"\n正在调用LLM...")
        result = llm_client.chat(prompt, context, stream=False)
        
        print(f"\nLLM调用结果:")
        print(f"成功: {result.get('success')}")
        print(f"错误: {result.get('error')}")
        
        if result.get('success'):
            response = result.get('response', '')
            print(f"响应长度: {len(response)}")
            print(f"响应内容: {response}")
        else:
            print(f"LLM调用失败: {result.get('error')}")
            
        return result
        
    except Exception as e:
        print(f"❌ LLM测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"LLM测试失败: {str(e)}"
        }

if __name__ == "__main__":
    result = test_llm_report_generation()
    print(f"\n=== 最终测试结果 ===")
    print(f"成功: {result.get('success')}")
    if not result.get('success'):
        print(f"错误: {result.get('error')}")