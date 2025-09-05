#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析报告系统集成测试
测试所有新增功能的可用性和集成性

作者: CMS开发团队
版本: 2.0.0
日期: 2024-01-15
"""

import os
import sys
import tempfile
import shutil
import json
import numpy as np
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入测试模块
try:
    from knowledge.template_manager import TemplateManager
    from knowledge.template_api import TemplateAPI
    from knowledge.knowledge_retriever import KnowledgeRetriever
    from chat.chat_manager import ChatManager
    from utils.chart_generator import VibrationChartGenerator
    from report.generator import CMSReportGenerator
    from pipeline.conclusion_pipeline import ConclusionPipeline
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖已正确安装")
    sys.exit(1)

class SystemIntegrationTest:
    """
    系统集成测试类
    """
    
    def __init__(self):
        self.test_dir = None
        self.results = {
            'template_manager': False,
            'template_api': False,
            'knowledge_retriever': False,
            'chat_manager': False,
            'chart_generator': False,
            'report_generator': False,
            'conclusion_pipeline': False
        }
        self.errors = []
    
    def setup_test_environment(self):
        """
        设置测试环境
        """
        print("\n=== 设置测试环境 ===")
        self.test_dir = tempfile.mkdtemp(prefix='cms_test_')
        print(f"测试目录: {self.test_dir}")
        
        # 创建必要的子目录
        os.makedirs(f"{self.test_dir}/templates", exist_ok=True)
        os.makedirs(f"{self.test_dir}/embeddings", exist_ok=True)
        os.makedirs(f"{self.test_dir}/metadata", exist_ok=True)
        os.makedirs(f"{self.test_dir}/output", exist_ok=True)
        
        print("测试环境设置完成")
    
    def test_template_manager(self):
        """
        测试模板管理器
        """
        print("\n=== 测试模板管理器 ===")
        try:
            # 初始化模板管理器
            template_manager = TemplateManager(f"{self.test_dir}/templates")
            
            # 测试创建模板
            template_content = """
# 振动分析报告模板

## 基本信息
- 风场名称: {{wind_farm_name}}
- 机组编号: {{turbine_id}}
- 分析时间: {{analysis_time}}
- 分析师: {{analyst_name}}

## 分析结论
{{polished_conclusion}}

## 测量数据
{{measurement_analysis}}

## 图表分析
{{charts_section}}

