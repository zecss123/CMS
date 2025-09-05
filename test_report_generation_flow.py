#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的报告生成流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import get_config
from chat.chat_manager import ChatManager
from chat.session_manager import SessionManager
from chat.intent_analyzer import IntentAnalyzer

def test_report_generation_flow():
    """测试报告生成流程"""
    print("=== 报告生成流程测试 ===")
    
    # 初始化配置和组件
    config = get_config()
    session_manager = SessionManager()
    chat_manager = ChatManager(config.config, session_manager)
    intent_analyzer = IntentAnalyzer()
    
    # 测试消息
    message = "华能风场A的A01风机"
    print(f"\n测试消息: {message}")
    
    # 步骤1: 意图分析
    print("\n--- 步骤1: 意图分析 ---")
    intent_result = intent_analyzer.analyze_intent(message)
    print(f"意图: {intent_result['intent']}")
    print(f"实体: {intent_result['entities']}")
    
    # 步骤2: 创建会话
    print("\n--- 步骤2: 创建会话 ---")
    session_id = session_manager.create_session("test_user")
    print(f"会话ID: {session_id}")
    
    # 步骤3: 直接调用报告生成处理
    print("\n--- 步骤3: 报告生成处理 ---")
    try:
        # 检查实体
        entities = intent_result.get('entities', {})
        print(f"风场: '{entities.get('wind_farm')}'")
        print(f"机组: '{entities.get('turbine')}'")
        
        if not entities.get('wind_farm') or not entities.get('turbine'):
            print("❌ 实体检查失败 - 缺少风场或机组信息")
            return
        
        print("✅ 实体检查通过")
        
        # 调用报告生成
        result = chat_manager._handle_report_generation(session_id, intent_result, stream=False)
        print(f"\n报告生成结果:")
        print(f"  成功: {result.get('success')}")
        print(f"  错误: {result.get('error')}")
        
        if result.get('success'):
            response = result.get('response', '')
            print(f"  响应长度: {len(response)}")
            print(f"  响应预览: {response[:200]}..." if len(response) > 200 else f"  响应: {response}")
        else:
            print(f"  完整错误信息: {result}")
            
    except Exception as e:
        print(f"❌ 报告生成处理失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 步骤4: 测试完整流程
    print("\n--- 步骤4: 完整流程测试 ---")
    try:
        full_result = chat_manager.process_message(
            user_id="test_user_2",
            message=message,
            session_id=None,
            stream=False
        )
        print(f"完整流程结果:")
        print(f"  成功: {full_result.get('success')}")
        print(f"  意图: {full_result.get('intent')}")
        
        if full_result.get('success'):
            response = full_result.get('response', '')
            print(f"  响应长度: {len(response)}")
            print(f"  响应预览: {response[:200]}..." if len(response) > 200 else f"  响应: {response}")
        else:
            print(f"  错误: {full_result.get('error')}")
            print(f"  完整结果: {full_result}")
            
    except Exception as e:
        print(f"❌ 完整流程失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_report_generation_flow()