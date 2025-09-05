# -*- coding: utf-8 -*-
"""
知识管理器 - 负责知识库的整体管理和协调
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .document_processor import DocumentProcessor
from .template_manager import TemplateManager
from .knowledge_retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)

class KnowledgeManager:
    """
    知识库管理器 - 统一管理文档处理、模板管理和知识检索
    """
    
    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        """
        初始化知识管理器
        
        Args:
            knowledge_base_path: 知识库存储路径
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base_path.mkdir(exist_ok=True)
        
        # 创建子目录
        self.documents_path = self.knowledge_base_path / "documents"
        self.templates_path = self.knowledge_base_path / "templates"
        self.embeddings_path = self.knowledge_base_path / "embeddings"
        self.metadata_path = self.knowledge_base_path / "metadata"
        
        for path in [self.documents_path, self.templates_path, 
                    self.embeddings_path, self.metadata_path]:
            path.mkdir(exist_ok=True)
        
        # 初始化组件
        self.document_processor = DocumentProcessor(str(self.documents_path))
        self.template_manager = TemplateManager(str(self.templates_path))
        self.knowledge_retriever = KnowledgeRetriever(
            str(self.embeddings_path), 
            str(self.metadata_path)
        )
        
        # 知识库索引文件
        self.index_file = self.knowledge_base_path / "index.json"
        self.load_index()
    
    def load_index(self):
        """加载知识库索引"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            else:
                self.index = {
                    "documents": {},
                    "templates": {},
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"加载索引失败: {e}")
            self.index = {
                "documents": {},
                "templates": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def save_index(self):
        """保存知识库索引"""
        try:
            self.index["last_updated"] = datetime.now().isoformat()
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存索引失败: {e}")
    
    def upload_document(self, file_path: str, document_type: str = "general", 
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        上传文档到知识库
        
        Args:
            file_path: 文档文件路径
            document_type: 文档类型 (general, technical, report_template, analysis_guide)
            metadata: 文档元数据
            
        Returns:
            上传结果信息
        """
        try:
            # 处理文档
            result = self.document_processor.process_document(
                file_path, document_type, metadata
            )
            
            if result["success"]:
                doc_id = result["document_id"]
                
                # 更新索引
                self.index["documents"][doc_id] = {
                    "file_name": os.path.basename(file_path),
                    "document_type": document_type,
                    "upload_time": datetime.now().isoformat(),
                    "metadata": metadata or {},
                    "processed_chunks": result.get("chunks_count", 0)
                }
                
                # 生成嵌入向量
                embedding_result = self.knowledge_retriever.add_document(
                    doc_id, result["chunks"], metadata
                )
                
                if embedding_result["success"]:
                    self.save_index()
                    logger.info(f"文档上传成功: {doc_id}")
                    return {
                        "success": True,
                        "document_id": doc_id,
                        "message": "文档上传并索引成功"
                    }
                else:
                    logger.error(f"文档嵌入失败: {embedding_result['error']}")
                    return {
                        "success": False,
                        "error": f"文档嵌入失败: {embedding_result['error']}"
                    }
            else:
                return result
                
        except Exception as e:
            logger.error(f"上传文档失败: {e}")
            return {
                "success": False,
                "error": f"上传文档失败: {str(e)}"
            }
    
    def upload_template(self, template_name: str, template_content: str,
                       template_type: str = "report", 
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        上传报告模板
        
        Args:
            template_name: 模板名称
            template_content: 模板内容
            template_type: 模板类型
            metadata: 模板元数据
            
        Returns:
            上传结果信息
        """
        try:
            result = self.template_manager.save_template(
                template_name, template_content, template_type, metadata
            )
            
            if result["success"]:
                template_id = result["template_id"]
                
                # 更新索引
                self.index["templates"][template_id] = {
                    "template_name": template_name,
                    "template_type": template_type,
                    "upload_time": datetime.now().isoformat(),
                    "metadata": metadata or {}
                }
                
                self.save_index()
                logger.info(f"模板上传成功: {template_id}")
                
            return result
            
        except Exception as e:
            logger.error(f"上传模板失败: {e}")
            return {
                "success": False,
                "error": f"上传模板失败: {str(e)}"
            }
    
    def search_knowledge(self, query: str, document_types: Optional[List[str]] = None,
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
            return self.knowledge_retriever.search(
                query, document_types, top_k
            )
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return {
                "success": False,
                "error": f"搜索失败: {str(e)}",
                "results": []
            }
    
    def get_template(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板内容和元数据
        """
        try:
            return self.template_manager.get_template(template_name)
        except Exception as e:
            logger.error(f"获取模板失败: {e}")
            return {
                "success": False,
                "error": f"获取模板失败: {str(e)}"
            }
    
    def list_documents(self, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出文档
        
        Args:
            document_type: 过滤文档类型
            
        Returns:
            文档列表
        """
        documents = []
        for doc_id, doc_info in self.index["documents"].items():
            if document_type is None or doc_info["document_type"] == document_type:
                documents.append({
                    "document_id": doc_id,
                    **doc_info
                })
        return documents
    
    def list_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出模板
        
        Args:
            template_type: 过滤模板类型
            
        Returns:
            模板列表
        """
        templates = []
        for template_id, template_info in self.index["templates"].items():
            if template_type is None or template_info["template_type"] == template_type:
                templates.append({
                    "template_id": template_id,
                    **template_info
                })
        return templates
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            删除结果
        """
        try:
            # 从知识检索器中删除
            retriever_result = self.knowledge_retriever.delete_document(document_id)
            
            # 从文档处理器中删除
            processor_result = self.document_processor.delete_document(document_id)
            
            # 从索引中删除
            if document_id in self.index["documents"]:
                del self.index["documents"][document_id]
                self.save_index()
            
            return {
                "success": True,
                "message": "文档删除成功"
            }
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return {
                "success": False,
                "error": f"删除文档失败: {str(e)}"
            }
    
    def delete_template(self, template_name: str) -> Dict[str, Any]:
        """
        删除模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            删除结果
        """
        try:
            result = self.template_manager.delete_template(template_name)
            
            if result["success"]:
                # 从索引中删除
                template_id = None
                for tid, tinfo in self.index["templates"].items():
                    if tinfo["template_name"] == template_name:
                        template_id = tid
                        break
                
                if template_id:
                    del self.index["templates"][template_id]
                    self.save_index()
            
            return result
            
        except Exception as e:
            logger.error(f"删除模板失败: {e}")
            return {
                "success": False,
                "error": f"删除模板失败: {str(e)}"
            }
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            统计信息
        """
        return {
            "total_documents": len(self.index["documents"]),
            "total_templates": len(self.index["templates"]),
            "document_types": list(set(
                doc["document_type"] for doc in self.index["documents"].values()
            )),
            "template_types": list(set(
                tmpl["template_type"] for tmpl in self.index["templates"].values()
            )),
            "last_updated": self.index["last_updated"]
        }