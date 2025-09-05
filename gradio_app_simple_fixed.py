#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析报告系统 - Gradio简化版（修复版）
快速修复输入窗口问题
"""

import gradio as gr
import os
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def chat_interface(message):
    """简单的聊天接口"""
    if not message or not message.strip():
        return "请输入有效的问题。"
    
    # 简单的回复逻辑
    response = f"""✅ **收到您的消息**: {message}

**处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

这是一个测试回复，用于验证输入窗口是否正常工作。

**系统状态**: 正常运行
**功能**: 文本输入和输出正常
"""
    
    return response

def main():
    """主函数"""
    try:
        # 使用Interface创建简单界面
        demo = gr.Interface(
            fn=chat_interface,
            inputs=gr.inputs.Textbox(
                lines=3,
                placeholder="请输入您的问题...",
                label="输入消息"
            ),
            outputs=gr.outputs.Textbox(
                label="AI回复"
            ),
            title="🔧 CMS振动分析报告系统（修复版）",
            description="测试文本输入窗口功能",
            examples=[
                "生成华能风场A的A01风机振动分析报告",
                "查询设备状态",
                "分析振动趋势"
            ]
        )
        
        # 启动应用
        demo.launch(
            server_name="0.0.0.0",
            server_port=7863,
            share=False,
            show_error=True
        )
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        print(f"❌ 应用启动失败: {e}")

if __name__ == "__main__":
    main()