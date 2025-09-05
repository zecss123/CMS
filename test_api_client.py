#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析系统 - API客户端测试脚本
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime

class CMSAPIClient:
    """CMS API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "cms-api-key-2024"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告"""
        try:
            response = requests.post(
                f"{self.base_url}/generate-report",
                headers=self.headers,
                json=report_data,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_report_status(self, task_id: str) -> Dict[str, Any]:
        """查询报告状态"""
        try:
            response = requests.get(
                f"{self.base_url}/report-status/{task_id}",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_report(self, task_id: str, save_path: str) -> bool:
        """下载报告"""
        try:
            response = requests.get(
                f"{self.base_url}/download-report/{task_id}",
                headers=self.headers,
                timeout=60
            )
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"下载失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"下载异常: {e}")
            return False
    
    def chat(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """聊天对话"""
        try:
            data = {"message": message}
            if session_id:
                data["session_id"] = session_id
            
            response = requests.post(
                f"{self.base_url}/chat",
                headers=self.headers,
                json=data,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def cleanup_reports(self) -> Dict[str, Any]:
        """清理旧报告"""
        try:
            response = requests.delete(
                f"{self.base_url}/cleanup-reports",
                headers=self.headers,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

def create_test_report_data() -> Dict[str, Any]:
    """创建测试报告数据"""
    return {
        "title": "API测试振动分析报告",
        "basic_info": {
            "wind_farm": "测试风场A",
            "turbine_id": "WT-API-001",
            "measurement_date": "2024-01-20",
            "operator": "API测试员",
            "equipment_status": "运行中"
        },
        "executive_summary": "通过API接口生成的测试报告，用于验证系统功能。设备运行状态良好，各项指标正常。",
        "measurement_results": [
            {
                "measurement_point": "主轴承DE",
                "rms_value": 2.8,
                "peak_value": 9.1,
                "main_frequency": 28.5,
                "alarm_level": "normal"
            },
            {
                "measurement_point": "齿轮箱HSS",
                "rms_value": 4.5,
                "peak_value": 14.2,
                "main_frequency": 1280.0,
                "alarm_level": "warning"
            },
            {
                "measurement_point": "发电机DE",
                "rms_value": 3.2,
                "peak_value": 10.8,
                "main_frequency": 50.0,
                "alarm_level": "normal"
            }
        ],
        "analysis_conclusion": "设备整体运行状态良好，齿轮箱HSS测点存在轻微异常，建议加强监测。",
        "recommendations": [
            "定期检查齿轮箱润滑系统",
            "增加HSS测点监测频次",
            "建议下次检测时间：2个月后",
            "关注温度变化趋势"
        ],
        "output_format": "pdf",
        "include_charts": True,
        "template_type": "vibration_analysis"
    }

def test_api_functionality():
    """测试API功能"""
    print("="*60)
    print("CMS振动分析系统 - API功能测试")
    print("="*60)
    
    # 初始化客户端
    client = CMSAPIClient()
    
    # 1. 测试连接
    print("\n1. 测试API连接...")
    if client.test_connection():
        print("✓ 连接成功")
    else:
        print("✗ 连接失败，请确保API服务已启动")
        return
    
    # 2. 健康检查
    print("\n2. 健康检查...")
    health = client.health_check()
    if health.get("success"):
        print("✓ 服务健康")
        print(f"  状态: {health['data']['status']}")
        components = health['data']['components']
        for comp, status in components.items():
            print(f"  {comp}: {'✓' if status else '✗'}")
    else:
        print(f"✗ 健康检查失败: {health.get('error')}")
    
    # 3. 测试报告生成
    print("\n3. 测试报告生成...")
    report_data = create_test_report_data()
    
    # 测试不同格式
    formats = ["pdf", "html", "docx"]
    
    for fmt in formats:
        print(f"\n3.{formats.index(fmt)+1} 测试{fmt.upper()}格式报告生成...")
        report_data["output_format"] = fmt
        
        # 提交生成任务
        result = client.generate_report(report_data)
        if not result.get("success"):
            print(f"✗ 任务创建失败: {result.get('error')}")
            continue
        
        task_id = result["data"]["task_id"]
        print(f"✓ 任务已创建: {task_id}")
        
        # 等待完成
        print("  等待报告生成...")
        max_wait = 120  # 最大等待2分钟
        wait_time = 0
        
        while wait_time < max_wait:
            status_result = client.get_report_status(task_id)
            if not status_result.get("success"):
                print(f"✗ 状态查询失败: {status_result.get('error')}")
                break
            
            status_data = status_result["data"]
            status = status_data["status"]
            progress = status_data["progress"]
            
            print(f"\r  进度: {progress}% ({status})", end="", flush=True)
            
            if status == "completed":
                print("\n✓ 报告生成完成")
                
                # 下载报告
                download_path = f"test_report_{fmt}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}"
                if client.download_report(task_id, download_path):
                    print(f"✓ 报告已下载: {download_path}")
                    print(f"  文件大小: {os.path.getsize(download_path)} bytes")
                else:
                    print("✗ 报告下载失败")
                break
                
            elif status == "failed":
                error_msg = status_data.get("error_message", "未知错误")
                print(f"\n✗ 报告生成失败: {error_msg}")
                break
            
            time.sleep(2)
            wait_time += 2
        
        if wait_time >= max_wait:
            print("\n✗ 等待超时")
    
    # 4. 测试聊天功能
    print("\n\n4. 测试聊天功能...")
    chat_messages = [
        "你好，请介绍一下CMS系统",
        "如何分析振动数据？",
        "什么是RMS值？"
    ]
    
    session_id = None
    for i, message in enumerate(chat_messages, 1):
        print(f"\n4.{i} 用户: {message}")
        chat_result = client.chat(message, session_id)
        
        if chat_result.get("success"):
            response_data = chat_result["data"]
            response = response_data.get("response", "")
            session_id = response_data.get("session_id")
            
            print(f"✓ 系统: {response[:100]}{'...' if len(response) > 100 else ''}")
            
            if response_data.get("intent"):
                print(f"  意图: {response_data['intent']}")
        else:
            print(f"✗ 聊天失败: {chat_result.get('error')}")
    
    # 5. 测试清理功能
    print("\n\n5. 测试清理功能...")
    cleanup_result = client.cleanup_reports()
    if cleanup_result.get("success"):
        data = cleanup_result["data"]
        print(f"✓ 清理完成")
        print(f"  删除文件: {data['deleted_files']} 个")
        print(f"  删除任务: {data['deleted_tasks']} 个")
    else:
        print(f"✗ 清理失败: {cleanup_result.get('error')}")
    
    print("\n" + "="*60)
    print("API功能测试完成")
    print("="*60)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CMS API客户端测试")
    parser.add_argument("--url", default="http://localhost:8000", help="API服务地址")
    parser.add_argument("--key", default="cms-api-key-2024", help="API密钥")
    parser.add_argument("--test", choices=["all", "connection", "health", "report", "chat"], 
                       default="all", help="测试类型")
    
    args = parser.parse_args()
    
    if args.test == "all":
        test_api_functionality()
    else:
        client = CMSAPIClient(args.url, args.key)
        
        if args.test == "connection":
            print("测试连接:", "成功" if client.test_connection() else "失败")
        elif args.test == "health":
            result = client.health_check()
            print("健康检查:", json.dumps(result, indent=2, ensure_ascii=False))
        elif args.test == "report":
            data = create_test_report_data()
            result = client.generate_report(data)
            print("报告生成:", json.dumps(result, indent=2, ensure_ascii=False))
        elif args.test == "chat":
            result = client.chat("你好，请介绍一下系统功能")
            print("聊天测试:", json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()