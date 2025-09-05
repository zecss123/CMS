# -*- coding: utf-8 -*-
"""
模板管理器 - 管理报告模板和分析模板
"""

import os
import json
import uuid
import logging
import hashlib
import shutil
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
from string import Template

logger = logging.getLogger(__name__)

class TemplateManager:
    """
    模板管理器 - 负责报告模板的存储、检索和渲染
    支持版本控制、模板导入导出、搜索等高级功能
    """
    
    def __init__(self, templates_path: str):
        """
        初始化模板管理器
        
        Args:
            templates_path: 模板存储路径
        """
        self.templates_path = Path(templates_path)
        self.templates_path.mkdir(exist_ok=True)
        
        # 版本控制目录
        self.versions_path = self.templates_path / "versions"
        self.versions_path.mkdir(exist_ok=True)
        
        # 模板元数据文件
        self.metadata_file = self.templates_path / "templates_metadata.json"
        self.versions_file = self.templates_path / "versions_metadata.json"
        self.load_metadata()
        
        # 预定义模板类型
        self.template_types = {
            "report": "分析报告模板",
            "summary": "摘要模板", 
            "alarm": "报警模板",
            "trend": "趋势分析模板",
            "maintenance": "维护建议模板"
        }
    
    def load_metadata(self):
        """加载模板元数据"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {}
                
            # 加载版本元数据
            if self.versions_file.exists():
                with open(self.versions_file, 'r', encoding='utf-8') as f:
                    self.versions_metadata = json.load(f)
            else:
                self.versions_metadata = {}
        except Exception as e:
            logger.error(f"加载模板元数据失败: {e}")
            self.metadata = {}
            self.versions_metadata = {}
    
    def save_metadata(self):
        """保存模板元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
            # 保存版本元数据
            with open(self.versions_file, 'w', encoding='utf-8') as f:
                json.dump(self.versions_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存模板元数据失败: {e}")
    
    def save_template(self, template_name: str, template_content: str,
                     template_type: str = "report", 
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        保存模板
        
        Args:
            template_name: 模板名称
            template_content: 模板内容
            template_type: 模板类型
            metadata: 模板元数据
            
        Returns:
            保存结果
        """
        try:
            # 生成模板ID
            template_id = str(uuid.uuid4())
            
            # 验证模板内容
            validation_result = self._validate_template(template_content)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"模板验证失败: {validation_result['error']}"
                }
            
            # 保存模板文件
            template_file = self.templates_path / f"{template_id}.txt"
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            # 更新元数据
            self.metadata[template_id] = {
                "template_name": template_name,
                "template_type": template_type,
                "file_path": str(template_file),
                "created_time": datetime.now().isoformat(),
                "updated_time": datetime.now().isoformat(),
                "metadata": metadata or {},
                "variables": validation_result["variables"]
            }
            
            self.save_metadata()
            
            logger.info(f"模板保存成功: {template_name} -> {template_id}")
            
            return {
                "success": True,
                "template_id": template_id,
                "message": "模板保存成功"
            }
            
        except Exception as e:
            logger.error(f"保存模板失败: {e}")
            return {
                "success": False,
                "error": f"保存模板失败: {str(e)}"
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
            # 查找模板ID
            template_id = None
            for tid, tmeta in self.metadata.items():
                if tmeta["template_name"] == template_name:
                    template_id = tid
                    break
            
            if not template_id:
                return {
                    "success": False,
                    "error": "模板不存在"
                }
            
            # 读取模板内容
            template_file = self.templates_path / f"{template_id}.txt"
            if not template_file.exists():
                return {
                    "success": False,
                    "error": "模板文件不存在"
                }
            
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "template_id": template_id,
                "template_name": template_name,
                "content": content,
                "metadata": self.metadata[template_id]
            }
            
        except Exception as e:
            logger.error(f"获取模板失败: {e}")
            return {
                "success": False,
                "error": f"获取模板失败: {str(e)}"
            }
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        渲染模板
        
        Args:
            template_name: 模板名称
            variables: 模板变量
            
        Returns:
            渲染结果
        """
        try:
            # 获取模板
            template_result = self.get_template(template_name)
            if not template_result["success"]:
                return template_result
            
            # 渲染模板
            template = Template(template_result["content"])
            
            # 检查必需的变量
            required_vars = template_result["metadata"]["variables"]
            missing_vars = [var for var in required_vars if var not in variables]
            
            if missing_vars:
                return {
                    "success": False,
                    "error": f"缺少必需的模板变量: {', '.join(missing_vars)}"
                }
            
            # 执行渲染
            rendered_content = template.safe_substitute(variables)
            
            return {
                "success": True,
                "rendered_content": rendered_content,
                "template_name": template_name,
                "variables_used": list(variables.keys())
            }
            
        except Exception as e:
            logger.error(f"渲染模板失败: {e}")
            return {
                "success": False,
                "error": f"渲染模板失败: {str(e)}"
            }
    
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
        try:
            # 查找模板ID
            template_id = None
            for tid, tmeta in self.metadata.items():
                if tmeta["template_name"] == template_name:
                    template_id = tid
                    break
            
            if not template_id:
                return {
                    "success": False,
                    "error": "模板不存在"
                }
            
            # 验证新模板内容
            validation_result = self._validate_template(template_content)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"模板验证失败: {validation_result['error']}"
                }
            
            # 更新模板文件
            template_file = self.templates_path / f"{template_id}.txt"
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            # 更新元数据
            self.metadata[template_id]["updated_time"] = datetime.now().isoformat()
            self.metadata[template_id]["variables"] = validation_result["variables"]
            
            if metadata:
                self.metadata[template_id]["metadata"].update(metadata)
            
            self.save_metadata()
            
            logger.info(f"模板更新成功: {template_name}")
            
            return {
                "success": True,
                "message": "模板更新成功"
            }
            
        except Exception as e:
            logger.error(f"更新模板失败: {e}")
            return {
                "success": False,
                "error": f"更新模板失败: {str(e)}"
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
            # 查找模板ID
            template_id = None
            for tid, tmeta in self.metadata.items():
                if tmeta["template_name"] == template_name:
                    template_id = tid
                    break
            
            if not template_id:
                return {
                    "success": False,
                    "error": "模板不存在"
                }
            
            # 删除模板文件
            template_file = self.templates_path / f"{template_id}.txt"
            if template_file.exists():
                template_file.unlink()
            
            # 删除元数据
            del self.metadata[template_id]
            self.save_metadata()
            
            logger.info(f"模板删除成功: {template_name}")
            
            return {
                "success": True,
                "message": "模板删除成功"
            }
            
        except Exception as e:
            logger.error(f"删除模板失败: {e}")
            return {
                "success": False,
                "error": f"删除模板失败: {str(e)}"
            }
    
    def list_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出模板
        
        Args:
            template_type: 过滤模板类型
            
        Returns:
            模板列表
        """
        templates = []
        for template_id, template_info in self.metadata.items():
            if template_type is None or template_info["template_type"] == template_type:
                templates.append({
                    "template_id": template_id,
                    "template_name": template_info["template_name"],
                    "template_type": template_info["template_type"],
                    "created_time": template_info["created_time"],
                    "updated_time": template_info["updated_time"],
                    "variables": template_info["variables"]
                })
        return templates
    
    def _validate_template(self, template_content: str) -> Dict[str, Any]:
        """
        验证模板内容
        
        Args:
            template_content: 模板内容
            
        Returns:
            验证结果
        """
        try:
            # 创建Template对象进行语法检查
            template = Template(template_content)
            
            # 提取模板变量
            import re
            variables = re.findall(r'\$\{?([a-zA-Z_][a-zA-Z0-9_]*)\}?', template_content)
            variables = list(set(variables))  # 去重
            
            return {
                "valid": True,
                "variables": variables
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "variables": []
            }
    
    def create_default_templates(self):
        """
        创建默认模板
        """
        default_templates = {
            "振动分析报告": {
                "type": "report",
                "content": """
# 振动分析报告

## 基本信息
- 风场名称: ${wind_farm_name}
- 机组编号: ${turbine_id}
- 分析时间: ${analysis_time}
- 报告生成时间: ${report_time}

## 分析摘要
${analysis_summary}

## 测点分析结果
${measurement_points_analysis}

## 趋势分析
${trend_analysis}

## 报警信息
${alarm_info}

## 维护建议
${maintenance_recommendations}

## 附件
- 趋势图: ${trend_charts}
- 频谱图: ${spectrum_charts}
"""
            },
            "报警通知": {
                "type": "alarm",
                "content": """
# 振动报警通知

**报警级别**: ${alarm_level}
**风场**: ${wind_farm_name}
**机组**: ${turbine_id}
**测点**: ${measurement_point}
**报警时间**: ${alarm_time}

## 报警详情
- 当前值: ${current_value}
- 报警阈值: ${alarm_threshold}
- 超标程度: ${exceed_percentage}%

## 建议措施
${recommended_actions}
"""
            },
            "维护建议": {
                "type": "maintenance",
                "content": """
# 维护建议报告

## 机组信息
- 风场: ${wind_farm_name}
- 机组: ${turbine_id}
- 评估时间: ${assessment_time}

## 健康状态评估
- 整体健康评分: ${health_score}/100
- 状态等级: ${health_level}

## 维护建议
${maintenance_suggestions}

## 优先级排序
${priority_ranking}

## 预计维护成本
${estimated_cost}
"""
            }
        }
        
        for template_name, template_info in default_templates.items():
            # 检查模板是否已存在
            existing = False
            for tid, tmeta in self.metadata.items():
                if tmeta["template_name"] == template_name:
                    existing = True
                    break
            
            if not existing:
                result = self.save_template(
                    template_name,
                    template_info["content"],
                    template_info["type"],
                    {"is_default": True}
                )
                if result["success"]:
                    logger.info(f"创建默认模板: {template_name}")
                else:
                    logger.error(f"创建默认模板失败: {template_name} - {result['error']}")
    
    def create_version(self, template_name: str, comment: str = "") -> Dict[str, Any]:
        """
        为模板创建版本
        
        Args:
            template_name: 模板名称
            comment: 版本注释
            
        Returns:
            版本创建结果
        """
        try:
            # 获取当前模板
            template_result = self.get_template(template_name)
            if not template_result["success"]:
                return template_result
            
            template_id = template_result["template_id"]
            content = template_result["content"]
            
            # 生成版本ID（基于内容哈希和时间戳）
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            version_id = f"{template_id}_{timestamp}_{content_hash}"
            
            # 保存版本文件
            version_file = self.versions_path / f"{version_id}.txt"
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新版本元数据
            if template_id not in self.versions_metadata:
                self.versions_metadata[template_id] = []
            
            version_info = {
                "version_id": version_id,
                "created_time": datetime.now().isoformat(),
                "comment": comment,
                "content_hash": content_hash,
                "file_path": str(version_file)
            }
            
            self.versions_metadata[template_id].append(version_info)
            
            # 保留最近10个版本
            if len(self.versions_metadata[template_id]) > 10:
                old_version = self.versions_metadata[template_id].pop(0)
                old_file = Path(old_version["file_path"])
                if old_file.exists():
                    old_file.unlink()
            
            self.save_metadata()
            
            logger.info(f"模板版本创建成功: {template_name} -> {version_id}")
            
            return {
                "success": True,
                "version_id": version_id,
                "message": "版本创建成功"
            }
            
        except Exception as e:
            logger.error(f"创建模板版本失败: {e}")
            return {
                "success": False,
                "error": f"创建模板版本失败: {str(e)}"
            }
    
    def get_template_versions(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板版本历史
        
        Args:
            template_name: 模板名称
            
        Returns:
            版本历史列表
        """
        try:
            # 查找模板ID
            template_id = None
            for tid, tmeta in self.metadata.items():
                if tmeta["template_name"] == template_name:
                    template_id = tid
                    break
            
            if not template_id:
                return {
                    "success": False,
                    "error": "模板不存在"
                }
            
            versions = self.versions_metadata.get(template_id, [])
            
            return {
                "success": True,
                "template_name": template_name,
                "versions": versions
            }
            
        except Exception as e:
            logger.error(f"获取模板版本失败: {e}")
            return {
                "success": False,
                "error": f"获取模板版本失败: {str(e)}"
            }
    
    def restore_version(self, template_name: str, version_id: str) -> Dict[str, Any]:
        """
        恢复模板到指定版本
        
        Args:
            template_name: 模板名称
            version_id: 版本ID
            
        Returns:
            恢复结果
        """
        try:
            # 查找模板ID
            template_id = None
            for tid, tmeta in self.metadata.items():
                if tmeta["template_name"] == template_name:
                    template_id = tid
                    break
            
            if not template_id:
                return {
                    "success": False,
                    "error": "模板不存在"
                }
            
            # 查找版本
            versions = self.versions_metadata.get(template_id, [])
            version_info = None
            for v in versions:
                if v["version_id"] == version_id:
                    version_info = v
                    break
            
            if not version_info:
                return {
                    "success": False,
                    "error": "版本不存在"
                }
            
            # 读取版本内容
            version_file = Path(version_info["file_path"])
            if not version_file.exists():
                return {
                    "success": False,
                    "error": "版本文件不存在"
                }
            
            with open(version_file, 'r', encoding='utf-8') as f:
                version_content = f.read()
            
            # 先创建当前版本的备份
            backup_result = self.create_version(template_name, f"恢复前备份 - {datetime.now().isoformat()}")
            if not backup_result["success"]:
                logger.warning(f"创建备份失败: {backup_result['error']}")
            
            # 更新模板内容
            update_result = self.update_template(template_name, version_content, {
                "restored_from": version_id,
                "restored_time": datetime.now().isoformat()
            })
            
            if update_result["success"]:
                logger.info(f"模板恢复成功: {template_name} -> {version_id}")
            
            return update_result
            
        except Exception as e:
            logger.error(f"恢复模板版本失败: {e}")
            return {
                "success": False,
                "error": f"恢复模板版本失败: {str(e)}"
            }
    
    def search_templates(self, query: str, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索模板
        
        Args:
            query: 搜索关键词
            template_type: 模板类型过滤
            
        Returns:
            匹配的模板列表
        """
        results = []
        query_lower = query.lower()
        
        for template_id, template_info in self.metadata.items():
            # 类型过滤
            if template_type and template_info["template_type"] != template_type:
                continue
            
            # 搜索匹配
            match_score = 0
            
            # 模板名称匹配
            if query_lower in template_info["template_name"].lower():
                match_score += 10
            
            # 元数据匹配
            metadata = template_info.get("metadata", {})
            for key, value in metadata.items():
                if isinstance(value, str) and query_lower in value.lower():
                    match_score += 5
            
            # 内容匹配（需要读取文件）
            try:
                template_file = Path(template_info["file_path"])
                if template_file.exists():
                    with open(template_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if query_lower in content.lower():
                        match_score += 3
            except Exception:
                pass
            
            if match_score > 0:
                result = template_info.copy()
                result["template_id"] = template_id
                result["match_score"] = match_score
                results.append(result)
        
        # 按匹配分数排序
        results.sort(key=lambda x: x["match_score"], reverse=True)
        
        return results
    
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
        try:
            # 获取模板
            template_result = self.get_template(template_name)
            if not template_result["success"]:
                return template_result
            
            template_id = template_result["template_id"]
            
            # 准备导出数据
            export_data = {
                "template_name": template_name,
                "content": template_result["content"],
                "metadata": template_result["metadata"],
                "export_time": datetime.now().isoformat(),
                "versions": []
            }
            
            # 包含版本历史
            if include_versions:
                versions = self.versions_metadata.get(template_id, [])
                for version_info in versions:
                    try:
                        version_file = Path(version_info["file_path"])
                        if version_file.exists():
                            with open(version_file, 'r', encoding='utf-8') as f:
                                version_content = f.read()
                            
                            export_data["versions"].append({
                                "version_id": version_info["version_id"],
                                "created_time": version_info["created_time"],
                                "comment": version_info["comment"],
                                "content": version_content
                            })
                    except Exception as e:
                        logger.warning(f"导出版本失败: {version_info['version_id']} - {e}")
            
            # 保存导出文件
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"模板导出成功: {template_name} -> {export_path}")
            
            return {
                "success": True,
                "export_path": str(export_file),
                "message": "模板导出成功"
            }
            
        except Exception as e:
            logger.error(f"导出模板失败: {e}")
            return {
                "success": False,
                "error": f"导出模板失败: {str(e)}"
            }
    
    def import_template(self, import_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        导入模板
        
        Args:
            import_path: 导入文件路径
            overwrite: 是否覆盖已存在的模板
            
        Returns:
            导入结果
        """
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                return {
                    "success": False,
                    "error": "导入文件不存在"
                }
            
            # 读取导入数据
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            template_name = import_data["template_name"]
            
            # 检查模板是否已存在
            existing_template = self.get_template(template_name)
            if existing_template["success"] and not overwrite:
                return {
                    "success": False,
                    "error": "模板已存在，请设置overwrite=True以覆盖"
                }
            
            # 导入模板
            if existing_template["success"] and overwrite:
                # 更新现有模板
                result = self.update_template(
                    template_name,
                    import_data["content"],
                    import_data["metadata"]
                )
            else:
                # 创建新模板
                template_type = import_data["metadata"].get("template_type", "report")
                result = self.save_template(
                    template_name,
                    import_data["content"],
                    template_type,
                    import_data["metadata"]
                )
            
            if not result["success"]:
                return result
            
            # 导入版本历史
            if "versions" in import_data and import_data["versions"]:
                template_id = None
                for tid, tmeta in self.metadata.items():
                    if tmeta["template_name"] == template_name:
                        template_id = tid
                        break
                
                if template_id:
                    imported_versions = []
                    for version_data in import_data["versions"]:
                        try:
                            # 生成新的版本ID
                            content_hash = hashlib.md5(version_data["content"].encode('utf-8')).hexdigest()[:8]
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            version_id = f"{template_id}_{timestamp}_{content_hash}"
                            
                            # 保存版本文件
                            version_file = self.versions_path / f"{version_id}.txt"
                            with open(version_file, 'w', encoding='utf-8') as f:
                                f.write(version_data["content"])
                            
                            version_info = {
                                "version_id": version_id,
                                "created_time": version_data["created_time"],
                                "comment": f"导入版本: {version_data['comment']}",
                                "content_hash": content_hash,
                                "file_path": str(version_file)
                            }
                            
                            imported_versions.append(version_info)
                            
                        except Exception as e:
                            logger.warning(f"导入版本失败: {e}")
                    
                    if imported_versions:
                        if template_id not in self.versions_metadata:
                            self.versions_metadata[template_id] = []
                        self.versions_metadata[template_id].extend(imported_versions)
                        
                        # 保留最近10个版本
                        if len(self.versions_metadata[template_id]) > 10:
                            excess_count = len(self.versions_metadata[template_id]) - 10
                            for _ in range(excess_count):
                                old_version = self.versions_metadata[template_id].pop(0)
                                old_file = Path(old_version["file_path"])
                                if old_file.exists():
                                    old_file.unlink()
                        
                        self.save_metadata()
            
            logger.info(f"模板导入成功: {template_name}")
            
            return {
                "success": True,
                "template_name": template_name,
                "message": "模板导入成功"
            }
            
        except Exception as e:
            logger.error(f"导入模板失败: {e}")
            return {
                "success": False,
                "error": f"导入模板失败: {str(e)}"
            }
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """
        获取模板统计信息
        
        Returns:
            统计信息
        """
        stats = {
            "total_templates": len(self.metadata),
            "template_types": {},
            "total_versions": 0,
            "recent_activity": []
        }
        
        # 统计模板类型
        for template_info in self.metadata.values():
            template_type = template_info["template_type"]
            stats["template_types"][template_type] = stats["template_types"].get(template_type, 0) + 1
        
        # 统计版本数量
        for versions in self.versions_metadata.values():
            stats["total_versions"] += len(versions)
        
        # 最近活动（最近更新的模板）
        recent_templates = sorted(
            [(tid, tinfo) for tid, tinfo in self.metadata.items()],
            key=lambda x: x[1]["updated_time"],
            reverse=True
        )[:5]
        
        for template_id, template_info in recent_templates:
            stats["recent_activity"].append({
                "template_name": template_info["template_name"],
                "template_type": template_info["template_type"],
                "updated_time": template_info["updated_time"]
            })
        
        return stats


if __name__ == "__main__":
    # 测试模板管理器功能
    import tempfile
    import shutil
    
    # 创建临时目录进行测试
    test_dir = tempfile.mkdtemp()
    print(f"测试目录: {test_dir}")
    
    try:
        # 初始化模板管理器
        tm = TemplateManager(test_dir)
        
        # 创建默认模板
        print("\n=== 创建默认模板 ===")
        tm.create_default_templates()
        
        # 列出所有模板
        print("\n=== 模板列表 ===")
        templates = tm.list_templates()
        for template in templates:
            print(f"- {template['template_name']} ({template['template_type']})")
        
        # 创建版本
        print("\n=== 创建版本 ===")
        version_result = tm.create_version("振动分析报告", "初始版本")
        print(f"版本创建结果: {version_result}")
        
        # 更新模板
        print("\n=== 更新模板 ===")
        new_content = """
# 更新的振动分析报告

## 基本信息
- 风场名称: ${wind_farm_name}
- 机组编号: ${turbine_id}
- 分析时间: ${analysis_time}
- 报告生成时间: ${report_time}
- 分析师: ${analyst_name}

## 分析摘要
${analysis_summary}

## 详细分析结果
${detailed_analysis}

## 维护建议
${maintenance_recommendations}
"""
        update_result = tm.update_template("振动分析报告", new_content)
        print(f"更新结果: {update_result}")
        
        # 再次创建版本
        version_result2 = tm.create_version("振动分析报告", "添加分析师字段")
        print(f"第二个版本创建结果: {version_result2}")
        
        # 获取版本历史
        print("\n=== 版本历史 ===")
        versions = tm.get_template_versions("振动分析报告")
        if versions["success"]:
            for version in versions["versions"]:
                print(f"- {version['version_id']}: {version['comment']} ({version['created_time']})")
        
        # 搜索模板
        print("\n=== 搜索模板 ===")
        search_results = tm.search_templates("振动")
        for result in search_results:
            print(f"- {result['template_name']} (匹配分数: {result['match_score']})")
        
        # 导出模板
        print("\n=== 导出模板 ===")
        export_path = f"{test_dir}/exported_template.json"
        export_result = tm.export_template("振动分析报告", export_path, include_versions=True)
        print(f"导出结果: {export_result}")
        
        # 获取统计信息
        print("\n=== 统计信息 ===")
        stats = tm.get_template_statistics()
        print(f"总模板数: {stats['total_templates']}")
        print(f"总版本数: {stats['total_versions']}")
        print(f"模板类型分布: {stats['template_types']}")
        
        # 渲染模板测试
        print("\n=== 模板渲染测试 ===")
        render_vars = {
            "wind_farm_name": "测试风场",
            "turbine_id": "WT001",
            "analysis_time": "2024-01-15 10:00:00",
            "report_time": "2024-01-15 11:00:00",
            "analyst_name": "张工程师",
            "analysis_summary": "机组运行正常，无异常振动",
            "detailed_analysis": "各测点振动值均在正常范围内",
            "maintenance_recommendations": "建议继续监测，无需特殊维护"
        }
        
        render_result = tm.render_template("振动分析报告", render_vars)
        if render_result["success"]:
            print("渲染成功！")
            print("渲染结果预览:")
            print(render_result["rendered_content"][:200] + "...")
        else:
            print(f"渲染失败: {render_result['error']}")
        
        print("\n=== 测试完成 ===")
        
    finally:
        # 清理测试目录
        shutil.rmtree(test_dir)
        print(f"已清理测试目录: {test_dir}")