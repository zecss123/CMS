# -*- coding: utf-8 -*-
"""
模板管理API接口 - 提供Web应用集成的模板管理功能
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from .template_manager import TemplateManager

logger = logging.getLogger(__name__)

class TemplateAPI:
    """
    模板管理API接口 - 提供Web应用集成的模板管理功能
    """
    
    def __init__(self, templates_path: str):
        """
        初始化模板API
        
        Args:
            templates_path: 模板存储路径
        """
        self.templates_path = Path(templates_path)
        self.templates_path.mkdir(exist_ok=True)
        self.manager = TemplateManager(templates_path)
    
    def get_template_types(self) -> List[Dict[str, str]]:
        """
        获取所有模板类型
        
        Returns:
            模板类型列表
        """
        return [
            {"id": type_id, "name": type_name}
            for type_id, type_name in self.manager.template_types.items()
        ]
    
    def get_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取模板列表
        
        Args:
            template_type: 模板类型过滤
            
        Returns:
            模板列表
        """
        return self.manager.list_templates(template_type)
    
    def get_template_content(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板内容
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板内容和元数据
        """
        return self.manager.get_template(template_name)
    
    def create_template(self, template_name: str, template_content: str, 
                       template_type: str = "report", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建新模板
        
        Args:
            template_name: 模板名称
            template_content: 模板内容
            template_type: 模板类型
            metadata: 模板元数据
            
        Returns:
            创建结果
        """
        return self.manager.save_template(template_name, template_content, template_type, metadata)
    
    def update_template(self, template_name: str, template_content: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        更新模板
        
        Args:
            template_name: 模板名称
            template_content: 新的模板内容
            metadata: 更新的元数据
            
        Returns:
            更新结果
        """
        # 先创建版本备份
        self.manager.create_version(template_name, "自动备份 - 更新前")
        return self.manager.update_template(template_name, template_content, metadata)
    
    def delete_template(self, template_name: str) -> Dict[str, Any]:
        """
        删除模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            删除结果
        """
        return self.manager.delete_template(template_name)
    
    def search_templates(self, query: str, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索模板
        
        Args:
            query: 搜索关键词
            template_type: 模板类型过滤
            
        Returns:
            匹配的模板列表
        """
        return self.manager.search_templates(query, template_type)
    
    def get_template_versions(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板版本历史
        
        Args:
            template_name: 模板名称
            
        Returns:
            版本历史列表
        """
        return self.manager.get_template_versions(template_name)
    
    def restore_version(self, template_name: str, version_id: str) -> Dict[str, Any]:
        """
        恢复模板到指定版本
        
        Args:
            template_name: 模板名称
            version_id: 版本ID
            
        Returns:
            恢复结果
        """
        return self.manager.restore_version(template_name, version_id)
    
    def export_template(self, template_name: str, export_path: str, include_versions: bool = False) -> Dict[str, Any]:
        """
        导出模板
        
        Args:
            template_name: 模板名称
            export_path: 导出路径
            include_versions: 是否包含版本历史
            
        Returns:
            导出结果
        """
        return self.manager.export_template(template_name, export_path, include_versions)
    
    def import_template(self, import_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        导入模板
        
        Args:
            import_path: 导入文件路径
            overwrite: 是否覆盖已存在的模板
            
        Returns:
            导入结果
        """
        return self.manager.import_template(import_path, overwrite)
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        渲染模板
        
        Args:
            template_name: 模板名称
            variables: 模板变量
            
        Returns:
            渲染结果
        """
        return self.manager.render_template(template_name, variables)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取模板统计信息
        
        Returns:
            统计信息
        """
        return self.manager.get_template_statistics()
    
    def initialize_default_templates(self) -> None:
        """
        初始化默认模板
        """
        self.manager.create_default_templates()
        logger.info("默认模板初始化完成")


if __name__ == "__main__":
    # 测试模板API
    import tempfile
    import shutil
    
    # 创建临时目录进行测试
    test_dir = tempfile.mkdtemp()
    print(f"测试目录: {test_dir}")
    
    try:
        # 初始化模板API
        api = TemplateAPI(test_dir)
        
        # 初始化默认模板
        api.initialize_default_templates()
        
        # 获取模板类型
        print("\n=== 模板类型 ===")
        types = api.get_template_types()
        for t in types:
            print(f"- {t['id']}: {t['name']}")
        
        # 获取模板列表
        print("\n=== 模板列表 ===")
        templates = api.get_templates()
        for template in templates:
            print(f"- {template['template_name']} ({template['template_type']})")
        
        # 创建新模板
        print("\n=== 创建新模板 ===")
        new_template = api.create_template(
            "测试模板",
            "# 测试模板\n\n这是一个测试模板，变量: ${test_var}",
            "summary",
            {"description": "这是一个测试模板"}
        )
        print(f"创建结果: {new_template}")
        
        # 搜索模板
        print("\n=== 搜索模板 ===")
        search_results = api.search_templates("测试")
        for result in search_results:
            print(f"- {result['template_name']} (匹配分数: {result['match_score']})")
        
        # 获取统计信息
        print("\n=== 统计信息 ===")
        stats = api.get_statistics()
        print(f"总模板数: {stats['total_templates']}")
        print(f"模板类型分布: {stats['template_types']}")
        
        print("\n=== 测试完成 ===")
        
    finally:
        # 清理测试目录
        shutil.rmtree(test_dir)
        print(f"已清理测试目录: {test_dir}")