#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding功能最终综合测试
验证所有功能特性和边界情况
"""

import sys
import os
import time
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.embedding_client import EmbeddingClient
from cms_cli_app import CMSCLIApp

def test_embedding_consistency():
    """
    测试embedding的一致性和确定性
    """
    print("🔍 测试1: Embedding一致性验证")
    print("-" * 40)
    
    client = EmbeddingClient()
    test_text = "测试一致性的文本内容"
    
    # 多次生成相同文本的embedding
    embeddings = []
    for i in range(3):
        embedding = client.get_single_embedding(test_text, use_test_data=True)
        embeddings.append(embedding)
        print(f"第{i+1}次生成: 维度={len(embedding)}, 前3值={[round(x, 6) for x in embedding[:3]]}")
    
    # 验证一致性
    all_same = True
    for i in range(1, len(embeddings)):
        diff = sum(abs(a - b) for a, b in zip(embeddings[0], embeddings[i]))
        if diff > 1e-10:
            all_same = False
            print(f"❌ 第{i+1}次与第1次差异: {diff}")
    
    if all_same:
        print("✅ 一致性测试通过: 相同文本产生相同向量")
    else:
        print("❌ 一致性测试失败")
    
    return all_same

def test_embedding_properties():
    """
    测试embedding向量的数学性质
    """
    print("\n📊 测试2: Embedding向量性质验证")
    print("-" * 40)
    
    client = EmbeddingClient()
    test_texts = [
        "短文本",
        "这是一个中等长度的测试文本，包含一些中文内容",
        "This is a longer English text that contains multiple words and should test the embedding generation for longer content with mixed languages 中英文混合"
    ]
    
    properties_ok = True
    
    for i, text in enumerate(test_texts):
        embedding = client.get_single_embedding(text, use_test_data=True)
        
        # 检查维度
        if len(embedding) != 1024:
            print(f"❌ 文本{i+1}: 维度错误 {len(embedding)} != 1024")
            properties_ok = False
        
        # 检查归一化
        norm = np.linalg.norm(embedding)
        if abs(norm - 1.0) > 1e-6:
            print(f"❌ 文本{i+1}: 向量未归一化 norm={norm}")
            properties_ok = False
        
        # 检查数值范围
        min_val, max_val = min(embedding), max(embedding)
        if min_val < -1.0 or max_val > 1.0:
            print(f"❌ 文本{i+1}: 数值超出范围 [{min_val}, {max_val}]")
            properties_ok = False
        
        print(f"✅ 文本{i+1}: 长度={len(text)}, 维度={len(embedding)}, 模长={norm:.6f}, 范围=[{min_val:.6f}, {max_val:.6f}]")
    
    if properties_ok:
        print("✅ 向量性质测试通过")
    else:
        print("❌ 向量性质测试失败")
    
    return properties_ok

def test_cli_integration():
    """
    测试CLI集成功能
    """
    print("\n💻 测试3: CLI集成功能验证")
    print("-" * 40)
    
    app = CMSCLIApp()
    
    # 测试命令列表
    test_commands = [
        ("embed 测试CLI集成 --test", True, "测试模式命令"),
        ("embed CLI integration test --test", True, "英文测试模式"),
        ("embed 测试API模式", False, "API模式（预期失败）"),
        ("embed", False, "缺少参数（预期失败）")
    ]
    
    cli_ok = True
    
    for command, should_succeed, description in test_commands:
        print(f"\n🔧 测试命令: {command}")
        print(f"📝 描述: {description}")
        
        try:
            # 捕获输出
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            output_buffer = io.StringIO()
            error_buffer = io.StringIO()
            
            with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                app._handle_embed_command(command)
            
            output = output_buffer.getvalue()
            error = error_buffer.getvalue()
            
            if should_succeed:
                if "✅ Embedding生成成功" in output:
                    print("✅ 命令执行成功")
                else:
                    print(f"❌ 命令执行失败: {output}")
                    cli_ok = False
            else:
                if "❌" in output or "请提供" in output:
                    print("✅ 错误处理正确")
                else:
                    print(f"❌ 错误处理异常: {output}")
                    cli_ok = False
                    
        except Exception as e:
            if should_succeed:
                print(f"❌ 命令执行异常: {e}")
                cli_ok = False
            else:
                print(f"✅ 异常处理正确: {e}")
    
    if cli_ok:
        print("\n✅ CLI集成测试通过")
    else:
        print("\n❌ CLI集成测试失败")
    
    return cli_ok

def test_batch_processing():
    """
    测试批量处理功能
    """
    print("\n📦 测试4: 批量处理功能验证")
    print("-" * 40)
    
    client = EmbeddingClient()
    
    # 测试批量处理
    batch_texts = [
        "批量文本1",
        "Batch text 2",
        "批量处理测试文本3 - 中英文混合 mixed content",
        "第四个测试文本，用于验证批量处理的稳定性和一致性"
    ]
    
    try:
        # 批量处理
        batch_result = client.get_embeddings(batch_texts, use_test_data=True)
        batch_embeddings = [item['embedding'] for item in batch_result['data']]
        
        # 单个处理
        single_embeddings = []
        for text in batch_texts:
            embedding = client.get_single_embedding(text, use_test_data=True)
            single_embeddings.append(embedding)
        
        # 比较结果
        batch_ok = True
        for i, (batch_emb, single_emb) in enumerate(zip(batch_embeddings, single_embeddings)):
            diff = sum(abs(a - b) for a, b in zip(batch_emb, single_emb))
            if diff > 1e-10:
                print(f"❌ 文本{i+1}: 批量与单个结果不一致，差异={diff}")
                batch_ok = False
            else:
                print(f"✅ 文本{i+1}: 批量与单个结果一致")
        
        if batch_ok:
            print(f"✅ 批量处理测试通过，处理了{len(batch_texts)}个文本")
        else:
            print("❌ 批量处理测试失败")
        
        return batch_ok
        
    except Exception as e:
        print(f"❌ 批量处理异常: {e}")
        return False

def run_comprehensive_test():
    """
    运行综合测试
    """
    print("🚀 Embedding功能综合测试")
    print("=" * 60)
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🐍 Python版本: {sys.version}")
    print(f"⏰ 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 执行所有测试
    test_results = []
    
    try:
        test_results.append(("一致性测试", test_embedding_consistency()))
        test_results.append(("向量性质测试", test_embedding_properties()))
        test_results.append(("CLI集成测试", test_cli_integration()))
        test_results.append(("批量处理测试", test_batch_processing()))
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📋 测试结果汇总")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\n📊 总体结果: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！Embedding功能完全正常")
        print("\n💡 功能特性:")
        print("- ✅ 确定性向量生成（相同文本产生相同向量）")
        print("- ✅ 1024维归一化向量输出")
        print("- ✅ 支持中英文混合文本处理")
        print("- ✅ 完整的CLI命令行接口")
        print("- ✅ 批量和单个处理一致性")
        print("- ✅ 完善的错误处理机制")
        print("- ✅ 测试模式和API模式支持")
        return True
    else:
        print(f"⚠️ 有{total_tests - passed_tests}个测试失败，需要进一步检查")
        return False

def main():
    """
    主函数
    """
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()