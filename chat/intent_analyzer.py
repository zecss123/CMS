# -*- coding: utf-8 -*-
"""
意图分析器 - 分析用户输入意图，判断是否需要生成报告
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class IntentAnalyzer:
    """
    意图分析器 - 解析用户输入，识别报告生成需求
    """
    
    def __init__(self):
        """
        初始化意图分析器
        """
        # 报告相关关键词
        self.report_keywords = [
            '报告', '分析', '检查', '评估', '诊断', '监测',
            '状态', '健康', '振动', '趋势', '异常', '故障'
        ]
        
        # 风场相关关键词
        self.windfarm_keywords = [
            '风场', '风电场', '风力发电场', '场站', '电站'
        ]
        
        # 机组相关关键词
        self.turbine_keywords = [
            '机组', '风机', '风力发电机', '发电机组', '风电机组'
        ]
        
        # 时间相关关键词
        self.time_keywords = {
            '今天': 0,
            '昨天': 1,
            '前天': 2,
            '本周': 7,
            '上周': 14,
            '本月': 30,
            '上月': 60,
            '最近': 7
        }
        
        # 意图类型
        self.intent_types = {
            'generate_report': '生成报告',
            'query_status': '查询状态',
            'upload_knowledge': '上传知识',
            'manage_template': '管理模板',
            'general_chat': '一般对话'
        }
    
    def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """
        分析用户输入意图
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            意图分析结果
        """
        try:
            user_input = user_input.strip()
            if not user_input:
                return self._create_intent_result('general_chat', '输入为空')
            
            # 转换为小写便于匹配
            input_lower = user_input.lower()
            
            # 检查是否为报告生成请求
            if self._is_report_request(input_lower):
                return self._analyze_report_request(user_input, input_lower)
            
            # 检查是否为状态查询
            if self._is_status_query(input_lower):
                return self._analyze_status_query(user_input, input_lower)
            
            # 检查是否为知识管理请求
            if self._is_knowledge_request(input_lower):
                return self._analyze_knowledge_request(user_input, input_lower)
            
            # 检查是否为模板管理请求
            if self._is_template_request(input_lower):
                return self._analyze_template_request(user_input, input_lower)
            
            # 默认为一般对话
            return self._create_intent_result('general_chat', user_input)
            
        except Exception as e:
            logger.error(f"意图分析失败: {e}")
            return self._create_intent_result('general_chat', user_input, error=str(e))
    
    def _is_report_request(self, input_lower: str) -> bool:
        """判断是否为报告生成请求"""
        # 检查报告关键词
        has_report_keyword = any(keyword in input_lower for keyword in self.report_keywords)
        
        # 检查风场关键词
        has_windfarm_keyword = any(keyword in input_lower for keyword in self.windfarm_keywords)
        
        # 检查机组关键词
        has_turbine_keyword = any(keyword in input_lower for keyword in self.turbine_keywords)
        
        # 如果有明确的报告关键词，只需要有风场或机组信息
        if has_report_keyword:
            return has_windfarm_keyword or has_turbine_keyword
        
        # 如果没有明确的报告关键词，但同时包含风场和机组信息，也认为是报告请求
        if has_windfarm_keyword and has_turbine_keyword:
            return True
            
        return False
    
    def _is_status_query(self, input_lower: str) -> bool:
        """判断是否为状态查询"""
        status_keywords = ['状态', '情况', '如何', '怎么样', '运行']
        return any(keyword in input_lower for keyword in status_keywords)
    
    def _is_knowledge_request(self, input_lower: str) -> bool:
        """判断是否为知识管理请求"""
        knowledge_keywords = ['上传', '文档', '资料', '知识', '添加文件']
        return any(keyword in input_lower for keyword in knowledge_keywords)
    
    def _is_template_request(self, input_lower: str) -> bool:
        """判断是否为模板管理请求"""
        template_keywords = ['模板', '格式', '样式', '模版']
        return any(keyword in input_lower for keyword in template_keywords)
    
    def _analyze_report_request(self, user_input: str, input_lower: str) -> Dict[str, Any]:
        """分析报告生成请求"""
        result = self._create_intent_result('report_generation', user_input)
        
        # 提取风场信息
        wind_farm = self._extract_wind_farm(user_input)
        if wind_farm:
            result['entities']['wind_farm'] = wind_farm
            logger.info(f"提取到风场信息: {wind_farm}")
        else:
            logger.warning(f"未能提取风场信息，输入文本: {user_input}")
        
        # 提取机组信息
        turbine = self._extract_turbine(user_input)
        if turbine:
            result['entities']['turbine'] = turbine
            logger.info(f"提取到机组信息: {turbine}")
        else:
            logger.warning(f"未能提取机组信息，输入文本: {user_input}")
        
        # 提取时间范围
        time_range = self._extract_time_range(input_lower)
        if time_range:
            result['entities']['time_range'] = time_range
        
        # 提取报告类型
        report_type = self._extract_report_type(input_lower)
        result['entities']['report_type'] = report_type
        
        # 设置置信度
        result['confidence'] = self._calculate_confidence(result['entities'])
        
        logger.info(f"意图分析结果: {result}")
        return result
    
    def _analyze_status_query(self, user_input: str, input_lower: str) -> Dict[str, Any]:
        """分析状态查询请求"""
        result = self._create_intent_result('query_status', user_input)
        
        # 提取查询目标
        wind_farm = self._extract_wind_farm(user_input)
        if wind_farm:
            result['entities']['wind_farm'] = wind_farm
        
        turbine = self._extract_turbine(user_input)
        if turbine:
            result['entities']['turbine'] = turbine
        
        result['confidence'] = 0.8
        return result
    
    def _analyze_knowledge_request(self, user_input: str, input_lower: str) -> Dict[str, Any]:
        """分析知识管理请求"""
        result = self._create_intent_result('upload_knowledge', user_input)
        
        # 检查具体操作
        if '上传' in input_lower or '添加' in input_lower:
            result['entities']['action'] = 'upload'
        elif '删除' in input_lower:
            result['entities']['action'] = 'delete'
        elif '查看' in input_lower or '列表' in input_lower:
            result['entities']['action'] = 'list'
        else:
            result['entities']['action'] = 'upload'  # 默认为上传
        
        result['confidence'] = 0.9
        return result
    
    def _analyze_template_request(self, user_input: str, input_lower: str) -> Dict[str, Any]:
        """分析模板管理请求"""
        result = self._create_intent_result('manage_template', user_input)
        
        # 检查具体操作
        if '创建' in input_lower or '新建' in input_lower:
            result['entities']['action'] = 'create'
        elif '修改' in input_lower or '编辑' in input_lower:
            result['entities']['action'] = 'edit'
        elif '删除' in input_lower:
            result['entities']['action'] = 'delete'
        elif '查看' in input_lower or '列表' in input_lower:
            result['entities']['action'] = 'list'
        else:
            result['entities']['action'] = 'list'  # 默认为列表
        
        result['confidence'] = 0.8
        return result
    
    def _extract_wind_farm(self, text: str) -> Optional[str]:
        """提取风场名称"""
        # 匹配风场名称模式 - 使用更精确的匹配
        patterns = [
            # 优先匹配：直接匹配常见风场名称格式
            r'(华能风场[A-Za-z0-9]*)',
            r'(大唐风场[A-Za-z0-9]*)',
            r'(国电风场[A-Za-z0-9]*)',
            r'(中电投风场[A-Za-z0-9]*)',
            r'(三峡风场[A-Za-z0-9]*)',
            # 通用模式：匹配"XX风场A"这样的格式，确保风场前面有边界
            r'(?:^|[^\u4e00-\u9fa5])([\u4e00-\u9fa5]+[A-Za-z0-9]*)风场',
            r'(?:^|[^\u4e00-\u9fa5])([\u4e00-\u9fa5]+[A-Za-z0-9]*)风电场',
            r'(?:^|[^\u4e00-\u9fa5])([\u4e00-\u9fa5]+[A-Za-z0-9]*)电站'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 选择最长的匹配结果
                longest_match = max(matches, key=len)
                return longest_match
        
        return None
    
    def _extract_turbine(self, text: str) -> Optional[str]:
        """提取机组编号"""
        # 匹配机组编号模式
        patterns = [
            r'([A-Za-z]\d+)(?:号?机组|号?风机)',  # A01机组, A01风机
            r'(\d+)号机组',
            r'机组(\d+)',
            r'(\d+)号风机',
            r'风机(\d+)',
            r'WT([A-Za-z0-9]+)',
            r'T([A-Za-z0-9]+)',
            r'([A-Za-z]\d+)(?=\s|$|的|风机|机组)',  # 匹配A01这种格式
            r'(\d+[A-Za-z]+)(?=\s|$|的|风机|机组)'   # 匹配01A这种格式
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_time_range(self, input_lower: str) -> Optional[Dict[str, Any]]:
        """提取时间范围"""
        now = datetime.now()
        
        # 检查时间关键词
        for keyword, days_ago in self.time_keywords.items():
            if keyword in input_lower:
                start_date = now - timedelta(days=days_ago)
                return {
                    'start_date': start_date.isoformat(),
                    'end_date': now.isoformat(),
                    'description': keyword
                }
        
        # 匹配具体日期
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, input_lower)
            if match:
                try:
                    if len(match.groups()) == 3:
                        year, month, day = match.groups()
                        if len(year) == 4:
                            date = datetime(int(year), int(month), int(day))
                        else:
                            date = datetime(now.year, int(year), int(month))
                    else:
                        month, day = match.groups()
                        date = datetime(now.year, int(month), int(day))
                    
                    return {
                        'start_date': date.isoformat(),
                        'end_date': date.isoformat(),
                        'description': match.group(0)
                    }
                except ValueError:
                    continue
        
        return None
    
    def _extract_report_type(self, input_lower: str) -> str:
        """提取报告类型"""
        if '振动' in input_lower:
            return 'vibration'
        elif '趋势' in input_lower:
            return 'trend'
        elif '健康' in input_lower:
            return 'health'
        elif '故障' in input_lower or '异常' in input_lower:
            return 'fault'
        elif '维护' in input_lower:
            return 'maintenance'
        else:
            return 'comprehensive'  # 综合报告
    
    def _calculate_confidence(self, entities: Dict[str, Any]) -> float:
        """计算置信度"""
        confidence = 0.5  # 基础置信度
        
        # 有风场信息加分
        if entities.get('wind_farm'):
            confidence += 0.2
        
        # 有机组信息加分
        if entities.get('turbine'):
            confidence += 0.2
        
        # 有时间范围加分
        if entities.get('time_range'):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _create_intent_result(self, intent_type: str, original_text: str, 
                            error: Optional[str] = None) -> Dict[str, Any]:
        """创建意图分析结果"""
        return {
            'intent': intent_type,
            'intent_description': self.intent_types.get(intent_type, '未知意图'),
            'original_text': original_text,
            'entities': {},
            'confidence': 0.5,
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
    
    def validate_report_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证报告生成所需的实体信息
        
        Args:
            entities: 提取的实体信息
            
        Returns:
            验证结果
        """
        validation_result = {
            'valid': True,
            'missing_entities': [],
            'suggestions': []
        }
        
        # 检查必需的实体
        if not entities.get('wind_farm') and not entities.get('turbine'):
            validation_result['valid'] = False
            validation_result['missing_entities'].append('target')
            validation_result['suggestions'].append('请指定要分析的风场或机组')
        
        # 如果只有风场没有机组，建议指定机组
        if entities.get('wind_farm') and not entities.get('turbine'):
            validation_result['suggestions'].append('建议指定具体的机组编号以获得更详细的分析')
        
        # 如果没有时间范围，使用默认值
        if not entities.get('time_range'):
            validation_result['suggestions'].append('未指定时间范围，将使用最近7天的数据')
            entities['time_range'] = {
                'start_date': (datetime.now() - timedelta(days=7)).isoformat(),
                'end_date': datetime.now().isoformat(),
                'description': '最近7天'
            }
        
        return validation_result