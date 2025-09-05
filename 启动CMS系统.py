#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析系统 - 一键启动脚本
双击此文件即可启动CMS系统，无需任何命令行操作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

def main():
    """主启动函数"""
    print("🔧 CMS振动分析系统 - 一键启动")
    print("=" * 50)
    print("欢迎使用CMS振动分析系统！")
    print("")
    
    print("请选择启动方式:")
    print("1. 🎯 离线演示版本 (推荐新手，无需网络)")
    print("2. 🌐 完整功能版本 (需要网络连接)")
    print("3. 💻 Web界面版本 (Gradio)")
    print("4. 📊 Web界面版本 (Streamlit)")
    print("5. 📖 查看使用指南")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请输入选项 (0-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 程序退出")
            break
        
        if choice == "0":
            print("👋 再见！")
            break
        elif choice == "1":
            start_offline_demo()
        elif choice == "2":
            start_full_version()
        elif choice == "3":
            start_gradio_app()
        elif choice == "4":
            start_streamlit_app()
        elif choice == "5":
            show_usage_guide()
        else:
            print("❌ 无效选项，请重新选择")

def start_offline_demo():
    """启动离线演示版本"""
    print("\n🎯 启动离线演示版本...")
    print("=" * 30)
    
    try:
        print("✅ 离线演示版本启动成功！")
        print("\n💡 提示: 此版本使用模拟数据，无需网络连接")
        print("按 Ctrl+C 可以随时退出")
        print("\n" + "=" * 50)
        
        # 使用subprocess运行离线演示
        import subprocess
        result = subprocess.run([sys.executable, 'cms_offline_demo.py'], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ 离线演示运行完成")
        else:
            print(f"\n⚠️ 程序退出，返回码: {result.returncode}")
        
    except KeyboardInterrupt:
        print("\n\n👋 用户退出离线演示")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("请检查文件是否存在: cms_offline_demo.py")

def start_full_version():
    """启动完整功能版本"""
    print("\n🌐 启动完整功能版本...")
    print("=" * 30)
    
    try:
        # 导入并运行完整版本
        import run_cms_direct
        print("✅ 完整功能版本启动成功！")
        print("\n💡 提示: 此版本需要网络连接以访问真实API")
        print("按 Ctrl+C 可以随时退出")
        print("\n" + "=" * 50)
        
        # 运行交互式界面
        run_cms_direct.main()
        
    except KeyboardInterrupt:
        print("\n\n👋 用户退出完整版本")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("请检查文件是否存在: run_cms_direct.py")

def start_gradio_app():
    """启动Gradio Web界面"""
    print("\n💻 启动Gradio Web界面...")
    print("=" * 30)
    
    try:
        # 检查Gradio是否可用
        try:
            import gradio as gr
            print("✅ Gradio库检测成功")
        except ImportError:
            print("❌ Gradio库未安装，请先安装: pip install gradio")
            return
        
        # 查找Gradio应用文件
        gradio_files = [
            "gradio_app_complete_final.py",
            "gradio_app.py"
        ]
        
        gradio_file = None
        for file in gradio_files:
            if os.path.exists(file):
                gradio_file = file
                break
        
        if not gradio_file:
            print("❌ 未找到Gradio应用文件")
            print("请检查以下文件是否存在:")
            for file in gradio_files:
                print(f"  - {file}")
            return
        
        print(f"✅ 找到Gradio应用: {gradio_file}")
        print("🚀 正在启动Web界面...")
        print("\n💡 提示:")
        print("  - 启动后会自动打开浏览器")
        print("  - 如果没有自动打开，请复制显示的URL到浏览器")
        print("  - 按 Ctrl+C 可以停止服务")
        print("\n" + "=" * 50)
        
        # 运行Gradio应用
        exec(open(gradio_file).read())
        
    except KeyboardInterrupt:
        print("\n\n👋 Web服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")

def start_streamlit_app():
    """启动Streamlit Web界面"""
    print("\n📊 启动Streamlit Web界面...")
    print("=" * 30)
    
    try:
        # 检查Streamlit是否可用
        try:
            import streamlit as st
            print("✅ Streamlit库检测成功")
        except ImportError:
            print("❌ Streamlit库未安装，请先安装: pip install streamlit")
            return
        
        # 检查Streamlit应用文件
        streamlit_file = "streamlit_app.py"
        if not os.path.exists(streamlit_file):
            print(f"❌ 未找到Streamlit应用文件: {streamlit_file}")
            return
        
        print(f"✅ 找到Streamlit应用: {streamlit_file}")
        print("🚀 正在启动Web界面...")
        print("\n💡 提示:")
        print("  - 启动后会自动打开浏览器")
        print("  - 如果没有自动打开，请访问 http://localhost:8501")
        print("  - 按 Ctrl+C 可以停止服务")
        print("\n" + "=" * 50)
        
        # 使用subprocess运行streamlit
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", streamlit_file])
        
    except KeyboardInterrupt:
        print("\n\n👋 Web服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")

def show_usage_guide():
    """显示使用指南"""
    print("\n📖 CMS系统使用指南")
    print("=" * 50)
    
    guide_file = "非命令行使用指南.md"
    if os.path.exists(guide_file):
        try:
            with open(guide_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 显示前面部分内容
            lines = content.split('\n')
            for i, line in enumerate(lines[:50]):  # 显示前50行
                print(line)
            
            if len(lines) > 50:
                print("\n... (更多内容请查看完整文档) ...")
            
            print(f"\n📄 完整指南文件: {guide_file}")
            print("💡 建议使用文本编辑器打开查看完整内容")
            
        except Exception as e:
            print(f"❌ 读取指南文件失败: {e}")
    else:
        print("❌ 使用指南文件不存在")
        print("\n📋 基本使用方法:")
        print("1. 选择离线演示版本 - 无需网络，使用模拟数据")
        print("2. 选择完整功能版本 - 需要网络，使用真实数据")
        print("3. 选择Web界面版本 - 图形化操作界面")
    
    try:
        input("\n按回车键返回主菜单...")
    except (EOFError, KeyboardInterrupt):
        pass  # 在非交互环境下忽略输入错误

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 6):
        print("⚠️ 警告: Python版本过低，建议使用3.6+")
    else:
        print("✅ Python版本符合要求")
    
    # 检查关键文件
    required_files = [
        "cms_offline_demo.py",
        "run_cms_direct.py",
        "cms_direct_app.py"
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (缺失)")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ 警告: 缺失 {len(missing_files)} 个关键文件")
        print("系统可能无法正常运行")
    else:
        print("\n✅ 所有关键文件检查通过")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    try:
        # 检查环境
        check_environment()
        
        # 启动主程序
        main()
        
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        print("\n🔧 故障排除建议:")
        print("1. 检查Python版本是否为3.6+")
        print("2. 检查所有必需文件是否存在")
        print("3. 检查网络连接（如使用完整版本）")
        print("4. 尝试重新下载或重新安装系统")
    
    try:
        input("\n按回车键退出...")
    except (EOFError, KeyboardInterrupt):
        pass  # 在非交互环境下忽略输入错误