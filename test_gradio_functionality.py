#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gradio应用功能全面测试脚本
直接测试应用模块的完整性和正确性
"""

import os
import sys
import time
import requests
import json
import importlib.util
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class GradioFunctionalityTester:
    def __init__(self, base_url="http://localhost:7861"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name, status, message=""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {message}")
        
    def test_server_connectivity(self):
        """测试服务器连接性"""
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                self.log_test("服务器连接性", "PASS", "Gradio应用正常运行")
                return True
            else:
                self.log_test("服务器连接性", "FAIL", f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("服务器连接性", "FAIL", f"连接失败: {str(e)}")
            return False
            
    def test_module_imports(self):
        """测试核心模块导入"""
        modules_to_test = [
            ("chat.chat_manager", "ChatManager"),
            ("chat.session_manager", "SessionManager"),
            ("knowledge.knowledge_manager", "KnowledgeManager"),
            ("report.generator", "CMSReportGenerator"),
            ("utils.chart_generator", "VibrationChartGenerator"),
            ("utils.data_processor", "VibrationDataProcessor")
        ]
        
        passed = 0
        for module_name, class_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, class_name):
                    self.log_test(f"模块导入-{module_name}", "PASS", f"{class_name}类可用")
                    passed += 1
                else:
                    self.log_test(f"模块导入-{module_name}", "FAIL", f"{class_name}类不存在")
            except Exception as e:
                self.log_test(f"模块导入-{module_name}", "FAIL", f"导入失败: {str(e)}")
                
        return passed == len(modules_to_test)
        
    def test_configuration_loading(self):
        """测试配置文件加载"""
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
            
    def test_chat_functionality(self):
        """测试聊天功能"""
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
            
    def test_data_processing(self):
        """测试数据处理功能"""
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
            
    def test_chart_generation(self):
        """测试图表生成功能"""
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
            
    def test_report_generation(self):
        """测试报告生成功能"""
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
            
            success = report_generator.generate_pdf_report(test_data, "test_report.pdf")
            
            if success:
                self.log_test("报告生成功能", "PASS", "PDF报告生成成功")
                return True
            else:
                self.log_test("报告生成功能", "FAIL", "报告生成失败")
                return False
                
        except Exception as e:
            self.log_test("报告生成功能", "FAIL", f"测试异常: {str(e)}")
            return False
            
    def test_knowledge_management(self):
        """测试知识库管理功能"""
        try:
            from knowledge.knowledge_manager import KnowledgeManager
            
            knowledge_manager = KnowledgeManager()
            
            # 测试知识库状态
            stats = knowledge_manager.get_knowledge_stats()
            
            if stats:
                self.log_test("知识库管理功能", "PASS", f"知识库统计: {stats.get('total_documents', 0)}个文档")
                return True
            else:
                self.log_test("知识库管理功能", "WARN", "知识库统计获取失败")
                return False
                
        except Exception as e:
            self.log_test("知识库管理功能", "FAIL", f"测试异常: {str(e)}")
            return False
            
    def test_ui_accessibility(self):
        """测试UI可访问性"""
        try:
            response = requests.get(self.base_url, timeout=10)
            html_content = response.text
            
            # 检查关键UI元素
            ui_elements = [
                "智能对话",
                "数据分析", 
                "报告生成",
                "知识库管理",
                "系统配置"
            ]
            
            present_elements = []
            missing_elements = []
            
            for element in ui_elements:
                if element in html_content:
                    present_elements.append(element)
                else:
                    missing_elements.append(element)
            
            if not missing_elements:
                self.log_test("UI可访问性", "PASS", f"所有{len(ui_elements)}个主要UI元素存在")
                return True
            else:
                self.log_test("UI可访问性", "WARN", f"存在{len(present_elements)}个，缺失{len(missing_elements)}个元素")
                return False
                
        except Exception as e:
            self.log_test("UI可访问性", "FAIL", f"测试异常: {str(e)}")
            return False
            
    def test_file_structure(self):
        """测试文件结构完整性"""
        required_files = [
            "gradio_app_complete.py",
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
        present_files = []
        
        for file_path in required_files:
            if os.path.exists(file_path):
                present_files.append(file_path)
            else:
                missing_files.append(file_path)
                
        if not missing_files:
            self.log_test("文件结构完整性", "PASS", f"所有{len(required_files)}个核心文件存在")
            return True
        else:
            self.log_test("文件结构完整性", "WARN", f"存在{len(present_files)}个，缺失{len(missing_files)}个文件")
            return False
            
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始Gradio应用功能全面测试...\n")
        
        # 测试列表
        tests = [
            ("服务器连接性测试", self.test_server_connectivity),
            ("文件结构完整性测试", self.test_file_structure),
            ("核心模块导入测试", self.test_module_imports),
            ("配置文件加载测试", self.test_configuration_loading),
            ("UI可访问性测试", self.test_ui_accessibility),
            ("聊天功能测试", self.test_chat_functionality),
            ("数据处理功能测试", self.test_data_processing),
            ("图表生成功能测试", self.test_chart_generation),
            ("报告生成功能测试", self.test_report_generation),
            ("知识库管理功能测试", self.test_knowledge_management)
        ]
        
        passed = 0
        failed = 0
        warnings = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 执行: {test_name}")
            try:
                result = test_func()
                if result:
                    passed += 1
                else:
                    # 检查是否是警告
                    last_result = self.test_results[-1]
                    if last_result["status"] == "WARN":
                        warnings += 1
                    else:
                        failed += 1
            except Exception as e:
                self.log_test(test_name, "FAIL", f"测试执行异常: {str(e)}")
                failed += 1
                
        # 生成测试报告
        self.generate_test_report(passed, failed, warnings)
        
    def generate_test_report(self, passed, failed, warnings):
        """生成测试报告"""
        total = passed + failed + warnings
        
        print("\n" + "="*60)
        print("📊 Gradio应用功能测试报告")
        print("="*60)
        print(f"总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️  警告: {warnings}")
        print(f"成功率: {(passed/total*100):.1f}%" if total > 0 else "成功率: 0%")
        
        print("\n📋 详细结果:")
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_symbol} {result['test']}: {result['message']}")
            
        # 保存测试报告到文件
        report_file = "gradio_test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "warnings": warnings,
                    "success_rate": (passed/total*100) if total > 0 else 0
                },
                "details": self.test_results
            }, f, ensure_ascii=False, indent=2)
            
        print(f"\n📄 详细测试报告已保存到: {report_file}")
        
        # 总结
        if failed == 0:
            print("\n🎉 所有核心功能测试通过！Gradio应用运行正常。")
        elif failed <= 2:
            print("\n⚠️  大部分功能正常，少数功能需要检查。")
        else:
            print("\n❌ 多个功能存在问题，需要进一步调试。")

def main():
    """主函数"""
    print("Gradio应用功能全面测试工具")
    print("测试应用的核心模块和功能完整性")
    
    # 等待用户确认
    input("\n按Enter键开始测试...")
    
    # 创建测试器并运行测试
    tester = GradioFunctionalityTester()
    tester.run_all_tests()
    
if __name__ == "__main__":
    main()