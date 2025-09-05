#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS振动分析系统环境检查脚本
用于验证当前环境是否满足系统运行要求
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    print(f"   当前版本: Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("   ✅ Python版本满足要求")
        return True
    else:
        print("   ❌ Python版本过低，需要3.8+")
        return False

def check_required_packages():
    """检查必需的Python包"""
    print("\n📦 检查必需的Python包...")
    
    required_packages = {
        'streamlit': '1.48.0',
        'torch': '2.7.1',
        'transformers': '4.55.0',
        'numpy': '2.2.6',
        'pandas': '2.3.1',
        'matplotlib': '3.10.5',
        'reportlab': '4.4.3',
        'weasyprint': '66.0',
        'chromadb': '1.0.16',
        'jinja2': '3.1.6',
        'fastapi': '0.116.1',
        'sentence_transformers': '5.1.0'
    }
    
    missing_packages = []
    version_mismatches = []
    
    for package, expected_version in required_packages.items():
        try:
            module = importlib.import_module(package.replace('-', '_'))
            if hasattr(module, '__version__'):
                actual_version = module.__version__
                if actual_version == expected_version:
                    print(f"   ✅ {package}: {actual_version}")
                else:
                    print(f"   ⚠️  {package}: {actual_version} (期望: {expected_version})")
                    version_mismatches.append((package, actual_version, expected_version))
            else:
                print(f"   ✅ {package}: 已安装 (无版本信息)")
        except ImportError:
            print(f"   ❌ {package}: 未安装")
            missing_packages.append(package)
    
    return missing_packages, version_mismatches

def check_cuda_availability():
    """检查CUDA可用性"""
    print("\n🚀 检查CUDA支持...")
    
    try:
        import torch
        if torch.cuda.is_available():
            cuda_version = torch.version.cuda
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "未知"
            print(f"   ✅ CUDA可用: {cuda_version}")
            print(f"   ✅ GPU数量: {gpu_count}")
            print(f"   ✅ GPU型号: {gpu_name}")
            return True
        else:
            print("   ⚠️  CUDA不可用，将使用CPU模式")
            return False
    except ImportError:
        print("   ❌ PyTorch未安装，无法检查CUDA")
        return False

def check_model_files():
    """检查模型文件"""
    print("\n🤖 检查模型文件...")
    
    model_paths = {
        'DeepSeek-7B': '/root/autodl-tmp/models/deepseek-7b',
        '嵌入模型缓存': '/root/autodl-tmp/models/embeddings'
    }
    
    for name, path in model_paths.items():
        if os.path.exists(path):
            size = sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file())
            size_gb = size / (1024**3)
            print(f"   ✅ {name}: {path} ({size_gb:.1f}GB)")
        else:
            print(f"   ⚠️  {name}: {path} (不存在)")

def check_config_files():
    """检查配置文件"""
    print("\n⚙️  检查配置文件...")
    
    config_files = {
        '主配置文件': 'config.yaml',
        '依赖文件': 'requirements.txt',
        '说明文档': 'README.md'
    }
    
    for name, filename in config_files.items():
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"   ✅ {name}: {filename} ({size} bytes)")
        else:
            print(f"   ❌ {name}: {filename} (不存在)")

def check_system_resources():
    """检查系统资源"""
    print("\n💻 检查系统资源...")
    
    try:
        import psutil
        
        # 内存检查
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"   💾 总内存: {memory_gb:.1f}GB")
        print(f"   💾 可用内存: {memory.available / (1024**3):.1f}GB")
        
        if memory_gb >= 16:
            print("   ✅ 内存充足")
        else:
            print("   ⚠️  内存可能不足，推荐16GB+")
        
        # 磁盘检查
        disk = psutil.disk_usage('/')
        disk_free_gb = disk.free / (1024**3)
        print(f"   💽 可用磁盘空间: {disk_free_gb:.1f}GB")
        
        if disk_free_gb >= 20:
            print("   ✅ 磁盘空间充足")
        else:
            print("   ⚠️  磁盘空间可能不足，推荐20GB+")
            
    except ImportError:
        print("   ⚠️  psutil未安装，无法检查系统资源")

def main():
    """主函数"""
    print("🔍 CMS振动分析系统环境检查")
    print("=" * 50)
    
    # 检查各项环境
    python_ok = check_python_version()
    missing_packages, version_mismatches = check_required_packages()
    cuda_ok = check_cuda_availability()
    check_model_files()
    check_config_files()
    check_system_resources()
    
    # 总结报告
    print("\n📋 环境检查总结")
    print("=" * 50)
    
    if python_ok and not missing_packages:
        print("✅ 环境检查通过，系统可以正常运行")
        
        if version_mismatches:
            print("\n⚠️  版本不匹配的包:")
            for pkg, actual, expected in version_mismatches:
                print(f"   - {pkg}: {actual} (期望: {expected})")
            print("\n建议运行: pip install -r requirements.txt --force-reinstall")
        
        if cuda_ok:
            print("🚀 GPU加速可用，性能最佳")
        else:
            print("💻 将使用CPU模式，性能可能较慢")
            
    else:
        print("❌ 环境检查失败，需要解决以下问题:")
        
        if not python_ok:
            print("   - 升级Python到3.8+")
        
        if missing_packages:
            print("   - 安装缺失的包:")
            for pkg in missing_packages:
                print(f"     pip install {pkg}")
            print("   或运行: pip install -r requirements.txt")
    
    print("\n🚀 启动命令:")
    print("   streamlit run streamlit_app.py")
    print("   或")
    print("   streamlit run app.py")

if __name__ == "__main__":
    main()