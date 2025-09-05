#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding模型客户端
用于调用bge-large-v1.5 embedding模型API
"""

import requests
import json
from typing import List, Dict, Any, Optional
from loguru import logger
import time
import numpy as np
import hashlib


class EmbeddingClient:
    """BGE-Large-v1.5 Embedding模型客户端"""
    
    def __init__(self):
        self.base_url = "http://172.16.253.39/api/model/services/68778965540afad16e749c43/app/v1/embeddings"
        self.headers = {
            "accept": "application/json",
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdPaWQiOiI2NjcxNGU2MmQzNWFkODE4ZGMzMGJjYWYiLCJ1c2VyT2lkIjoiNjY3MTQ5YjNkMzVhZDgxOGRjMzBiMDZmIiwibmFtZSI6IkRpZnkiLCJpc09wZW5BUEkiOnRydWUsImFwcCI6Ik1vZGVsU2VydmljZSIsImFwcElkIjoiNjg3Nzg5NjU1NDBhZmFkMTZlNzQ5YzQzIiwiaWF0IjoxNzUyNjY0NDUyLCJpc3MiOiJodHRwOi8vMTcyLjE2LjI1My4zOSJ9.RvPLsh093FJvDCFC5K-XglsDtzDjOSrXZwS0RA58SwM"
        }
        self.timeout = 30
        
    def get_embeddings(self, texts: List[str], model: str = "bge-large-v1.5", use_test_data: bool = False) -> Dict[str, Any]:
        """
        获取文本的embedding向量
        
        Args:
            texts: 要处理的文本列表
            model: 模型名称，默认为bge-large-v1.5
            use_test_data: 是否使用测试数据
            
        Returns:
            包含embedding结果的字典
        """
        if use_test_data:
            return self._generate_test_embeddings_batch(texts)
        payload = {
            "input": texts,
            "model": model
        }
        
        try:
            response = requests.post(
                url=self.base_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"成功获取{len(texts)}个文本的embedding向量")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Embedding API请求失败: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Embedding API响应解析失败: {e}")
            raise
        except Exception as e:
            logger.error(f"获取embedding向量失败: {e}")
            raise
    
    def _generate_test_embedding(self, text: str, dimension: int = 1024) -> List[float]:
        """
        生成测试用的embedding向量
        
        Args:
            text: 输入文本
            dimension: 向量维度
            
        Returns:
            模拟的embedding向量
        """
        # 使用文本的hash值作为随机种子，确保相同文本生成相同向量
        hash_value = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
        np.random.seed(hash_value % (2**32))
        
        # 生成随机向量并归一化
        vector = np.random.normal(0, 1, dimension)
        vector = vector / np.linalg.norm(vector)
        
        logger.info(f"生成测试embedding向量，文本长度: {len(text)}, 向量维度: {dimension}")
        return vector.tolist()
    
    def _generate_test_embeddings_batch(self, texts: List[str]) -> Dict[str, Any]:
        """
        批量生成测试用的embedding向量
        
        Args:
            texts: 文本列表
            
        Returns:
            模拟的API响应格式
        """
        data = []
        for i, text in enumerate(texts):
            embedding = self._generate_test_embedding(text)
            data.append({
                "object": "embedding",
                "embedding": embedding,
                "index": i
            })
        
        result = {
            "object": "list",
            "data": data,
            "model": "bge-large-v1.5-test",
            "usage": {
                "prompt_tokens": sum(len(text.split()) for text in texts),
                "total_tokens": sum(len(text.split()) for text in texts)
            }
        }
        
        logger.info(f"生成批量测试embedding，文本数量: {len(texts)}")
        return result
    
    def get_single_embedding(self, text: str, model: str = "bge-large-v1.5", use_test_data: bool = False) -> List[float]:
        """
        获取单个文本的embedding向量
        
        Args:
            text: 要处理的文本
            model: 模型名称，默认为bge-large-v1.5
            use_test_data: 是否使用测试数据
            
        Returns:
            embedding向量列表
        """
        if use_test_data:
            return self._generate_test_embedding(text)
            
        result = self.get_embeddings([text], model)
        
        if 'data' in result and len(result['data']) > 0:
            return result['data'][0]['embedding']
        else:
            raise ValueError("无法从API响应中提取embedding向量")
    
    def batch_embeddings(self, texts: List[str], batch_size: int = 10, model: str = "bge-large-v1.5") -> List[List[float]]:
        """
        批量获取文本的embedding向量
        
        Args:
            texts: 要处理的文本列表
            batch_size: 批处理大小
            model: 模型名称，默认为bge-large-v1.5
            
        Returns:
            embedding向量列表的列表
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            result = self.get_embeddings(batch_texts, model)
            
            if 'data' in result:
                batch_embeddings = [item['embedding'] for item in result['data']]
                all_embeddings.extend(batch_embeddings)
            else:
                raise ValueError(f"批次 {i//batch_size + 1} 处理失败")
        
        return all_embeddings
    
    def test_connection(self) -> bool:
        """
        测试与embedding API的连接
        
        Returns:
            连接是否成功
        """
        try:
            test_result = self.get_embeddings(["测试连接"])
            logger.info("Embedding API连接测试成功")
            return True
        except Exception as e:
            logger.error(f"Embedding API连接测试失败: {e}")
            return False


# 全局实例
_embedding_client = None

def get_embedding_client() -> EmbeddingClient:
    """
    获取全局embedding客户端实例
    
    Returns:
        EmbeddingClient实例
    """
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client


if __name__ == "__main__":
    # 测试代码
    client = EmbeddingClient()
    
    # 测试连接
    if client.test_connection():
        print("✅ Embedding API连接成功")
        
        # 测试单个文本
        try:
            embedding = client.get_single_embedding("这是一个测试文本")
            print(f"✅ 单个文本embedding获取成功，维度: {len(embedding)}")
        except Exception as e:
            print(f"❌ 单个文本embedding获取失败: {e}")
        
        # 测试批量文本
        try:
            embeddings = client.batch_embeddings(["文本1", "文本2", "文本3"])
            print(f"✅ 批量文本embedding获取成功，数量: {len(embeddings)}")
        except Exception as e:
            print(f"❌ 批量文本embedding获取失败: {e}")
    else:
        print("❌ Embedding API连接失败")