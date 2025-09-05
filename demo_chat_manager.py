#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatManager功能演示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat.chat_manager import ChatManager
import json

def demo_chat_manager():
    """演示ChatManager的主要功能"""
    print("=== CMS振动分析系统 ChatManager 演示 ===")
    
    # 创建配置
    config = {
        'llm': {
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'api_key': 'test-key'
        },
        'knowledge': {
            'embeddings_path': 'embeddings',
            'metadata_path': 'metadata'
        },
        'api': {
            'base_url': 'http://localhost:8000'
        },
        'database': {
            'url': 'sqlite:///vibration.db'
        }
    }
    
    try:
        # 初始化ChatManager
        print("\n1. 初始化ChatManager...")
        chat_manager = ChatManager(config)
        print("✅ ChatManager初始化成功")
        
        # 获取系统状态
        print("\n2. 获取系统状态...")
        status = chat_manager.get_system_status()
        print(f"系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 模拟用户对话
        print("\n3. 模拟用户对话...")
        test_messages = [
            "生成风场A机组T001的振动分析报告",
            "查询风场B的设备状态",
            "什么是振动分析？",
            "帮我查找振动分析相关的知识"
        ]
        
        user_id = "demo_user"
        session_id = None
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n3.{i} 用户消息: {message}")
            try:
                response = chat_manager.process_message(
                    user_id=user_id,
                    message=message,
                    session_id=session_id,
                    stream=False
                )
                
                if response.get('success'):
                    print(f"✅ 响应: {response.get('response', '无响应内容')[:100]}...")
                    if not session_id:
                        session_id = response.get('session_id')
                        print(f"会话ID: {session_id}")
                else:
                    print(f"❌ 错误: {response.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"❌ 处理消息失败: {e}")
        
        # 获取会话历史
        if session_id:
            print(f"\n4. 获取会话历史 (会话ID: {session_id})...")
            try:
                history = chat_manager.get_session_history(session_id)
                if history.get('success'):
                    messages = history.get('messages', [])
                    print(f"✅ 会话包含 {len(messages)} 条消息")
                    for msg in (messages[-2:] if len(messages) >= 2 else messages):  # 显示最后2条消息
                        content = msg.get('content', '')
                        preview = content[:50] + '...' if len(content) > 50 else content
                        print(f"  - {msg.get('role', 'unknown')}: {preview}")
                else:
                    print(f"❌ 获取会话历史失败: {history.get('error')}")
            except Exception as e:
                print(f"❌ 获取会话历史失败: {e}")
        
        print("\n=== 演示完成 ===")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_chat_manager()
    if success:
        print("\n🎉 ChatManager演示成功完成！")
    else:
        print("\n💥 ChatManager演示失败")
        sys.exit(1)