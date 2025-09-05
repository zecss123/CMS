#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding功能演示脚本
测试CLI应用中的embedding功能，包括测试模式和API模式
"""

import subprocess
import time
import sys
from pathlib import Path

def run_cli_command(command: str, timeout: int = 10) -> str:
    """
    运行CLI命令并返回输出
    
    Args:
        command: 要执行的命令
        timeout: 超时时间（秒）
        
    Returns:
        命令输出结果
    """
    try:
        # 使用echo将命令传递给CLI应用
        full_command = f'echo "{command}" | python cms_cli_app.py --mode interactive'
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "命令执行超时"
    except Exception as e:
        return f"执行错误: {e}"

def test_embedding_functionality():
    """
    测试embedding功能的各种场景
    """
    print("🧪 开始测试Embedding功能")
    print("=" * 60)
    
    # 测试场景列表
    test_cases = [
        {
            "name": "帮助命令测试",
            "command": "help",
            "description": "查看embedding命令的帮助信息"
        },
        {
            "name": "测试模式 - 中文文本",
            "command": "embed 这是一个中文测试文本 --test",
            "description": "使用测试模式生成中文文本的embedding向量"
        },
        {
            "name": "测试模式 - 英文文本",
            "command": "embed Hello World Test --test",
            "description": "使用测试模式生成英文文本的embedding向量"
        },
        {
            "name": "测试模式 - 长文本",
            "command": "embed 这是一个比较长的测试文本，用来验证embedding功能是否能够正确处理较长的输入内容 --test",
            "description": "使用测试模式处理长文本"
        },
        {
            "name": "测试模式 - 重复文本验证",
            "command": "embed Hello World Test --test",
            "description": "再次使用相同文本，验证是否产生相同向量"
        },
        {
            "name": "API模式测试",
            "command": "embed 测试API模式",
            "description": "尝试使用API模式（预期会失败并提示使用测试模式）"
        },
        {
            "name": "错误参数测试",
            "command": "embed",
            "description": "测试缺少参数时的错误处理"
        }
    ]
    
    # 执行测试用例
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        print(f"📝 描述: {test_case['description']}")
        print(f"💻 命令: {test_case['command']}")
        print("-" * 40)
        
        # 执行命令
        output = run_cli_command(test_case['command'])
        print(output)
        
        # 等待一下再执行下一个测试
        time.sleep(1)
    
    print("\n✅ 所有测试完成！")
    print("\n💡 测试总结:")
    print("- 测试模式应该能正常生成1024维向量")
    print("- 相同文本应该产生相同的向量值")
    print("- API模式应该提示连接失败并建议使用测试模式")
    print("- 错误参数应该显示正确的使用提示")

def main():
    """
    主函数
    """
    print("🚀 Embedding功能测试演示")
    print(f"📁 工作目录: {Path.cwd()}")
    print(f"🐍 Python版本: {sys.version}")
    print()
    
    try:
        test_embedding_functionality()
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()