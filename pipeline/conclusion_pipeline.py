# -*- coding: utf-8 -*-
"""
结论处理管道 - 完整的API结论到报告集成流程
"""

import os
import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# 导入相关模块
try:
    from ..chat.chat_manager import ChatManager
    from ..knowledge.knowledge_retriever import KnowledgeRetriever
    from ..knowledge.template_api import TemplateAPI
    from ..utils.chart_generator import VibrationChartGenerator
    from ..report.generator import CMSReportGenerator
except ImportError:
    # 用于测试时的导入
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from chat.chat_manager import ChatManager
    from knowledge.knowledge_retriever import KnowledgeRetriever
    from knowledge.template_api import TemplateAPI
    from utils.chart_generator import VibrationChartGenerator
    from report.generator import CMSReportGenerator

logger = logging.getLogger(__name__)

class ConclusionPipeline:
    """
    结论处理管道 - 完整的API结论到报告集成流程
    
    主要功能：
    1. 接收原始API分析结论
    2. 通过LLM进行结论润色
    3. 生成相关图表
    4. 检索合适的报告模板
    5. 生成最终报告
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化结论处理管道
        
        Args:
            config: 配置参数，包含各组件的配置
        """
        self.config = config
        
        # 初始化各组件
        self.chat_manager = ChatManager(config.get('chat_config', {}))
        knowledge_config = config.get('knowledge_config', {})
        self.knowledge_retriever = KnowledgeRetriever(
            embeddings_path=knowledge_config.get('embeddings_path', 'embeddings'),
            metadata_path=knowledge_config.get('metadata_path', 'metadata')
        )
        self.template_api = TemplateAPI(config.get('templates_path', './knowledge/report_templates'))
        self.chart_generator = VibrationChartGenerator()
        self.report_generator = CMSReportGenerator(config.get('report_config', {}).get('template_storage_path'))
        
        # 管道配置
        self.pipeline_config = config.get('pipeline_config', {
            'enable_polish': True,
            'enable_charts': True,
            'enable_template_retrieval': True,
            'default_template': '振动分析报告',
            'output_formats': ['pdf', 'docx', 'html']
        })
        
        logger.info("结论处理管道初始化完成")
    
    def process_conclusion(self, raw_conclusion: Dict[str, Any], 
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理原始结论，生成完整报告
        
        Args:
            raw_conclusion: 原始API分析结论
            context: 上下文信息（风场、机组等）
            
        Returns:
            处理结果，包含润色结论、图表、报告等
        """
        try:
            logger.info("开始处理结论")
            
            # 初始化结果
            result = {
                'success': True,
                'raw_conclusion': raw_conclusion,
                'context': context or {},
                'polished_conclusion': None,
                'charts': [],
                'template_info': None,
                'reports': {},
                'processing_steps': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # 步骤1: 结论润色
            if self.pipeline_config.get('enable_polish', True):
                polish_result = self._polish_conclusion(raw_conclusion, context)
                result['polished_conclusion'] = polish_result
                result['processing_steps'].append('conclusion_polish')
                logger.info("结论润色完成")
            else:
                result['polished_conclusion'] = raw_conclusion
            
            # 步骤2: 生成图表
            if self.pipeline_config.get('enable_charts', True):
                charts_result = self._generate_charts(raw_conclusion, context)
                result['charts'] = charts_result
                result['processing_steps'].append('chart_generation')
                logger.info(f"图表生成完成，共生成{len(charts_result)}个图表")
            
            # 步骤3: 检索模板
            if self.pipeline_config.get('enable_template_retrieval', True):
                template_result = self._retrieve_template(raw_conclusion, context)
                result['template_info'] = template_result
                result['processing_steps'].append('template_retrieval')
                logger.info(f"模板检索完成: {template_result.get('template_name', 'N/A')}")
            
            # 步骤4: 生成报告
            reports_result = self._generate_reports(result)
            result['reports'] = reports_result
            result['processing_steps'].append('report_generation')
            logger.info(f"报告生成完成，格式: {list(reports_result.keys())}")
            
            logger.info("结论处理完成")
            return result
            
        except Exception as e:
            logger.error(f"结论处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'raw_conclusion': raw_conclusion,
                'context': context or {},
                'timestamp': datetime.now().isoformat()
            }
    
    def _polish_conclusion(self, raw_conclusion: Dict[str, Any], 
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        润色原始结论
        
        Args:
            raw_conclusion: 原始结论
            context: 上下文信息
            
        Returns:
            润色后的结论
        """
        try:
            # 构建润色请求
            polish_request = {
                'raw_conclusion': raw_conclusion,
                'context': context or {},
                'polish_type': 'vibration_analysis',
                'requirements': {
                    'professional': True,
                    'detailed': True,
                    'actionable': True
                }
            }
            
            # 调用ChatManager进行润色
            conclusion_text = str(raw_conclusion.get('conclusion', raw_conclusion))
            polish_result = self.chat_manager.polish_conclusion(conclusion_text, context)
            
            if polish_result.get('success', False):
                return {
                    'success': True,
                    'polished_text': polish_result.get('polished_conclusion', ''),
                    'improvements': polish_result.get('improvements', []),
                    'confidence': polish_result.get('confidence', 0.8)
                }
            else:
                logger.warning(f"结论润色失败: {polish_result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'error': polish_result.get('error', 'Polish failed'),
                    'fallback_text': str(raw_conclusion)
                }
                
        except Exception as e:
            logger.error(f"结论润色异常: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_text': str(raw_conclusion)
            }
    
    def _generate_charts(self, raw_conclusion: Dict[str, Any], 
                        context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        生成相关图表
        
        Args:
            raw_conclusion: 原始结论
            context: 上下文信息
            
        Returns:
            生成的图表列表
        """
        charts = []
        
        try:
            # 从结论中提取数据
            analysis_data = raw_conclusion.get('analysis_data', {})
            
            # 生成时域图表
            if 'time_series' in analysis_data:
                signal_data = analysis_data['time_series']
                if isinstance(signal_data, dict):
                    signal = signal_data.get('signal', [])
                    sampling_rate = signal_data.get('sampling_rate', 2048)
                else:
                    signal = signal_data
                    sampling_rate = 2048
                
                if len(signal) > 0:
                    time_chart = self.chart_generator.create_time_series_chart(
                        np.array(signal),
                        sampling_rate=sampling_rate,
                        title="时域波形分析"
                    )
                    if time_chart:
                        charts.append({
                            'type': 'time_series',
                            'title': '时域波形分析',
                            'image': time_chart,
                            'description': '机组振动时域波形图'
                        })
            
            # 生成频域图表
            if 'frequency_spectrum' in analysis_data:
                freq_data = analysis_data['frequency_spectrum']
                if isinstance(freq_data, dict):
                    frequencies = np.array(freq_data.get('frequencies', []))
                    magnitudes = np.array(freq_data.get('magnitudes', []))
                else:
                    # 如果是简单数组，生成频率轴
                    magnitudes = np.array(freq_data)
                    frequencies = np.linspace(0, 1000, len(magnitudes))
                
                if len(frequencies) > 0 and len(magnitudes) > 0:
                    freq_chart = self.chart_generator.create_frequency_spectrum(
                        frequencies,
                        magnitudes,
                        title="频域谱分析"
                    )
                    if freq_chart:
                        charts.append({
                            'type': 'frequency_spectrum',
                            'title': '频域谱分析',
                            'image': freq_chart,
                            'description': '机组振动频域谱图'
                        })
            
            # 生成趋势图表
            if 'trend_data' in analysis_data:
                trend_chart = self.chart_generator.create_trend_chart(
                    analysis_data['trend_data'],
                    title="振动趋势分析"
                )
                if trend_chart:
                    charts.append({
                        'type': 'trend',
                        'title': '振动趋势分析',
                        'image': trend_chart,
                        'description': '机组振动趋势变化图'
                    })
            
            # 生成轴承分析图表
            if 'bearing_analysis' in analysis_data:
                bearing_chart = self.chart_generator.create_bearing_analysis_chart(
                    analysis_data['bearing_analysis'],
                    title="轴承诊断分析"
                )
                if bearing_chart:
                    charts.append({
                        'type': 'bearing_analysis',
                        'title': '轴承诊断分析',
                        'image': bearing_chart,
                        'description': '轴承状态诊断图'
                    })
            
            logger.info(f"成功生成{len(charts)}个图表")
            
        except Exception as e:
            logger.error(f"图表生成异常: {e}")
        
        return charts
    
    def _retrieve_template(self, raw_conclusion: Dict[str, Any], 
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        检索合适的报告模板
        
        Args:
            raw_conclusion: 原始结论
            context: 上下文信息
            
        Returns:
            模板信息
        """
        try:
            # 分析结论类型
            conclusion_type = self._analyze_conclusion_type(raw_conclusion)
            
            # 构建检索查询
            query_terms = []
            
            # 添加结论类型相关词汇
            if conclusion_type == 'alarm':
                query_terms.extend(['报警', '异常', '故障'])
            elif conclusion_type == 'maintenance':
                query_terms.extend(['维护', '保养', '建议'])
            elif conclusion_type == 'trend':
                query_terms.extend(['趋势', '变化', '监测'])
            else:
                query_terms.extend(['振动', '分析', '报告'])
            
            # 添加上下文相关词汇
            if context:
                if 'turbine_type' in context:
                    query_terms.append(context['turbine_type'])
                if 'analysis_type' in context:
                    query_terms.append(context['analysis_type'])
            
            # 搜索模板
            search_query = ' '.join(query_terms)
            search_results = self.template_api.search_templates(search_query)
            
            if search_results:
                # 选择匹配度最高的模板
                best_template = search_results[0]
                template_content = self.template_api.get_template_content(best_template['template_name'])
                
                return {
                    'success': True,
                    'template_name': best_template['template_name'],
                    'template_type': best_template['template_type'],
                    'match_score': best_template['match_score'],
                    'template_content': template_content.get('content', ''),
                    'variables': template_content.get('metadata', {}).get('variables', [])
                }
            else:
                # 使用默认模板
                default_template = self.pipeline_config.get('default_template', '振动分析报告')
                template_content = self.template_api.get_template_content(default_template)
                
                return {
                    'success': True,
                    'template_name': default_template,
                    'template_type': 'report',
                    'match_score': 0,
                    'template_content': template_content.get('content', ''),
                    'variables': template_content.get('metadata', {}).get('variables', []),
                    'is_default': True
                }
                
        except Exception as e:
            logger.error(f"模板检索异常: {e}")
            return {
                'success': False,
                'error': str(e),
                'template_name': None
            }
    
    def _analyze_conclusion_type(self, raw_conclusion: Dict[str, Any]) -> str:
        """
        分析结论类型
        
        Args:
            raw_conclusion: 原始结论
            
        Returns:
            结论类型
        """
        conclusion_text = str(raw_conclusion).lower()
        
        # 关键词匹配
        if any(word in conclusion_text for word in ['报警', '异常', '故障', '超标', '警告']):
            return 'alarm'
        elif any(word in conclusion_text for word in ['维护', '保养', '建议', '检修', '更换']):
            return 'maintenance'
        elif any(word in conclusion_text for word in ['趋势', '变化', '监测', '跟踪']):
            return 'trend'
        else:
            return 'analysis'
    
    def _generate_reports(self, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成最终报告
        
        Args:
            pipeline_result: 管道处理结果
            
        Returns:
            生成的报告
        """
        reports = {}
        
        try:
            # 准备报告数据
            report_data = self._prepare_report_data(pipeline_result)
            
            # 获取模板信息
            template_info = pipeline_result.get('template_info', {})
            template_name = template_info.get('template_name', self.pipeline_config.get('default_template', '振动分析报告'))
            
            # 生成不同格式的报告
            output_formats = self.pipeline_config.get('output_formats', ['pdf', 'docx', 'html'])
            
            for format_type in output_formats:
                try:
                    # 根据格式调用相应的生成方法
                    report_result = None
                    if format_type == 'pdf':
                        report_result = self.report_generator.generate_pdf_report(report_data, template_name)
                    elif format_type == 'docx':
                        report_result = self.report_generator.generate_docx_report(report_data, template_name)
                    elif format_type == 'html':
                        report_result = self.report_generator.generate_html_report(report_data, template_name)
                    else:
                        continue
                    
                    # 处理可能的布尔返回值或字典返回值
                    if isinstance(report_result, dict):
                        if report_result.get('success', False):
                            reports[format_type] = {
                                'success': True,
                                'file_path': report_result.get('file_path', ''),
                                'file_size': report_result.get('file_size', 0)
                            }
                        else:
                            reports[format_type] = {
                                'success': False,
                                'error': report_result.get('error', 'Generation failed')
                            }
                    elif isinstance(report_result, bool):
                        reports[format_type] = {
                            'success': report_result,
                            'file_path': '' if not report_result else f'{format_type}_report',
                            'file_size': 0,
                            'error': 'Generation failed' if not report_result else None
                        }
                    else:
                        reports[format_type] = {
                            'success': False,
                            'error': 'Invalid return type from report generator'
                        }
                        
                except Exception as e:
                    logger.error(f"生成{format_type}报告失败: {e}")
                    reports[format_type] = {
                        'success': False,
                        'error': str(e)
                    }
            
        except Exception as e:
            logger.error(f"报告生成异常: {e}")
            return {'error': str(e)}
        
        return reports
    
    def _prepare_report_data(self, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备报告数据
        
        Args:
            pipeline_result: 管道处理结果
            
        Returns:
            报告数据
        """
        # 基本信息
        context = pipeline_result.get('context', {})
        
        # 润色后的结论
        polished_conclusion = pipeline_result.get('polished_conclusion', {})
        conclusion_text = polished_conclusion.get('polished_text', '') or polished_conclusion.get('fallback_text', '')
        
        # 图表信息
        charts = pipeline_result.get('charts', [])
        
        # 构建报告数据
        report_data = {
            # 基本信息
            'wind_farm_name': context.get('wind_farm_name', '未知风场'),
            'turbine_id': context.get('turbine_id', '未知机组'),
            'analysis_time': context.get('analysis_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'analyst_name': context.get('analyst_name', '系统自动分析'),
            
            # 分析结论
            'analysis_summary': conclusion_text,
            'detailed_analysis': conclusion_text,
            'measurement_points_analysis': self._extract_measurement_analysis(pipeline_result),
            
            # 图表
            'trend_charts': [chart['image'] for chart in charts if chart['type'] == 'trend'],
            'spectrum_charts': [chart['image'] for chart in charts if chart['type'] == 'frequency_spectrum'],
            'time_series_charts': [chart['image'] for chart in charts if chart['type'] == 'time_series'],
            
            # 其他信息
            'alarm_info': self._extract_alarm_info(pipeline_result),
            'maintenance_recommendations': self._extract_maintenance_recommendations(pipeline_result),
            'trend_analysis': self._extract_trend_analysis(pipeline_result)
        }
        
        return report_data
    
    def _extract_measurement_analysis(self, pipeline_result: Dict[str, Any]) -> str:
        """
        提取测点分析信息
        """
        raw_conclusion = pipeline_result.get('raw_conclusion', {})
        measurement_data = raw_conclusion.get('measurement_points', {})
        
        if not measurement_data:
            return "暂无测点分析数据"
        
        analysis_parts = []
        for point_name, point_data in measurement_data.items():
            if isinstance(point_data, dict):
                status = point_data.get('status', '正常')
                value = point_data.get('value', 'N/A')
                analysis_parts.append(f"- {point_name}: {status} (当前值: {value})")
        
        return '\n'.join(analysis_parts) if analysis_parts else "暂无测点分析数据"
    
    def _extract_alarm_info(self, pipeline_result: Dict[str, Any]) -> str:
        """
        提取报警信息
        """
        raw_conclusion = pipeline_result.get('raw_conclusion', {})
        alarms = raw_conclusion.get('alarms', [])
        
        if not alarms:
            return "无报警信息"
        
        alarm_parts = []
        for alarm in alarms:
            if isinstance(alarm, dict):
                level = alarm.get('level', '未知')
                message = alarm.get('message', '无描述')
                alarm_parts.append(f"- [{level}] {message}")
            else:
                alarm_parts.append(f"- {alarm}")
        
        return '\n'.join(alarm_parts)
    
    def _extract_maintenance_recommendations(self, pipeline_result: Dict[str, Any]) -> str:
        """
        提取维护建议
        """
        polished_conclusion = pipeline_result.get('polished_conclusion', {})
        improvements = polished_conclusion.get('improvements', [])
        
        if improvements:
            return '\n'.join([f"- {improvement}" for improvement in improvements])
        
        # 从原始结论中提取
        raw_conclusion = pipeline_result.get('raw_conclusion', {})
        recommendations = raw_conclusion.get('recommendations', [])
        
        if recommendations:
            return '\n'.join([f"- {rec}" for rec in recommendations])
        
        return "建议继续监测，定期检查设备状态"
    
    def _extract_trend_analysis(self, pipeline_result: Dict[str, Any]) -> str:
        """
        提取趋势分析
        """
        raw_conclusion = pipeline_result.get('raw_conclusion', {})
        trend_info = raw_conclusion.get('trend_analysis', {})
        
        if not trend_info:
            return "暂无趋势分析数据"
        
        trend_parts = []
        if 'direction' in trend_info:
            trend_parts.append(f"趋势方向: {trend_info['direction']}")
        if 'rate' in trend_info:
            trend_parts.append(f"变化速率: {trend_info['rate']}")
        if 'prediction' in trend_info:
            trend_parts.append(f"预测结果: {trend_info['prediction']}")
        
        return '\n'.join(trend_parts) if trend_parts else "暂无趋势分析数据"
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        获取管道状态信息
        
        Returns:
            管道状态
        """
        return {
            'pipeline_config': self.pipeline_config,
            'components_status': {
                'chat_manager': bool(self.chat_manager),
                'knowledge_retriever': bool(self.knowledge_retriever),
                'template_api': bool(self.template_api),
                'chart_generator': bool(self.chart_generator),
                'report_generator': bool(self.report_generator)
            },
            'template_statistics': self.template_api.get_statistics()
        }


if __name__ == "__main__":
    # 测试结论处理管道
    import tempfile
    import shutil
    
    # 创建临时目录
    test_dir = tempfile.mkdtemp()
    print(f"测试目录: {test_dir}")
    
    try:
        # 配置
        config = {
            'templates_path': f"{test_dir}/templates",
            'pipeline_config': {
                'enable_polish': True,
                'enable_charts': True,
                'enable_template_retrieval': True,
                'default_template': '振动分析报告',
                'output_formats': ['html']
            }
        }
        
        # 初始化管道
        pipeline = ConclusionPipeline(config)
        
        # 模拟原始结论
        raw_conclusion = {
            'analysis_type': 'vibration_analysis',
            'conclusion': '机组振动正常，各测点数值在正常范围内',
            'measurement_points': {
                '1X水平': {'status': '正常', 'value': '2.5 mm/s'},
                '1X垂直': {'status': '正常', 'value': '1.8 mm/s'}
            },
            'alarms': [],
            'recommendations': ['继续监测', '定期检查'],
            'analysis_data': {
                'time_series': {
                    'signal': [1.0, 2.0, 1.5, 3.0, 2.5] * 100,  # 模拟时域信号
                    'sampling_rate': 2048
                },
                'frequency_spectrum': {
                    'frequencies': list(range(0, 1000, 10)),
                    'magnitudes': [0.5 + 0.3 * np.sin(i/10) for i in range(100)]
                }
            }
        }
        
        # 上下文信息
        context = {
            'wind_farm_name': '测试风场',
            'turbine_id': 'WT001',
            'analysis_time': '2024-01-15 10:00:00',
            'analyst_name': '测试分析师'
        }
        
        # 处理结论
        print("\n=== 开始处理结论 ===")
        result = pipeline.process_conclusion(raw_conclusion, context)
        
        if result['success']:
            print("处理成功！")
            print(f"处理步骤: {result['processing_steps']}")
            print(f"生成图表数量: {len(result['charts'])}")
            print(f"使用模板: {result['template_info'].get('template_name', 'N/A')}")
            print(f"生成报告格式: {list(result['reports'].keys())}")
        else:
            print(f"处理失败: {result['error']}")
        
        # 获取管道状态
        print("\n=== 管道状态 ===")
        status = pipeline.get_pipeline_status()
        print(f"组件状态: {status['components_status']}")
        
        print("\n=== 测试完成 ===")
        
    finally:
        # 清理测试目录
        shutil.rmtree(test_dir)
        print(f"已清理测试目录: {test_dir}")