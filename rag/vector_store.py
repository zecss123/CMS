# -*- coding: utf-8 -*-
"""
向量数据库模块
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Tuple
import uuid
import json
from pathlib import Path
from loguru import logger

from config.settings import VECTOR_DB_CONFIG
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class SimpleTextEmbedding:
    """简单的文本嵌入实现，作为SentenceTransformer的备选方案"""
    
    def __init__(self, embedding_dim=384):
        self.embedding_dim = embedding_dim
        self.word_to_idx = {}
        self.idx_counter = 0
    
    def encode(self, texts):
        """编码文本为向量"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        for text in texts:
            # 简单的词袋模型嵌入
            words = text.lower().split()
            embedding = np.zeros(self.embedding_dim, dtype=np.float32)
            
            for i, word in enumerate(words[:self.embedding_dim]):
                if word not in self.word_to_idx:
                    self.word_to_idx[word] = self.idx_counter
                    self.idx_counter += 1
                
                idx = self.word_to_idx[word] % self.embedding_dim
                embedding[idx] += 1.0
            
            # 归一化
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            embeddings.append(embedding)
        
        return np.array(embeddings, dtype=np.float32)

class VectorStore:
    """向量数据库管理器"""
    
    def __init__(self):
        self.persist_directory = VECTOR_DB_CONFIG["persist_directory"]
        self.collection_name = VECTOR_DB_CONFIG["collection_name"]
        self.embedding_model_name = VECTOR_DB_CONFIG["embedding_model"]
        
        # 确保目录存在
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 初始化嵌入模型
        self.embedding_model = None
        self.collection = None
        
        logger.info(f"向量数据库初始化完成，存储路径: {self.persist_directory}")
    
    def _load_embedding_model(self):
        """加载嵌入模型"""
        if self.embedding_model is None:
            logger.info(f"尝试加载嵌入模型: {self.embedding_model_name}")
            try:
                # 首先尝试加载本地缓存的模型
                self.embedding_model = SentenceTransformer(self.embedding_model_name, local_files_only=True)
                logger.info("嵌入模型加载成功（本地缓存）")
            except Exception as e:
                logger.warning(f"本地模型加载失败: {str(e)}，使用简单文本嵌入")
                # 使用简单的文本嵌入作为备选方案
                self.embedding_model = SimpleTextEmbedding()
                logger.info("使用简单文本嵌入模型")
    
    def _get_collection(self):
        """获取或创建集合"""
        if self.collection is None:
            try:
                # 尝试获取现有集合
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"获取现有集合: {self.collection_name}")
            except:
                # 创建新集合
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "CMS振动分析知识库"}
                )
                logger.info(f"创建新集合: {self.collection_name}")
        
        return self.collection
    
    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]] = None, 
                     ids: List[str] = None) -> bool:
        """添加文档到向量数据库"""
        try:
            if not documents:
                logger.warning("没有文档需要添加")
                return False
                
            self._load_embedding_model()
            collection = self._get_collection()
            
            if self.embedding_model is None:
                logger.error("嵌入模型未初始化")
                return False
            
            # 生成嵌入向量
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # 生成ID（如果未提供）
            final_ids = ids if ids is not None else [str(uuid.uuid4()) for _ in documents]
            
            # 准备元数据
            final_metadatas = metadatas if metadatas is not None else [{} for _ in documents]
            
            # 添加到集合
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=final_metadatas,
                ids=final_ids
            )
            
            logger.info(f"成功添加 {len(documents)} 个文档到向量数据库")
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            return False
    
    def search(self, query: str, n_results: int = 5, 
              where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索相关文档"""
        try:
            self._load_embedding_model()
            collection = self._get_collection()
            
            if self.embedding_model is None:
                logger.error("嵌入模型未初始化")
                return []
            
            # 生成查询嵌入
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # 构建查询参数
            query_params = {
                "query_embeddings": query_embedding,
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"]
            }
            if where is not None:
                query_params["where"] = where
            
            # 执行搜索
            results = collection.query(**query_params)
            
            # 安全解析结果
            if not results:
                return []
                
            documents = results.get("documents", [[]])[0] if results.get("documents") else []
            metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            distances = results.get("distances", [[]])[0] if results.get("distances") else []
            
            # 格式化结果
            formatted_results = []
            for i in range(len(documents)):
                formatted_results.append({
                    "document": documents[i],
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else 1.0,
                    "similarity": 1 - distances[i] if i < len(distances) else 0.0  # 转换为相似度
                })
            
            logger.info(f"搜索完成，返回 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            return []
    
    def delete_documents(self, ids: List[str]) -> bool:
        """删除文档"""
        try:
            collection = self._get_collection()
            collection.delete(ids=ids)
            logger.info(f"成功删除 {len(ids)} 个文档")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            collection = self._get_collection()
            count = collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "persist_directory": str(self.persist_directory),
                "embedding_model": self.embedding_model_name
            }
        except Exception as e:
            logger.error(f"获取集合信息失败: {str(e)}")
            return {}
    
    def reset_collection(self) -> bool:
        """重置集合"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = None
            logger.info(f"集合 {self.collection_name} 已重置")
            return True
        except Exception as e:
            logger.error(f"重置集合失败: {str(e)}")
            return False

class KnowledgeBase:
    """振动分析知识库"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.knowledge_data = self._get_default_knowledge()
    
    def _get_default_knowledge(self) -> List[Dict[str, Any]]:
        """获取默认知识库内容"""
        return [
            {
                "content": "风电机组不平衡故障特征：主要表现为1X转频处振动幅值增大，通常伴有2X、3X谐波成分。不平衡可能由叶片积冰、叶片损伤、转子质量分布不均等原因引起。",
                "metadata": {"category": "故障诊断", "fault_type": "不平衡", "frequency": "1X"}
            },
            {
                "content": "轴系不对中故障特征：主要表现为2X转频处振动突出，径向和轴向振动都会增大。不对中分为平行不对中和角度不对中，会导致轴承过早磨损。",
                "metadata": {"category": "故障诊断", "fault_type": "不对中", "frequency": "2X"}
            },
            {
                "content": "滚动轴承故障特征：表现为高频振动增加，频谱中出现轴承特征频率及其谐波。内圈故障频率约为转频的6-8倍，外圈故障频率约为转频的3-5倍。",
                "metadata": {"category": "故障诊断", "fault_type": "轴承故障", "frequency": "高频"}
            },
            {
                "content": "齿轮箱故障特征：主要表现为齿轮啮合频率及其边频带异常。齿轮磨损会导致啮合频率处振动增大，齿轮断齿会产生冲击性振动。",
                "metadata": {"category": "故障诊断", "fault_type": "齿轮箱故障", "frequency": "啮合频率"}
            },
            {
                "content": "机械松动故障特征：表现为多次谐波成分丰富，频谱复杂。松动会导致1X、2X、3X等多个频率成分同时增大，时域波形出现削波现象。",
                "metadata": {"category": "故障诊断", "fault_type": "松动", "frequency": "多谐波"}
            },
            {
                "content": "风电机组振动监测标准：根据ISO 10816标准，风电机组振动烈度分为四个等级：A级(良好)≤2.8mm/s，B级(满意)2.8-7.1mm/s，C级(尚可)7.1-18mm/s，D级(不允许)>18mm/s。",
                "metadata": {"category": "标准规范", "standard": "ISO 10816"}
            },
            {
                "content": "振动测点布置原则：主轴承处应布置径向和轴向测点，齿轮箱高速端应重点监测，发电机两端轴承是关键监测位置。测点应避开节点位置。",
                "metadata": {"category": "监测技术", "topic": "测点布置"}
            },
            {
                "content": "频域分析方法：FFT分析可识别周期性故障，包络分析适用于轴承故障诊断，倒频谱分析可分离调制信号，小波分析适用于非平稳信号处理。",
                "metadata": {"category": "分析方法", "topic": "频域分析"}
            },
            {
                "content": "时域分析指标：RMS值反映振动能量，峰值反映冲击程度，峰峰值反映振动幅度，峭度因子反映冲击性，偏度因子反映波形对称性。",
                "metadata": {"category": "分析方法", "topic": "时域分析"}
            },
            {
                "content": "趋势分析要点：建立振动基线，设置报警阈值，关注振动趋势变化，结合运行工况分析，定期更新分析模型。长期趋势比瞬时值更重要。",
                "metadata": {"category": "分析方法", "topic": "趋势分析"}
            }
        ]
    
    def initialize_knowledge_base(self) -> bool:
        """初始化知识库"""
        logger.info("开始初始化振动分析知识库")
        
        # 检查是否已有数据
        info = self.vector_store.get_collection_info()
        if info.get("count", 0) > 0:
            logger.info(f"知识库已存在 {info['count']} 条记录")
            return True
        
        # 添加默认知识
        documents = [item["content"] for item in self.knowledge_data]
        metadatas = [item["metadata"] for item in self.knowledge_data]
        
        success = self.vector_store.add_documents(
            documents=documents,
            metadatas=metadatas
        )
        
        if success:
            logger.info("知识库初始化成功")
        else:
            logger.error("知识库初始化失败")
        
        return success
    
    def search_knowledge(self, query: str, category: str = None, 
                        n_results: int = 3) -> List[Dict[str, Any]]:
        """搜索相关知识"""
        where_filter = None
        if category:
            where_filter = {"category": category}
        
        results = self.vector_store.search(
            query=query,
            n_results=n_results,
            where=where_filter
        )
        
        return results
    
    def add_knowledge(self, content: str, metadata: Dict[str, Any]) -> bool:
        """添加新知识"""
        return self.vector_store.add_documents(
            documents=[content],
            metadatas=[metadata]
        )
    
    def get_fault_knowledge(self, fault_type: str) -> List[Dict[str, Any]]:
        """获取特定故障类型的知识"""
        return self.search_knowledge(
            query=f"{fault_type}故障特征诊断",
            category="故障诊断",
            n_results=2
        )
    
    def get_analysis_knowledge(self, analysis_type: str) -> List[Dict[str, Any]]:
        """获取分析方法相关知识"""
        return self.search_knowledge(
            query=f"{analysis_type}分析方法",
            category="分析方法",
            n_results=2
        )

# 全局知识库实例
knowledge_base = KnowledgeBase()

# 便捷函数
def initialize_kb() -> bool:
    """初始化知识库"""
    return knowledge_base.initialize_knowledge_base()

def search_kb(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """搜索知识库"""
    return knowledge_base.search_knowledge(query, n_results=n_results)

def get_fault_info(fault_type: str) -> List[Dict[str, Any]]:
    """获取故障信息"""
    return knowledge_base.get_fault_knowledge(fault_type)

if __name__ == "__main__":
    # 测试代码
    kb = KnowledgeBase()
    
    # 初始化知识库
    if kb.initialize_knowledge_base():
        print("知识库初始化成功")
        
        # 测试搜索
        results = kb.search_knowledge("不平衡故障")
        for result in results:
            print(f"相似度: {result['similarity']:.3f}")
            print(f"内容: {result['document']}")
            print(f"元数据: {result['metadata']}")
            print("-" * 50)
    else:
        print("知识库初始化失败")