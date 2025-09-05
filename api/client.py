# -*- coding: utf-8 -*-
"""
API客户端 - 处理与外部数据源的HTTP通信
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from loguru import logger
import json


class APIClient:
    """API客户端类"""
    
    def __init__(self, base_url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None):
        """初始化API客户端
        
        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            headers: 默认请求头
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.default_headers = headers or {}
        self.session: Optional[httpx.AsyncClient] = None
        
        # 默认请求头
        self.default_headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'CMS-Vibration-RAG/1.0'
        })
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
    
    async def connect(self) -> None:
        """建立连接"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self.default_headers,
                verify=False  # 在生产环境中应该设置为True
            )
            logger.info(f"API客户端连接成功: {self.base_url}")
    
    async def disconnect(self) -> None:
        """断开连接"""
        if self.session:
            await self.session.aclose()
            self.session = None
            logger.info("API客户端连接已断开")
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                  headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """发送GET请求
        
        Args:
            endpoint: API端点
            params: 查询参数
            headers: 额外请求头
            
        Returns:
            Dict: 响应数据，失败时返回None
        """
        return await self._request('GET', endpoint, params=params, headers=headers)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
                   params: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """发送POST请求
        
        Args:
            endpoint: API端点
            data: 请求体数据
            params: 查询参数
            headers: 额外请求头
            
        Returns:
            Dict: 响应数据，失败时返回None
        """
        return await self._request('POST', endpoint, data=data, params=params, headers=headers)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
                  params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """发送PUT请求
        
        Args:
            endpoint: API端点
            data: 请求体数据
            params: 查询参数
            headers: 额外请求头
            
        Returns:
            Dict: 响应数据，失败时返回None
        """
        return await self._request('PUT', endpoint, data=data, params=params, headers=headers)
    
    async def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """发送DELETE请求
        
        Args:
            endpoint: API端点
            params: 查询参数
            headers: 额外请求头
            
        Returns:
            Dict: 响应数据，失败时返回None
        """
        return await self._request('DELETE', endpoint, params=params, headers=headers)
    
    async def _request(self, method: str, endpoint: str, 
                       data: Optional[Dict[str, Any]] = None,
                       params: Optional[Dict[str, Any]] = None,
                       headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求体数据
            params: 查询参数
            headers: 额外请求头
            
        Returns:
            Dict: 响应数据，失败时返回None
        """
        if not self.session:
            await self.connect()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            logger.debug(f"发送{method}请求: {url}")
            
            # 构建请求参数
            request_kwargs = {
                'method': method,
                'url': url,
                'headers': request_headers,
                'params': params
            }
            
            if data and method in ['POST', 'PUT', 'PATCH']:
                request_kwargs['json'] = data
            
            # 发送请求
            if self.session is None:
                logger.error("会话未初始化")
                return None
            response = await self.session.request(**request_kwargs)
            
            # 检查响应状态
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.debug(f"请求成功: {url}, 状态码: {response.status_code}")
                    return result
                except json.JSONDecodeError:
                    logger.warning(f"响应不是有效的JSON: {url}")
                    return {'text': response.text}
            else:
                logger.error(f"请求失败: {url}, 状态码: {response.status_code}, 响应: {response.text}")
                return None
                
        except httpx.TimeoutException:
            logger.error(f"请求超时: {url}")
            return None
        except httpx.ConnectError:
            logger.error(f"连接失败: {url}")
            return None
        except Exception as e:
            logger.error(f"请求异常: {url}, 错误: {e}")
            return None
    
    def sync_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """同步GET请求
        
        Args:
            endpoint: API端点
            params: 查询参数
            headers: 额外请求头
            
        Returns:
            Dict: 响应数据，失败时返回None
        """
        return asyncio.run(self.get(endpoint, params, headers))
    
    def sync_post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
                  params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """同步POST请求
        
        Args:
            endpoint: API端点
            data: 请求体数据
            params: 查询参数
            headers: 额外请求头
            
        Returns:
            Dict: 响应数据，失败时返回None
        """
        return asyncio.run(self.post(endpoint, data, params, headers))
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 服务是否健康
        """
        try:
            response = await self.get('/health')
            return response is not None
        except Exception:
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息
        
        Returns:
            Dict: 连接信息
        """
        return {
            'base_url': self.base_url,
            'timeout': self.timeout,
            'connected': self.session is not None,
            'headers': self.default_headers
        }


