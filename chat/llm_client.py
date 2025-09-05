# -*- coding: utf-8 -*-
"""
大模型客户端 - 与AI模型进行交互
"""

import json
import logging
import requests
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMClient:
    """
    大模型客户端 - 支持多种AI模型接口
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        初始化大模型客户端
        
        Args:
            model_config: 模型配置
        """
        self.model_config = model_config
        self.model_type = model_config.get('type', 'openai')
        
        # 根据模型类型获取对应的配置
        if self.model_type == 'openai':
            config = model_config.get('openai', {})
        elif self.model_type == 'local':
            config = model_config.get('local', {})
        elif self.model_type == 'deepseek_api':
            config = model_config.get('deepseek_api', {})
        elif self.model_type == 'custom':
            config = model_config.get('custom', {})
        else:
            config = {}
            
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        self.model_name = config.get('model_name', 'gpt-3.5-turbo')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.7)
        
        # 会话历史
        self.conversation_history = []
        
        # 系统提示词
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """
你是一个专业的风电机组振动分析专家助手。你具备以下能力：

1. 振动数据分析：能够分析风电机组的振动数据，识别异常模式和潜在故障
2. 报告生成：根据分析结果生成专业的技术报告
3. 知识检索：从技术文档和历史数据中检索相关信息
4. 维护建议：基于分析结果提供维护和检修建议

请始终保持专业、准确、有用的回答风格。当用户询问振动分析相关问题时，请提供详细的技术解释和建议。
"""
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None,
            stream: bool = False) -> Dict[str, Any]:
        """
        与大模型对话
        
        Args:
            message: 用户消息
            context: 上下文信息（如检索到的知识）
            stream: 是否流式输出
            
        Returns:
            对话结果
        """
        try:
            # 构建消息
            messages = self._build_messages(message, context)
            
            if stream:
                return self._chat_stream(messages)
            else:
                return self._chat_complete(messages)
                
        except Exception as e:
            logger.error(f"大模型对话失败: {e}")
            return {
                "success": False,
                "error": f"对话失败: {str(e)}",
                "response": "抱歉，我现在无法回答您的问题，请稍后再试。"
            }
    
    def _build_messages(self, message: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """构建对话消息"""
        messages = []
        
        # 添加系统消息
        messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        # 添加上下文信息
        if context and context.get('knowledge_results'):
            knowledge_results = context['knowledge_results']
            # 处理知识检索结果的不同格式
            if isinstance(knowledge_results, dict) and 'results' in knowledge_results:
                # KnowledgeRetriever返回的格式: {'success': True, 'results': [...], ...}
                results_list = knowledge_results.get('results', [])
            elif isinstance(knowledge_results, list):
                # 直接的结果列表
                results_list = knowledge_results
            else:
                # 其他格式，转换为列表
                results_list = [knowledge_results] if knowledge_results else []
            
            if results_list:
                context_content = self._format_context(results_list)
                messages.append({
                    "role": "system",
                    "content": f"相关技术资料：\n{context_content}"
                })
        
        # 添加历史对话
        if self.conversation_history:
            messages.extend(self.conversation_history[-10:])  # 保留最近10轮对话
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": message
        })
        
        return messages
    
    def _format_context(self, knowledge_results: List[Dict[str, Any]]) -> str:
        """格式化上下文信息"""
        context_parts = []
        for i, result in enumerate(knowledge_results[:3], 1):  # 最多使用3个结果
            text = result.get('text', '') or result.get('content', '') or str(result)
            if len(text) > 500:
                text = text[:500] + "..."
            context_parts.append(f"资料{i}：{text}")
        return "\n\n".join(context_parts)
    
    def _chat_complete(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """完整对话（非流式）"""
        if self.model_type == 'openai':
            return self._openai_chat(messages)
        elif self.model_type == 'local':
            return self._local_chat(messages)
        else:
            return {
                "success": False,
                "error": f"不支持的模型类型: {self.model_type}"
            }
    
    def _chat_stream(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """流式对话"""
        if self.model_type == 'openai':
            return self._openai_chat_stream(messages)
        elif self.model_type == 'local':
            return self._local_chat_stream(messages)
        else:
            return {
                "success": False,
                "error": f"不支持的模型类型: {self.model_type}"
            }
    
    def _openai_chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """OpenAI API对话"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result['choices'][0]['message']['content']
                
                # 更新对话历史
                self.conversation_history.append({
                    "role": "user",
                    "content": messages[-1]['content']
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                return {
                    "success": True,
                    "response": assistant_message,
                    "usage": result.get('usage', {})
                }
            else:
                return {
                    "success": False,
                    "error": f"API请求失败: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI API调用失败: {str(e)}"
            }
    
    def _openai_chat_stream(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """OpenAI API流式对话"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                def stream_generator():
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str.strip() == '[DONE]':
                                    break
                                try:
                                    data = json.loads(data_str)
                                    if 'choices' in data and len(data['choices']) > 0:
                                        delta = data['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            content = delta['content']
                                            full_response += content
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                    
                    # 更新对话历史
                    self.conversation_history.append({
                        "role": "user",
                        "content": messages[-1]['content']
                    })
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": full_response
                    })
                
                return {
                    "success": True,
                    "stream": stream_generator()
                }
            else:
                return {
                    "success": False,
                    "error": f"API请求失败: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI API流式调用失败: {str(e)}"
            }
    
    def _local_chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """本地模型对话"""
        try:
            # 这里可以集成本地模型，如Transformers
            # 暂时返回模拟响应
            user_message = messages[-1]['content']
            
            # 检查是否是报告生成请求
            if '报告' in user_message and ('风场' in user_message or '机组' in user_message):
                # 生成详细的振动分析报告
                response = self._generate_mock_report(user_message)
            elif '报告' in user_message:
                response = "我将为您生成振动分析报告。请提供具体的风场和机组信息。"
            elif '振动' in user_message:
                response = "振动分析是风电机组健康监测的重要手段。我可以帮您分析振动数据并识别潜在问题。"
            elif '故障' in user_message:
                response = "根据振动数据可以识别多种故障类型，包括轴承故障、齿轮箱问题、叶片不平衡等。"
            else:
                response = "我是风电机组振动分析专家助手，可以帮您进行数据分析、生成报告和提供维护建议。"
            
            # 更新对话历史
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return {
                "success": True,
                "response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"本地模型调用失败: {str(e)}"
            }
    
    def _generate_mock_report(self, user_message: str) -> str:
        """生成模拟的振动分析报告"""
        # 从消息中提取风场和机组信息
        wind_farm = "未指定风场"
        turbine = "未指定机组"
        
        if "华能风场A" in user_message:
            wind_farm = "华能风场A"
        if "A01" in user_message:
            turbine = "A01"
        
        report = f"""# 风电机组振动分析报告

## 基本信息
- **风场名称**: {wind_farm}
- **机组编号**: {turbine}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **数据来源**: 模拟数据

## 执行摘要
本报告基于{wind_farm}的{turbine}风机振动数据进行分析。通过对振动信号的频域和时域分析，评估机组运行状态并识别潜在故障。

## 数据分析结果
### 振动水平评估
- **整体振动水平**: 正常范围内
- **主要频率成分**: 1X转频、2X转频、齿轮啮合频率
- **振动趋势**: 稳定，无明显异常增长

### 频谱分析
- **低频段(0-10Hz)**: 主要为转频及其倍频，幅值正常
- **中频段(10-1000Hz)**: 齿轮箱相关频率，无异常峰值
- **高频段(1000Hz以上)**: 轴承特征频率，状态良好

## 异常识别和诊断
### 当前状态评估
- **轴承状态**: 良好，无明显磨损迹象
- **齿轮箱状态**: 正常运行，齿轮啮合良好
- **叶片平衡**: 平衡状态良好，无明显不平衡
- **塔架振动**: 在正常范围内

### 潜在风险点
- 建议持续监测高频振动变化
- 关注温度变化对振动的影响

## 维护建议
1. **定期监测**: 建议每月进行一次全面振动检测
2. **润滑维护**: 按计划进行齿轮箱和轴承润滑
3. **紧固检查**: 检查各连接部位的紧固状态
4. **清洁维护**: 保持传感器清洁，确保数据准确性

## 结论和建议
{wind_farm}的{turbine}风机当前振动状态良好，各主要部件运行正常。建议继续按现有维护计划执行，并加强日常监测。如发现振动水平异常增长，应及时进行详细检查。

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*分析系统: CMS振动分析系统*"""
        
        return report
    
    def _local_chat_stream(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """本地模型流式对话"""
        try:
            # 模拟流式输出
            response = self._local_chat(messages)
            if response['success']:
                def stream_generator():
                    text = response['response']
                    for char in text:
                        yield char
                
                return {
                    "success": True,
                    "stream": stream_generator()
                }
            else:
                return response
                
        except Exception as e:
            return {
                "success": False,
                "error": f"本地模型流式调用失败: {str(e)}"
            }
    
    def generate_report(self, report_data: Dict[str, Any], 
                       template: Optional[str] = None) -> Dict[str, Any]:
        """生成分析报告"""
        try:
            # 构建报告生成提示
            prompt = self._build_report_prompt(report_data, template)
            
            # 调用大模型生成报告
            result = self.chat(prompt)
            
            if result['success']:
                return {
                    "success": True,
                    "report": result['response'],
                    "report_data": report_data,
                    "generated_time": datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return {
                "success": False,
                "error": f"生成报告失败: {str(e)}"
            }
    
    def _build_report_prompt(self, report_data: Dict[str, Any], 
                           template: Optional[str] = None) -> str:
        """构建报告生成提示"""
        prompt_parts = []
        
        if template:
            prompt_parts.append(f"请根据以下模板生成报告：\n{template}\n")
        else:
            prompt_parts.append("请生成一份专业的风电机组振动分析报告。")
        
        prompt_parts.append("报告数据：")
        
        # 添加基本信息
        if 'wind_farm' in report_data:
            prompt_parts.append(f"风场：{report_data['wind_farm']}")
        if 'turbine' in report_data:
            prompt_parts.append(f"机组：{report_data['turbine']}")
        if 'time_range' in report_data:
            prompt_parts.append(f"分析时间：{report_data['time_range']}")
        
        # 添加分析数据
        if 'analysis_results' in report_data:
            prompt_parts.append("分析结果：")
            for key, value in report_data['analysis_results'].items():
                prompt_parts.append(f"- {key}: {value}")
        
        # 添加要求
        prompt_parts.append("\n请确保报告包含以下内容：")
        prompt_parts.append("1. 执行摘要")
        prompt_parts.append("2. 数据分析结果")
        prompt_parts.append("3. 异常识别")
        prompt_parts.append("4. 维护建议")
        prompt_parts.append("5. 结论")
        
        return "\n".join(prompt_parts)
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self.system_prompt = prompt
