#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析系统 - 报告生成测试脚本
测试API服务的报告生成功能
"""

import requests
import json
import time
import os
from datetime import datetime

# API服务配置
API_BASE_URL = "http://localhost:8000"
API_ENDPOINTS = {
    "generate_report": f"{API_BASE_URL}/generate-report",
    "get_report_status": f"{API_BASE_URL}/report-status/{{report_id}}",
    "download_report": f"{API_BASE_URL}/download-report/{{report_id}}",
    "health_check": f"{API_BASE_URL}/health"
}

def test_health_check():
    """测试API服务健康状态"""
    print("\n=== 测试API服务健康状态 ===")
    try:
        response = requests.get(API_ENDPOINTS["health_check"], timeout=10)
        if response.status_code == 200:
            print("✅ API服务运行正常")
            print(f"响应: {response.json()}")
            return True
        else:
            print(f"❌ API服务异常，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到API服务: {e}")
        return False

def test_report_generation(output_format="pdf"):
    """测试报告生成功能"""
    print(f"\n=== 测试{output_format.upper()}报告生成 ===")
    
    # 构造测试请求数据 - 包含多个CMS问题的异常情况
    test_data = {
        "title": "CMS振动分析测试报告 - 紧急故障诊断",
        "basic_info": {
            "wind_farm": "某重工企业",
            "turbine_id": "COMP-002",
            "measurement_date": "2024-09-04",
            "operator": "李工程师",
            "equipment_status": "异常运行"
        },
        "measurement_results": [
            {
                "measurement_point": "压缩机轴承座水平",
                "rms_value": 12.8,
                "peak_value": 45.2,
                "main_frequency": 47.5,
                "alarm_level": "critical",
                "rms_acceleration": 8.5,
                "peak_acceleration": 28.6,
                "temperature": 85.3,
                "status": "严重报警"
            },
            {
                "measurement_point": "压缩机轴承座垂直",
                "rms_value": 15.6,
                "peak_value": 52.8,
                "main_frequency": 142.5,
                "alarm_level": "critical",
                "rms_acceleration": 11.2,
                "peak_acceleration": 35.4,
                "temperature": 87.1,
                "status": "严重报警"
            },
            {
                "measurement_point": "电机驱动端轴向",
                "rms_value": 8.9,
                "peak_value": 32.1,
                "main_frequency": 95.0,
                "alarm_level": "warning",
                "rms_acceleration": 5.8,
                "peak_acceleration": 19.7,
                "temperature": 78.9,
                "status": "中度报警"
            },
            {
                "measurement_point": "齿轮箱输入端",
                "rms_value": 18.3,
                "peak_value": 68.7,
                "main_frequency": 285.0,
                "alarm_level": "critical",
                "rms_acceleration": 14.6,
                "peak_acceleration": 48.9,
                "temperature": 92.5,
                "status": "极严重报警"
            },
            {
                "measurement_point": "联轴器处径向",
                "rms_value": 11.2,
                "peak_value": 38.9,
                "main_frequency": 190.0,
                "alarm_level": "critical",
                "rms_acceleration": 7.8,
                "peak_acceleration": 26.3,
                "temperature": 81.7,
                "status": "严重报警"
            }
        ],
        "executive_summary": "设备存在多个严重故障，包括转子不平衡、对中不良、齿轮磨损等问题，需要立即停机检修。",
        "analysis_conclusion": "经过详细的振动分析，发现设备存在以下严重问题：1)转子严重不平衡；2)联轴器对中不良；3)齿轮箱内部磨损严重；4)轴承可能存在缺陷；5)整体温度异常升高。建议立即停机进行全面检修。",
        "recommendations": [
            "立即停机，避免设备进一步损坏",
            "检查并重新平衡转子",
            "重新校正联轴器对中",
            "拆检齿轮箱，更换磨损齿轮",
            "检查并更换损坏轴承",
            "检查润滑系统，更换润滑油",
            "检修后进行试运行和振动复测",
            "建立更频繁的在线监测计划"
        ],
        "output_format": output_format,
        "include_charts": True,
        "template_type": "vibration_analysis"
    }
    
    try:
        # 发送报告生成请求
        print("📤 发送报告生成请求...")
        # 添加API密钥认证
        headers = {
            "Authorization": "Bearer cms-api-key-2024",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            API_ENDPOINTS["generate_report"],
            json=test_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ 报告生成请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
        result = response.json()
        if result.get("success"):
            report_id = result.get("data", {}).get("task_id")
            
            if not report_id:
                print("❌ 未获取到报告ID")
                return None
                
            print(f"✅ 报告生成请求成功，报告ID: {report_id}")
            return report_id
        else:
            print(f"❌ 报告生成失败: {result.get('message', '未知错误')}")
            return None
        
    except Exception as e:
        print(f"❌ 报告生成请求异常: {e}")
        return None

def check_report_status(report_id, max_wait_time=60):
    """检查报告生成状态"""
    print(f"\n=== 检查报告状态 (ID: {report_id}) ===")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            status_url = API_ENDPOINTS["get_report_status"].format(report_id=report_id)
            headers = {"Authorization": "Bearer cms-api-key-2024"}
            response = requests.get(status_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    status_data = result.get("data", {})
                    status = status_data.get("status")
                    progress = status_data.get("progress", 0)
                    
                    print(f"📊 报告状态: {status}, 进度: {progress}%")
                    
                    if status == "completed":
                        print("✅ 报告生成完成")
                        return True
                    elif status == "failed":
                        error_msg = status_data.get("error_message", "未知错误")
                        print(f"❌ 报告生成失败: {error_msg}")
                        return False
                else:
                    print(f"❌ 获取状态失败: {result.get('message', '未知错误')}")
                    return False
                    
            time.sleep(2)  # 等待2秒后再次检查
            
        except Exception as e:
            print(f"❌ 检查报告状态异常: {e}")
            time.sleep(2)
    
    print(f"⏰ 等待超时 ({max_wait_time}秒)")
    return False

def download_report(report_id, save_dir="./test_reports"):
    """下载生成的报告"""
    print(f"\n=== 下载报告 (ID: {report_id}) ===")
    
    try:
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
        
        download_url = API_ENDPOINTS["download_report"].format(report_id=report_id)
        headers = {"Authorization": "Bearer cms-api-key-2024"}
        response = requests.get(download_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # 从响应头获取文件名
            content_disposition = response.headers.get('content-disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            else:
                # 默认文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"cms_report_{timestamp}.pdf"
            
            file_path = os.path.join(save_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"✅ 报告下载成功")
            print(f"📁 保存路径: {file_path}")
            print(f"📊 文件大小: {file_size} 字节")
            
            return file_path
        else:
            print(f"❌ 报告下载失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 报告下载异常: {e}")
        return None

def test_complete_workflow():
    """测试完整的报告生成工作流程"""
    print("\n" + "="*50)
    print("🚀 开始测试CMS振动分析系统报告生成功能")
    print("="*50)
    
    # 1. 健康检查
    if not test_health_check():
        print("\n❌ API服务不可用，测试终止")
        return False
    
    # 2. 测试不同格式的报告生成
    formats_to_test = ["pdf", "html", "docx"]
    successful_tests = 0
    
    for format_type in formats_to_test:
        print(f"\n{'='*30}")
        print(f"测试 {format_type.upper()} 格式报告")
        print(f"{'='*30}")
        
        # 生成报告
        report_id = test_report_generation(format_type)
        if not report_id:
            print(f"❌ {format_type.upper()} 报告生成失败")
            continue
        
        # 检查状态
        if not check_report_status(report_id):
            print(f"❌ {format_type.upper()} 报告状态检查失败")
            continue
        
        # 下载报告
        file_path = download_report(report_id)
        if file_path:
            print(f"✅ {format_type.upper()} 报告测试成功")
            successful_tests += 1
        else:
            print(f"❌ {format_type.upper()} 报告下载失败")
    
    # 测试结果汇总
    print("\n" + "="*50)
    print("📋 测试结果汇总")
    print("="*50)
    print(f"总测试数: {len(formats_to_test)}")
    print(f"成功数: {successful_tests}")
    print(f"失败数: {len(formats_to_test) - successful_tests}")
    print(f"成功率: {successful_tests/len(formats_to_test)*100:.1f}%")
    
    if successful_tests == len(formats_to_test):
        print("\n🎉 所有测试通过！API服务工作正常")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查API服务")
        return False

if __name__ == "__main__":
    # 运行完整测试
    success = test_complete_workflow()
    
    if success:
        print("\n✅ 测试完成：API服务报告生成功能正常")
    else:
        print("\n❌ 测试完成：发现问题，请检查服务状态")
        exit(1)