class VibrationDataAPIClient(APIClient):
    """振动数据API客户端"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, **kwargs):
        """初始化振动数据API客户端
        
        Args:
            base_url: API基础URL
            api_key: API密钥
            **kwargs: 其他参数传递给父类
        """
        headers = kwargs.get('headers', {})
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        kwargs['headers'] = headers
        
        super().__init__(base_url, **kwargs)
    
    async def get_measurement_point_data(self, point_id: str, 
                                         start_time: Optional[datetime] = None,
                                         end_time: Optional[datetime] = None,
                                         data_type: str = 'trend') -> Optional[Dict[str, Any]]:
        """获取测点数据
        
        Args:
            point_id: 测点ID
            start_time: 开始时间
            end_time: 结束时间
            data_type: 数据类型 (trend/spectrum/envelope)
            
        Returns:
            Dict: 测点数据
        """
        params = {
            'point_id': point_id,
            'data_type': data_type
        }
        
        if start_time:
            params['start_time'] = start_time.isoformat()
        if end_time:
            params['end_time'] = end_time.isoformat()
        
        return await self.get('/api/v1/measurement-data', params=params)
    
    async def get_trend_analysis(self, point_id: str,
                                 analysis_period: int = 30) -> Optional[Dict[str, Any]]:
        """获取趋势分析
        
        Args:
            point_id: 测点ID
            analysis_period: 分析周期（天）
            
        Returns:
            Dict: 趋势分析结果
        """
        params = {
            'point_id': point_id,
            'period_days': analysis_period
        }
        
        return await self.get('/api/v1/trend-analysis', params=params)
    
    async def get_spectrum_data(self, point_id: str,
                                timestamp: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """获取频谱数据
        
        Args:
            point_id: 测点ID
            timestamp: 时间戳，None表示最新数据
            
        Returns:
            Dict: 频谱数据
        """
        params = {'point_id': point_id}
        
        if timestamp:
            params['timestamp'] = timestamp.isoformat()
        
        return await self.get('/api/v1/spectrum-data', params=params)
    
    async def get_alarm_status(self, point_id: str) -> Optional[Dict[str, Any]]:
        """获取报警状态
        
        Args:
            point_id: 测点ID
            
        Returns:
            Dict: 报警状态信息
        """
        params = {'point_id': point_id}
        return await self.get('/api/v1/alarm-status', params=params)
    
    async def batch_get_measurement_data(self, point_ids: List[str],
                                         data_type: str = 'trend') -> Optional[Dict[str, Any]]:
        """批量获取测点数据
        
        Args:
            point_ids: 测点ID列表
            data_type: 数据类型
            
        Returns:
            Dict: 批量数据结果
        """
        data = {
            'point_ids': point_ids,
            'data_type': data_type
        }
        
        return await self.post('/api/v1/batch-measurement-data', data=data)
    
    def sync_get_measurement_point_data(self, point_id: str, 
                                        start_time: Optional[datetime] = None,
                                        end_time: Optional[datetime] = None,
                                        data_type: str = 'trend') -> Optional[Dict[str, Any]]:
        """同步获取测点数据
        
        Args:
            point_id: 测点ID
            start_time: 开始时间
            end_time: 结束时间
            data_type: 数据类型
            
        Returns:
            Dict: 测点数据
        """
        return asyncio.run(self.get_measurement_point_data(point_id, start_time, end_time, data_type))
    
    def sync_get_trend_analysis(self, point_id: str,
                                analysis_period: int = 30) -> Optional[Dict[str, Any]]:
        """同步获取趋势分析
        
        Args:
            point_id: 测点ID
            analysis_period: 分析周期（天）
            
        Returns:
            Dict: 趋势分析结果
        """
        return asyncio.run(self.get_trend_analysis(point_id, analysis_period))