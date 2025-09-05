#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试报告生成过程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import get_config
from chat.chat_manager import ChatManager
from chat.session_manager import SessionManager
from chat.intent_analyzer import IntentAnalyzer

def debug_report_generation_step_by_step():
    """逐步调试报告生成"""
    print("=== 逐步调试报告生成 ===")
    
    # 初始化组件
    config = get_config()
    session_manager = SessionManager()
    chat_manager = ChatManager(config.config, session_manager)
    intent_analyzer = IntentAnalyzer()
    
    # 测试消息
    message = "华能风场A的A01风机"
    print(f"\n测试消息: {message}")
    
    # 意图分析
    intent_result = intent_analyzer.analyze_intent(message)
    print(f"\n意图分析结果: {intent_result}")
    
    # 创建会话
    session_id = session_manager.create_session("test_user")
    print(f"\n会话ID: {session_id}")
    
    # 手动执行_handle_report_generation的每个步骤
    print("\n=== 手动执行报告生成步骤 ===")
    
    try:
        # 步骤1: 获取实体
        entities = intent_result.get('entities', {})
        print(f"\n步骤1 - 获取实体:")
        print(f"  entities原始数据: {entities}")
        print(f"  wind_farm: '{entities.get('wind_farm')}'")
        print(f"  turbine: '{entities.get('turbine')}'")
        print(f"  wind_farm类型: {type(entities.get('wind_farm'))}")
        print(f"  turbine类型: {type(entities.get('turbine'))}")
        
        # 步骤2: 检查必需参数
        print(f"\n步骤2 - 检查必需参数:")
        wind_farm_check = not entities.get('wind_farm')
        turbine_check = not entities.get('turbine')
        print(f"  not entities.get('wind_farm'): {wind_farm_check}")
        print(f"  not entities.get('turbine'): {turbine_check}")
        print(f"  条件判断结果: {wind_farm_check or turbine_check}")
        
        if wind_farm_check or turbine_check:
            print("  ❌ 检查失败 - 应该返回错误")
            return {
                "success": False,
                "error": "请提供风场和机组信息",
                "response": "生成报告需要指定风场和机组，请提供完整信息。"
            }
        else:
            print("  ✅ 检查通过 - 继续处理")
        
        # 步骤3: 检查配置
        print(f"\n步骤3 - 检查配置:")
        use_mock_data = config.config.get('development', {}).get('use_mock_data', True)
        print(f"  use_mock_data: {use_mock_data}")
        
        # 步骤4: 获取数据
        print(f"\n步骤4 - 获取振动数据:")
        if use_mock_data:
            data_result = chat_manager._get_mock_vibration_data(entities)
        else:
            data_result = chat_manager._get_api_vibration_data(entities)
        
        print(f"  数据获取结果: {data_result.get('success')}")
        if not data_result.get('success'):
            print(f"  数据获取失败: {data_result.get('error')}")
            return data_result
        
        print(f"  ✅ 数据获取成功")
        
        # 步骤5: 检索知识
        print(f"\n步骤5 - 检索相关知识:")
        knowledge_query = f"{entities['wind_farm']} {entities['turbine']} 振动分析"
        print(f"  知识检索查询: {knowledge_query}")
        
        knowledge_results = chat_manager.knowledge_retriever.search(
            query=knowledge_query,
            top_k=3
        )
        print(f"  知识检索结果: {knowledge_results}")
        
        # 步骤6: 获取模板
        print(f"\n步骤6 - 获取报告模板:")
        template_result = chat_manager.template_manager.get_template(
            template_name='vibration_analysis_report'
        )
        print(f"  模板获取结果: {template_result}")
        
        # 步骤7: 构建报告数据
        print(f"\n步骤7 - 构建报告数据:")
        report_data = {
            'wind_farm': entities['wind_farm'],
            'turbine': entities['turbine'],
            'time_range': entities.get('time_range'),
            'vibration_data': data_result['data'],
            'knowledge_context': knowledge_results,
            'template': template_result.get('content') if template_result.get('success') else None
        }
        print(f"  报告数据构建完成")
        
        # 步骤8: 生成报告
        print(f"\n步骤8 - 生成报告:")
        final_result = chat_manager._generate_report_complete(report_data)
        print(f"  最终结果: {final_result}")
        
        return final_result
        
    except Exception as e:
        print(f"❌ 调试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"调试失败: {str(e)}",
            "response": "调试过程中出现错误。"
        }

if __name__ == "__main__":
    result = debug_report_generation_step_by_step()
    print(f"\n=== 最终调试结果 ===")
    print(f"成功: {result.get('success')}")
    print(f"错误: {result.get('error')}")
    if result.get('response'):
        response = result.get('response')
        print(f"响应长度: {len(response)}")
        print(f"响应内容: {response[:300]}..." if len(response) > 300 else f"响应内容: {response}")