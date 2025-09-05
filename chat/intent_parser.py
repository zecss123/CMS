# -*- coding: utf-8 -*-
"""
意图识别器 - 解析用户输入意图
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger


@dataclass
class Intent:
    """意图数据类"""
    type: str  # 意图类型
    confidence: float  # 置信度
    entities: Dict[str, Any]  # 提取的实体
    raw_text: str  # 原始文本
    

class IntentParser:
    """意图识别器"""
    
    def __init__(self):
        self.intent_patterns = {
            'report_request': [
                r'生成.*报告',
                r'.*报告.*生成',
                r'我要.*报告',
                r'需要.*报告',
                r'给我.*分析报告',
                r'帮我.*生成.*报告'
            ],
            'data_query': [
                r'查看.*数据',
                r'.*数据.*怎么样',
                r'显示.*振动',
                r'.*状态.*如何',
                r'检查.*设备',
                r'.*运行.*情况'
            ],
            'knowledge_query': [
                r'什么是.*',
                r'.*是什么意思',
                r'解释.*',
                r'.*原理',
                r'如何.*',
                r'怎么.*'
            ],
            'system_status': [
                r'系统.*状态',
                r'.*运行.*正常',
                r'检查.*系统',
                r'.*工作.*情况'
            ]
        }
        
        # 实体提取模式
        self.entity_patterns = {
            'wind_farm': r'([\u4e00-\u9fa5]+风场|[A-Za-z]+风场|风场[A-Za-z0-9]+)',
            'turbine_id': r'([A-Za-z0-9]+号机组|机组[A-Za-z0-9]+|[A-Za-z0-9]{2,6})',
            'time_range': r'(今天|昨天|本周|上周|本月|上月|最近.*天|[0-9]+天前)',
            'measurement_point': r'(主轴承|齿轮箱|发电机|叶轮|塔筒).*?(DE|NDE|HSS|LSS|上|下|前|后)?'
        }
        
    def parse(self, text: str) -> Intent:
        """解析用户输入文本"""
        try:
            # 预处理文本
            cleaned_text = self._preprocess_text(text)
            
            # 识别意图类型
            intent_type, confidence = self._classify_intent(cleaned_text)
            
            # 提取实体
            entities = self._extract_entities(cleaned_text)
            
            return Intent(
                type=intent_type,
                confidence=confidence,
                entities=entities,
                raw_text=text
            )
            
        except Exception as e:
            logger.error(f"意图解析失败: {e}")
            return Intent(
                type='unknown',
                confidence=0.0,
                entities={},
                raw_text=text
            )
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        # 转换为小写（保留中文）
        return text
    
    def _classify_intent(self, text: str) -> Tuple[str, float]:
        """分类意图"""
        best_intent = 'unknown'
        best_score = 0.0
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            matched_patterns = 0
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matched_patterns += 1
                    score += 1.0
            
            # 计算置信度
            if matched_patterns > 0:
                confidence = score / len(patterns)
                if confidence > best_score:
                    best_score = confidence
                    best_intent = intent_type
        
        return best_intent, min(best_score, 1.0)
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """提取实体信息"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if entity_type == 'time_range':
                    entities[entity_type] = self._parse_time_range(matches[0])
                else:
                    entities[entity_type] = matches[0]
        
        return entities
    
    def _parse_time_range(self, time_text: str) -> Dict[str, str]:
        """解析时间范围"""
        now = datetime.now()
        
        if '今天' in time_text:
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now
        elif '昨天' in time_text:
            yesterday = now - timedelta(days=1)
            start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif '本周' in time_text:
            days_since_monday = now.weekday()
            start_time = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now
        elif '上周' in time_text:
            days_since_monday = now.weekday()
            last_monday = now - timedelta(days=days_since_monday + 7)
            start_time = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = (last_monday + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
        elif '本月' in time_text:
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_time = now
        elif '上月' in time_text:
            if now.month == 1:
                last_month = now.replace(year=now.year-1, month=12, day=1)
            else:
                last_month = now.replace(month=now.month-1, day=1)
            start_time = last_month.replace(hour=0, minute=0, second=0, microsecond=0)
            # 计算上月最后一天
            if last_month.month == 12:
                next_month = last_month.replace(year=last_month.year+1, month=1, day=1)
            else:
                next_month = last_month.replace(month=last_month.month+1, day=1)
            end_time = (next_month - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # 处理"最近X天"或"X天前"
            days_match = re.search(r'(\d+)', time_text)
            if days_match:
                days = int(days_match.group(1))
                start_time = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = now
            else:
                # 默认为今天
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = now
        
        return {
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'raw_text': time_text
        }
    
    def get_intent_description(self, intent_type: str) -> str:
        """获取意图类型描述"""
        descriptions = {
            'report_request': '报告生成请求',
            'data_query': '数据查询请求',
            'knowledge_query': '知识库查询',
            'system_status': '系统状态查询',
            'unknown': '未知意图'
        }
        return descriptions.get(intent_type, '未知意图')
    
    def validate_entities(self, intent: Intent) -> List[str]:
        """验证提取的实体是否完整"""
        missing_entities = []
        
        if intent.type == 'report_request':
            if 'wind_farm' not in intent.entities:
                missing_entities.append('风场名称')
            if 'turbine_id' not in intent.entities:
                missing_entities.append('机组编号')
        
        elif intent.type == 'data_query':
            if 'wind_farm' not in intent.entities and 'turbine_id' not in intent.entities:
                missing_entities.append('风场名称或机组编号')
        
        return missing_entities