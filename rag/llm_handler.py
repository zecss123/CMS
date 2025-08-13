# -*- coding: utf-8 -*-
"""
LLM模型处理模块 - 使用DeepSeek API
"""

import requests
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from config.settings import MODEL_CONFIG
from config.prompts import SYSTEM_PROMPT

class DeepSeekLLMHandler:
    """DeepSeek API处理器"""
    
    def __init__(self):
        self.api_key = "sk-a2590db6f1334022983b08ecf157e6b5"
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.model_name = "deepseek-chat"
        self.max_length = MODEL_CONFIG.get("max_length", 4096)
        self.temperature = MODEL_CONFIG.get("temperature", 0.7)
        self.top_p = MODEL_CONFIG.get("top_p", 0.9)
        
        logger.info(f"初始化DeepSeek API处理器，模型: {self.model_name}")
    
    def load_model(self) -> bool:
        """测试API连接"""
        try:
            # 发送一个简单的测试请求
            test_response = self._call_api("Hello", max_tokens=10)
            if test_response:
                logger.info("DeepSeek API连接成功")
                return True
            else:
                logger.error("DeepSeek API连接失败")
                return False
        except Exception as e:
            logger.error(f"API连接测试失败: {str(e)}")
            return False
    
    def _call_api(self, prompt: str, max_tokens: int = 512, system_prompt: Optional[str] = None) -> str:
        """调用DeepSeek API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            data = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"API响应格式错误: {result}")
                    return "API响应格式错误"
            else:
                logger.error(f"API请求失败: {response.status_code}, {response.text}")
                return f"API请求失败: {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            return "API请求超时，请稍后重试"
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求异常: {str(e)}")
            return f"API请求异常: {str(e)}"
        except Exception as e:
            logger.error(f"调用API时发生错误: {str(e)}")
            return f"调用API时发生错误: {str(e)}"
    
    def generate_response(self, prompt: str, max_new_tokens: int = 512) -> str:
        """生成回复"""
        return self._call_api(prompt, max_new_tokens)
    
    def generate_rag_response(self, query: str, context: str, max_new_tokens: int = 512) -> str:
        """基于检索上下文生成回复"""
        rag_prompt = f"""基于以下上下文信息回答问题：

上下文：
{context}

问题：{query}

请基于上下文信息提供准确、详细的回答。如果上下文中没有相关信息，请明确说明。"""
        
        return self._call_api(rag_prompt, max_new_tokens, SYSTEM_PROMPT)
    
    def analyze_vibration_data(self, data_summary: str, analysis_request: str) -> str:
        """分析振动数据"""
        analysis_prompt = f"""作为一名专业的机械振动分析工程师，请分析以下振动数据：

数据摘要：
{data_summary}

分析要求：
{analysis_request}

请提供详细的技术分析，包括：
1. 数据特征分析
2. 可能的故障模式识别
3. 严重程度评估
4. 建议的维护措施

请确保分析结果专业、准确、实用。"""
        
        return self._call_api(analysis_prompt, 1024, SYSTEM_PROMPT)
    
    def generate_report(self, analysis_results: Dict[str, Any]) -> str:
        """生成分析报告"""
        report_prompt = f"""基于以下分析结果生成专业的振动分析报告：

分析结果：
{json.dumps(analysis_results, ensure_ascii=False, indent=2)}

请生成一份结构化的专业报告，包括：
1. 执行摘要
2. 数据分析详情
3. 发现的问题
4. 风险评估
5. 建议措施
6. 结论

报告应该专业、清晰、易于理解。"""
        
        return self._call_api(report_prompt, 1500, SYSTEM_PROMPT)
    
    def cleanup(self):
        """清理资源（API模式下无需特殊清理）"""
        logger.info("API模式无需清理资源")
    
    def __del__(self):
        """析构函数"""
        self.cleanup()
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_type": "DeepSeek API",
            "model_name": self.model_name,
            "api_endpoint": self.base_url,
            "max_length": self.max_length,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "status": "API模式"
        }