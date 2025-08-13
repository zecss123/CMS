# -*- coding: utf-8 -*-
"""
CMS振动分析报告生成系统配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = Path("/root/autodl-tmp/models")

# 模型配置
MODEL_CONFIG = {
    "model_name": "deepseek-7b",
    "model_path": MODELS_DIR / "deepseek-7b",
    "max_length": 4096,
    "temperature": 0.7,
    "top_p": 0.9,
    "device": "auto",  # auto, cuda, cpu
}

# 向量数据库配置
VECTOR_DB_CONFIG = {
    "persist_directory": PROJECT_ROOT / "data" / "vector_db",
    "collection_name": "cms_vibration_knowledge",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "chunk_size": 500,
    "chunk_overlap": 50,
}

# CMS振动数据配置
CMS_CONFIG = {
    "measurement_points": [
        "1X水平振动",
        "1Y垂直振动", 
        "2X水平振动",
        "2Y垂直振动",
        "3X水平振动",
        "3Y垂直振动"
    ],
    "frequency_range": (0, 1000),  # Hz
    "sampling_rate": 2048,  # Hz
    "data_length": 8192,  # 数据点数
    "alarm_levels": {
        "正常": (0, 2.5),
        "注意": (2.5, 6.3),
        "警告": (6.3, 10.0),
        "危险": (10.0, float('inf'))
    }
}

# 风场和机组配置
WIND_FARM_CONFIG = {
    "farms": {
        "华能风场A": {
            "turbines": [f"A{i:02d}" for i in range(1, 21)],  # A01-A20
            "location": "内蒙古",
            "capacity": "2.0MW"
        },
        "大唐风场B": {
            "turbines": [f"B{i:02d}" for i in range(1, 16)],  # B01-B15
            "location": "新疆", 
            "capacity": "2.5MW"
        },
        "国电风场C": {
            "turbines": [f"C{i:02d}" for i in range(1, 26)],  # C01-C25
            "location": "甘肃",
            "capacity": "3.0MW"
        }
    }
}

# 报告模板配置
REPORT_CONFIG = {
    "template_dir": PROJECT_ROOT / "data" / "templates",
    "output_dir": PROJECT_ROOT / "output",
    "formats": ["docx", "pdf"],
    "company_name": "风电设备状态监测中心",
    "report_title": "CMS振动分析报告",
    "logo_path": None,  # 可选：公司logo路径
}

# Streamlit配置
STREAMLIT_CONFIG = {
    "page_title": "CMS振动分析报告生成系统",
    "page_icon": "⚡",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    "rotation": "10 MB",
    "retention": "7 days",
    "log_file": PROJECT_ROOT / "logs" / "cms_rag.log"
}

# 确保必要目录存在
def ensure_directories():
    """确保必要的目录存在"""
    dirs_to_create = [
        VECTOR_DB_CONFIG["persist_directory"],
        REPORT_CONFIG["output_dir"],
        LOGGING_CONFIG["log_file"].parent,
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_directories()
    print("配置文件加载完成")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"模型路径: {MODEL_CONFIG['model_path']}")