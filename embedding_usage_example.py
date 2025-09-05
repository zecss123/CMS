#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding功能使用示例
展示如何在实际应用中使用embedding功能
"""

import sys
import os
import numpy as np
from typing import List, Tuple
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.embedding_client import EmbeddingClient

def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的余弦相似度
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        余弦相似度值 (-1 到 1)
    """
    # 转换为numpy数组
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    # 计算余弦相似度
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

def find_most_similar(query_text: str, candidate_texts: List[str], client: EmbeddingClient) -> List[Tuple[str, float]]:
    """
    找到与查询文本最相似的候选文本
    
    Args:
        query_text: 查询文本
        candidate_texts: 候选文本列表
        client: Embedding客户端
        
    Returns:
        按相似度排序的(文本, 相似度)列表
    """
    # 生成查询文本的embedding
    query_embedding = client.get_single_embedding(query_text, use_test_data=True)
    
    # 生成所有候选文本的embedding
    candidate_embeddings = []
    for text in candidate_texts:
        embedding = client.get_single_embedding(text, use_test_data=True)
        candidate_embeddings.append(embedding)
    
    # 计算相似度
    similarities = []
    for i, candidate_embedding in enumerate(candidate_embeddings):
        similarity = calculate_similarity(query_embedding, candidate_embedding)
        similarities.append((candidate_texts[i], similarity))
    
    # 按相似度排序
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities

def demo_text_similarity():
    """
    演示文本相似度计算
    """
    print("🔍 文本相似度计算演示")
    print("=" * 50)
    
    client = EmbeddingClient()
    
    # 查询文本
    query = "振动监测系统故障诊断"
    
    # 候选文本库
    candidates = [
        "设备振动异常检测方法",
        "机械故障诊断技术研究",
        "温度传感器校准程序",
        "振动信号频谱分析",
        "设备维护保养计划",
        "故障预警系统设计",
        "数据采集系统配置",
        "振动测试标准规范"
    ]
    
    print(f"🎯 查询文本: {query}")
    print(f"📚 候选文本数量: {len(candidates)}")
    print("\n🔄 正在计算相似度...")
    
    # 计算相似度
    similarities = find_most_similar(query, candidates, client)
    
    print("\n📊 相似度排序结果:")
    print("-" * 40)
    
    for i, (text, similarity) in enumerate(similarities, 1):
        similarity_percent = similarity * 100
        print(f"{i:2d}. {text:<20} | 相似度: {similarity_percent:6.2f}%")
    
    # 分析结果
    print("\n💡 结果分析:")
    top_3 = similarities[:3]
    for i, (text, similarity) in enumerate(top_3, 1):
        if similarity > 0.8:
            level = "高度相关"
        elif similarity > 0.6:
            level = "中度相关"
        elif similarity > 0.4:
            level = "低度相关"
        else:
            level = "不相关"
        print(f"  {i}. {text} - {level}")

def demo_text_clustering():
    """
    演示文本聚类
    """
    print("\n\n🎯 文本聚类演示")
    print("=" * 50)
    
    client = EmbeddingClient()
    
    # 测试文本集合
    texts = [
        "振动监测设备安装",
        "温度传感器配置",
        "设备故障诊断",
        "振动信号分析",
        "温度数据采集",
        "故障预警系统",
        "振动频谱检测",
        "温度异常报警"
    ]
    
    print(f"📝 文本数量: {len(texts)}")
    print("\n🔄 正在生成embedding向量...")
    
    # 生成所有文本的embedding
    embeddings = []
    for text in texts:
        embedding = client.get_single_embedding(text, use_test_data=True)
        embeddings.append(embedding)
    
    print("\n📊 文本相似度矩阵:")
    print("    ", end="")
    for i in range(len(texts)):
        print(f"{i:4d}", end="")
    print()
    
    # 计算相似度矩阵
    similarity_matrix = []
    for i in range(len(embeddings)):
        row = []
        print(f"{i:2d}: ", end="")
        for j in range(len(embeddings)):
            similarity = calculate_similarity(embeddings[i], embeddings[j])
            row.append(similarity)
            print(f"{similarity:4.2f}", end="")
        similarity_matrix.append(row)
        print(f"  {texts[i][:15]}...")
    
    # 简单聚类分析
    print("\n🔍 聚类分析:")
    threshold = 0.7
    clusters = []
    used = set()
    
    for i in range(len(texts)):
        if i in used:
            continue
        
        cluster = [i]
        used.add(i)
        
        for j in range(i + 1, len(texts)):
            if j not in used and similarity_matrix[i][j] > threshold:
                cluster.append(j)
                used.add(j)
        
        clusters.append(cluster)
    
    for i, cluster in enumerate(clusters, 1):
        print(f"\n📂 聚类 {i}:")
        for idx in cluster:
            print(f"  - {texts[idx]}")

def demo_semantic_search():
    """
    演示语义搜索
    """
    print("\n\n🔎 语义搜索演示")
    print("=" * 50)
    
    client = EmbeddingClient()
    
    # 知识库
    knowledge_base = [
        "振动监测系统用于实时监控设备运行状态",
        "温度传感器可以检测设备的热状态变化",
        "故障诊断需要结合多种传感器数据进行分析",
        "频谱分析是振动信号处理的重要方法",
        "预警系统可以提前发现设备异常情况",
        "数据采集系统负责收集各种传感器信息",
        "设备维护应该根据监测数据制定计划",
        "信号处理算法用于提取有用的特征信息"
    ]
    
    # 搜索查询
    queries = [
        "如何监控设备状态？",
        "温度异常怎么检测？",
        "振动信号如何分析？"
    ]
    
    print(f"📚 知识库条目: {len(knowledge_base)}")
    print(f"🔍 搜索查询: {len(queries)}")
    
    for query in queries:
        print(f"\n❓ 查询: {query}")
        print("📋 搜索结果:")
        
        similarities = find_most_similar(query, knowledge_base, client)
        
        # 显示前3个最相关的结果
        for i, (text, similarity) in enumerate(similarities[:3], 1):
            similarity_percent = similarity * 100
            print(f"  {i}. [{similarity_percent:5.1f}%] {text}")

def main():
    """
    主函数
    """
    print("🚀 Embedding功能应用示例")
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"⏰ 运行时间: {os.popen('date').read().strip()}")
    print("=" * 60)
    
    try:
        # 运行各种演示
        demo_text_similarity()
        demo_text_clustering()
        demo_semantic_search()
        
        print("\n" + "=" * 60)
        print("🎉 所有演示完成！")
        print("\n💡 应用场景总结:")
        print("- 🔍 文本相似度计算 - 找到相关文档")
        print("- 🎯 文本聚类分析 - 自动分组相似内容")
        print("- 🔎 语义搜索 - 基于含义而非关键词搜索")
        print("- 📊 内容推荐 - 推荐相关文档或信息")
        print("- 🤖 智能问答 - 匹配最相关的答案")
        print("\n✨ 这些功能都基于embedding向量的数学运算实现")
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()