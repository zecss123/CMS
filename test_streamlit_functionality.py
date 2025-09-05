#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit应用功能测试脚本
测试所有核心功能模块的可用性和正确性
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

class StreamlitFunctionalityTester:
    def __init__(self):
        self.test_results = []
        self.base_url = "http://localhost:8501"
        
    def log_test(self, test_name: str, status: str, message: str):
        """记录测试结果"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": timestamp
        }
        self.test_results.append(result)
        
        # 输出到控制台
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {test_name}: {message}")
    
    def test_server_connectivity(self) -> bool:
        """测试Streamlit服务器连接性"""
        print("\n📋 执行: 服务器连接性测试")
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                self.log_test("服务器连接性", "PASS", "Streamlit应用正常运行")
                return True
            else:
                self.log_test("服务器连接性", "FAIL", f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("服务器连接性", "FAIL", f"连接失败: {str(e)}")
            return False
    
    def test_file_structure(self) -> bool:
        """测试文件结构完整性"""
        print("\n📋 执行: 文件结构完整性测试")
        required_files = [
            "streamlit_app.py",
            "config.yaml",
            "chat/chat_manager.py",
            "chat/session_manager.py",
            "knowledge/knowledge_manager.py",
            "report/generator.py",
            "utils/chart_generator.py",
            "utils/data_processor.py",
            "data/mock_data.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if not missing_files:
            self.log_test("文件结构完整性", "PASS", f"所有{len(required_files)}个核心文件存在")
            return True
        else:
            self.log_test("文件结构完整性", "FAIL", f"缺失文件: {', '.join(missing_files)}")
            return False
    
    def test_module_imports(self) -> bool:
        """测试核心模块导入"""
        print("\n📋 执行: 模块导入测试")
        modules_to_test = [
            ("chat.chat_manager", "ChatManager"),
            ("chat.session_manager", "SessionManager"),
            ("knowledge.knowledge_manager", "KnowledgeManager"),
            ("report.generator", "CMSReportGenerator"),
            ("utils.chart_generator", "VibrationChartGenerator"),
            ("utils.data_processor", "VibrationDataProcessor")
        ]
        
        all_passed = True
        for module_name, class_name in modules_to_test:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                self.log_test(f"模块导入-{module_name}", "PASS", f"{class_name}类可用")
            except Exception as e:
                self.log_test(f"模块导入-{module_name}", "FAIL", f"导入失败: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_config_loading(self) -> bool:
        """测试配置文件加载"""
        print("\n📋 执行: 配置文件加载测试")
        try:
            config_file = "config.yaml"
            if os.path.exists(config_file):
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                if config:
                    self.log_test("配置文件加载", "PASS", "config.yaml加载成功")
                    return True
                else:
                    self.log_test("配置文件加载", "FAIL", "配置内容为空")
                    return False
            else:
                self.log_test("配置文件加载", "FAIL", "config.yaml文件不存在")
                return False
        except Exception as e:
            self.log_test("配置文件加载", "FAIL", f"加载异常: {str(e)}")
            return False
    
    def test_streamlit_components(self) -> bool:
        """测试Streamlit组件可用性"""
        print("\n📋 执行: Streamlit组件测试")
        try:
            import streamlit as st
            
            # 测试主要组件
            components = [
                "sidebar", "columns", "tabs", "selectbox", "text_input",
                "button", "file_uploader", "dataframe", "plotly_chart", "download_button"
            ]
            
            missing_components = []
            for component in components:
                if not hasattr(st, component):
                    missing_components.append(component)
            
            if not missing_components:
                self.log_test("Streamlit组件", "PASS", f"所有{len(components)}个核心组件可用")
                return True
            else:
                self.log_test("Streamlit组件", "FAIL", f"缺失组件: {', '.join(missing_components)}")
                return False
                
        except Exception as e:
            self.log_test("Streamlit组件", "FAIL", f"测试异常: {str(e)}")
            return False
    
    def test_chat_functionality(self) -> bool:
        """测试聊天功能"""
        print("\n📋 执行: 聊天功能测试")
        try:
            from chat.chat_manager import ChatManager
            from chat.session_manager import SessionManager
            import yaml
            
            # 加载配置
            with open("config.yaml", 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 初始化聊天管理器
            session_manager = SessionManager()
            chat_manager = ChatManager(config=config, session_manager=session_manager)
            
            # 测试简单对话
            test_message = "你好，请介绍一下系统功能"
            response = chat_manager.process_message(test_message, "test_session")
            
            if response and len(response) > 0:
                self.log_test("聊天功能", "PASS", "聊天管理器响应正常")
                return True
            else:
                self.log_test("聊天功能", "FAIL", "聊天管理器无响应")
                return False
                
        except Exception as e:
            self.log_test("聊天功能", "FAIL", f"测试异常: {str(e)}")
            return False
    
    def test_data_processing(self) -> bool:
        """测试数据处理功能"""
        print("\n📋 执行: 数据处理功能测试")
        try:
            from utils.data_processor import VibrationDataProcessor
            import numpy as np
            
            # 生成测试信号
            t = np.linspace(0, 1, 2048)
            test_signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100 * t) + 0.1 * np.random.randn(len(t))
            
            # 测试数据处理
            processor = VibrationDataProcessor()
            time_features = processor.process_time_series(test_signal)
            freq_features = processor.fft_analysis(test_signal)
            
            if time_features and freq_features:
                self.log_test("数据处理功能", "PASS", f"成功处理时域和频域特征")
                return True
            else:
                self.log_test("数据处理功能", "FAIL", "数据处理失败")
                return False
                
        except Exception as e:
            self.log_test("数据处理功能", "FAIL", f"测试异常: {str(e)}")
            return False
    
    def test_chart_generation(self) -> bool:
        """测试图表生成功能"""
        print("\n📋 执行: 图表生成功能测试")
        try:
            from utils.chart_generator import VibrationChartGenerator
            import numpy as np
            
            # 生成测试信号
            t = np.linspace(0, 1, 2048)
            test_signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100 * t) + 0.1 * np.random.randn(len(t))
            
            chart_generator = VibrationChartGenerator()
            
            # 测试时域图表生成
            time_chart = chart_generator.create_time_series_chart(test_signal, 2048, "测试时域波形")
            
            # 测试频域图表生成
            fft_result = np.fft.fft(test_signal)
            frequencies = np.fft.fftfreq(len(test_signal), 1/2048)[:len(test_signal)//2]
            magnitudes = np.abs(fft_result)[:len(test_signal)//2]
            freq_chart = chart_generator.create_frequency_spectrum(frequencies, magnitudes, "测试频谱图")
            
            if time_chart and freq_chart:
                self.log_test("图表生成功能", "PASS", "时域和频域图表生成成功")
                return True
            else:
                self.log_test("图表生成功能", "FAIL", "图表生成失败")
                return False
                
        except Exception as e:
            self.log_test("图表生成功能", "FAIL", f"测试异常: {str(e)}")
            return False
    
    def test_report_generation(self) -> bool:
        """测试报告生成功能"""
        print("\n📋 执行: 报告生成功能测试")
        try:
            from report.generator import CMSReportGenerator
            
            report_generator = CMSReportGenerator()
            
            # 测试报告生成
            test_data = {
                "title": "测试振动分析报告",
                "basic_info": {
                    "wind_farm": "风场A",
                    "turbine_id": "风机001",
                    "measurement_date": "2024-01-15",
                    "operator": "测试员",
                    "equipment_status": "运行中"
                },
                "executive_summary": "测试报告生成功能",
                "measurement_results": [],
                "analysis_conclusion": "功能测试正常",
                "recommendations": ["继续监测"]
            }
            
            success = report_generator.generate_pdf_report(test_data, "streamlit_test_report.pdf")
            
            if success:
                self.log_test("报告生成功能", "PASS", "PDF报告生成成功")
                return True
            else:
                self.log_test("报告生成功能", "FAIL", "报告生成失败")
                return False
                
        except Exception as e:
            self.log_test("报告生成功能", "FAIL", f"测试异常: {str(e)}")
            return False
    
    def test_knowledge_management(self) -> bool:
        """测试知识库管理功能"""
        print("\n📋 执行: 知识库管理功能测试")
        try:
            from knowledge.knowledge_manager import KnowledgeManager
            
            knowledge_manager = KnowledgeManager()
            
            # 测试知识库统计
            stats = knowledge_manager.get_knowledge_stats()
            
            if isinstance(stats, dict):
                doc_count = stats.get('document_count', 0)
                self.log_test("知识库管理功能", "PASS", f"知识库统计: {doc_count}个文档")
                return True
            else:
                self.log_test("知识库管理功能", "FAIL", "知识库统计获取失败")
                return False
                
        except Exception as e:
            self.log_test("知识库管理功能", "FAIL", f"测试异常: {str(e)}")
            return False
    
    def test_mock_data_generation(self) -> bool:
        """测试模拟数据生成"""
        print("\n📋 执行: 模拟数据生成测试")
        try:
            from data.mock_data import CMSDataGenerator
            
            # 生成测试数据
            generator = CMSDataGenerator()
            test_data = generator.generate_measurement_data("风场A", "风机001", "1X水平振动")
            
            if test_data and isinstance(test_data, dict):
                self.log_test("模拟数据生成", "PASS", "成功生成振动测量数据")
                return True
            else:
                self.log_test("模拟数据生成", "FAIL", "数据生成失败")
                return False
                
        except Exception as e:
            self.log_test("模拟数据生成", "FAIL", f"测试异常: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始Streamlit应用功能测试...\n")
        
        # 执行所有测试
        tests = [
            self.test_server_connectivity,
            self.test_file_structure,
            self.test_module_imports,
            self.test_config_loading,
            self.test_streamlit_components,
            self.test_chat_functionality,
            self.test_data_processing,
            self.test_chart_generation,
            self.test_report_generation,
            self.test_knowledge_management,
            self.test_mock_data_generation
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, "FAIL", f"测试执行异常: {str(e)}")
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARNING'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print("\n" + "="*60)
        print("📊 Streamlit应用功能测试报告")
        print("="*60)
        print(f"总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️  警告: {warnings}")
        print(f"成功率: {success_rate:.1f}%")
        
        print("\n📋 详细结果:")
        for result in self.test_results:
            emoji = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            print(f"{emoji} {result['test']}: {result['message']}")
        
        # 保存JSON报告
        report_data = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "success_rate": success_rate
            },
            "details": self.test_results
        }
        
        report_file = "streamlit_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细测试报告已保存到: {report_file}")
        
        if success_rate == 100:
            print("\n🎉 所有核心功能测试通过！Streamlit应用运行正常。")
        elif success_rate >= 80:
            print("\n⚠️  大部分功能正常，但存在一些问题需要关注。")
        else:
            print("\n❌ 发现多个严重问题，需要进行修复。")

if __name__ == "__main__":
    tester = StreamlitFunctionalityTester()
    tester.run_all_tests()