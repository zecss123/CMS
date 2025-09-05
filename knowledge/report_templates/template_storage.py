# -*- coding: utf-8 -*-
"""
报告模板存储管理

提供报告模板的文件系统存储、检索和版本控制功能。
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import uuid
from loguru import logger

from .template_metadata import TemplateMetadata, TemplateType


class TemplateStorage:
    """报告模板存储管理类"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """初始化模板存储
        
        Args:
            base_dir: 模板存储基础目录，默认为当前模块所在目录下的templates子目录
        """
        if base_dir is None:
            # 默认存储在当前模块目录下的templates子目录
            module_dir = Path(__file__).parent
            base_dir = str(module_dir / "templates")
        
        self.base_dir = Path(base_dir)
        self._ensure_storage_structure()
    
    def _ensure_storage_structure(self) -> None:
        """确保存储结构存在"""
        # 创建基础目录
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 创建各类型模板目录
        for template_type in TemplateType:
            type_dir = self.base_dir / template_type.value
            os.makedirs(type_dir, exist_ok=True)
    
    def _get_template_path(self, template_id: str, template_type: TemplateType) -> Path:
        """获取模板文件路径
        
        Args:
            template_id: 模板ID
            template_type: 模板类型
            
        Returns:
            模板文件路径
        """
        return self.base_dir / template_type.value / f"{template_id}.json"
    
    def _get_metadata_path(self, template_id: str, template_type: TemplateType) -> Path:
        """获取模板元数据文件路径
        
        Args:
            template_id: 模板ID
            template_type: 模板类型
            
        Returns:
            模板元数据文件路径
        """
        return self.base_dir / template_type.value / f"{template_id}.metadata.json"
    
    def save_template(self, template_content: Dict[str, Any], metadata: TemplateMetadata) -> str:
        """保存模板
        
        Args:
            template_content: 模板内容
            metadata: 模板元数据
            
        Returns:
            模板ID
        """
        # 确保模板ID存在
        if not metadata.template_id:
            metadata.template_id = str(uuid.uuid4())
        
        # 更新时间戳
        metadata.updated_at = datetime.now()
        
        # 保存模板内容
        template_path = self._get_template_path(metadata.template_id, metadata.template_type)
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_content, f, ensure_ascii=False, indent=2)
        
        # 保存元数据
        metadata_path = self._get_metadata_path(metadata.template_id, metadata.template_type)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"模板已保存: {metadata.name} (ID: {metadata.template_id})")
        return metadata.template_id
    
    def get_template(self, template_id: str, template_type: TemplateType) -> Tuple[Dict[str, Any], TemplateMetadata]:
        """获取模板
        
        Args:
            template_id: 模板ID
            template_type: 模板类型
            
        Returns:
            模板内容和元数据的元组
            
        Raises:
            FileNotFoundError: 模板不存在
        """
        # 获取模板内容
        template_path = self._get_template_path(template_id, template_type)
        if not template_path.exists():
            raise FileNotFoundError(f"模板不存在: {template_id}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = json.load(f)
        
        # 获取元数据
        metadata_path = self._get_metadata_path(template_id, template_type)
        if not metadata_path.exists():
            logger.warning(f"模板元数据不存在: {template_id}，将创建默认元数据")
            metadata = TemplateMetadata(
                template_id=template_id,
                template_type=template_type
            )
        else:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            metadata = TemplateMetadata.from_dict(metadata_dict)
        
        return template_content, metadata
    
    def list_templates(self, template_type: Optional[TemplateType] = None) -> List[TemplateMetadata]:
        """列出模板
        
        Args:
            template_type: 模板类型，如果为None则列出所有类型
            
        Returns:
            模板元数据列表
        """
        result = []
        
        # 确定要搜索的目录
        if template_type is not None:
            type_dirs = [self.base_dir / template_type.value]
        else:
            type_dirs = [self.base_dir / t.value for t in TemplateType]
        
        # 搜索每个目录
        for type_dir in type_dirs:
            if not type_dir.exists():
                continue
                
            # 查找所有元数据文件
            for metadata_file in type_dir.glob("*.metadata.json"):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata_dict = json.load(f)
                    metadata = TemplateMetadata.from_dict(metadata_dict)
                    result.append(metadata)
                except Exception as e:
                    logger.error(f"读取模板元数据失败: {metadata_file}, 错误: {e}")
        
        # 按更新时间排序
        result.sort(key=lambda x: x.updated_at, reverse=True)
        return result
    
    def delete_template(self, template_id: str, template_type: TemplateType) -> bool:
        """删除模板
        
        Args:
            template_id: 模板ID
            template_type: 模板类型
            
        Returns:
            是否成功删除
        """
        template_path = self._get_template_path(template_id, template_type)
        metadata_path = self._get_metadata_path(template_id, template_type)
        
        success = True
        
        # 删除模板文件
        if template_path.exists():
            try:
                os.remove(template_path)
            except Exception as e:
                logger.error(f"删除模板文件失败: {template_path}, 错误: {e}")
                success = False
        
        # 删除元数据文件
        if metadata_path.exists():
            try:
                os.remove(metadata_path)
            except Exception as e:
                logger.error(f"删除模板元数据文件失败: {metadata_path}, 错误: {e}")
                success = False
        
        return success
    
    def search_templates(self, query: str, template_type: Optional[TemplateType] = None) -> List[TemplateMetadata]:
        """搜索模板
        
        Args:
            query: 搜索关键词
            template_type: 模板类型，如果为None则搜索所有类型
            
        Returns:
            匹配的模板元数据列表
        """
        all_templates = self.list_templates(template_type)
        query = query.lower()
        
        # 简单的关键词匹配
        result = []
        for metadata in all_templates:
            # 在名称、描述、标签中搜索
            if (query in metadata.name.lower() or 
                query in metadata.description.lower() or 
                any(query in tag.lower() for tag in metadata.tags)):
                result.append(metadata)
        
        return result