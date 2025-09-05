#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析报告系统 - 命令行版本
无前端界面，通过主函数启动，接收用户信息并返回报告
集成真实API调用，替换测试数据生成功能
"""

import requests
import json
import pandas as pd
import base64
import io
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
from loguru import logger
import argparse

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入现有模块
try:
    from config.config_loader import ConfigLoader
    from chat.session_manager import SessionManager
    from knowledge.knowledge_retriever import KnowledgeRetriever
    from chat.chat_manager import ChatManager
    from api.embedding_client import EmbeddingClient, get_embedding_client
except ImportError as e:
    logger.warning(f"模块导入失败: {e}，使用基础功能")

class CMSAPIClient:
    """CMS API客户端，处理与真实API的交互"""
    
    def __init__(self):
        self.base_url = "http://172.16.253.39/api/model/services"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer your_token_here",
            "User-Agent": "CMS-CLI/1.0"
        }
        self.timeout = 1000
        
        # API端点配置
        self.endpoints = {
            "data_fetch": "6853afa7540afad16e5114f8",  # 数据获取API
            "model_run": "681c0f2e016a0cd2dd73295f",   # 模型运行API
            "chart_gen": "6879cd88540afad16e77dbc3"    # 图表生成API
        }
    
    def fetch_vibration_data(self, region: str, station: str, position: str, 
                           point: str, features: str, start_time: str, end_time: str) -> pd.DataFrame:
        """获取振动数据"""
        url = f"{self.base_url}/{self.endpoints['data_fetch']}"
        
        payload = {
            "content": {
                "input": {
                    "region_": region,
                    "station_": f"`{station}`",
                    "position": f"`{position}`",
                    "point_": point,
                    "Features": features,
                    "start_time": start_time,
                    "end_time": end_time
                }
            }
        }
        
        try:
            response = requests.post(
                url=url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            output_str = result['output']
            
            # 处理双重转义的output字段
            decoded_output = json.loads(output_str.encode('utf-8').decode('unicode_escape'))
            
            # 转换为DataFrame
            df = pd.DataFrame.from_dict(decoded_output)
            if 'Time' in df.columns:
                df['Time'] = pd.to_datetime(df['Time'] + 28800000, unit='ns')
            
            logger.info(f"成功获取振动数据，共{len(df)}条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取振动数据失败: {e}")
            raise
    
    def run_analysis_model(self, model_id: str, wfid: str, run_date: str = "0") -> str:
        """运行分析模型"""
        url = f"{self.base_url}/{self.endpoints['model_run']}"
        
        payload = {
            "content": {
                "input": {
                    "run_date": run_date,
                    "model_id": model_id,
                    "wfid": wfid
                }
            }
        }
        
        try:
            response = requests.post(
                url=url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            output_message = result['output']
            execution_time = result.get('time', 0)
            
            logger.info(f"模型运行完成，耗时: {execution_time:.2f}秒")
            return output_message
            
        except Exception as e:
            logger.error(f"模型运行失败: {e}")
            raise
    
    def generate_chart(self, region: str, station: str, position: str, 
                      point: str, features: str, start_time: str, end_time: str, 
                      output_path: Optional[str] = None) -> str:
        """生成可视化图表"""
        url = f"{self.base_url}/{self.endpoints['chart_gen']}"
        
        payload = {
            "content": {
                "input": {
                    "Features": features,
                    "region_": region,
                    "station_": f"`{station}`",
                    "position": f"`{position}`",
                    "point_": point,
                    "start_time": start_time,
                    "end_time": end_time
                }
            }
        }
        
        try:
            response = requests.post(
                url=url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            base64_str = result['output']
            
            # 提取base64编码部分
            if base64_str.startswith('data:image/'):
                base64_str = base64_str.split(",", 1)[1]
            
            # 解码并保存图片
            img_data = base64.b64decode(base64_str)
            
            if output_path is None:
                output_path = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            # 确保output_path不为None
            if output_path is None:
                output_path = "chart_default.png"
            
            with open(output_path, "wb") as f:
                f.write(img_data)
            
            logger.info(f"图表已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成图表失败: {e}")
            raise

class CMSCLIApp:
    """CMS命令行应用主类"""
    
    def __init__(self):
        self.api_client = CMSAPIClient()
        
        # 初始化Embedding客户端
        try:
            embedding_client_func = globals().get('get_embedding_client')
            if embedding_client_func:
                self.embedding_client = embedding_client_func()
                logger.info("Embedding客户端初始化成功")
            else:
                self.embedding_client = None
        except Exception as e:
            logger.warning(f"Embedding客户端初始化失败: {e}")
            self.embedding_client = None
        
        self.config = self._load_config()
        
        # 初始化其他组件
        try:
            # 尝试初始化ChatManager，如果类存在的话
            chat_manager_class = globals().get('ChatManager')
            if chat_manager_class:
                # 尝试使用默认用户ID初始化
                self.chat_manager = chat_manager_class(user_id="default_user")
            else:
                self.chat_manager = None
            
            # 尝试初始化KnowledgeRetriever，如果类存在的话
            knowledge_retriever_class = globals().get('KnowledgeRetriever')
            if knowledge_retriever_class:
                self.knowledge_retriever = knowledge_retriever_class(
                    embeddings_path="embeddings", 
                    metadata_path="metadata"
                )
            else:
                self.knowledge_retriever = None
        except Exception as e:
            logger.warning(f"高级功能初始化失败，使用基础功能: {e}")
            self.chat_manager = None
            self.knowledge_retriever = None
    
    def _load_config(self) -> dict:
        """加载配置"""
        try:
            # 检查ConfigLoader是否可用
            config_loader_class = globals().get('ConfigLoader')
            if config_loader_class:
                config_loader = config_loader_class()
                # 使用config属性获取配置
                if hasattr(config_loader, 'config'):
                    return config_loader.config
                elif hasattr(config_loader, 'get'):
                    # 返回整个配置字典
                    return {
                        "default_features": config_loader.get("api.default_features", "Time_Domain_RMS_Value"),
                        "default_model_id": config_loader.get("api.default_model_id", "906"),
                        "timeout": config_loader.get("api.timeout", 30)
                    }
                else:
                    logger.warning("ConfigLoader没有预期的方法")
            else:
                logger.warning("ConfigLoader类不可用")
        except Exception as e:
            logger.warning(f"配置加载失败: {e}")
        
        # 返回默认配置
        return {
            "default_region": "A08",
            "default_station": "1003",
            "default_position": "8",
            "default_features": "Sample_Rate,Speed,Time_Domain_RMS_Value,Time_Domain_10_5000Hz_Acceleration_RMS",
            "default_model_id": "906"
        }
    
    def analyze_vibration_data(self, region: str, station: str, position: str, 
                             point: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """分析振动数据"""
        logger.info(f"开始分析振动数据: {region}-{station}-{position}-{point}")
        
        try:
            # 1. 获取振动数据
            features = self.config.get("default_features", "Time_Domain_RMS_Value")
            df = self.api_client.fetch_vibration_data(
                region, station, position, point, features, start_time, end_time
            )
            
            # 2. 运行分析模型
            model_id = self.config.get("default_model_id", "906")
            model_result = self.api_client.run_analysis_model(model_id, station)
            
            # 3. 生成可视化图表
            chart_path = self.api_client.generate_chart(
                region, station, position, point, "Time_Domain_RMS_Value", 
                start_time, end_time
            )
            
            # 4. 数据统计分析
            stats = self._calculate_statistics(df)
            
            # 5. 生成分析报告
            report = self._generate_analysis_report(df, stats, model_result, chart_path)
            
            return {
                "success": True,
                "data": df,
                "statistics": stats,
                "model_result": model_result,
                "chart_path": chart_path,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"振动数据分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算统计信息"""
        stats = {}
        
        # 基础统计
        stats["record_count"] = len(df)
        stats["time_range"] = {
            "start": df['Time'].min().strftime('%Y-%m-%d %H:%M:%S') if 'Time' in df.columns else None,
            "end": df['Time'].max().strftime('%Y-%m-%d %H:%M:%S') if 'Time' in df.columns else None
        }
        
        # 振动数据统计
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_columns:
            if 'RMS' in col or 'Speed' in col:
                stats[col] = {
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "median": float(df[col].median())
                }
        
        return stats
    
    def _generate_analysis_report(self, df: pd.DataFrame, stats: Dict[str, Any], 
                                model_result: str, chart_path: str) -> str:
        """生成分析报告"""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("CMS振动分析报告")
        report_lines.append("=" * 60)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 数据概览
        report_lines.append("📊 数据概览")
        report_lines.append("-" * 30)
        report_lines.append(f"数据记录数: {stats['record_count']}")
        if stats['time_range']['start']:
            report_lines.append(f"时间范围: {stats['time_range']['start']} ~ {stats['time_range']['end']}")
        report_lines.append("")
        
        # 振动数据统计
        report_lines.append("🔧 振动数据统计")
        report_lines.append("-" * 30)
        for col, col_stats in stats.items():
            if isinstance(col_stats, dict) and 'mean' in col_stats:
                report_lines.append(f"{col}:")
                report_lines.append(f"  平均值: {col_stats['mean']:.4f}")
                report_lines.append(f"  标准差: {col_stats['std']:.4f}")
                report_lines.append(f"  最小值: {col_stats['min']:.4f}")
                report_lines.append(f"  最大值: {col_stats['max']:.4f}")
                report_lines.append(f"  中位数: {col_stats['median']:.4f}")
                report_lines.append("")
        
        # 模型分析结果
        report_lines.append("🤖 模型分析结果")
        report_lines.append("-" * 30)
        report_lines.append(model_result)
        report_lines.append("")
        
        # 可视化图表
        report_lines.append("📈 可视化图表")
        report_lines.append("-" * 30)
        report_lines.append(f"图表文件: {chart_path}")
        report_lines.append("")
        
        # 结论和建议
        report_lines.append("💡 结论和建议")
        report_lines.append("-" * 30)
        
        # 基于RMS值给出建议
        rms_columns = [col for col in stats.keys() if 'RMS' in str(col) and isinstance(stats[col], dict)]
        if rms_columns:
            rms_col = rms_columns[0]
            rms_mean = stats[rms_col]['mean']
            
            if rms_mean < 0.6:
                report_lines.append("✅ 振动水平正常，设备运行状态良好")
            elif rms_mean < 1.0:
                report_lines.append("⚠️ 振动水平略高，建议加强监控")
            else:
                report_lines.append("🚨 振动水平异常，建议立即检查设备")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def interactive_mode(self):
        """交互模式"""
        print("🔧 CMS振动分析系统 - 命令行版本")
        print("输入 'help' 查看帮助，输入 'quit' 退出")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n请输入命令 > ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 再见！")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                elif user_input.lower().startswith('analyze'):
                    self._handle_analyze_command(user_input)
                elif user_input.lower().startswith('chat'):
                    self._handle_chat_command(user_input)
                elif user_input.lower().startswith('embed'):
                    self._handle_embed_command(user_input)
                else:
                    print("❌ 未知命令，输入 'help' 查看帮助")
                    
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
📖 命令帮助:

