#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析系统 - API服务启动脚本
"""

import os
import sys
import argparse
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """检查依赖是否安装"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'loguru'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"缺少依赖包: {', '.join(missing_packages)}")
        logger.info("请运行: pip install -r requirements_api.txt")
        return False
    
    return True

def setup_environment():
    """设置环境"""
    # 创建必要的目录
    directories = [
        "output/api_reports",
        "logs",
        "data/temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # 设置日志
    log_file = "logs/api_server.log"
    logger.add(
        log_file,
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    logger.info("环境设置完成")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CMS振动分析系统API服务")
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="开启热重载（开发模式）")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="日志级别")
    
    args = parser.parse_args()
    
    print("="*60)
    print("CMS振动分析系统 - API服务")
    print("="*60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 显示启动信息
    print(f"服务地址: http://{args.host}:{args.port}")
    print(f"API文档: http://{args.host}:{args.port}/docs")
    print(f"ReDoc文档: http://{args.host}:{args.port}/redoc")
    print(f"日志级别: {args.log_level}")
    print(f"热重载: {'开启' if args.reload else '关闭'}")
    print("-"*60)
    
    try:
        import uvicorn
        from cms_api_server import app
        
        # 启动服务
        uvicorn.run(
            "cms_api_server:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1,
            log_level=args.log_level,
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()