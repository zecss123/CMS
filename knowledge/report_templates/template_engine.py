# -*- coding: utf-8 -*-
"""
报告模板引擎

提供模板填充、变量替换、格式化输出等核心功能。
"""

import re
import json
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from loguru import logger

from .template_metadata import TemplateMetadata, TemplateType
from .template_validator import TemplateValidator, ValidationResult


@dataclass
class RenderContext:
    """渲染上下文"""
    variables: Dict[str, Any]
    functions: Dict[str, Callable]
    metadata: Optional[TemplateMetadata] = None
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量值"""
        return self.variables.get(name, default)
    
    def call_function(self, name: str, *args, **kwargs) -> Any:
        """调用函数"""
        if name in self.functions:
            return self.functions[name](*args, **kwargs)
        raise ValueError(f"未定义的函数: {name}")


@dataclass
class RenderResult:
    """渲染结果"""
    success: bool
    content: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class TemplateEngine:
    """报告模板引擎"""
    
    # 变量模式
    VARIABLE_PATTERN = re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}')
    
    # 函数调用模式
    FUNCTION_PATTERN = re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*\}\}')
    
    def __init__(self):
        """初始化模板引擎"""
        self.validator = TemplateValidator()
        self._builtin_functions = self._init_builtin_functions()
    
    def _init_builtin_functions(self) -> Dict[str, Callable]:
        """初始化内置函数"""
        return {
            'now': lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'today': lambda: datetime.now().strftime('%Y-%m-%d'),
            'format_number': lambda x, precision=2: f"{float(x):.{precision}f}",
            'upper': lambda x: str(x).upper(),
            'lower': lambda x: str(x).lower(),
            'title': lambda x: str(x).title(),
            'len': lambda x: len(x) if hasattr(x, '__len__') else 0,
            'default': lambda x, default_val: x if x is not None else default_val
        }
    
    def render_template(self, 
                       template_content: Dict[str, Any], 
                       context: RenderContext,
                       validate: bool = True) -> RenderResult:
        """渲染模板
        
        Args:
            template_content: 模板内容
            context: 渲染上下文
            validate: 是否验证模板
            
        Returns:
            渲染结果
        """
        result = RenderResult(success=True)
        
        try:
            # 验证模板（如果需要）
            if validate and context.metadata:
                validation_result = self.validator.validate_template(
                    template_content, context.metadata.template_type
                )
                if not validation_result.is_valid:
                    result.success = False
                    if result.errors is None:
                        result.errors = []
                    result.errors.extend(validation_result.errors)
                    return result
                if result.warnings is None:
                    result.warnings = []
                result.warnings.extend(validation_result.warnings)
            
            # 深拷贝模板内容以避免修改原始模板
            rendered_content = self._deep_copy_and_render(template_content, context)
            result.content = rendered_content
            
        except Exception as e:
            logger.error(f"模板渲染失败: {e}")
            result.success = False
            if result.errors is None:
                result.errors = []
            result.errors.append(f"渲染错误: {str(e)}")
        
        return result
    
    def _deep_copy_and_render(self, obj: Any, context: RenderContext) -> Any:
        """深拷贝并渲染对象"""
        if isinstance(obj, str):
            return self._render_string(obj, context)
        elif isinstance(obj, dict):
            return {key: self._deep_copy_and_render(value, context) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy_and_render(item, context) for item in obj]
        else:
            return obj
    
    def _render_string(self, template_str: str, context: RenderContext) -> str:
        """渲染字符串模板
        
        Args:
            template_str: 模板字符串
            context: 渲染上下文
            
        Returns:
            渲染后的字符串
        """
        # 首先处理函数调用
        result = self._render_functions(template_str, context)
        
        # 然后处理变量替换
        result = self._render_variables(result, context)
        
        return result
    
    def _render_functions(self, template_str: str, context: RenderContext) -> str:
        """渲染函数调用"""
        def replace_function(match):
            func_name = match.group(1)
            args_str = match.group(2).strip()
            
            try:
                # 解析参数
                args = self._parse_function_args(args_str, context)
                
                # 调用函数
                if func_name in self._builtin_functions:
                    result = self._builtin_functions[func_name](*args)
                elif func_name in context.functions:
                    result = context.functions[func_name](*args)
                else:
                    logger.warning(f"未知函数: {func_name}")
                    return match.group(0)  # 保持原样
                
                return str(result)
            except Exception as e:
                logger.error(f"函数调用失败: {func_name}, 错误: {e}")
                return match.group(0)  # 保持原样
        
        return self.FUNCTION_PATTERN.sub(replace_function, template_str)
    
    def _render_variables(self, template_str: str, context: RenderContext) -> str:
        """渲染变量"""
        def replace_variable(match):
            var_path = match.group(1)
            
            try:
                # 支持点号路径，如 user.name
                value = self._get_nested_value(context.variables, var_path)
                
                if value is None:
                    logger.warning(f"未定义的变量: {var_path}")
                    return match.group(0)  # 保持原样
                
                return str(value)
            except Exception as e:
                logger.error(f"变量替换失败: {var_path}, 错误: {e}")
                return match.group(0)  # 保持原样
        
        return self.VARIABLE_PATTERN.sub(replace_variable, template_str)
    
    def _parse_function_args(self, args_str: str, context: RenderContext) -> List[Any]:
        """解析函数参数"""
        if not args_str:
            return []
        
        args = []
        # 简单的参数解析，支持字符串、数字和变量
        for arg in args_str.split(','):
            arg = arg.strip()
            
            if not arg:
                continue
            
            # 字符串参数
            if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                args.append(arg[1:-1])
            # 数字参数
            elif arg.replace('.', '').replace('-', '').isdigit():
                args.append(float(arg) if '.' in arg else int(arg))
            # 变量参数
            else:
                value = self._get_nested_value(context.variables, arg)
                args.append(value)
        
        return args
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套值
        
        Args:
            data: 数据字典
            path: 路径，如 'user.name' 或 'settings.display.theme'
            
        Returns:
            值或None
        """
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def get_template_variables(self, template_content: Dict[str, Any]) -> List[str]:
        """获取模板中的所有变量
        
        Args:
            template_content: 模板内容
            
        Returns:
            变量名列表
        """
        return self.validator.get_template_variables(template_content)
    
    def create_sample_context(self, template_content: Dict[str, Any]) -> RenderContext:
        """创建示例上下文
        
        Args:
            template_content: 模板内容
            
        Returns:
            示例渲染上下文
        """
        variables = self.get_template_variables(template_content)
        
        # 为每个变量创建示例值
        sample_variables = {}
        for var in variables:
            if 'date' in var.lower() or 'time' in var.lower():
                sample_variables[var] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif 'name' in var.lower():
                sample_variables[var] = '示例名称'
            elif 'value' in var.lower() or 'result' in var.lower():
                sample_variables[var] = 123.45
            elif 'count' in var.lower() or 'number' in var.lower():
                sample_variables[var] = 10
            elif 'description' in var.lower() or 'content' in var.lower():
                sample_variables[var] = '这是示例内容描述'
            else:
                sample_variables[var] = f'示例_{var}'
        
        return RenderContext(
            variables=sample_variables,
            functions={}
        )
    
    def preview_template(self, template_content: Dict[str, Any]) -> RenderResult:
        """预览模板
        
        Args:
            template_content: 模板内容
            
        Returns:
            预览渲染结果
        """
        context = self.create_sample_context(template_content)
        return self.render_template(template_content, context, validate=False)