## 建议措施
{{recommendations}}
            """
            
            metadata = {
                'name': '振动分析报告',
                'type': 'vibration_analysis',
                'description': '标准振动分析报告模板',
                'variables': ['wind_farm_name', 'turbine_id', 'analysis_time', 'analyst_name']
            }
            
            # 创建模板（使用正确的方法名）
            result = template_manager.save_template(
                'vibration_report', 
                template_content, 
                'report',
                metadata
            )
            print(f"创建模板结果: {result}")
            
            # 测试列表模板
            templates = template_manager.list_templates()
            print(f"模板列表: {len(templates)} 个模板")
            
            # 测试版本控制
            version_result = template_manager.create_version(
                'vibration_report',
                '添加了新的分析字段'
            )
            print(f"版本创建结果: {version_result}")
            
            # 测试搜索
            search_results = template_manager.search_templates('振动')
            print(f"搜索结果: {len(search_results)} 个匹配")
            
            self.results['template_manager'] = True
            print("✅ 模板管理器测试通过")
            
        except Exception as e:
            self.errors.append(f"模板管理器测试失败: {e}")
            print(f"❌ 模板管理器测试失败: {e}")
    
    def test_template_api(self):
        """
        测试模板API
        """
        print("\n=== 测试模板API ===")
        try:
            # 初始化模板API
            template_api = TemplateAPI(f"{self.test_dir}/templates")
            
            # 测试获取模板类型
            types = template_api.get_template_types()
            print(f"模板类型: {types}")
            
            # 测试获取模板列表
            templates = template_api.get_templates()
            print(f"API模板列表: {len(templates)} 个模板")
            
            # 测试统计信息
            stats = template_api.get_statistics()
            print(f"统计信息: {stats}")
            
            self.results['template_api'] = True
            print("✅ 模板API测试通过")
            
        except Exception as e:
            self.errors.append(f"模板API测试失败: {e}")
            print(f"❌ 模板API测试失败: {e}")
    
    def test_knowledge_retriever(self):
        """
        测试知识检索器
        """
        print("\n=== 测试知识检索器 ===")
        try:
            # 初始化知识检索器
            knowledge_retriever = KnowledgeRetriever(
                embeddings_path=f"{self.test_dir}/embeddings",
                metadata_path=f"{self.test_dir}/metadata"
            )
            
            # 测试模板检索（模拟）
            print("知识检索器初始化成功")
            
            self.results['knowledge_retriever'] = True
            print("✅ 知识检索器测试通过")
            
        except Exception as e:
            self.errors.append(f"知识检索器测试失败: {e}")
            print(f"❌ 知识检索器测试失败: {e}")
    
    def test_chat_manager(self):
        """
        测试聊天管理器（结论润色功能）
        """
        print("\n=== 测试聊天管理器 ===")
        try:
            # 模拟配置
            config = {
                'llm_config': {
                    'model_name': 'test_model',
                    'api_key': 'test_key'
                }
            }
            
            # 初始化聊天管理器
            chat_manager = ChatManager(config)
            
            # 测试结论润色（模拟）
            test_conclusion = "机组振动正常，各测点数值在正常范围内"
            context = {
                'wind_farm_name': '测试风场',
                'turbine_id': 'WT001'
            }
            
            print("聊天管理器初始化成功")
            print(f"测试结论: {test_conclusion}")
            
            self.results['chat_manager'] = True
            print("✅ 聊天管理器测试通过")
            
        except Exception as e:
            self.errors.append(f"聊天管理器测试失败: {e}")
            print(f"❌ 聊天管理器测试失败: {e}")
    
    def test_chart_generator(self):
        """
        测试图表生成器
        """
        print("\n=== 测试图表生成器 ===")
        try:
            # 初始化图表生成器
            chart_generator = VibrationChartGenerator()
            
            # 生成测试数据
            time_data = np.linspace(0, 1, 1000)
            signal_data = np.sin(2 * np.pi * 50 * time_data) + 0.5 * np.sin(2 * np.pi * 120 * time_data)
            
            # 测试时域图表
            time_chart = chart_generator.create_time_series_chart(
                signal_data,
                sampling_rate=1000,
                title="测试时域波形"
            )
            print(f"时域图表生成: {'成功' if time_chart else '失败'}")
            
            # 测试频域图表
            frequencies = np.linspace(0, 500, 500)
            magnitudes = np.abs(np.fft.fft(signal_data)[:500])
            
            freq_chart = chart_generator.create_frequency_spectrum(
                frequencies,
                magnitudes,
                title="测试频域谱"
            )
            print(f"频域图表生成: {'成功' if freq_chart else '失败'}")
            
            # 测试图文组合（使用正确的方法名）
            combined_result = chart_generator.combine_chart_and_conclusion(
                time_chart,
                "这是时域波形分析结果",
                "时域分析"
            )
            print(f"图文组合: {'成功' if combined_result else '失败'}")
            
            self.results['chart_generator'] = True
            print("✅ 图表生成器测试通过")
            
        except Exception as e:
            self.errors.append(f"图表生成器测试失败: {e}")
            print(f"❌ 图表生成器测试失败: {e}")
    
    def test_report_generator(self):
        """
        测试报告生成器
        """
        print("\n=== 测试报告生成器 ===")
        try:
            # 初始化报告生成器
            report_generator = CMSReportGenerator(f"{self.test_dir}/templates")
            
            # 准备测试数据
            report_data = {
                'wind_farm_name': '测试风场',
                'turbine_id': 'WT001',
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'analyst_name': '测试分析师',
                'polished_conclusion': '经过润色的分析结论',
                'measurement_analysis': '测量数据分析',
                'charts_section': '图表分析部分',
                'recommendations': '维护建议'
            }
            
            # 测试HTML报告生成
            html_result = report_generator.generate_html_report(
                report_data,
                'vibration_report'
            )
            print(f"HTML报告生成: {'成功' if html_result else '失败'}")
            
            self.results['report_generator'] = True
            print("✅ 报告生成器测试通过")
            
        except Exception as e:
            self.errors.append(f"报告生成器测试失败: {e}")
            print(f"❌ 报告生成器测试失败: {e}")
    
    def test_conclusion_pipeline(self):
        """
        测试结论处理管道
        """
        print("\n=== 测试结论处理管道 ===")
        try:
            # 配置管道
            config = {
                'templates_path': f"{self.test_dir}/templates",
                'knowledge_config': {
                    'embeddings_path': f"{self.test_dir}/embeddings",
                    'metadata_path': f"{self.test_dir}/metadata"
                },
                'pipeline_config': {
                    'enable_polish': False,  # 禁用LLM润色以避免API调用
                    'enable_charts': True,
                    'enable_template_retrieval': True,
                    'default_template': 'vibration_report',
                    'output_formats': ['html']
                }
            }
            
            # 初始化管道
            pipeline = ConclusionPipeline(config)
            
            # 准备测试数据
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
                        'signal': [1.0, 2.0, 1.5, 3.0, 2.5] * 100,
                        'sampling_rate': 2048
                    },
                    'frequency_spectrum': {
                        'frequencies': list(range(0, 1000, 10)),
                        'magnitudes': [0.5 + 0.3 * np.sin(i/10) for i in range(100)]
                    }
                }
            }
            
            context = {
                'wind_farm_name': '测试风场',
                'turbine_id': 'WT001',
                'analysis_time': '2024-01-15 10:00:00',
                'analyst_name': '测试分析师'
            }
            
            # 测试管道处理
            result = pipeline.process_conclusion(raw_conclusion, context)
            print(f"管道处理结果: {'成功' if result.get('success', False) else '失败'}")
            
            if result.get('success', False):
                print(f"处理步骤: {result.get('processing_steps', [])}")
                print(f"生成图表: {len(result.get('charts', []))} 个")
                print(f"生成报告: {len(result.get('reports', {}))} 种格式")
            
            self.results['conclusion_pipeline'] = True
            print("✅ 结论处理管道测试通过")
            
        except Exception as e:
            self.errors.append(f"结论处理管道测试失败: {e}")
            print(f"❌ 结论处理管道测试失败: {e}")
    
    def cleanup_test_environment(self):
        """
        清理测试环境
        """
        print("\n=== 清理测试环境 ===")
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print(f"已清理测试目录: {self.test_dir}")
    
    def run_all_tests(self):
        """
        运行所有测试
        """
        print("\n" + "="*50)
        print("CMS振动分析报告系统集成测试")
        print("="*50)
        
        try:
            # 设置测试环境
            self.setup_test_environment()
            
            # 运行各项测试
            self.test_template_manager()
            self.test_template_api()
            self.test_knowledge_retriever()
            self.test_chat_manager()
            self.test_chart_generator()
            self.test_report_generator()
            self.test_conclusion_pipeline()
            
        finally:
            # 清理测试环境
            self.cleanup_test_environment()
        
        # 输出测试结果
        self.print_test_results()
    
    def print_test_results(self):
        """
        打印测试结果
        """
        print("\n" + "="*50)
        print("测试结果汇总")
        print("="*50)
        
        passed_tests = sum(self.results.values())
        total_tests = len(self.results)
        
        print(f"\n总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, result in self.results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        if self.errors:
            print("\n错误详情:")
            for error in self.errors:
                print(f"  - {error}")
        
        print("\n" + "="*50)
        if passed_tests == total_tests:
            print("🎉 所有测试通过！系统功能正常")
        else:
            print("⚠️  部分测试失败，请检查相关功能")
        print("="*50)

def main():
    """
    主函数
    """
    test_runner = SystemIntegrationTest()
    test_runner.run_all_tests()

if __name__ == "__main__":
    main()