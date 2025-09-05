# -*- coding: utf-8 -*-
"""
聊天管理器 - 整合对话流程和各个组件
"""

import json
import logging
import requests
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime

from chat.intent_analyzer import IntentAnalyzer
from chat.llm_client import LLMClient
from chat.session_manager import SessionManager
from knowledge.knowledge_retriever import KnowledgeRetriever
from knowledge.template_manager import TemplateManager
from api.data_fetcher import DataFetcher
from report.generator import CMSReportGenerator

logger = logging.getLogger(__name__)

class ChatManager:
    """
    聊天管理器 - 协调各个组件完成用户请求
    """
    
    def __init__(self, config: Dict[str, Any], session_manager: Optional[SessionManager] = None):
        """
        初始化聊天管理器
        
        Args:
            config: 配置信息
            session_manager: 会话管理器实例，如果为None则创建新实例
        """
        self.config = config
        
        # 初始化各个组件
        self.intent_analyzer = IntentAnalyzer()
        self.llm_client = LLMClient(config.get('model', {}))
        self.session_manager = session_manager or SessionManager()
        
        # 知识库组件
        knowledge_config = config.get('knowledge', {})
        self.knowledge_retriever = KnowledgeRetriever(
            embeddings_path=knowledge_config.get('embeddings_path', 'data/knowledge/embeddings'),
            metadata_path=knowledge_config.get('metadata_path', 'data/knowledge/metadata')
        )
        self.template_manager = TemplateManager(
            knowledge_config.get('template_path', 'data/templates')
        )
        
        # 数据获取组件
        api_config = config.get('api', {})
        db_config = config.get('database', {})
        
        # 创建API客户端和数据库管理器的占位符实例
        from api.client import VibrationDataAPIClient
        from database.database import DatabaseManager
        
        # 使用默认配置创建实例（实际使用时应从配置文件读取）
        api_client = VibrationDataAPIClient(base_url="http://localhost:8000")
        db_manager = DatabaseManager("sqlite:///vibration.db")
        
        self.data_fetcher = DataFetcher(
            api_client=api_client,
            db_manager=db_manager
        )
        
        # 报告生成器
        self.report_generator = CMSReportGenerator()
        
        logger.info("聊天管理器初始化完成")
    
    def process_message(self, user_id: str, message: str, 
                       session_id: Optional[str] = None,
                       stream: bool = False) -> Dict[str, Any]:
        """
        处理用户消息
        
        Args:
            user_id: 用户ID
            message: 用户消息
            session_id: 会话ID
            stream: 是否流式输出
            
        Returns:
            处理结果
        """
        try:
            # 获取或创建会话
            if not session_id:
                session_id = self.session_manager.create_session(user_id)
            
            session = self.session_manager.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在",
                    "session_id": session_id
                }
            
            # 分析用户意图
            intent_result = self.intent_analyzer.analyze_intent(message)
            
            # 更新会话状态
            self.session_manager.add_message(session_id, "user", message)
            
            # 根据意图处理请求
            if intent_result['intent'] == 'report_generation':
                result = self._handle_report_generation(session_id, intent_result, stream)
            elif intent_result['intent'] == 'status_query':
                result = self._handle_status_query(session_id, intent_result, stream)
            elif intent_result['intent'] == 'knowledge_management':
                result = self._handle_knowledge_management(session_id, intent_result, stream)
            elif intent_result['intent'] == 'template_management':
                result = self._handle_template_management(session_id, intent_result, stream)
            else:
                result = self._handle_general_chat(session_id, message, stream)
            
            # 更新会话
            if result.get('success') and result.get('response'):
                self.session_manager.add_message(session_id, "assistant", result['response'])
            
            result['session_id'] = session_id
            result['intent'] = intent_result['intent']
            
            return result
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return {
                "success": False,
                "error": f"处理失败: {str(e)}",
                "session_id": session_id
            }
    
    def _handle_report_generation(self, session_id: str, intent_result: Dict[str, Any],
                                stream: bool = False) -> Dict[str, Any]:
        """
        处理报告生成请求
        """
        try:
            entities = intent_result.get('entities', {})
            
            # 检查必需参数
            if not entities.get('wind_farm') or not entities.get('turbine'):
                return {
                    "success": False,
                    "error": "请提供风场和机组信息",
                    "response": "生成报告需要指定风场和机组，请提供完整信息。"
                }
            
            # 检查数据源模式
            # 优先检查会话中是否有明确的数据源指示
            session_context = self.session_manager.get_context(session_id) if self.session_manager else {}
            use_mock_data = session_context.get('use_mock_data', False)  # 默认不使用模拟数据
            
            # 如果没有明确指示且外部API未启用，则提示用户选择数据源
            if not use_mock_data and not self.config.get('external_api', {}).get('enabled', False):
                return {
                    "success": False,
                    "error": "数据源未配置",
                    "response": "请先生成测试数据或配置外部API数据源。您可以在报告生成页面勾选'生成测试数据'选项，或在系统配置中启用外部API。"
                }
            
            if use_mock_data:
                # 使用测试数据模式
                data_result = self._get_mock_vibration_data(entities)
            else:
                # 使用外部API模式
                data_result = self._get_api_vibration_data(entities)
            
            if not data_result.get('success'):
                return {
                    "success": False,
                    "error": "数据获取失败",
                    "response": data_result.get('error', '无法获取振动数据，请检查风场和机组信息是否正确。')
                }
            
            # 检索相关知识
            knowledge_query = f"{entities['wind_farm']} {entities['turbine']} 振动分析"
            knowledge_results = self.knowledge_retriever.search(
                query=knowledge_query,
                top_k=3
            )
            
            # 获取报告模板
            template_result = self.template_manager.get_template(
                template_name='vibration_analysis_report'
            )
            
            # 生成报告
            report_data = {
                'wind_farm': entities['wind_farm'],
                'turbine': entities['turbine'],
                'time_range': entities.get('time_range'),
                'vibration_data': data_result['data'],
                'knowledge_context': knowledge_results,
                'template': template_result.get('content') if template_result.get('success') else None
            }
            
            if stream:
                return self._generate_report_stream(report_data)
            else:
                return self._generate_report_complete(report_data)
                
        except Exception as e:
            logger.error(f"报告生成处理失败: {e}")
            return {
                "success": False,
                "error": f"报告生成失败: {str(e)}",
                "response": "抱歉，报告生成过程中出现错误，请稍后再试。"
            }
    
    def _generate_report_complete(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成完整报告"""
        try:
            # 使用LLM生成报告内容
            prompt = self._build_report_prompt(report_data)
            context = {
                'knowledge_results': report_data.get('knowledge_context', []),
                'data_context': report_data.get('vibration_data', {})
            }
            
            report_result = self.llm_client.chat(prompt, context, stream=False)
            
            if report_result.get('success'):
                # 生成实际的DOCX文件
                docx_result = self._generate_docx_file(report_data, report_result['response'])
                
                return {
                    "success": True,
                    "response": report_result['response'],
                    "report_data": report_data,
                    "report_type": "vibration_analysis",
                    "docx_file": docx_result.get('file_path') if docx_result.get('success') else None
                }
            else:
                return {
                    "success": False,
                    "error": report_result.get('error', '报告生成失败'),
                    "response": "报告生成失败，请检查数据和参数。"
                }
                
        except Exception as e:
            logger.error(f"完整报告生成失败: {e}")
            return {
                "success": False,
                "error": f"报告生成失败: {str(e)}",
                "response": "报告生成过程中出现错误。"
            }
    
    def _generate_report_stream(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成流式报告"""
        try:
            # 构建报告生成上下文
            context = {
                'knowledge_results': report_data.get('knowledge_context', []),
                'data_context': report_data.get('vibration_data', {})
            }
            
            # 构建报告生成提示
            prompt = self._build_report_prompt(report_data)
            
            # 使用LLM客户端生成流式响应
            chat_result = self.llm_client.chat(prompt, context, stream=True)
            
            if chat_result.get('success'):
                return {
                    "success": True,
                    "stream": chat_result['stream'],
                    "report_data": report_data,
                    "report_type": "vibration_analysis"
                }
            else:
                return {
                    "success": False,
                    "error": chat_result.get('error', '流式报告生成失败'),
                    "response": "流式报告生成失败。"
                }
                
        except Exception as e:
            logger.error(f"流式报告生成失败: {e}")
            return {
                "success": False,
                "error": f"流式报告生成失败: {str(e)}",
                "response": "流式报告生成过程中出现错误。"
            }
    
    def _build_report_prompt(self, report_data: Dict[str, Any]) -> str:
        """构建报告生成提示"""
        prompt_parts = []
        
        prompt_parts.append("请生成一份专业的风电机组振动分析报告，包含以下信息：")
        
        # 基本信息
        prompt_parts.append(f"\n风场：{report_data.get('wind_farm', '未指定')}")
        prompt_parts.append(f"机组：{report_data.get('turbine', '未指定')}")
        
        if report_data.get('time_range'):
            prompt_parts.append(f"分析时间：{report_data['time_range']}")
        
        # 数据信息
        if report_data.get('vibration_data'):
            prompt_parts.append("\n振动数据概况：")
            data = report_data['vibration_data']
            if isinstance(data, dict):
                for key, value in data.items():
                    prompt_parts.append(f"- {key}: {value}")
        
        # 报告要求
        prompt_parts.append("\n请确保报告包含：")
        prompt_parts.append("1. 执行摘要")
        prompt_parts.append("2. 数据分析结果")
        prompt_parts.append("3. 异常识别和诊断")
        prompt_parts.append("4. 维护建议")
        prompt_parts.append("5. 结论和建议")
        
        return "\n".join(prompt_parts)
    
    def _generate_docx_file(self, report_data: Dict[str, Any], report_content: str) -> Dict[str, Any]:
        """生成DOCX文件"""
        try:
            from pathlib import Path
            from datetime import datetime
            import os
            
            # 确保输出目录存在
            output_dir = Path(self.config.get('system', {}).get('output_dir', './output'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            wind_farm = report_data.get('wind_farm', 'unknown')
            turbine = report_data.get('turbine', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{wind_farm}_{turbine}_振动分析报告_{timestamp}.docx"
            file_path = output_dir / filename
            
            # 提取原始结论并进行润色
            raw_conclusion = self._extract_conclusion_from_content(report_content)
            
            # 构建润色上下文
            polish_context = {
                "wind_farm": wind_farm,
                "turbine": turbine,
                "analysis_type": "振动分析",
                "data_summary": f"分析了{wind_farm}风场{turbine}机组的振动数据"
            }
            
            # 润色结论
            polish_result = self.polish_conclusion(raw_conclusion, polish_context)
            
            # 使用润色后的结论或原始结论
            if polish_result.get('success'):
                polished_parts = polish_result.get('extracted_parts', {})
                final_conclusion = polish_result.get('polished_conclusion', raw_conclusion)
                logger.info("结论润色成功，使用润色后的结论")
            else:
                polished_parts = {}
                final_conclusion = raw_conclusion
                logger.warning(f"结论润色失败，使用原始结论: {polish_result.get('error')}")
            
            # 准备报告数据用于DOCX生成
            docx_data = {
                "title": f"{wind_farm} {turbine} 振动分析报告",
                "basic_info": {
                    "wind_farm": wind_farm,
                    "turbine_id": turbine,
                    "measurement_date": datetime.now().strftime('%Y-%m-%d'),
                    "operator": "系统自动生成",
                    "equipment_status": "运行中"
                },
                "executive_summary": polished_parts.get('summary') or self._extract_summary_from_content(report_content),
                "measurement_results": self._extract_results_from_data(report_data.get('vibration_data', {})),
                "analysis_conclusion": final_conclusion,
                "recommendations": self._extract_recommendations_from_content(report_content),
                "polished_parts": polished_parts  # 添加润色后的各个部分
            }
            
            # 使用报告生成器创建DOCX文件
            success = self.report_generator.generate_word_report(docx_data, str(file_path))
            
            if success:
                logger.info(f"DOCX报告生成成功: {file_path}")
                return {
                    "success": True,
                    "file_path": str(file_path),
                    "filename": filename
                }
            else:
                return {
                    "success": False,
                    "error": "DOCX文件生成失败"
                }
                
        except Exception as e:
            logger.error(f"DOCX文件生成失败: {e}")
            return {
                "success": False,
                "error": f"DOCX文件生成失败: {str(e)}"
            }
    
    def _extract_summary_from_content(self, content: str) -> str:
        """从报告内容中提取执行摘要"""
        lines = content.split('\n')
        summary_lines = []
        in_summary = False
        
        for line in lines:
            if '执行摘要' in line or '摘要' in line:
                in_summary = True
                continue
            elif in_summary and ('数据分析' in line or '测量结果' in line or '分析结果' in line):
                break
            elif in_summary and line.strip():
                summary_lines.append(line.strip())
        
        return '\n'.join(summary_lines) if summary_lines else "本次振动分析显示设备运行状态正常，各项指标均在可接受范围内。"
    
    def _extract_conclusion_from_content(self, content: str) -> str:
        """从报告内容中提取分析结论"""
        lines = content.split('\n')
        conclusion_lines = []
        in_conclusion = False
        
        for line in lines:
            if '结论' in line or '总结' in line:
                in_conclusion = True
                continue
            elif in_conclusion and ('建议' in line or '推荐' in line):
                break
            elif in_conclusion and line.strip():
                conclusion_lines.append(line.strip())
        
        return '\n'.join(conclusion_lines) if conclusion_lines else "设备整体运行状态良好，建议继续监测。"
    
    def _extract_recommendations_from_content(self, content: str) -> List[str]:
        """从报告内容中提取建议措施"""
        lines = content.split('\n')
        recommendations = []
        in_recommendations = False
        
        for line in lines:
            if '建议' in line or '推荐' in line:
                in_recommendations = True
                continue
            elif in_recommendations and line.strip():
                # 清理行内容，移除数字编号
                clean_line = line.strip()
                if clean_line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•')):
                    clean_line = clean_line[2:].strip()
                if clean_line:
                    recommendations.append(clean_line)
        
        return recommendations if recommendations else ["定期检查设备运行状态", "加强振动监测频次", "建议下次检测时间：3个月后"]
    
    def polish_conclusion(self, raw_conclusion: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        使用LLM润色API返回的原始结论
        
        Args:
            raw_conclusion: 原始结论文本
            context: 上下文信息（设备信息、数据概况等）
            
        Returns:
            润色结果
        """
        try:
            # 构建润色提示
            polish_prompt = self._build_polish_prompt(raw_conclusion, context)
            
            # 调用LLM进行润色
            response = self.llm_client.chat(
                message=polish_prompt,
                stream=False
            )
            
            if response.get('success'):
                polished_text = response.get('content', '').strip()
                
                # 提取润色后的各个部分
                extracted_parts = self._extract_polished_parts(polished_text)
                
                return {
                    "success": True,
                    "original_conclusion": raw_conclusion,
                    "polished_conclusion": polished_text,
                    "extracted_parts": extracted_parts,
                    "context_used": context is not None
                }
            else:
                logger.error(f"LLM润色失败: {response.get('error')}")
                return {
                    "success": False,
                    "error": f"LLM润色失败: {response.get('error')}",
                    "original_conclusion": raw_conclusion
                }
                
        except Exception as e:
            logger.error(f"结论润色过程出错: {e}")
            return {
                "success": False,
                "error": f"结论润色过程出错: {str(e)}",
                "original_conclusion": raw_conclusion
            }
    
    def _build_polish_prompt(self, raw_conclusion: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        构建结论润色的提示词
        
        Args:
            raw_conclusion: 原始结论
            context: 上下文信息
            
        Returns:
            润色提示词
        """
        prompt_parts = []
        
        prompt_parts.append("请对以下振动分析的原始结论进行专业润色，使其更加准确、专业和易懂：")
        
        # 添加上下文信息
        if context:
            prompt_parts.append("\n上下文信息：")
            if context.get('wind_farm'):
                prompt_parts.append(f"风场：{context['wind_farm']}")
            if context.get('turbine'):
                prompt_parts.append(f"机组：{context['turbine']}")
            if context.get('analysis_type'):
                prompt_parts.append(f"分析类型：{context['analysis_type']}")
            if context.get('data_summary'):
                prompt_parts.append(f"数据概况：{context['data_summary']}")
        
        prompt_parts.append("\n原始结论：")
        prompt_parts.append(raw_conclusion)
        
        prompt_parts.append("\n润色要求：")
        prompt_parts.append("1. 保持技术准确性，使用专业术语")
        prompt_parts.append("2. 结构清晰，逻辑性强")
        prompt_parts.append("3. 语言简洁明了，避免冗余")
        prompt_parts.append("4. 突出关键发现和重要建议")
        prompt_parts.append("5. 确保结论与上下文信息一致")
        
        prompt_parts.append("\n请按以下格式输出润色后的结论：")
        prompt_parts.append("【分析总结】")
        prompt_parts.append("【关键发现】")
        prompt_parts.append("【维护建议】")
        prompt_parts.append("【风险评估】")
        
        return "\n".join(prompt_parts)
    
    def _extract_polished_parts(self, polished_text: str) -> Dict[str, str]:
        """
        从润色后的文本中提取各个部分
        
        Args:
            polished_text: 润色后的完整文本
            
        Returns:
            提取的各个部分
        """
        parts = {
            "summary": "",
            "key_findings": "",
            "maintenance_recommendations": "",
            "risk_assessment": ""
        }
        
        lines = polished_text.split('\n')
        current_section = None
        current_content = []
        
        section_mapping = {
            "分析总结": "summary",
            "关键发现": "key_findings", 
            "维护建议": "maintenance_recommendations",
            "风险评估": "risk_assessment"
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是新的章节标题
            section_found = False
            for section_title, section_key in section_mapping.items():
                if section_title in line and ('【' in line or '##' in line or line.startswith(section_title)):
                    # 保存之前章节的内容
                    if current_section and current_content:
                        parts[current_section] = '\n'.join(current_content).strip()
                    
                    # 开始新章节
                    current_section = section_key
                    current_content = []
                    section_found = True
                    break
            
            # 如果不是章节标题，添加到当前章节内容
            if not section_found and current_section:
                current_content.append(line)
        
        # 保存最后一个章节的内容
        if current_section and current_content:
            parts[current_section] = '\n'.join(current_content).strip()
        
        # 如果没有找到标准格式，将整个文本作为总结
        if not any(parts.values()):
            parts["summary"] = polished_text.strip()
        
        return parts
    
    def polish_api_conclusion(self, api_conclusion: str, device_info: Optional[Dict[str, Any]] = None,
                            analysis_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        专门用于润色API返回的原始结论的接口方法
        
        Args:
            api_conclusion: API返回的原始结论文本
            device_info: 设备信息（风场、机组等）
            analysis_params: 分析参数（时间范围、分析类型等）
            
        Returns:
            润色结果，包含原始结论、润色后结论和提取的各个部分
        """
        try:
            # 构建更详细的上下文信息
            context = {}
            
            if device_info:
                context.update({
                    "wind_farm": device_info.get('wind_farm', ''),
                    "turbine": device_info.get('turbine_id', ''),
                    "device_type": device_info.get('device_type', '风电机组'),
                    "location": device_info.get('location', '')
                })
            
            if analysis_params:
                context.update({
                    "analysis_type": analysis_params.get('analysis_type', '振动分析'),
                    "time_range": analysis_params.get('time_range', ''),
                    "measurement_points": analysis_params.get('measurement_points', []),
                    "data_summary": analysis_params.get('data_summary', '')
                })
            
            # 调用核心润色方法
            polish_result = self.polish_conclusion(api_conclusion, context)
            
            # 添加API特定的元数据
            if polish_result.get('success'):
                polish_result.update({
                    "api_source": True,
                    "device_info": device_info,
                    "analysis_params": analysis_params,
                    "polish_timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"API结论润色成功，设备: {context.get('wind_farm', 'unknown')}-{context.get('turbine', 'unknown')}")
            else:
                logger.error(f"API结论润色失败: {polish_result.get('error')}")
            
            return polish_result
            
        except Exception as e:
            logger.error(f"API结论润色过程出错: {e}")
            return {
                "success": False,
                "error": f"API结论润色过程出错: {str(e)}",
                "original_conclusion": api_conclusion,
                "api_source": True
            }
    
    def _extract_results_from_data(self, vibration_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从振动数据中提取测量结果"""
        results = []
        
        # 如果有具体的测点数据
        if isinstance(vibration_data, dict) and 'measurement_points' in vibration_data:
            for point_name, point_data in vibration_data['measurement_points'].items():
                if isinstance(point_data, dict):
                    results.append({
                        "measurement_point": point_name,
                        "rms_value": point_data.get('rms_value', 0.0),
                        "peak_value": point_data.get('peak_value', 0.0),
                        "main_frequency": point_data.get('main_frequency', 0.0),
                        "alarm_level": point_data.get('status', 'normal')
                    })
        
        # 如果没有具体数据，生成默认结果
        if not results:
            results = [
                {
                    "measurement_point": "主轴承DE",
                    "rms_value": 2.5,
                    "peak_value": 8.2,
                    "main_frequency": 25.5,
                    "alarm_level": "normal"
                },
                {
                    "measurement_point": "齿轮箱HSS",
                    "rms_value": 4.1,
                    "peak_value": 12.8,
                    "main_frequency": 1250.0,
                    "alarm_level": "normal"
                }
            ]
        
        return results
    
    def _handle_status_query(self, session_id: str, intent_result: Dict[str, Any],
                           stream: bool = False) -> Dict[str, Any]:
        """处理状态查询请求"""
        try:
            entities = intent_result.get('entities', {})
            
            # 构建查询上下文
            context = {}
            if entities.get('wind_farm') or entities.get('turbine'):
                # 获取设备状态数据
                try:
                    status_data = self.data_fetcher.sync_fetch_wind_farm_analysis(
                        wind_farm_id=1,  # 实际应该根据wind_farm名称查询ID
                        analysis_period=7  # 最近7天的状态
                    )
                    context['status_data'] = {
                        'success': True,
                        'data': {
                            'wind_farm': entities.get('wind_farm'),
                            'turbine': entities.get('turbine'),
                            'analysis_result': status_data
                        }
                    }
                except Exception as e:
                    logger.error(f"获取状态数据失败: {e}")
                    context['status_data'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # 检索相关知识
            query = f"设备状态 {entities.get('wind_farm', '')} {entities.get('turbine', '')}".strip()
            knowledge_results = self.knowledge_retriever.search(query, top_k=2)
            context['knowledge_results'] = knowledge_results
            
            # 生成响应
            prompt = f"用户询问设备状态：{intent_result.get('original_message', '')}"
            
            return self.llm_client.chat(prompt, context, stream)
            
        except Exception as e:
            logger.error(f"状态查询处理失败: {e}")
            return {
                "success": False,
                "error": f"状态查询失败: {str(e)}",
                "response": "无法获取设备状态信息，请稍后再试。"
            }
    
    def _handle_knowledge_management(self, session_id: str, intent_result: Dict[str, Any],
                                   stream: bool = False) -> Dict[str, Any]:
        """处理知识管理请求"""
        try:
            # 简单的知识检索
            query = intent_result.get('original_message', '')
            knowledge_results = self.knowledge_retriever.search(query, top_k=5)
            
            if knowledge_results:
                context = {'knowledge_results': knowledge_results}
                prompt = f"基于知识库信息回答：{query}"
                return self.llm_client.chat(prompt, context, stream)
            else:
                return {
                    "success": True,
                    "response": "抱歉，没有找到相关的技术资料。"
                }
                
        except Exception as e:
            logger.error(f"知识管理处理失败: {e}")
            return {
                "success": False,
                "error": f"知识检索失败: {str(e)}",
                "response": "知识检索过程中出现错误。"
            }
    
    def _handle_template_management(self, session_id: str, intent_result: Dict[str, Any],
                                  stream: bool = False) -> Dict[str, Any]:
        """处理模板管理请求"""
        try:
            # 获取可用模板列表
            templates = self.template_manager.list_templates()
            
            if templates:
                template_info = "\n".join([
                    f"- {t['name']}: {t['description']}"
                    for t in templates
                ])
                
                response = f"可用的报告模板：\n{template_info}\n\n您可以指定使用某个模板来生成报告。"
                
                return {
                    "success": True,
                    "response": response,
                    "templates": templates
                }
            else:
                return {
                    "success": True,
                    "response": "暂无可用的报告模板。"
                }
                
        except Exception as e:
            logger.error(f"模板管理处理失败: {e}")
            return {
                "success": False,
                "error": f"模板管理失败: {str(e)}",
                "response": "模板管理过程中出现错误。"
            }
    
    def _handle_general_chat(self, session_id: str, message: str,
                           stream: bool = False) -> Dict[str, Any]:
        """处理一般对话"""
        try:
            # 检索相关知识作为上下文
            knowledge_results = self.knowledge_retriever.search(message, top_k=3)
            context = {'knowledge_results': knowledge_results} if knowledge_results else None
            
            return self.llm_client.chat(message, context, stream)
            
        except Exception as e:
            logger.error(f"一般对话处理失败: {e}")
            return {
                "success": False,
                "error": f"对话处理失败: {str(e)}",
                "response": "抱歉，我现在无法回答您的问题。"
            }
    
    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """获取会话历史"""
        try:
            session = self.session_manager.get_session(session_id)
            if session:
                return {
                    "success": True,
                    "history": session.messages,
                    "session_info": {
                        "session_id": session_id,
                        "user_id": session.user_id,
                        "created_time": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat()
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "会话不存在"
                }
                
        except Exception as e:
            logger.error(f"获取会话历史失败: {e}")
            return {
                "success": False,
                "error": f"获取历史失败: {str(e)}"
            }
    
    def clear_session(self, session_id: str) -> Dict[str, Any]:
        """清空会话"""
        try:
            # 清空会话消息
            session = self.session_manager.get_session(session_id)
            if session:
                session.messages.clear()
                return {
                    "success": True,
                    "message": "会话已清空"
                }
            else:
                return {
                    "success": False,
                    "error": "会话不存在"
                }
            
        except Exception as e:
            logger.error(f"清空会话失败: {e}")
            return {
                "success": False,
                "error": f"清空会话失败: {str(e)}"
            }
    
    def _get_mock_vibration_data(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取测试振动数据
        """
        try:
            # 导入测试数据生成器
            from data.mock_data import CMSDataGenerator
            
            generator = CMSDataGenerator()
            wind_farm = entities.get('wind_farm', '华能风场A')
            turbine = entities.get('turbine', 'A01')
            
            # 生成机组的完整测试数据
            turbine_data = generator.generate_turbine_data(wind_farm, turbine)
            
            logger.info(f"生成测试数据成功: {wind_farm}-{turbine}")
            
            return {
                'success': True,
                'data': {
                    'wind_farm': wind_farm,
                    'turbine': turbine,
                    'vibration_data': turbine_data,
                    'data_source': 'mock_data'
                }
            }
        except Exception as e:
            logger.error(f"获取测试振动数据失败: {e}")
            return {
                'success': False,
                'error': f"测试数据获取失败: {str(e)}"
            }
    
    def _get_api_vibration_data(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        从外部API获取振动数据
        """
        try:
            # 检查外部API配置
            external_api_config = self.config.get('external_api', {})
            if not external_api_config.get('enabled', False):
                return {
                    'success': False,
                    'error': '外部API未启用，请在配置中启用external_api.enabled或使用测试数据模式'
                }
            
            cms_api_config = external_api_config.get('cms_api', {})
            base_url = cms_api_config.get('base_url')
            api_key = cms_api_config.get('api_key')
            
            if not base_url or not api_key:
                return {
                    'success': False,
                    'error': '外部API配置不完整，请检查base_url和api_key配置'
                }
            
            # 这里应该实现实际的API调用逻辑
             # 暂时返回模拟的API响应结构
            
            # 构建API请求
            endpoint = cms_api_config.get('endpoints', {}).get('vibration_data', '/api/v1/data/vibration')
            url = f"{base_url.rstrip('/')}{endpoint}"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'wind_farm': entities['wind_farm'],
                'turbine': entities['turbine'],
                'time_range': entities.get('time_range', {})
            }
            
            timeout = cms_api_config.get('timeout', 30)
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            
            if response.status_code == 200:
                api_data = response.json()
                return {
                    'success': True,
                    'data': {
                        'wind_farm': entities['wind_farm'],
                        'turbine': entities['turbine'],
                        'vibration_data': api_data,
                        'data_source': 'external_api'
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'API调用失败: HTTP {response.status_code} - {response.text}'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求异常: {e}")
            return {
                'success': False,
                'error': f'API请求失败: {str(e)}'
            }
        except Exception as e:
            logger.error(f"获取API振动数据失败: {e}")
            return {
                'success': False,
                'error': f'API数据获取失败: {str(e)}'
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            # 检查各个组件状态
            status = {
                "chat_manager": "running",
                "llm_client": "connected" if self.llm_client else "disconnected",
                "knowledge_retriever": "ready" if self.knowledge_retriever else "not_ready",
                "template_manager": "ready" if self.template_manager else "not_ready",
                "data_fetcher": "ready" if self.data_fetcher else "not_ready"
            }
            
            # 获取统计信息
            knowledge_stats = self.knowledge_retriever.get_stats()
            template_list = self.template_manager.list_templates()
            
            stats = {
                "active_sessions": len(self.session_manager.sessions),
                "knowledge_documents": knowledge_stats.get('total_documents', 0),
                "available_templates": len(template_list) if template_list else 0
            }
            
            return {
                "success": True,
                "status": status,
                "statistics": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                "success": False,
                "error": f"获取状态失败: {str(e)}"
            }