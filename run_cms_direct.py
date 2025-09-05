#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析系统 - 简单启动脚本
直接运行此文件即可使用CMS系统，无需命令行参数
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入CMS直接调用应用
from cms_direct_app import get_cms_app, analyze_vibration, get_text_embedding, chat_with_cms

def main():
    """主函数 - 提供交互式界面"""
    print("🔧 CMS振动分析系统")
    print("=" * 50)
    print("欢迎使用CMS振动分析系统！")
    print("")
    
    while True:
        print("\n请选择功能:")
        print("1. 振动数据分析")
        print("2. 文本嵌入向量生成")
        print("3. 智能对话")
        print("4. 快速分析（使用默认参数）")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-4): ").strip()
        
        if choice == "0":
            print("👋 再见！")
            break
        elif choice == "1":
            vibration_analysis_interactive()
        elif choice == "2":
            embedding_interactive()
        elif choice == "3":
            chat_interactive()
        elif choice == "4":
            quick_analysis()
        else:
            print("❌ 无效选项，请重新选择")

def vibration_analysis_interactive():
    """交互式振动数据分析"""
    print("\n📊 振动数据分析")
    print("-" * 30)
    
    # 获取用户输入
    region = input("请输入区域 (默认: A08): ").strip() or "A08"
    station = input("请输入风场 (默认: 1003): ").strip() or "1003"
    position = input("请输入位置 (默认: 8): ").strip() or "8"
    point = input("请输入测点 (默认: AI_CMS024): ").strip() or "AI_CMS024"
    
    # 时间范围
    print("\n时间范围设置:")
    print("1. 最近24小时")
    print("2. 最近7天")
    print("3. 自定义时间")
    
    time_choice = input("请选择时间范围 (1-3): ").strip()
    
    if time_choice == "1":
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
    elif time_choice == "2":
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
    elif time_choice == "3":
        start_str = input("请输入开始时间 (YYYY-MM-DD HH:MM:SS): ").strip()
        end_str = input("请输入结束时间 (YYYY-MM-DD HH:MM:SS): ").strip()
        try:
            start_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("❌ 时间格式错误，使用默认时间范围（最近24小时）")
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
    else:
        print("❌ 无效选项，使用默认时间范围（最近24小时）")
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
    
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n🔄 开始分析...")
    print(f"参数: {region}-{station}-{position}-{point}")
    print(f"时间: {start_time_str} ~ {end_time_str}")
    
    try:
        result = analyze_vibration(region, station, position, point, start_time_str, end_time_str)
        
        if result["success"]:
            print("\n✅ 分析完成！")
            print("\n" + "=" * 60)
            print(result["report"])
            
            # 询问是否保存报告
            save_choice = input("\n是否保存报告到文件？(y/n): ").strip().lower()
            if save_choice == 'y':
                filename = f"vibration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result["report"])
                print(f"📄 报告已保存到: {filename}")
        else:
            print(f"\n❌ 分析失败: {result['error']}")
    
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")

def embedding_interactive():
    """交互式文本嵌入向量生成"""
    print("\n🔤 文本嵌入向量生成")
    print("-" * 30)
    
    text = input("请输入要生成嵌入向量的文本: ").strip()
    if not text:
        print("❌ 文本不能为空")
        return
    
    use_test = input("是否使用测试数据模式？(y/n, 默认: y): ").strip().lower()
    use_test_data = use_test != 'n'
    
    print(f"\n🔄 生成嵌入向量...")
    
    try:
        embedding = get_text_embedding(text, use_test_data=use_test_data)
        
        if embedding:
            print(f"\n✅ 嵌入向量生成成功！")
            print(f"维度: {len(embedding)}")
            print(f"前10个值: {embedding[:10]}")
            print(f"向量范数: {sum(x*x for x in embedding)**0.5:.6f}")
            
            # 询问是否保存向量
            save_choice = input("\n是否保存向量到文件？(y/n): ").strip().lower()
            if save_choice == 'y':
                filename = f"embedding_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"文本: {text}\n")
                    f.write(f"维度: {len(embedding)}\n")
                    f.write(f"向量: {embedding}\n")
                print(f"📄 向量已保存到: {filename}")
        else:
            print("\n❌ 嵌入向量生成失败")
    
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")

def chat_interactive():
    """交互式智能对话"""
    print("\n💬 智能对话")
    print("-" * 30)
    print("输入 'quit' 或 'exit' 退出对话")
    
    while True:
        message = input("\n👤 您: ").strip()
        
        if message.lower() in ['quit', 'exit', '退出']:
            print("👋 对话结束")
            break
        
        if not message:
            print("❌ 消息不能为空")
            continue
        
        try:
            response = chat_with_cms(message)
            print(f"🤖 CMS: {response}")
        except Exception as e:
            print(f"❌ 对话失败: {e}")

def quick_analysis():
    """快速分析（使用默认参数）"""
    print("\n⚡ 快速分析")
    print("-" * 30)
    print("使用默认参数进行快速分析...")
    
    # 默认参数
    region = "A08"
    station = "1003"
    position = "8"
    point = "AI_CMS024"
    
    # 最近24小时
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"参数: {region}-{station}-{position}-{point}")
    print(f"时间: {start_time_str} ~ {end_time_str}")
    print("\n🔄 分析中...")
    
    try:
        result = analyze_vibration(region, station, position, point, start_time_str, end_time_str)
        
        if result["success"]:
            print("\n✅ 快速分析完成！")
            print("\n" + "=" * 60)
            print(result["report"])
            
            # 自动保存报告
            filename = f"quick_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(result["report"])
            print(f"\n📄 报告已自动保存到: {filename}")
        else:
            print(f"\n❌ 分析失败: {result['error']}")
    
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")

# 直接调用函数示例
def demo_direct_calls():
    """演示直接函数调用"""
    print("\n🎯 直接函数调用演示")
    print("=" * 50)
    
    # 1. 直接分析振动数据
    print("\n1. 直接分析振动数据")
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    result = analyze_vibration(
        region="A08",
        station="1003",
        position="8", 
        point="AI_CMS024",
        start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time=end_time.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    if result["success"]:
        print("✅ 分析成功")
        print(f"数据记录数: {result['statistics']['record_count']}")
    else:
        print(f"❌ 分析失败: {result['error']}")
    
    # 2. 直接生成嵌入向量
    print("\n2. 直接生成嵌入向量")
    embedding = get_text_embedding("振动分析测试文本", use_test_data=True)
    if embedding:
        print(f"✅ 向量生成成功，维度: {len(embedding)}")
    else:
        print("❌ 向量生成失败")
    
    # 3. 直接对话
    print("\n3. 直接对话")
    response = chat_with_cms("请介绍振动分析的基本原理")
    print(f"🤖 {response}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CMS振动分析系统")
    parser.add_argument("--demo", action="store_true", help="运行演示")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    
    args = parser.parse_args()
    
    if args.demo:
        demo_direct_calls()
    elif args.interactive or len(sys.argv) == 1:
        main()
    else:
        print("使用 --help 查看帮助信息")