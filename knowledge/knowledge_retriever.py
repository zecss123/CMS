# -*- coding: utf-8 -*-
"""
知识检索器 - 负责知识的向量化存储和语义搜索
"""

import os
import json
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# 导入模板相关模块
try:
    from .report_templates.template_storage import TemplateStorage
    from .report_templates.template_metadata import TemplateMetadata, TemplateType
except ImportError:
    TemplateStorage = None
    TemplateMetadata = None
    TemplateType = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import faiss
except ImportError:
    faiss = None

logger = logging.getLogger(__name__)

class KnowledgeRetriever:
    """
    知识检索器 - 使用向量相似度进行语义搜索
    """
    
    def __init__(self, embeddings_path: str, metadata_path: str, 
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化知识检索器
        
        Args:
            embeddings_path: 向量存储路径
            metadata_path: 元数据存储路径
            model_name: 嵌入模型名称
        """
        self.embeddings_path = Path(embeddings_path)
        self.metadata_path = Path(metadata_path)
        self.embeddings_path.mkdir(exist_ok=True)
        self.metadata_path.mkdir(exist_ok=True)
        
        self.model_name = model_name
        self.model = None
        self.index = None
        self.chunk_metadata = {}
        
        # 向量索引文件
        self.index_file = self.embeddings_path / "faiss_index.bin"
        self.metadata_file = self.metadata_path / "chunks_metadata.json"
        
        # 初始化模板存储
        self.template_storage = None
        if TemplateStorage is not None:
            template_dir = self.metadata_path.parent / "report_templates"
            self.template_storage = TemplateStorage(str(template_dir))
        
        # 初始化模型和索引
        self._initialize_model()
        self._load_index()
    
    def _initialize_model(self):
        """初始化嵌入模型"""
        if SentenceTransformer is None:
            logger.warning("sentence-transformers未安装，将使用简单的文本匹配")
            return
        
        try:
            # 尝试加载模型，如果网络连接失败则使用fallback
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"嵌入模型加载成功: {self.model_name}")
        except OSError as e:
            if "couldn't connect to 'https://huggingface.co'" in str(e):
                logger.warning(f"无法连接到Hugging Face下载模型 {self.model_name}，将使用简单的文本匹配")
                logger.info("提示：如需使用向量搜索，请确保网络连接正常或预先下载模型")
            else:
                logger.error(f"加载嵌入模型失败: {e}")
            self.model = None
        except Exception as e:
            logger.error(f"加载嵌入模型失败: {e}")
            self.model = None
    
    def _load_index(self):
        """加载向量索引"""
        try:
            # 加载元数据
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.chunk_metadata = json.load(f)
            
            # 加载FAISS索引
            if self.index_file.exists() and faiss is not None:
                self.index = faiss.read_index(str(self.index_file))
                logger.info(f"向量索引加载成功，包含 {self.index.ntotal} 个向量")
            else:
                self._create_empty_index()
                
        except Exception as e:
            logger.error(f"加载向量索引失败: {e}")
            self._create_empty_index()
    
    def _create_empty_index(self):
        """创建空的向量索引"""
        if faiss is None:
            logger.warning("faiss未安装，无法创建向量索引")
            return
        
        try:
            # 创建384维的向量索引（all-MiniLM-L6-v2的维度）
            dimension = 384
            self.index = faiss.IndexFlatIP(dimension)  # 内积相似度
            logger.info("创建空向量索引成功")
        except Exception as e:
            logger.error(f"创建向量索引失败: {e}")
            self.index = None
    
    def _save_index(self):
        """保存向量索引"""
        try:
            # 保存FAISS索引
            if self.index is not None and faiss is not None:
                faiss.write_index(self.index, str(self.index_file))
            
            # 保存元数据
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存向量索引失败: {e}")
    
    def add_document(self, document_id: str, chunks: List[Dict[str, Any]], 
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        添加文档到知识库
        
        Args:
            document_id: 文档ID
            chunks: 文档块列表
            metadata: 文档元数据
            
        Returns:
            添加结果
        """
        try:
            if self.model is None:
                return self._add_document_simple(document_id, chunks, metadata)
            
            # 提取文本并生成嵌入
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            # 标准化向量（用于内积相似度）
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)  # 避免除零
            embeddings = embeddings / norms
            
            # 添加到FAISS索引
            if self.index is not None and faiss is not None:
                try:
                    start_idx = self.index.ntotal
                    embeddings_array = embeddings.astype(np.float32)
                    self.index.add(embeddings_array)
                except Exception as e:
                    logger.error(f"FAISS索引添加失败: {e}")
                    return self._add_document_simple(document_id, chunks, metadata)
                
                # 保存块元数据
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{document_id}_{chunk['chunk_id']}"
                    self.chunk_metadata[str(start_idx + i)] = {
                        "chunk_id": chunk_id,
                        "document_id": document_id,
                        "text": chunk["text"],
                        "start_pos": chunk["start_pos"],
                        "end_pos": chunk["end_pos"],
                        "length": chunk["length"],
                        "metadata": metadata or {},
                        "added_time": datetime.now().isoformat()
                    }
                
                # 保存索引
                self._save_index()
                
                logger.info(f"文档添加到向量索引成功: {document_id}, {len(chunks)} 个块")
                
                return {
                    "success": True,
                    "chunks_added": len(chunks),
                    "total_chunks": self.index.ntotal
                }
            else:
                return {
                    "success": False,
                    "error": "向量索引未初始化"
                }
                
        except Exception as e:
            logger.error(f"添加文档到向量索引失败: {e}")
            return {
                "success": False,
                "error": f"添加文档失败: {str(e)}"
            }
    
    def _add_document_simple(self, document_id: str, chunks: List[Dict[str, Any]], 
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """简单模式添加文档（无向量化）"""
        try:
            # 直接保存文本块到元数据
            for chunk in chunks:
                chunk_id = f"{document_id}_{chunk['chunk_id']}"
                self.chunk_metadata[chunk_id] = {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "text": chunk["text"],
                    "start_pos": chunk["start_pos"],
                    "end_pos": chunk["end_pos"],
                    "length": chunk["length"],
                    "metadata": metadata or {},
                    "added_time": datetime.now().isoformat()
                }
            
            # 保存元数据
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "chunks_added": len(chunks),
                "total_chunks": len(self.chunk_metadata)
            }
            
        except Exception as e:
            logger.error(f"简单模式添加文档失败: {e}")
            return {
                "success": False,
                "error": f"添加文档失败: {str(e)}"
            }
    
    def search(self, query: str, document_types: Optional[List[str]] = None,
              top_k: int = 5) -> Dict[str, Any]:
        """
        搜索知识库
        
        Args:
            query: 搜索查询
            document_types: 限制搜索的文档类型
            top_k: 返回结果数量
            
        Returns:
            搜索结果
        """
        try:
            if self.model is None or self.index is None:
                return self._search_simple(query, document_types, top_k)
            
            # 生成查询向量
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            query_norm = np.linalg.norm(query_embedding, axis=1, keepdims=True)
            query_norm = np.where(query_norm == 0, 1, query_norm)  # 避免除零
            query_embedding = query_embedding / query_norm
            
            # 搜索相似向量
            k = min(top_k * 2, self.index.ntotal)
            if faiss is not None:
                try:
                    query_array = query_embedding.astype(np.float32)
                    scores, indices = self.index.search(query_array, k)
                except Exception as e:
                    logger.error(f"FAISS搜索失败: {e}")
                    return self._search_simple(query, document_types, top_k)
            else:
                # Fallback when faiss is not available
                return self._search_simple(query, document_types, top_k)
            
            # 处理搜索结果
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS返回-1表示无效索引
                    continue
                
                chunk_info = self.chunk_metadata.get(str(idx))
                if chunk_info is None:
                    continue
                
                # 文档类型过滤
                if document_types:
                    doc_type = chunk_info["metadata"].get("document_type")
                    if doc_type not in document_types:
                        continue
                
                results.append({
                    "chunk_id": chunk_info["chunk_id"],
                    "document_id": chunk_info["document_id"],
                    "text": chunk_info["text"],
                    "score": float(score),
                    "metadata": chunk_info["metadata"]
                })
                
                if len(results) >= top_k:
                    break
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_found": len(results)
            }
            
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return {
                "success": False,
                "error": f"搜索失败: {str(e)}",
                "results": []
            }
    
    def _search_simple(self, query: str, document_types: Optional[List[str]] = None,
                      top_k: int = 5) -> Dict[str, Any]:
        """简单文本匹配搜索"""
        try:
            query_lower = query.lower()
            results = []
            
            for chunk_info in self.chunk_metadata.values():
                # 文档类型过滤
                if document_types:
                    doc_type = chunk_info["metadata"].get("document_type")
                    if doc_type not in document_types:
                        continue
                
                # 简单文本匹配
                text_lower = chunk_info["text"].lower()
                if query_lower in text_lower:
                    # 计算简单相似度分数
                    score = text_lower.count(query_lower) / len(text_lower.split())
                    
                    results.append({
                        "chunk_id": chunk_info["chunk_id"],
                        "document_id": chunk_info["document_id"],
                        "text": chunk_info["text"],
                        "score": score,
                        "metadata": chunk_info["metadata"]
                    })
            
            # 按分数排序
            results.sort(key=lambda x: x["score"], reverse=True)
            if len(results) > top_k:
                results = results[:top_k]
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_found": len(results)
            }
            
        except Exception as e:
            logger.error(f"简单搜索失败: {e}")
            return {
                "success": False,
                "error": f"搜索失败: {str(e)}",
                "results": []
            }
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            删除结果
        """
        try:
            # 找到要删除的块
            chunks_to_delete = []
            for idx, chunk_info in self.chunk_metadata.items():
                if chunk_info["document_id"] == document_id:
                    chunks_to_delete.append(idx)
            
            # 从元数据中删除
            for idx in chunks_to_delete:
                del self.chunk_metadata[idx]
            
            # 注意：FAISS不支持直接删除向量，这里只是从元数据中删除
            # 在实际应用中，可能需要重建索引来完全删除向量
            
            # 保存更新后的元数据
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"文档删除成功: {document_id}, 删除了 {len(chunks_to_delete)} 个块")
            
            return {
                "success": True,
                "chunks_deleted": len(chunks_to_delete),
                "message": "文档删除成功"
            }
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return {
                "success": False,
                "error": f"删除文档失败: {str(e)}"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            统计信息
        """
        try:
            total_chunks = len(self.chunk_metadata)
            total_documents = len(set(
                chunk["document_id"] for chunk in self.chunk_metadata.values()
            ))
            
            document_types = list(set(
                chunk["metadata"].get("document_type", "unknown")
                for chunk in self.chunk_metadata.values()
            ))
            
            return {
                "total_chunks": total_chunks,
                "total_documents": total_documents,
                "document_types": document_types,
                "index_size": self.index.ntotal if self.index else 0,
                "model_name": self.model_name,
                "has_vector_search": self.model is not None and self.index is not None
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "total_chunks": 0,
                "total_documents": 0,
                "document_types": [],
                "index_size": 0,
                "model_name": self.model_name,
                "has_vector_search": False
            }
    
    # ========== 模板检索相关方法 ==========
    
    def search_templates(self, template_type: Optional[str] = None, 
                        query: Optional[str] = None, 
                        top_k: int = 10) -> Dict[str, Any]:
        """
        搜索报告模板
        
        Args:
            template_type: 模板类型 (vibration_analysis, fault_diagnosis等)
            query: 搜索关键词
            top_k: 返回结果数量
            
        Returns:
            搜索结果
        """
        try:
            if self.template_storage is None:
                return {
                    "success": False,
                    "error": "模板存储未初始化",
                    "results": []
                }
            
            # 转换模板类型
            template_type_enum = None
            if template_type and TemplateType is not None:
                try:
                    template_type_enum = TemplateType(template_type.lower())
                except ValueError:
                    logger.warning(f"未知的模板类型: {template_type}")
            
            # 搜索模板
            if query:
                templates = self.template_storage.search_templates(query, template_type_enum)
            else:
                templates = self.template_storage.list_templates(template_type_enum)
            
            # 限制结果数量
            if len(templates) > top_k:
                templates = templates[:top_k]
            
            # 转换为返回格式
            results = []
            for template_metadata in templates:
                results.append({
                    "template_id": template_metadata.template_id,
                    "name": template_metadata.name,
                    "description": template_metadata.description,
                    "template_type": template_metadata.template_type.value,
                    "version": template_metadata.version,
                    "tags": template_metadata.tags,
                    "created_at": template_metadata.created_at.isoformat(),
                    "updated_at": template_metadata.updated_at.isoformat()
                })
            
            return {
                "success": True,
                "query": query,
                "template_type": template_type,
                "results": results,
                "total_found": len(results)
            }
            
        except Exception as e:
            logger.error(f"搜索模板失败: {e}")
            return {
                "success": False,
                "error": f"搜索模板失败: {str(e)}",
                "results": []
            }
    
    def get_template(self, template_id: str, template_type: str) -> Dict[str, Any]:
        """
        获取特定模板
        
        Args:
            template_id: 模板ID
            template_type: 模板类型
            
        Returns:
            模板内容和元数据
        """
        try:
            if self.template_storage is None:
                return {
                    "success": False,
                    "error": "模板存储未初始化"
                }
            
            # 转换模板类型
            if TemplateType is None:
                return {
                    "success": False,
                    "error": "模板类型未定义"
                }
            
            try:
                template_type_enum = TemplateType(template_type.lower())
            except ValueError:
                return {
                    "success": False,
                    "error": f"未知的模板类型: {template_type}"
                }
            
            # 获取模板
            template_content, metadata = self.template_storage.get_template(
                template_id, template_type_enum
            )
            
            return {
                "success": True,
                "template_content": template_content,
                "metadata": {
                    "template_id": metadata.template_id,
                    "name": metadata.name,
                    "description": metadata.description,
                    "template_type": metadata.template_type.value,
                    "version": metadata.version,
                    "tags": metadata.tags,
                    "created_at": metadata.created_at.isoformat(),
                    "updated_at": metadata.updated_at.isoformat()
                }
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"模板不存在: {template_id}"
            }
        except Exception as e:
            logger.error(f"获取模板失败: {e}")
            return {
                "success": False,
                "error": f"获取模板失败: {str(e)}"
            }
    
    def get_template_by_criteria(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据条件获取最佳匹配模板
        
        Args:
            criteria: 搜索条件，包含:
                - template_type: 模板类型
                - device_type: 设备类型 (可选)
                - analysis_type: 分析类型 (可选)
                - tags: 标签列表 (可选)
                
        Returns:
            最佳匹配的模板
        """
        try:
            template_type = criteria.get("template_type")
            device_type = criteria.get("device_type")
            analysis_type = criteria.get("analysis_type")
            required_tags = criteria.get("tags", [])
            
            # 搜索模板
            search_result = self.search_templates(template_type=template_type)
            
            if not search_result["success"] or not search_result["results"]:
                return {
                    "success": False,
                    "error": "未找到匹配的模板"
                }
            
            # 评分和排序
            scored_templates = []
            for template in search_result["results"]:
                score = 0
                
                # 设备类型匹配
                if device_type and device_type.lower() in [tag.lower() for tag in template["tags"]]:
                    score += 10
                
                # 分析类型匹配
                if analysis_type and analysis_type.lower() in [tag.lower() for tag in template["tags"]]:
                    score += 10
                
                # 标签匹配
                template_tags_lower = [tag.lower() for tag in template["tags"]]
                for required_tag in required_tags:
                    if required_tag.lower() in template_tags_lower:
                        score += 5
                
                # 版本新旧程度（新版本得分更高）
                try:
                    version_parts = template["version"].split(".")
                    version_score = int(version_parts[0]) * 100 + int(version_parts[1]) * 10
                    if len(version_parts) > 2:
                        version_score += int(version_parts[2])
                    score += version_score * 0.1
                except:
                    pass
                
                scored_templates.append((score, template))
            
            # 按分数排序，选择最佳匹配
            scored_templates.sort(key=lambda x: x[0], reverse=True)
            best_template = scored_templates[0][1]
            
            # 获取完整模板内容
            template_result = self.get_template(
                best_template["template_id"], 
                best_template["template_type"]
            )
            
            if template_result["success"]:
                template_result["match_score"] = scored_templates[0][0]
                template_result["criteria"] = criteria
            
            return template_result
            
        except Exception as e:
            logger.error(f"根据条件获取模板失败: {e}")
            return {
                "success": False,
                "error": f"获取模板失败: {str(e)}"
            }