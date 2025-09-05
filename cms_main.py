#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析系统 - 主启动程序
提供完整的用户交互界面，支持真实API和模拟数据模式
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 导入系统组件
from cms_offline_demo import CMSOfflineDemo, demo_analyze_vibration, demo_get_embedding, demo_chat
from loguru import logger

class CMSMainApp:
    """CMS主应用程序"""
    
    def __init__(self):
        self.use_real_api = False
        self.demo_app = None
        
    def show_welcome(self):
        """显示欢迎界面"""
        print("\n" + "=" * 60)
        print("🔧 CMS振动分析系统 - 主控制台")
        print("=" * 60)
        print("欢迎使用CMS振动分析系统！")
        print(f"当前模式: {'真实API' if self.use_real_api else '模拟数据'}")
        print("")
        
    def show_main_menu(self):
        """显示主菜单"""
        print("\n📋 主菜单:")
        print("-" * 30)
        print("1. 🔍 振动数据分析")
        print("2. 🔤 文本嵌入向量生成")
        print("3. 💬 智能技术问答")
        print("4. 📊 生成分析报告")
        print("5. ⚙️  系统设置")
        print("6. 📖 使用帮助")
        print("0. 🚪 退出系统")
        
    def show_settings_menu(self):
        """显示设置菜单"""
        print("\n⚙️ 系统设置:")
        print("-" * 30)
        print(f"1. 切换API模式 (当前: {'真实API' if self.use_real_api else '模拟数据'})")
        print("2. 测试API连接")
        print("3. 查看系统状态")
        print("0. 返回主菜单")
        
    def vibration_analysis(self):
        """振动数据分析功能"""
        print("\n🔍 振动数据分析")
        print("-" * 30)
        
        # 获取用户输入
        try:
            region = input("请输入区域代码 (默认: A08): ").strip() or "A08"
            station = input("请输入站点编号 (默认: 1003): ").strip() or "1003"
            position = input("请输入位置编号 (默认: 8): ").strip() or "8"
            point = input("请输入测点编号 (默认: AI_CMS024): ").strip() or "AI_CMS024"
            hours = input("请输入分析时间范围/小时 (默认: 1): ").strip() or "1"
            
            try:
                hours = int(hours)
            except ValueError:
                print("❌ 时间范围必须是数字，使用默认值1小时")
                hours = 1
                
            print(f"\n📊 正在分析 {region}-{station}-{position}-{point} 最近{hours}小时的数据...")
            
            # 执行分析
            result = demo_analyze_vibration(
                region=region,
                station=station,
                position=position,
                point=point,
                hours=hours,
                use_real_api=self.use_real_api
            )
            
            if result["success"]:
                print("\n✅ 分析完成！")
                print(f"📋 分析结论: {result['conclusion']}")
                print(f"💡 维护建议: {result['recommendations']}")
                if result.get('report_path'):
                    print(f"📄 报告已保存: {result['report_path']}")
            else:
                print(f"\n❌ 分析失败: {result.get('error', '未知错误')}")
                
        except KeyboardInterrupt:
            print("\n⏹️ 分析已取消")
        except Exception as e:
            print(f"\n❌ 分析过程出错: {e}")
            
    def text_embedding(self):
        """文本嵌入向量生成功能"""
        print("\n🔤 文本嵌入向量生成")
        print("-" * 30)
        
        try:
            text = input("请输入要生成向量的文本: ").strip()
            if not text:
                print("❌ 文本不能为空")
                return
                
            print(f"\n🔄 正在生成文本向量...")
            
            embedding = demo_get_embedding(text, use_real_api=self.use_real_api)
            
            if embedding:
                print("\n✅ 向量生成成功！")
                print(f"📏 向量维度: {len(embedding)}")
                print(f"🔢 前10个值: {embedding[:10]}")
                
                # 计算向量范数
                import numpy as np
                norm = np.linalg.norm(embedding)
                print(f"📊 向量范数: {norm:.6f}")
            else:
                print("\n❌ 向量生成失败")
                
        except KeyboardInterrupt:
            print("\n⏹️ 生成已取消")
        except Exception as e:
            print(f"\n❌ 生成过程出错: {e}")
            
    def intelligent_chat(self):
        """智能技术问答功能"""
        print("\n💬 智能技术问答")
        print("-" * 30)
        print("💡 提示: 您可以询问关于振动分析、设备维护等技术问题")
        print("输入 'quit' 或 'exit' 退出对话")
        print("")
        
        try:
            while True:
                question = input("❓ 请输入您的问题: ").strip()
                
                if question.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 对话结束")
                    break
                    
                if not question:
                    print("❌ 问题不能为空")
                    continue
                    
                print("\n🤖 正在思考...")
                
                answer = demo_chat(question, use_real_api=self.use_real_api)
                print(f"🤖 {answer}\n")
                
        except KeyboardInterrupt:
            print("\n⏹️ 对话已结束")
        except Exception as e:
            print(f"\n❌ 对话过程出错: {e}")
            
    def generate_report(self):
        """生成分析报告功能"""
        print("\n📊 生成分析报告")
        print("-" * 30)
        
        try:
            # 获取参数
            region = input("请输入区域代码 (默认: A08): ").strip() or "A08"
            station = input("请输入站点编号 (默认: 1003): ").strip() or "1003"
            position = input("请输入位置编号 (默认: 8): ").strip() or "8"
            point = input("请输入测点编号 (默认: AI_CMS024): ").strip() or "AI_CMS024"
            hours = input("请输入分析时间范围/小时 (默认: 1): ").strip() or "1"
            
            print("\n📋 请选择报告格式:")
            print("1. HTML (推荐)")
            print("2. PDF")
            print("3. DOCX")
            
            format_choice = input("请选择格式 (1-3, 默认: 1): ").strip() or "1"
            format_map = {"1": "html", "2": "pdf", "3": "docx"}
            report_format = format_map.get(format_choice, "html")
            
            try:
                hours = int(hours)
            except ValueError:
                hours = 1
                
            print(f"\n📊 正在生成{report_format.upper()}报告...")
            
            # 初始化应用
            if self.demo_app is None:
                self.demo_app = CMSOfflineDemo(use_real_api=self.use_real_api)
                
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # 生成分析报告
            result = self.demo_app.analyze_vibration_data(
                region=region,
                station=station,
                position=position,
                point=point,
                start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_time=end_time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            if result["success"]:
                # 保存报告到文件
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_filename = f"cms_report_{timestamp}.{report_format}"
                
                if report_format == "html" and "report_data" in result:
                    # 使用HTML报告生成器
                    from report.generator import CMSReportGenerator
                    generator = CMSReportGenerator()
                    success = generator.generate_html_report(result["report_data"], report_filename)
                    report_path = report_filename if success else None
                elif report_format == "pdf" and "report_data" in result:
                    # 使用PDF报告生成器
                    from report.generator import CMSReportGenerator
                    generator = CMSReportGenerator()
                    success = generator.generate_pdf_report(result["report_data"], report_filename)
                    report_path = report_filename if success else None
                elif report_format == "docx" and "report_data" in result:
                    # 使用DOCX报告生成器
                    from report.generator import CMSReportGenerator
                    generator = CMSReportGenerator()
                    success = generator.generate_docx_report(result["report_data"], report_filename)
                    report_path = report_filename if success else None
                else:
                    # 回退到文本报告
                    with open(report_filename, 'w', encoding='utf-8') as f:
                        f.write(result["report"])
                    report_path = report_filename
            else:
                report_path = None
            
            if report_path:
                print(f"\n✅ 报告生成成功！")
                print(f"📄 报告路径: {report_path}")
            else:
                print("\n❌ 报告生成失败")
                
        except KeyboardInterrupt:
            print("\n⏹️ 报告生成已取消")
        except Exception as e:
            print(f"\n❌ 报告生成出错: {e}")
            
    def system_settings(self):
        """系统设置功能"""
        while True:
            self.show_settings_menu()
            
            try:
                choice = input("\n请输入选项 (0-3): ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    self.toggle_api_mode()
                elif choice == "2":
                    self.test_api_connection()
                elif choice == "3":
                    self.show_system_status()
                else:
                    print("❌ 无效选项，请重新选择")
                    
            except KeyboardInterrupt:
                break
                
    def toggle_api_mode(self):
        """切换API模式"""
        print(f"\n当前模式: {'真实API' if self.use_real_api else '模拟数据'}")
        
        if self.use_real_api:
            confirm = input("是否切换到模拟数据模式? (y/N): ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                self.use_real_api = False
                self.demo_app = None  # 重置应用实例
                print("✅ 已切换到模拟数据模式")
        else:
            confirm = input("是否切换到真实API模式? (y/N): ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                self.use_real_api = True
                self.demo_app = None  # 重置应用实例
                print("✅ 已切换到真实API模式")
                print("⚠️ 注意: 真实API模式需要网络连接")
                
    def test_api_connection(self):
        """测试API连接"""
        print("\n🔄 正在测试API连接...")
        
        try:
            if self.demo_app is None:
                self.demo_app = CMSOfflineDemo(use_real_api=self.use_real_api)
                
            if hasattr(self.demo_app.api_client, 'test_connection'):
                success = self.demo_app.api_client.test_connection()
                if success:
                    print("✅ API连接测试成功")
                else:
                    print("❌ API连接测试失败")
            else:
                print("✅ 模拟数据模式，无需网络连接")
                
        except Exception as e:
            print(f"❌ 连接测试出错: {e}")
            
    def show_system_status(self):
        """显示系统状态"""
        print("\n📊 系统状态:")
        print("-" * 30)
        print(f"API模式: {'真实API' if self.use_real_api else '模拟数据'}")
        print(f"Python版本: {sys.version.split()[0]}")
        print(f"工作目录: {os.getcwd()}")
        
        # 检查关键文件
        key_files = [
            "cms_offline_demo.py",
            "api/real_cms_client.py",
            "report/generator.py"
        ]
        
        print("\n📁 关键文件状态:")
        for file in key_files:
            status = "✅" if os.path.exists(file) else "❌"
            print(f"  {status} {file}")
            
    def show_help(self):
        """显示使用帮助"""
        print("\n📖 使用帮助")
        print("=" * 50)
        print("\n🔍 振动数据分析:")
        print("  - 输入设备参数进行振动数据分析")
        print("  - 支持自定义时间范围")
        print("  - 自动生成分析结论和维护建议")
        
        print("\n🔤 文本嵌入向量生成:")
        print("  - 将文本转换为高维向量")
        print("  - 支持中英文文本")
        print("  - 可用于相似度计算")
        
        print("\n💬 智能技术问答:")
        print("  - 询问振动分析相关问题")
        print("  - 获得专业技术解答")
        print("  - 支持连续对话")
        
        print("\n📊 生成分析报告:")
        print("  - 生成专业分析报告")
        print("  - 支持HTML、PDF、DOCX格式")
        print("  - 包含图表和详细分析")
        
        print("\n⚙️ 系统设置:")
        print("  - 切换真实API和模拟数据模式")
        print("  - 测试API连接状态")
        print("  - 查看系统运行状态")
        
        print("\n💡 使用技巧:")
        print("  - 新手建议使用模拟数据模式")
        print("  - 真实API模式需要网络连接")
        print("  - 按Ctrl+C可随时中断操作")
        print("  - 所有生成的文件保存在当前目录")
        
    def run(self):
        """运行主程序"""
        try:
            self.show_welcome()
            
            while True:
                self.show_main_menu()
                
                try:
                    choice = input("\n请输入选项 (0-6): ").strip()
                    
                    if choice == "0":
                        print("\n👋 感谢使用CMS振动分析系统！")
                        break
                    elif choice == "1":
                        self.vibration_analysis()
                    elif choice == "2":
                        self.text_embedding()
                    elif choice == "3":
                        self.intelligent_chat()
                    elif choice == "4":
                        self.generate_report()
                    elif choice == "5":
                        self.system_settings()
                    elif choice == "6":
                        self.show_help()
                    else:
                        print("❌ 无效选项，请重新选择")
                        
                except KeyboardInterrupt:
                    print("\n⏹️ 操作已取消")
                    continue
                    
        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断")
        except Exception as e:
            print(f"\n❌ 程序运行出错: {e}")
            logger.error(f"主程序错误: {e}")

def main():
    """主入口函数"""
    app = CMSMainApp()
    app.run()

if __name__ == "__main__":
    # 配置日志
    logger.add("cms_main.log", rotation="10 MB", level="INFO")
    
    print("🚀 正在启动CMS振动分析系统...")
    main()