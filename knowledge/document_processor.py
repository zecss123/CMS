# -*- coding: utf-8 -*-
"""
文档处理器 - 处理各种格式的文档并提取文本内容
"""

import os
import json
import uuid
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    文档处理器 - 支持多种文档格式的处理和文本提取
    """
    
    def __init__(self, storage_path: str):
        """
        初始化文档处理器
        
        Args:
            storage_path: 文档存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # 支持的文件格式
        self.supported_formats = {
            '.txt': self._process_text,
            '.md': self._process_text,
            '.pdf': self._process_pdf,
            '.docx': self._process_docx,
            '.doc': self._process_docx,
            '.xlsx': self._process_excel,
            '.xls': self._process_excel,
            '.csv': self._process_csv,
            '.json': self._process_json
        }
        
        # 文档元数据存储
        self.metadata_file = self.storage_path / "documents_metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """加载文档元数据"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {}
        except Exception as e:
            logger.error(f"加载文档元数据失败: {e}")
            self.metadata = {}
    
    def save_metadata(self):
        """保存文档元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存文档元数据失败: {e}")
    
    def process_document(self, file_path: str, document_type: str = "general",
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理文档
        
        Args:
            file_path: 文档文件路径
            document_type: 文档类型
            metadata: 额外的元数据
            
        Returns:
            处理结果
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "文件不存在"
                }
            
            # 获取文件信息
            file_ext = Path(file_path).suffix.lower()
            file_name = os.path.basename(file_path)
            
            if file_ext not in self.supported_formats:
                return {
                    "success": False,
                    "error": f"不支持的文件格式: {file_ext}"
                }
            
            # 生成文档ID
            doc_id = self._generate_document_id(file_path)
            
            # 处理文档内容
            processor = self.supported_formats[file_ext]
            content_result = processor(file_path)
            
            if not content_result["success"]:
                return content_result
            
            # 分块处理
            chunks = self._chunk_text(content_result["content"])
            
            # 保存处理后的文档
            processed_doc = {
                "document_id": doc_id,
                "file_name": file_name,
                "file_path": file_path,
                "document_type": document_type,
                "file_format": file_ext,
                "content": content_result["content"],
                "chunks": chunks,
                "chunks_count": len(chunks),
                "processed_time": datetime.now().isoformat(),
                "metadata": metadata or {},
                "file_size": os.path.getsize(file_path),
                "content_length": len(content_result["content"])
            }
            
            # 保存到存储
            doc_file = self.storage_path / f"{doc_id}.json"
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(processed_doc, f, ensure_ascii=False, indent=2)
            
            # 更新元数据
            self.metadata[doc_id] = {
                "file_name": file_name,
                "document_type": document_type,
                "file_format": file_ext,
                "processed_time": processed_doc["processed_time"],
                "chunks_count": len(chunks),
                "metadata": metadata or {}
            }
            self.save_metadata()
            
            logger.info(f"文档处理成功: {file_name} -> {doc_id}")
            
            return {
                "success": True,
                "document_id": doc_id,
                "chunks": chunks,
                "chunks_count": len(chunks),
                "content_length": len(content_result["content"])
            }
            
        except Exception as e:
            logger.error(f"处理文档失败: {e}")
            return {
                "success": False,
                "error": f"处理文档失败: {str(e)}"
            }
    
    def _generate_document_id(self, file_path: str) -> str:
        """生成文档ID"""
        # 使用文件路径和修改时间生成唯一ID
        file_stat = os.stat(file_path)
        content = f"{file_path}_{file_stat.st_mtime}_{file_stat.st_size}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, Any]]:
        """
        将文本分块
        
        Args:
            text: 原始文本
            chunk_size: 块大小
            overlap: 重叠大小
            
        Returns:
            文本块列表
        """
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # 尝试在句号或换行符处分割
            if end < len(text):
                last_period = chunk_text.rfind('。')
                last_newline = chunk_text.rfind('\n')
                split_point = max(last_period, last_newline)
                
                if split_point > start + chunk_size // 2:
                    chunk_text = text[start:start + split_point + 1]
                    end = start + split_point + 1
            
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text.strip(),
                "start_pos": start,
                "end_pos": end,
                "length": len(chunk_text.strip())
            })
            
            start = end - overlap
            chunk_id += 1
        
        return chunks
    
    def _process_text(self, file_path: str) -> Dict[str, Any]:
        """处理文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "success": True,
                "content": content
            }
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                return {
                    "success": True,
                    "content": content
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"读取文本文件失败: {str(e)}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理文本文件失败: {str(e)}"
            }
    
    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """处理PDF文件"""
        if PyPDF2 is None:
            return {
                "success": False,
                "error": "PyPDF2未安装，无法处理PDF文件"
            }
        
        try:
            content = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
            
            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理PDF文件失败: {str(e)}"
            }
    
    def _process_docx(self, file_path: str) -> Dict[str, Any]:
        """处理Word文档"""
        if Document is None:
            return {
                "success": False,
                "error": "python-docx未安装，无法处理Word文档"
            }
        
        try:
            doc = Document(file_path)
            content = ""
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
            
            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理Word文档失败: {str(e)}"
            }
    
    def _process_excel(self, file_path: str) -> Dict[str, Any]:
        """处理Excel文件"""
        if pd is None:
            return {
                "success": False,
                "error": "pandas未安装，无法处理Excel文件"
            }
        
        try:
            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            content = ""
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                content += f"工作表: {sheet_name}\n"
                content += df.to_string(index=False) + "\n\n"
            
            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理Excel文件失败: {str(e)}"
            }
    
    def _process_csv(self, file_path: str) -> Dict[str, Any]:
        """处理CSV文件"""
        if pd is None:
            return {
                "success": False,
                "error": "pandas未安装，无法处理CSV文件"
            }
        
        try:
            df = pd.read_csv(file_path)
            content = df.to_string(index=False)
            
            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理CSV文件失败: {str(e)}"
            }
    
    def _process_json(self, file_path: str) -> Dict[str, Any]:
        """处理JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 将JSON转换为可读文本
            content = json.dumps(data, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理JSON文件失败: {str(e)}"
            }
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取处理后的文档"""
        try:
            doc_file = self.storage_path / f"{document_id}.json"
            if doc_file.exists():
                with open(doc_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """删除文档"""
        try:
            doc_file = self.storage_path / f"{document_id}.json"
            if doc_file.exists():
                doc_file.unlink()
            
            if document_id in self.metadata:
                del self.metadata[document_id]
                self.save_metadata()
            
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
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """列出所有文档"""
        documents = []
        for doc_id, doc_info in self.metadata.items():
            documents.append({
                "document_id": doc_id,
                **doc_info
            })
        return documents