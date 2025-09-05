#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析报告系统 - 直接调用版本
无需命令行参数，可直接通过函数调用使用
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
            "User-Agent": "CMS-Direct/1.0"
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
            
            with open(output_path, "wb") as f:
                f.write(img_data)
            
            logger.info(f"图表已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成图表失败: {e}")
            raise

class CMSDirectApp:
    """CMS直接调用应用主类"""
    
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
            chat_manager_class = globals().get('ChatManager')
            if chat_manager_class:
                self.chat_manager = chat_manager_class(user_id="default_user")
            else:
                self.chat_manager = None
            
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
            config_loader_class = globals().get('ConfigLoader')
            if config_loader_class:
                config_loader = config_loader_class()
                if hasattr(config_loader, 'config'):
                    return config_loader.config
                elif hasattr(config_loader, 'get'):
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
    
    def get_embedding(self, text: str, use_test_data: bool = True) -> Optional[List[float]]:
        """获取文本的embedding向量"""
        if self.embedding_client:
            try:
                if hasattr(self.embedding_client, 'get_single_embedding'):
                    return self.embedding_client.get_single_embedding(text, use_test_data=use_test_data)
                elif hasattr(self.embedding_client, 'get_embeddings'):
                    result = self.embedding_client.get_embeddings([text], use_test_data=use_test_data)
                    return result[0] if result else None
                else:
                    logger.warning("Embedding客户端没有预期的方法")
                    return None
            except Exception as e:
                logger.error(f"获取embedding失败: {e}")
                return None
        else:
            logger.warning("Embedding客户端不可用")
            return None
    
    def chat(self, message: str) -> str:
        """智能对话"""
        if self.chat_manager:
            try:
                if hasattr(self.chat_manager, 'process_message'):
                    return self.chat_manager.process_message(message=message)
                elif hasattr(self.chat_manager, 'send_message'):
                    return self.chat_manager.send_message(message)
                elif hasattr(self.chat_manager, 'get_response'):
                    return self.chat_manager.get_response(message)
                else:
                    return f"收到消息: {message}（模拟回复）"
            except Exception as e:
                logger.error(f"对话处理失败: {e}")
                return f"对话处理失败: {e}"
        else:
            return "对话功能不可用"

# 全局应用实例
_app_instance = None

def get_cms_app() -> CMSDirectApp:
    """获取CMS应用实例（单例模式）"""
    global _app_instance
    if _app_instance is None:
        _app_instance = CMSDirectApp()
    return _app_instance

# 便捷函数
def analyze_vibration(region: str, station: str, position: str, 
                     point: str, start_time: str, end_time: str) -> Dict[str, Any]:
    """分析振动数据的便捷函数"""
    app = get_cms_app()
    return app.analyze_vibration_data(region, station, position, point, start_time, end_time)

def get_text_embedding(text: str, use_test_data: bool = True) -> Optional[List[float]]:
    """获取文本embedding的便捷函数"""
    app = get_cms_app()
    return app.get_embedding(text, use_test_data)

def chat_with_cms(message: str) -> str:
    """与CMS系统对话的便捷函数"""
    app = get_cms_app()
    return app.chat(message)

# 示例使用
if __name__ == "__main__":
    # 配置日志
    logger.add("cms_direct.log", rotation="10 MB", level="INFO")
    
    print("🔧 CMS振动分析系统 - 直接调用版本")
    print("=" * 50)
    
    # 示例1: 分析振动数据
    print("\n📊 示例1: 分析振动数据")
    try:
        result = analyze_vibration(
            region="A08",
            station="1003", 
            position="8",
            point="AI_CMS024",
            start_time="2025-01-12 00:00:00",
            end_time="2025-01-13 00:00:00"
        )
        
        if result["success"]:
            print("✅ 分析完成！")
            print(result["report"])
        else:
            print(f"❌ 分析失败: {result['error']}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    # 示例2: 获取文本embedding
    print("\n🔤 示例2: 获取文本embedding")
    try:
        embedding = get_text_embedding("这是一个测试文本", use_test_data=True)
        if embedding:
            print(f"✅ Embedding生成成功，维度: {len(embedding)}")
            print(f"前5个值: {embedding[:5]}")
        else:
            print("❌ Embedding生成失败")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    # 示例3: 智能对话
    print("\n💬 示例3: 智能对话")
    try:
        response = chat_with_cms("请分析最近的振动趋势")
        print(f"🤖 {response}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    print("\n" + "=" * 50)
    print("演示完成！")