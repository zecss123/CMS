#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ChatManager完整集成流程
专门用于调试slice(None, 3, None)错误
"""

import sys
import os
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chat.chat_manager import ChatManager
from config.settings import (
    MODEL_CONFIG, VECTOR_DB_CONFIG, CMS_CONFIG, 
    WIND_FARM_CONFIG, REPORT_CONFIG, LOGGING_CONFIG
)

def get_config():
    """构建配置字典"""
    return {
        'llm': MODEL_CONFIG,
        'knowledge': {
            'embeddings_path': 'embeddings',
            'metadata_path': 'metadata',
            'template_path': 'data/templates'
        },
        'api': {},
        'database': {}
    }

def test_chat_manager_integration():
    """测试ChatManager完整集成"""
    try:
        print("=== ChatManager集成测试开始 ===")
        
        # 1. 初始化配置
        print("\n1. 加载配置...")
        config = get_config()
        print(f"配置加载成功: {type(config)}")
        
        # 2. 初始化ChatManager
        print("\n2. 初始化ChatManager...")
        chat_manager = ChatManager(config)
        print("ChatManager初始化成功")
        
        # 3. 测试不同类型的消息
        test_messages = [
            "你好",
            "什么是振动分析？",
            "生成一个报告",
            "查询系统状态"
        ]
        
        print("\n3. 测试消息处理...")
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- 测试消息 {i}: {message} ---")
            try:
                # 直接调用process_message
                result = chat_manager.process_message(
                    user_id=f"test_user_{i}",
                    message=message,
                    session_id=None,
                    stream=False
                )
                
                print(f"处理结果: {result.get('success', False)}")
                if not result.get('success', False):
                    print(f"错误信息: {result.get('error', 'Unknown error')}")
                else:
                    response = result.get('response', '')
                    preview = response[:100] + '...' if len(response) > 100 else response
                    print(f"响应预览: {preview}")
                    
            except Exception as e:
                print(f"消息处理异常: {e}")
                print(f"异常类型: {type(e)}")
                traceback.print_exc()
        
        print("\n=== ChatManager集成测试完成 ===")
        return True
        
    except Exception as e:
        print(f"\n集成测试失败: {e}")
        print(f"异常类型: {type(e)}")
        traceback.print_exc()
        return False

def test_knowledge_integration():
    """专门测试知识检索集成"""
    try:
        print("\n=== 知识检索集成测试 ===")
        
        config = get_config()
        chat_manager = ChatManager(config)
        
        # 直接测试_handle_general_chat方法
        print("\n测试_handle_general_chat方法...")
        result = chat_manager._handle_general_chat(
            session_id="test_session",
            message="什么是振动分析？",
            stream=False
        )
        
        print(f"知识检索集成结果: {result}")
        return True
        
    except Exception as e:
        print(f"知识检索集成测试失败: {e}")
        print(f"异常类型: {type(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始ChatManager集成调试...")
    
    # 运行集成测试
    success1 = test_chat_manager_integration()
    success2 = test_knowledge_integration()
    
    if success1 and success2:
        print("\n✅ 所有集成测试通过")
    else:
        print("\n❌ 集成测试失败")
        sys.exit(1)