#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门调试slice(None, 3, None)错误的脚本
"""

import sys
import os
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chat.llm_client import LLMClient
from knowledge.knowledge_retriever import KnowledgeRetriever
from config.settings import MODEL_CONFIG

def debug_llm_client():
    """调试LLMClient"""
    print("=== 调试LLMClient ===")
    
    try:
        # 初始化LLMClient
        llm_client = LLMClient(MODEL_CONFIG)
        print(f"LLMClient初始化成功，模型类型: {llm_client.model_type}")
        print(f"对话历史类型: {type(llm_client.conversation_history)}")
        print(f"对话历史内容: {llm_client.conversation_history}")
        
        # 测试_build_messages方法
        print("\n--- 测试_build_messages ---")
        messages = llm_client._build_messages("测试消息")
        print(f"构建的消息: {messages}")
        
        # 测试chat方法
        print("\n--- 测试chat方法 ---")
        result = llm_client.chat("你好")
        print(f"Chat结果: {result}")
        
        return True
        
    except Exception as e:
        print(f"LLMClient调试失败: {e}")
        print(f"异常类型: {type(e)}")
        traceback.print_exc()
        return False

def debug_knowledge_retriever():
    """调试KnowledgeRetriever"""
    print("\n=== 调试KnowledgeRetriever ===")
    
    try:
        # 初始化KnowledgeRetriever
        knowledge_retriever = KnowledgeRetriever(
            embeddings_path='embeddings',
            metadata_path='metadata'
        )
        print("KnowledgeRetriever初始化成功")
        
        # 测试search方法
        print("\n--- 测试search方法 ---")
        results = knowledge_retriever.search("振动分析", top_k=3)
        print(f"搜索结果类型: {type(results)}")
        print(f"搜索结果: {results}")
        
        # 检查结果中是否有slice对象
        if results:
            for i, result in enumerate(results):
                print(f"结果{i}类型: {type(result)}")
                if isinstance(result, dict):
                    for key, value in result.items():
                        print(f"  {key}: {type(value)} = {value}")
                        if isinstance(value, slice):
                            print(f"  ⚠️ 发现slice对象: {value}")
        
        return True
        
    except Exception as e:
        print(f"KnowledgeRetriever调试失败: {e}")
        print(f"异常类型: {type(e)}")
        traceback.print_exc()
        return False

def debug_integration():
    """调试集成流程"""
    print("\n=== 调试集成流程 ===")
    
    try:
        # 初始化组件
        llm_client = LLMClient(MODEL_CONFIG)
        knowledge_retriever = KnowledgeRetriever(
            embeddings_path='embeddings',
            metadata_path='metadata'
        )
        
        # 模拟ChatManager的_handle_general_chat流程
        print("\n--- 模拟_handle_general_chat流程 ---")
        message = "什么是振动分析？"
        
        # 1. 知识检索
        print("1. 执行知识检索...")
        knowledge_results = knowledge_retriever.search(message, top_k=3)
        print(f"知识检索结果: {knowledge_results}")
        
        # 2. 构建上下文
        print("2. 构建上下文...")
        context = {'knowledge_results': knowledge_results} if knowledge_results else None
        print(f"上下文: {context}")
        
        # 3. LLM对话
        print("3. 执行LLM对话...")
        result = llm_client.chat(message, context, stream=False)
        print(f"LLM对话结果: {result}")
        
        return True
        
    except Exception as e:
        print(f"集成流程调试失败: {e}")
        print(f"异常类型: {type(e)}")
        traceback.print_exc()
        return False

def test_slice_operations():
    """测试各种slice操作"""
    print("\n=== 测试slice操作 ===")
    
    try:
        # 测试正常的slice操作
        test_list = [1, 2, 3, 4, 5]
        print(f"正常列表切片: {test_list[:3]}")
        
        # 测试None的slice操作
        try:
            none_value = None
            none_slice = none_value[:3]  # type: ignore
            print(f"None切片结果: {none_slice}")
        except Exception as e:
            print(f"None切片错误: {e}")
        
        # 测试slice对象
        slice_obj = slice(None, 3, None)
        print(f"slice对象: {slice_obj}")
        print(f"slice对象字符串: {str(slice_obj)}")
        
        # 测试slice对象应用到列表
        sliced_result = test_list[slice_obj]
        print(f"slice对象应用结果: {sliced_result}")
        
        return True
        
    except Exception as e:
        print(f"slice操作测试失败: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始slice错误调试...")
    
    # 运行各项调试
    success1 = test_slice_operations()
    success2 = debug_llm_client()
    success3 = debug_knowledge_retriever()
    success4 = debug_integration()
    
    if all([success1, success2, success3, success4]):
        print("\n✅ 所有调试测试通过")
    else:
        print("\n❌ 调试测试失败")
        sys.exit(1)