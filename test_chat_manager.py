#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ChatManager功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat.chat_manager import ChatManager

def test_chat_manager():
    """测试ChatManager基本功能"""
    try:
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
        
        # 初始化ChatManager
        chat_manager = ChatManager(config)
        print("ChatManager初始化成功")
        
        # 测试系统状态
        status = chat_manager.get_system_status()
        print(f"系统状态: {status}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chat_manager()
    if success:
        print("\n✅ ChatManager测试通过")
    else:
        print("\n❌ ChatManager测试失败")
        sys.exit(1)