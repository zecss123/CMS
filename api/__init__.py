# -*- coding: utf-8 -*-
"""
API模块 - 用于与外部数据源进行交互
"""

from .client import APIClient
from .data_fetcher import DataFetcher
from .trend_analyzer import TrendAnalyzer

__all__ = [
    'APIClient',
    'DataFetcher',
    'TrendAnalyzer'
]