#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试ChatManager报告生成处理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import get_config
from chat.chat_manager import ChatManager
from chat.session_manager import SessionManager
from chat.intent_analyzer import IntentAnalyzer

def debug_chat_manager_detailed():
    """详细调试ChatManager"""
    print("=== ChatManager详细调试 ===")
    
    # 初始化配置
    config = get_config()
    print(f"配置加载成功: {type(config)}")
    
    # 初始化组件
    session_manager = SessionManager()
    chat_manager = ChatManager(config.config, session_manager)
    intent_analyzer = IntentAnalyzer()
    
    # 测试消息
    message = "华能风场A的A01风机"
    print(f"\n测试消息: {message}")
    
    # 1. 测试意图分析
    print("\n--- 步骤1: 意图分析 ---")
    intent_result = intent_analyzer.analyze_intent(message)
    print(f"意图结果: {intent_result}")
    
    # 2. 创建会话
    print("\n--- 步骤2: 创建会话 ---")
    session_id = session_manager.create_session("test_user")
    print(f"会话ID: {session_id}")
    
    # 3. 直接测试_handle_report_generation方法
    print("\n--- 步骤3: 测试报告生成处理 ---")
    try:
        result = chat_manager._handle_report_generation(session_id, intent_result, stream=False)
        print(f"报告生成结果: {result}")
        
        # 检查实体提取
        entities = intent_result.get('entities', {})
        print(f"\n实体检查:")
        print(f"  风场: '{entities.get('wind_farm')}'")
        print(f"  机组: '{entities.get('turbine')}'")
        print(f"  风场为空: {not entities.get('wind_farm')}")
        print(f"  机组为空: {not entities.get('turbine')}")
        
        # 检查配置
        print(f"\n配置检查:")
        use_mock_data = config.config.get('development', {}).get('use_mock_data', True)
        print(f"  使用模拟数据: {use_mock_data}")
        
    except Exception as e:
        print(f"报告生成处理失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 测试完整流程
    print("\n--- 步骤4: 测试完整流程 ---")
    try:
        full_result = chat_manager.process_message(
            user_id="test_user",
            message=message,
            session_id=None,
            stream=False
        )
        print(f"完整流程结果: {full_result}")
    except Exception as e:
        print(f"完整流程失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_chat_manager_detailed()