1. analyze <region> <station> <position> <point> <start_time> <end_time>
   分析振动数据
   示例: analyze A08 1003 8 AI_CMS024 "2025-01-12 00:00:00" "2025-01-13 00:00:00"

2. chat <message>
   智能对话
   示例: chat 请分析最近的振动趋势

3. embed <text> [--test]
   获取文本的embedding向量
   参数:
     --test: 使用测试模式生成模拟向量(推荐)
   示例: 
     embed 这是一个测试文本 --test  (测试模式)
     embed 这是一个测试文本          (API模式)

4. help
   显示此帮助信息

5. quit/exit/q
   退出程序

💡 提示:
   - embedding功能建议使用 --test 参数进行测试
   - 测试模式会基于文本hash生成模拟向量，相同文本产生相同向量
"""
        print(help_text)
    
    def _handle_analyze_command(self, command: str):
        """处理分析命令"""
        parts = command.split()[1:]  # 去掉 'analyze'
        
        if len(parts) < 6:
            print("❌ 参数不足，格式: analyze <region> <station> <position> <point> <start_time> <end_time>")
            return
        
        region, station, position, point = parts[:4]
        start_time = parts[4].strip('"')
        end_time = parts[5].strip('"')
        
        print(f"🔄 开始分析 {region}-{station}-{position}-{point} 的振动数据...")
        
        result = self.analyze_vibration_data(region, station, position, point, start_time, end_time)
        
        if result["success"]:
            print("✅ 分析完成！")
            print("\n" + result["report"])
        else:
            print(f"❌ 分析失败: {result['error']}")
    
    def _handle_chat_command(self, command: str):
        """处理对话命令"""
        message = " ".join(command.split()[1:])  # 去掉 'chat'
        
        if not message:
            print("❌ 请输入对话内容")
            return
        
        if self.chat_manager:
            try:
                # 检查chat_manager是否有process_message方法
                if hasattr(self.chat_manager, 'process_message'):
                    response = self.chat_manager.process_message(message=message)
                elif hasattr(self.chat_manager, 'send_message'):
                    response = self.chat_manager.send_message(message)
                elif hasattr(self.chat_manager, 'get_response'):
                    response = self.chat_manager.get_response(message)
                else:
                    response = f"收到消息: {message}（模拟回复）"
                print(f"🤖 {response}")
            except Exception as e:
                print(f"❌ 对话处理失败: {e}")
        else:
            print("❌ 对话功能不可用")
    
    def _handle_embed_command(self, command: str) -> None:
        """
        处理embed命令
        
        Args:
            command: 用户输入的命令
        """
        # 解析命令参数
        parts = command.split()
        if len(parts) < 2:
            print("❌ 请提供要生成embedding的文本")
            print("💡 用法: embed <文本内容> [--test]")
            print("💡 示例: embed 这是一段测试文本 --test")
            return
        
        # 检查是否使用测试数据
        use_test_data = '--test' in parts
        if use_test_data:
            parts.remove('--test')
        
        # 提取文本内容
        text = ' '.join(parts[1:])  # 移除'embed'前缀
        if not text:
            print("❌ 请提供要生成embedding的文本")
            return
        
        if self.embedding_client:
            try:
                mode_text = "测试模式" if use_test_data else "API模式"
                print(f"🔄 正在生成embedding向量... ({mode_text})")
                
                # 使用正确的方法名
                if hasattr(self.embedding_client, 'get_single_embedding'):
                    embedding = self.embedding_client.get_single_embedding(text, use_test_data=use_test_data)
                elif hasattr(self.embedding_client, 'get_embeddings'):
                    result = self.embedding_client.get_embeddings([text], use_test_data=use_test_data)
                    if 'data' in result and len(result['data']) > 0:
                        embedding = result['data'][0]['embedding']
                    else:
                        raise ValueError("无法从API响应中提取embedding向量")
                else:
                    raise ValueError("Embedding客户端缺少必要的方法")
                
                print(f"✅ Embedding生成成功 ({mode_text})")
                print(f"📊 向量维度: {len(embedding)}")
                print(f"🔢 向量前10个值: {[round(x, 6) for x in embedding[:10]]}")
                print(f"📝 文本内容: {text[:50]}{'...' if len(text) > 50 else ''}")
                
                if use_test_data:
                    print("ℹ️  注意: 这是基于文本hash生成的测试向量，相同文本会产生相同向量")
                    
            except Exception as e:
                if not use_test_data:
                    print(f"❌ API模式失败: {e}")
                    print("💡 提示: 可以使用 --test 参数尝试测试模式")
                    print(f"💡 示例: embed {text} --test")
                else:
                    print(f"❌ Embedding生成失败: {e}")
        else:
            print("❌ Embedding功能不可用")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CMS振动分析系统 - 命令行版本')
    parser.add_argument('--mode', choices=['interactive', 'batch'], default='interactive',
                       help='运行模式: interactive(交互模式) 或 batch(批处理模式)')
    parser.add_argument('--region', help='区域代码')
    parser.add_argument('--station', help='风场代码')
    parser.add_argument('--position', help='位置代码')
    parser.add_argument('--point', help='测点代码')
    parser.add_argument('--start-time', help='开始时间')
    parser.add_argument('--end-time', help='结束时间')
    parser.add_argument('--output', help='输出文件路径')
    
    args = parser.parse_args()
    
    # 配置日志
    logger.add("cms_cli.log", rotation="10 MB", level="INFO")
    
    app = CMSCLIApp()
    
    if args.mode == 'interactive':
        app.interactive_mode()
    elif args.mode == 'batch':
        if not all([args.region, args.station, args.position, args.point, args.start_time, args.end_time]):
            print("❌ 批处理模式需要提供所有参数")
            parser.print_help()
            return
        
        print(f"🔄 批处理模式: 分析 {args.region}-{args.station}-{args.position}-{args.point}")
        
        result = app.analyze_vibration_data(
            args.region, args.station, args.position, args.point,
            args.start_time, args.end_time
        )
        
        if result["success"]:
            print("✅ 分析完成！")
            print("\n" + result["report"])
            
            # 保存报告到文件
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(result["report"])
                print(f"📄 报告已保存到: {args.output}")
        else:
            print(f"❌ 分析失败: {result['error']}")

if __name__ == "__main__":
    main()