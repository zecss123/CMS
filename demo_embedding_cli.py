#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding CLI功能演示
直接调用CLI应用的embedding处理方法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cms_cli_app import CMSCLIApp

def demo_embedding_commands():
    """
    演示embedding命令的各种用法
    """
    print("🚀 Embedding CLI功能演示")
    print("=" * 60)
    
    # 初始化CLI应用
    app = CMSCLIApp()
    
    # 演示命令列表
    demo_commands = [
        {
            "name": "帮助命令",
            "description": "显示所有可用命令的帮助信息",
            "command": "help"
        },
        {
            "name": "测试模式 - 中文文本",
            "description": "使用测试模式生成中文文本的embedding向量",
            "command": "embed 这是一个中文测试文本 --test"
        },
        {
            "name": "测试模式 - 英文文本",
            "description": "使用测试模式生成英文文本的embedding向量",
            "command": "embed Hello World Test --test"
        },
        {
            "name": "测试模式 - 长文本",
            "description": "测试处理较长的文本内容",
            "command": "embed 这是一个比较长的测试文本，用来验证embedding功能是否能够正确处理较长的输入内容，包含中英文混合 Mixed content --test"
        },
        {
            "name": "重复文本验证",
            "description": "验证相同文本产生相同向量",
            "command": "embed Hello World Test --test"
        },
        {
            "name": "API模式测试",
            "description": "尝试API模式（预期失败并提示使用测试模式）",
            "command": "embed 测试API连接"
        },
        {
            "name": "错误处理测试",
            "description": "测试缺少参数时的错误处理",
            "command": "embed"
        }
    ]
    
    # 执行演示命令
    for i, demo in enumerate(demo_commands, 1):
        print(f"\n📋 演示 {i}: {demo['name']}")
        print(f"📝 描述: {demo['description']}")
        print(f"💻 命令: {demo['command']}")
        print("-" * 50)
        
        try:
            # 解析并执行命令
            command_line = demo['command']
            
            if command_line == "help":
                app._show_help()
            elif command_line.startswith("embed"):
                app._handle_embed_command(command_line)
            else:
                print(f"❌ 未知命令: {command_line}")
                
        except Exception as e:
            print(f"❌ 执行错误: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 50)
        
        # 在演示之间稍作停顿
        import time
        time.sleep(0.5)
    
    print("\n🎉 所有演示完成！")
    print("\n💡 功能总结:")
    print("- ✅ 支持测试模式和API模式")
    print("- ✅ 自动生成1024维归一化向量")
    print("- ✅ 相同文本产生一致结果")
    print("- ✅ 完善的错误处理和用户提示")
    print("- ✅ 支持中英文混合文本")
    print("- ✅ 提供详细的使用帮助")

def main():
    """
    主函数
    """
    print("🧪 CMS振动分析系统 - Embedding功能演示")
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🐍 Python版本: {sys.version}")
    print()
    
    try:
        demo_embedding_commands()
    except KeyboardInterrupt:
        print("\n⚠️ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()