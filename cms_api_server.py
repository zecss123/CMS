# -*- coding: utf-8 -*-
"""
CMS振动分析系统 - 后端API服务
提供RESTful API接口用于报告生成和数据分析
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import os
import json
import asyncio
from loguru import logger
import uvicorn

# 导入现有模块
from report.generator import CMSReportGenerator
from api.real_cms_client import RealCMSAPIClient
from chat.chat_manager import ChatManager
from config.config_loader import ConfigLoader
from utils.chart_generator import VibrationChartGenerator
# from utils.data_processor import DataProcessor  # 暂时注释，如果不存在的话

# API模型定义
class BasicInfo(BaseModel):
    """基本信息模型"""
    wind_farm: str = Field(..., description="风场名称")
    turbine_id: str = Field(..., description="风机编号")
    measurement_date: str = Field(..., description="测量日期")
    operator: str = Field(..., description="操作员")
    equipment_status: str = Field(default="运行中", description="设备状态")
    report_date: Optional[str] = Field(default=None, description="报告日期")

class MeasurementResult(BaseModel):
    """测量结果模型"""
    measurement_point: str = Field(..., description="测量点")
    rms_value: float = Field(..., description="RMS值")
    peak_value: float = Field(..., description="峰值")
    main_frequency: float = Field(..., description="主频率")
    alarm_level: str = Field(default="normal", description="报警级别")

class ReportRequest(BaseModel):
    """报告生成请求模型"""
    title: str = Field(default="CMS振动分析报告", description="报告标题")
    basic_info: BasicInfo = Field(..., description="基本信息")
    executive_summary: Optional[str] = Field(default=None, description="执行摘要")
    measurement_results: List[MeasurementResult] = Field(default=[], description="测量结果")
    analysis_conclusion: Optional[str] = Field(default=None, description="分析结论")
    recommendations: List[str] = Field(default=[], description="建议措施")
    output_format: str = Field(default="pdf", description="输出格式: pdf, html, docx")
    include_charts: bool = Field(default=True, description="是否包含图表")
    template_type: str = Field(default="vibration_analysis", description="模板类型")

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")

class APIResponse(BaseModel):
    """API响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")
    error: Optional[str] = Field(default=None, description="错误信息")

