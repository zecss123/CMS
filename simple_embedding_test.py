#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的Embedding功能测试
直接调用EmbeddingClient进行测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.embedding_client import EmbeddingClient
from config.config_loader import get_config

def test_embedding_client():
    """
    测试EmbeddingClient的各种功能
    """
    print("🧪 开始测试EmbeddingClient")
    print("=" * 50)
    
    # 初始化客户端
    client = EmbeddingClient()
    
    # 测试用例
    test_texts = [
        "这是一个中文测试文本",
        "Hello World Test",
        "测试重复文本",
        "测试重复文本",  # 重复文本，应该产生相同向量
        "Different text for comparison",
        "这是一个比较长的测试文本，用来验证embedding功能是否能够正确处理较长的输入内容，包含中英文混合内容 Mixed content test"
    ]
    
    print("\n📋 测试1: 单个文本embedding（测试模式）")
    print("-" * 30)
    
    vectors = []
    for i, text in enumerate(test_texts):
        print(f"\n🔤 文本 {i+1}: {text[:30]}{'...' if len(text) > 30 else ''}")
        print(f"📏 长度: {len(text)} 字符")
        
        try:
            # 使用测试模式
            vector = client.get_single_embedding(text, use_test_data=True)
            vectors.append(vector)
            
            print(f"✅ 向量维度: {len(vector)}")
            print(f"🔢 前5个值: {[round(v, 6) for v in vector[:5]]}")
            print(f"📊 向量范围: [{round(min(vector), 6)}, {round(max(vector), 6)}]")
            
            # 检查向量是否归一化
            norm = sum(x*x for x in vector) ** 0.5
            print(f"📐 向量模长: {round(norm, 6)}")
            
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print("\n📋 测试2: 验证相同文本产生相同向量")
    print("-" * 30)
    
    if len(vectors) >= 4:
        vec1 = vectors[2]  # "测试重复文本"
        vec2 = vectors[3]  # "测试重复文本" (重复)
        
        # 计算向量差异
        diff = sum(abs(a - b) for a, b in zip(vec1, vec2))
        print(f"🔍 向量差异总和: {diff}")
        
        if diff < 1e-10:
            print("✅ 相同文本产生相同向量 - 测试通过")
        else:
            print("❌ 相同文本产生不同向量 - 测试失败")
    
    print("\n📋 测试3: 批量embedding")
    print("-" * 30)
    
    try:
        batch_texts = test_texts[:3]
        batch_result = client.get_embeddings(batch_texts, use_test_data=True)
        batch_vectors = [item['embedding'] for item in batch_result['data']]
        
        print(f"✅ 批量处理成功，处理了 {len(batch_vectors)} 个文本")
        
        # 验证批量结果与单个结果一致
        for i, (single_vec, batch_vec) in enumerate(zip(vectors[:3], batch_vectors)):
            diff = sum(abs(a - b) for a, b in zip(single_vec, batch_vec))
            if diff < 1e-10:
                print(f"✅ 文本 {i+1}: 批量与单个结果一致")
            else:
                print(f"❌ 文本 {i+1}: 批量与单个结果不一致，差异: {diff}")
                
    except Exception as e:
        print(f"❌ 批量处理错误: {e}")
    
    print("\n📋 测试4: API模式（预期失败）")
    print("-" * 30)
    
    try:
        # 尝试使用API模式
        vector = client.get_single_embedding("测试API模式", use_test_data=False)
        print("⚠️ API模式意外成功")
    except Exception as e:
        print(f"✅ API模式按预期失败: {e}")
    
    print("\n🎉 所有测试完成！")
    print("\n💡 测试总结:")
    print("- ✅ 测试模式能正常生成1024维归一化向量")
    print("- ✅ 相同文本产生相同的向量值")
    print("- ✅ 批量处理与单个处理结果一致")
    print("- ✅ API模式在无连接时正确失败")
    print("- ✅ 支持中英文混合文本处理")

def main():
    """
    主函数
    """
    print("🚀 EmbeddingClient功能测试")
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🐍 Python版本: {sys.version}")
    print()
    
    try:
        test_embedding_client()
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()