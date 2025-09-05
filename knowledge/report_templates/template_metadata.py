# -*- coding: utf-8 -*-
"""
报告模板元数据管理

定义模板类型、版本和元数据信息，支持模板的分类和检索。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


class TemplateType(Enum):
    """报告模板类型枚举"""
    VIBRATION_ANALYSIS = "vibration_analysis"  # 振动分析报告
    FAULT_DIAGNOSIS = "fault_diagnosis"        # 故障诊断报告
    TREND_ANALYSIS = "trend_analysis"          # 趋势分析报告
    MAINTENANCE_SUGGESTION = "maintenance"     # 维护建议报告
    COMPREHENSIVE = "comprehensive"            # 综合分析报告
    CUSTOM = "custom"                          # 自定义报告


class ValidationLevel(Enum):
    """模板验证级别枚举"""
    STRICT = "strict"  # 严格验证，所有必需字段都必须存在
    WARN = "warn"      # 警告模式，缺失字段会警告但不阻止
    NONE = "none"      # 不进行验证


@dataclass
class TemplateMetadata:
    """报告模板元数据"""
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    template_type: TemplateType = TemplateType.VIBRATION_ANALYSIS
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    author: str = ""
    tags: List[str] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    supported_languages: List[str] = field(default_factory=lambda: ["zh-CN", "en-US"])
    
    # 模板特定配置
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "author": self.author,
            "tags": self.tags,
            "sections": self.sections,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "supported_languages": self.supported_languages,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateMetadata':
        """从字典创建元数据对象"""
        template_type = TemplateType(data.get("template_type", TemplateType.VIBRATION_ANALYSIS.value))
        
        # 处理日期时间字段
        created_at_str = data.get("created_at")
        updated_at_str = data.get("updated_at")
        
        created_at = datetime.fromisoformat(created_at_str) if isinstance(created_at_str, str) else datetime.now()
        updated_at = datetime.fromisoformat(updated_at_str) if isinstance(updated_at_str, str) else datetime.now()
        
        return cls(
            template_id=data.get("template_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            template_type=template_type,
            version=data.get("version", "1.0.0"),
            created_at=created_at,
            updated_at=updated_at,
            author=data.get("author", ""),
            tags=data.get("tags", []),
            sections=data.get("sections", []),
            required_fields=data.get("required_fields", []),
            optional_fields=data.get("optional_fields", []),
            supported_languages=data.get("supported_languages", ["zh-CN", "en-US"]),
            config=data.get("config", {})
        )