class ReportStatus(BaseModel):
    """报告状态模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="状态: pending, processing, completed, failed")
    progress: int = Field(default=0, description="进度百分比")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    file_path: Optional[str] = Field(default=None, description="文件路径")
    error_message: Optional[str] = Field(default=None, description="错误消息")

# 全局变量
app = FastAPI(
    title="CMS振动分析系统API",
    description="提供振动分析报告生成和智能问答服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全配置
security = HTTPBearer()

# 全局实例
report_generator = None
api_client = None
chat_manager = None
config_loader = None
chart_generator = None
# data_processor = None  # 暂时注释

# 任务状态存储
task_status: Dict[str, ReportStatus] = {}

# API密钥配置（生产环境应从环境变量或配置文件读取）
VALID_API_KEYS = {
    "cms-api-key-2024": "default",
    "test-key-123": "test"
}

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证API密钥"""
    token = credentials.credentials
    if token not in VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return VALID_API_KEYS[token]

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global report_generator, api_client, chat_manager, config_loader, chart_generator, data_processor
    
    try:
        # 初始化配置加载器
        config_loader = ConfigLoader()
        
        # 初始化报告生成器
        report_generator = CMSReportGenerator()
        
        # 初始化API客户端
        api_client = RealCMSAPIClient()
        
        # 初始化聊天管理器
        try:
            chat_manager = ChatManager(config_loader.config if config_loader and hasattr(config_loader, 'config') else {})
        except Exception as e:
            logger.warning(f"聊天管理器初始化失败: {e}")
            chat_manager = None
        
        # 初始化图表生成器
        chart_generator = VibrationChartGenerator()
        
        # 初始化数据处理器
        # data_processor = DataProcessor()  # 暂时注释
        
        # 创建输出目录
        output_dir = Path("output/api_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("CMS API服务启动成功")
        
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise

@app.get("/", response_model=APIResponse)
async def root():
    """根路径 - 服务状态检查"""
    return APIResponse(
        success=True,
        message="CMS振动分析系统API服务运行正常",
        data={
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "endpoints": [
                "/docs",
                "/generate-report",
                "/chat",
                "/report-status/{task_id}",
                "/download-report/{task_id}"
            ]
        }
    )

@app.post("/generate-report", response_model=APIResponse)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """生成振动分析报告"""
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务状态
        task_status[task_id] = ReportStatus(
            task_id=task_id,
            status="pending",
            progress=0,
            created_at=datetime.now()
        )
        
        # 添加后台任务
        background_tasks.add_task(
            process_report_generation,
            task_id,
            request
        )
        
        return APIResponse(
            success=True,
            message="报告生成任务已创建",
            data={
                "task_id": task_id,
                "status": "pending",
                "estimated_time": "30-60秒"
            }
        )
        
    except Exception as e:
        logger.error(f"创建报告生成任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_report_generation(task_id: str, request: ReportRequest):
    """处理报告生成任务"""
    try:
        # 更新状态为处理中
        task_status[task_id].status = "processing"
        task_status[task_id].progress = 10
        
        # 准备报告数据
        report_data = {
            "title": request.title,
            "basic_info": request.basic_info.dict(),
            "executive_summary": request.executive_summary,
            "measurement_results": [result.dict() for result in request.measurement_results],
            "analysis_conclusion": request.analysis_conclusion,
            "recommendations": request.recommendations
        }
        
        # 设置报告日期
        if not report_data["basic_info"].get("report_date"):
            report_data["basic_info"]["report_date"] = datetime.now().strftime("%Y-%m-%d")
        
        task_status[task_id].progress = 30
        
        # 生成图表（如果需要）
        if request.include_charts and request.measurement_results:
            try:
                charts = await generate_charts_for_report(request.measurement_results)
                report_data["charts"] = charts
                task_status[task_id].progress = 60
            except Exception as e:
                logger.warning(f"图表生成失败: {e}")
        
        # 生成报告文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cms_report_{timestamp}_{task_id[:8]}.{request.output_format}"
        output_path = f"output/api_reports/{filename}"
        
        task_status[task_id].progress = 80
        
        # 调用报告生成器
        if report_generator:
            if request.output_format.lower() == "pdf":
                success = report_generator.generate_pdf_report(report_data, output_path)
            elif request.output_format.lower() == "html":
                success = report_generator.generate_html_report(report_data, output_path)
            elif request.output_format.lower() == "docx":
                success = report_generator.generate_docx_report(report_data, output_path)
            else:
                raise ValueError(f"不支持的输出格式: {request.output_format}")
        else:
            raise ValueError("报告生成器不可用")
        
        if success:
            task_status[task_id].status = "completed"
            task_status[task_id].progress = 100
            task_status[task_id].completed_at = datetime.now()
            task_status[task_id].file_path = output_path
            logger.info(f"报告生成成功: {output_path}")
        else:
            raise Exception("报告生成失败")
            
    except Exception as e:
        task_status[task_id].status = "failed"
        task_status[task_id].error_message = str(e)
        logger.error(f"报告生成任务失败 {task_id}: {e}")

async def generate_charts_for_report(measurement_results: List[MeasurementResult]) -> Dict[str, str]:
    """为报告生成图表"""
    import numpy as np
    charts = {}
    
    try:
        # 提取数据
        points = [result.measurement_point for result in measurement_results]
        rms_values = [result.rms_value for result in measurement_results]
        peak_values = [result.peak_value for result in measurement_results]
        frequencies = [result.main_frequency for result in measurement_results]
        
        # 生成RMS值图表
        if chart_generator:
            rms_chart = chart_generator.create_time_series_chart(
                signal=np.array(rms_values),
                title="RMS值分布"
            )
            if rms_chart:
                charts["rms_distribution"] = rms_chart
        
        # 生成峰值图表
        if chart_generator:
            peak_chart = chart_generator.create_frequency_spectrum(
                frequencies=np.array(range(len(peak_values))),
                magnitudes=np.array(peak_values),
                title="峰值分布"
            )
            if peak_chart:
                charts["peak_distribution"] = peak_chart
        
        # 生成频率图表
        if chart_generator:
            trend_data = [{'timestamp': f'Point_{i}', 'rms_value': freq} for i, freq in enumerate(frequencies)]
            freq_chart = chart_generator.create_trend_chart(
                trend_data=trend_data,
                title="主频率分布"
            )
            if freq_chart:
                charts["frequency_distribution"] = freq_chart
            
    except Exception as e:
        logger.error(f"图表生成失败: {e}")
    
    return charts

@app.get("/report-status/{task_id}", response_model=APIResponse)
async def get_report_status(task_id: str, api_key: str = Depends(verify_api_key)):
    """查询报告生成状态"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    status = task_status[task_id]
    return APIResponse(
        success=True,
        message="状态查询成功",
        data=status.dict()
    )

@app.get("/download-report/{task_id}")
async def download_report(task_id: str, api_key: str = Depends(verify_api_key)):
    """下载生成的报告"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    status = task_status[task_id]
    
    if status.status != "completed":
        raise HTTPException(status_code=400, detail="报告尚未生成完成")
    
    if not status.file_path or not os.path.exists(status.file_path):
        raise HTTPException(status_code=404, detail="报告文件不存在")
    
    filename = os.path.basename(status.file_path)
    return FileResponse(
        path=status.file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.post("/chat", response_model=APIResponse)
async def chat_with_system(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """与系统进行智能对话"""
    try:
        # 处理聊天请求
        if not chat_manager:
            raise HTTPException(status_code=503, detail="聊天服务不可用")
            
        response = chat_manager.process_message(
            user_id="api_user",
            message=request.message,
            session_id=request.session_id,
            stream=False
        )
        
        return APIResponse(
            success=True,
            message="对话处理成功",
            data={
                "response": response.get("response", ""),
                "session_id": response.get("session_id"),
                "intent": response.get("intent"),
                "entities": response.get("entities", {}),
                "suggestions": response.get("suggestions", [])
            }
        )
        
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=APIResponse)
async def health_check():
    """健康检查"""
    try:
        # 检查各组件状态
        components_status = {
            "report_generator": report_generator is not None,
            "api_client": api_client is not None,
            "chat_manager": chat_manager is not None,
            "config_loader": config_loader is not None
        }
        
        all_healthy = all(components_status.values())
        
        return APIResponse(
            success=all_healthy,
            message="健康检查完成",
            data={
                "status": "healthy" if all_healthy else "unhealthy",
                "components": components_status,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return APIResponse(
            success=False,
            message="健康检查失败",
            error=str(e)
        )

@app.delete("/cleanup-reports", response_model=APIResponse)
async def cleanup_old_reports(api_key: str = Depends(verify_api_key)):
    """清理旧报告文件"""
    try:
        output_dir = Path("output/api_reports")
        if not output_dir.exists():
            return APIResponse(
                success=True,
                message="无需清理",
                data={"deleted_files": 0}
            )
        
        # 删除7天前的文件
        cutoff_time = datetime.now() - timedelta(days=7)
        deleted_count = 0
        
        for file_path in output_dir.iterdir():
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
        
        # 清理过期的任务状态
        expired_tasks = [
            task_id for task_id, status in task_status.items()
            if status.created_at < cutoff_time
        ]
        
        for task_id in expired_tasks:
            del task_status[task_id]
        
        return APIResponse(
            success=True,
            message="清理完成",
            data={
                "deleted_files": deleted_count,
                "deleted_tasks": len(expired_tasks)
            }
        )
        
    except Exception as e:
        logger.error(f"清理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 开发环境运行
    uvicorn.run(
        "cms_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )