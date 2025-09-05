# -*- coding: utf-8 -*-
"""
报告模板验证器

提供报告模板格式验证、内容检查和结构验证功能。
"""

import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from .template_metadata import TemplateType


class ValidationLevel(Enum):
    """验证级别"""
    STRICT = "strict"      # 严格验证
    NORMAL = "normal"      # 正常验证
    LOOSE = "loose"        # 宽松验证


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def add_error(self, message: str) -> None:
        """添加错误"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """添加警告"""
        self.warnings.append(message)
    
    def add_suggestion(self, message: str) -> None:
        """添加建议"""
        self.suggestions.append(message)


class TemplateValidator:
    """报告模板验证器"""
    
    # 必需的模板字段
    REQUIRED_FIELDS = {
        "template_info",
        "sections",
        "format_config"
    }
    
    # 模板信息必需字段
    REQUIRED_TEMPLATE_INFO = {
        "name",
        "version",
        "description"
    }
    
    # 节必需字段
    REQUIRED_SECTION_FIELDS = {
        "id",
        "name",
        "type",
        "content"
    }
    
    # 支持的节类型
    SUPPORTED_SECTION_TYPES = {
        "text",
        "image",
        "chart",
        "table",
        "image_text_pair",
        "analysis_conclusion"
    }
    
    # 变量名模式
    VARIABLE_PATTERN = re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}')
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.NORMAL):
        """初始化验证器
        
        Args:
            validation_level: 验证级别
        """
        self.validation_level = validation_level
    
    def validate_template(self, template_content: Dict[str, Any], template_type: TemplateType) -> ValidationResult:
        """验证模板
        
        Args:
            template_content: 模板内容
            template_type: 模板类型
            
        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], suggestions=[])
        
        # 基础结构验证
        self._validate_basic_structure(template_content, result)
        
        # 模板信息验证
        if "template_info" in template_content:
            self._validate_template_info(template_content["template_info"], result)
        
        # 节验证
        if "sections" in template_content:
            self._validate_sections(template_content["sections"], result)
        
        # 格式配置验证
        if "format_config" in template_content:
            self._validate_format_config(template_content["format_config"], result)
        
        # 类型特定验证
        self._validate_type_specific(template_content, template_type, result)
        
        # 变量一致性验证
        self._validate_variable_consistency(template_content, result)
        
        return result
    
    def _validate_basic_structure(self, template_content: Dict[str, Any], result: ValidationResult) -> None:
        """验证基础结构"""
        # 检查必需字段
        for field in self.REQUIRED_FIELDS:
            if field not in template_content:
                result.add_error(f"缺少必需字段: {field}")
        
        # 检查字段类型
        if "sections" in template_content and not isinstance(template_content["sections"], list):
            result.add_error("sections字段必须是列表类型")
        
        if "template_info" in template_content and not isinstance(template_content["template_info"], dict):
            result.add_error("template_info字段必须是字典类型")
        
        if "format_config" in template_content and not isinstance(template_content["format_config"], dict):
            result.add_error("format_config字段必须是字典类型")
    
    def _validate_template_info(self, template_info: Dict[str, Any], result: ValidationResult) -> None:
        """验证模板信息"""
        # 检查必需字段
        for field in self.REQUIRED_TEMPLATE_INFO:
            if field not in template_info:
                result.add_error(f"template_info缺少必需字段: {field}")
        
        # 验证版本格式
        if "version" in template_info:
            version = template_info["version"]
            if not isinstance(version, str) or not re.match(r'^\d+\.\d+(\.\d+)?$', version):
                result.add_error("版本号格式不正确，应为x.y或x.y.z格式")
    
    def _validate_sections(self, sections: List[Dict[str, Any]], result: ValidationResult) -> None:
        """验证节"""
        if not sections:
            result.add_warning("模板没有定义任何节")
            return
        
        section_ids = set()
        
        for i, section in enumerate(sections):
            # 检查必需字段
            for field in self.REQUIRED_SECTION_FIELDS:
                if field not in section:
                    result.add_error(f"第{i+1}个节缺少必需字段: {field}")
            
            # 检查节ID唯一性
            if "id" in section:
                section_id = section["id"]
                if section_id in section_ids:
                    result.add_error(f"节ID重复: {section_id}")
                section_ids.add(section_id)
            
            # 检查节类型
            if "type" in section:
                section_type = section["type"]
                if section_type not in self.SUPPORTED_SECTION_TYPES:
                    result.add_error(f"不支持的节类型: {section_type}")
                
                # 类型特定验证
                self._validate_section_by_type(section, result)
    
    def _validate_section_by_type(self, section: Dict[str, Any], result: ValidationResult) -> None:
        """根据类型验证节"""
        section_type = section.get("type")
        section_id = section.get("id", "未知")
        
        if section_type == "image_text_pair":
            # 图文对节需要特殊字段
            content = section.get("content", {})
            if "image_placeholder" not in content:
                result.add_error(f"图文对节 {section_id} 缺少 image_placeholder 字段")
            if "text_template" not in content:
                result.add_error(f"图文对节 {section_id} 缺少 text_template 字段")
        
        elif section_type == "analysis_conclusion":
            # 分析结论节需要特殊字段
            content = section.get("content", {})
            if "conclusion_template" not in content:
                result.add_error(f"分析结论节 {section_id} 缺少 conclusion_template 字段")
            if "polish_config" not in content:
                result.add_warning(f"分析结论节 {section_id} 建议添加 polish_config 字段")
        
        elif section_type == "chart":
            # 图表节验证
            content = section.get("content", {})
            if "chart_type" not in content:
                result.add_warning(f"图表节 {section_id} 建议指定 chart_type")
    
    def _validate_format_config(self, format_config: Dict[str, Any], result: ValidationResult) -> None:
        """验证格式配置"""
        # 检查页面设置
        if "page_settings" in format_config:
            page_settings = format_config["page_settings"]
            if "size" in page_settings and page_settings["size"] not in ["A4", "A3", "Letter"]:
                result.add_warning(f"不常见的页面尺寸: {page_settings['size']}")
        
        # 检查样式设置
        if "styles" in format_config:
            styles = format_config["styles"]
            if "font_family" in styles:
                # 检查中文字体支持
                font_family = styles["font_family"]
                chinese_fonts = ["SimHei", "Microsoft YaHei", "SimSun", "KaiTi"]
                if not any(font in font_family for font in chinese_fonts):
                    result.add_suggestion("建议添加中文字体支持")
    
    def _validate_type_specific(self, template_content: Dict[str, Any], template_type: TemplateType, result: ValidationResult) -> None:
        """类型特定验证"""
        if template_type == TemplateType.VIBRATION_ANALYSIS:
            # 振动分析模板特定验证
            sections = template_content.get("sections", [])
            
            # 检查是否包含必要的振动分析节
            section_types = {section.get("type") for section in sections}
            
            if "analysis_conclusion" not in section_types:
                result.add_warning("振动分析模板建议包含分析结论节")
            
            if "chart" not in section_types:
                result.add_warning("振动分析模板建议包含图表节")
        
        elif template_type == TemplateType.FAULT_DIAGNOSIS:
            # 故障诊断模板特定验证
            sections = template_content.get("sections", [])
            section_types = {section.get("type") for section in sections}
            
            if "analysis_conclusion" not in section_types:
                result.add_error("故障诊断模板必须包含分析结论节")
    
    def _validate_variable_consistency(self, template_content: Dict[str, Any], result: ValidationResult) -> None:
        """验证变量一致性"""
        # 收集所有变量
        all_variables = set()
        self._collect_variables(template_content, all_variables)
        
        # 检查变量命名规范
        for var in all_variables:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
                result.add_error(f"变量名不符合命名规范: {var}")
            
            # 检查常见的变量名
            if var.startswith('temp_') or var.startswith('tmp_'):
                result.add_suggestion(f"变量名 {var} 可能是临时变量，建议使用更有意义的名称")
    
    def _collect_variables(self, obj: Any, variables: Set[str]) -> None:
        """递归收集变量"""
        if isinstance(obj, str):
            # 从字符串中提取变量
            matches = self.VARIABLE_PATTERN.findall(obj)
            variables.update(matches)
        elif isinstance(obj, dict):
            for value in obj.values():
                self._collect_variables(value, variables)
        elif isinstance(obj, list):
            for item in obj:
                self._collect_variables(item, variables)
    
    def get_template_variables(self, template_content: Dict[str, Any]) -> List[str]:
        """获取模板中的所有变量
        
        Args:
            template_content: 模板内容
            
        Returns:
            变量名列表
        """
        variables = set()
        self._collect_variables(template_content, variables)
        return sorted(list(variables))