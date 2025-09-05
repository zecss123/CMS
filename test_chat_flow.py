#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ChatManager完整流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import get_config
from chat.chat_manager import ChatManager
from chat.session_manager import SessionManager

def test_chat_flow():
    """测试聊天流程"""
    print("=== ChatManager完整流程测试 ===")
    
    # 初始化配置
    config = get_config()
    print(f"配置加载成功: {type(config)}")
    
    # 初始化SessionManager
    session_manager = SessionManager()
    print("SessionManager初始化完成")
    
    # 初始化ChatManager
    chat_manager = ChatManager(config.config, session_manager)
    print("ChatManager初始化完成")
    
    # 测试消息
    test_messages = [
        "华能风场A的A01风机",
        "生成华能风场A的A01风机振动分析报告"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- 测试消息 {i}: {message} ---")
        try:
            result = chat_manager.process_message(
                user_id="test_user",
                message=message,
                session_id=None,
                stream=False
            )
            
            print(f"处理成功: {result.get('success', False)}")
            if result.get('success'):
                response = result.get('response', '无响应')
                print(f"响应: {response[:200]}..." if len(response) > 200 else f"响应: {response}")
            else:
                print(f"错误: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"处理失败: {e}")

if __name__ == "__main__":
    test_chat_flow()