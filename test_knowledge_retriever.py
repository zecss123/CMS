#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试知识检索器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge.knowledge_retriever import KnowledgeRetriever

def test_knowledge_retriever():
    """测试知识检索器"""
    try:
        print("1. 创建知识检索器...")
        retriever = KnowledgeRetriever(
            embeddings_path="./embeddings",
            metadata_path="./metadata"
        )
        print("✅ 知识检索器创建成功")
        
        print("\n2. 测试搜索...")
        test_queries = [
            "振动分析",
            "故障诊断",
            "风电机组"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n2.{i} 搜索查询: {query}")
            try:
                result = retriever.search(query, top_k=3)
                if result.get('success'):
                    results = result.get('results', [])
                    print(f"✅ 找到 {len(results)} 个结果")
                    for j, res in enumerate(results[:2], 1):
                        text = res.get('text', '')
                        preview = text[:50] + '...' if len(text) > 50 else text
                        print(f"  结果{j}: {preview}")
                else:
                    print(f"❌ 搜索失败: {result.get('error')}")
            except Exception as e:
                print(f"❌ 搜索异常: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n=== 测试完成 ===")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_knowledge_retriever()
    if success:
        print("\n🎉 知识检索器测试成功！")
    else:
        print("\n💥 知识检索器测试失败")
        sys.exit(1)