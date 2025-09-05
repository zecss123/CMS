# -*- coding: utf-8 -*-
"""
数据获取器 - 处理外部API数据的获取、缓存和预处理
"""

import asyncio
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from loguru import logger
import json
import hashlib
from pathlib import Path

from api.client import VibrationDataAPIClient
from database.models import WindFarm, Turbine, MeasurementPoint
from database.repository import (
    WindFarmRepository, TurbineRepository, 
    MeasurementPointRepository, AnalysisResultRepository
)
from database.database import DatabaseManager


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache", ttl_seconds: int = 3600):
        """初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            ttl_seconds: 缓存生存时间（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_seconds = ttl_seconds
    
    def _get_cache_key(self, **kwargs) -> str:
        """生成缓存键
        
        Args:
            **kwargs: 缓存参数
            
        Returns:
            str: 缓存键
        """
        # 将参数排序并序列化
        sorted_params = sorted(kwargs.items())
        param_str = json.dumps(sorted_params, sort_keys=True, default=str)
        return hashlib.md5(param_str.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径
        
        Args:
            cache_key: 缓存键
            
        Returns:
            Path: 缓存文件路径
        """
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, **kwargs) -> Optional[Dict[str, Any]]:
        """获取缓存数据
        
        Args:
            **kwargs: 缓存参数
            
        Returns:
            Dict: 缓存数据，过期或不存在时返回None
        """
        cache_key = self._get_cache_key(**kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查是否过期
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > timedelta(seconds=self.ttl_seconds):
                cache_path.unlink()  # 删除过期缓存
                return None
            
            logger.debug(f"缓存命中: {cache_key}")
            return cache_data['data']
            
        except Exception as e:
            logger.warning(f"读取缓存失败: {cache_key}, 错误: {e}")
            return None
    
    def set(self, data: Dict[str, Any], **kwargs) -> None:
        """设置缓存数据
        
        Args:
            data: 要缓存的数据
            **kwargs: 缓存参数
        """
        cache_key = self._get_cache_key(**kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2, default=str)
            logger.debug(f"缓存已保存: {cache_key}")
        except Exception as e:
            logger.warning(f"保存缓存失败: {cache_key}, 错误: {e}")
    
    def clear(self) -> None:
        """清空所有缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("缓存已清空")
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")


class DataFetcher:
    """数据获取器"""
    
    def __init__(self, api_client: VibrationDataAPIClient, 
                 db_manager: DatabaseManager,
                 cache_ttl: int = 3600):
        """初始化数据获取器
        
        Args:
            api_client: API客户端
            db_manager: 数据库管理器
            cache_ttl: 缓存生存时间（秒）
        """
        self.api_client = api_client
        self.db_manager = db_manager
        self.cache = DataCache(ttl_seconds=cache_ttl)
        
        # 初始化仓库
        self.wind_farm_repo = WindFarmRepository()
        self.turbine_repo = TurbineRepository()
        self.measurement_point_repo = MeasurementPointRepository()
        self.analysis_result_repo = AnalysisResultRepository()
    
    async def fetch_measurement_point_data(self, point_id: str,
                                           start_time: Optional[datetime] = None,
                                           end_time: Optional[datetime] = None,
                                           data_type: str = 'trend',
                                           use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """获取测点数据
        
        Args:
            point_id: 测点ID
            start_time: 开始时间
            end_time: 结束时间
            data_type: 数据类型
            use_cache: 是否使用缓存
            
        Returns:
            Dict: 测点数据
        """
        # 检查缓存
        if use_cache:
            cached_data = self.cache.get(
                point_id=point_id,
                start_time=start_time,
                end_time=end_time,
                data_type=data_type
            )
            if cached_data:
                return cached_data
        
        # 从API获取数据
        try:
            data = await self.api_client.get_measurement_point_data(
                point_id=point_id,
                start_time=start_time,
                end_time=end_time,
                data_type=data_type
            )
            
            if data and use_cache:
                # 缓存数据
                self.cache.set(
                    data,
                    point_id=point_id,
                    start_time=start_time,
                    end_time=end_time,
                    data_type=data_type
                )
            
            logger.info(f"获取测点数据成功: {point_id}, 类型: {data_type}")
            return data
            
        except Exception as e:
            logger.error(f"获取测点数据失败: {point_id}, 错误: {e}")
            return None
    
    async def fetch_trend_analysis(self, point_id: str,
                                   analysis_period: int = 30,
                                   use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """获取趋势分析
        
        Args:
            point_id: 测点ID
            analysis_period: 分析周期（天）
            use_cache: 是否使用缓存
            
        Returns:
            Dict: 趋势分析结果
        """
        # 检查缓存
        if use_cache:
            cached_data = self.cache.get(
                point_id=point_id,
                analysis_period=analysis_period,
                analysis_type='trend'
            )
            if cached_data:
                return cached_data
        
        # 从API获取数据
        try:
            data = await self.api_client.get_trend_analysis(
                point_id=point_id,
                analysis_period=analysis_period
            )
            
            if data and use_cache:
                # 缓存数据
                self.cache.set(
                    data,
                    point_id=point_id,
                    analysis_period=analysis_period,
                    analysis_type='trend'
                )
            
            logger.info(f"获取趋势分析成功: {point_id}, 周期: {analysis_period}天")
            return data
            
        except Exception as e:
            logger.error(f"获取趋势分析失败: {point_id}, 错误: {e}")
            return None
    
    async def fetch_all_measurement_points_data(self, wind_farm_id: Optional[int] = None,
                                                turbine_id: Optional[int] = None,
                                                data_type: str = 'trend',
                                                use_cache: bool = True) -> Dict[str, Dict[str, Any]]:
        """获取所有测点数据
        
        Args:
            wind_farm_id: 风场ID，None表示所有风场
            turbine_id: 机组ID，None表示所有机组
            data_type: 数据类型
            use_cache: 是否使用缓存
            
        Returns:
            Dict: 测点数据字典，键为测点ID
        """
        # 获取测点列表
        if turbine_id:
            measurement_points = self.measurement_point_repo.get_by_turbine(turbine_id)
        elif wind_farm_id:
            # 先获取风场下的所有机组
            turbines = self.turbine_repo.get_by_wind_farm(wind_farm_id)
            measurement_points = []
            for turbine in turbines:
                # 确保turbine.id是整数类型
                turbine_id = turbine.id if hasattr(turbine.id, '__int__') else int(turbine.id)
                points = self.measurement_point_repo.get_by_turbine(turbine_id)
                measurement_points.extend(points)
        else:
            # 获取所有测点需要通过查询所有机组实现
            session = self.measurement_point_repo.get_session()
            if session:
                try:
                    measurement_points = session.query(MeasurementPoint).all()
                except Exception as e:
                    logger.error(f"获取所有测点失败: {e}")
                    measurement_points = []
                finally:
                    self.measurement_point_repo.close_session(session)
            else:
                measurement_points = []
        
        # 并发获取数据
        results = {}
        tasks = []
        
        for point in measurement_points:
            task = self.fetch_measurement_point_data(
                point_id=point.point_code,
                data_type=data_type,
                use_cache=use_cache
            )
            tasks.append((point.point_code, task))
        
        # 执行并发任务
        for point_id, task in tasks:
            try:
                data = await task
                if data:
                    results[point_id] = data
            except Exception as e:
                logger.error(f"获取测点数据失败: {point_id}, 错误: {e}")
        
        logger.info(f"批量获取测点数据完成，成功: {len(results)}/{len(measurement_points)}")
        return results
    
    async def fetch_wind_farm_analysis(self, wind_farm_id: int,
                                       analysis_period: int = 30,
                                       use_cache: bool = True) -> Dict[str, Any]:
        """获取风场分析数据
        
        Args:
            wind_farm_id: 风场ID
            analysis_period: 分析周期（天）
            use_cache: 是否使用缓存
            
        Returns:
            Dict: 风场分析数据
        """
        # 获取风场信息
        wind_farm = self.wind_farm_repo.get_by_id(wind_farm_id)
        if not wind_farm:
            logger.error(f"风场不存在: {wind_farm_id}")
            return {}
        
        # 获取风场下所有机组
        turbines = self.turbine_repo.get_by_wind_farm(wind_farm_id)
        
        # 获取所有测点
        all_measurement_points = []
        for turbine in turbines:
            # 确保turbine.id是整数类型
            turbine_id = turbine.id if hasattr(turbine.id, '__int__') else int(turbine.id)
            points = self.measurement_point_repo.get_by_turbine(turbine_id)
            all_measurement_points.extend(points)
        
        # 并发获取趋势分析
        trend_results = {}
        tasks = []
        
        for point in all_measurement_points:
            task = self.fetch_trend_analysis(
                point_id=point.point_code,
                analysis_period=analysis_period,
                use_cache=use_cache
            )
            tasks.append((point.point_code, task))
        
        # 执行并发任务
        for point_id, task in tasks:
            try:
                data = await task
                if data:
                    trend_results[point_id] = data
            except Exception as e:
                logger.error(f"获取趋势分析失败: {point_id}, 错误: {e}")
        
        # 汇总分析结果
        analysis_summary = {
            'wind_farm': wind_farm.to_dict(),
            'turbine_count': len(turbines),
            'measurement_point_count': len(all_measurement_points),
            'analysis_period_days': analysis_period,
            'trend_analysis': trend_results,
            'summary': self._generate_analysis_summary(trend_results),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"风场分析完成: {wind_farm.name}, 测点数: {len(all_measurement_points)}")
        return analysis_summary
    
    def _generate_analysis_summary(self, trend_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """生成分析摘要
        
        Args:
            trend_results: 趋势分析结果
            
        Returns:
            Dict: 分析摘要
        """
        if not trend_results:
            return {'status': 'no_data'}
        
        # 统计报警级别
        alarm_counts = {'normal': 0, 'warning': 0, 'alarm': 0, 'critical': 0}
        total_points = len(trend_results)
        
        for point_id, result in trend_results.items():
            alarm_level = result.get('alarm_level', 'normal')
            if alarm_level in alarm_counts:
                alarm_counts[alarm_level] += 1
        
        # 计算健康度评分（0-100）
        health_score = (
            alarm_counts['normal'] * 100 +
            alarm_counts['warning'] * 70 +
            alarm_counts['alarm'] * 40 +
            alarm_counts['critical'] * 10
        ) / total_points if total_points > 0 else 0
        
        return {
            'total_points': total_points,
            'alarm_distribution': alarm_counts,
            'health_score': round(health_score, 2),
            'status': 'critical' if alarm_counts['critical'] > 0 else
                     'alarm' if alarm_counts['alarm'] > 0 else
                     'warning' if alarm_counts['warning'] > 0 else 'normal'
        }
    
    def sync_fetch_measurement_point_data(self, point_id: str,
                                          start_time: Optional[datetime] = None,
                                          end_time: Optional[datetime] = None,
                                          data_type: str = 'trend',
                                          use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """同步获取测点数据
        
        Args:
            point_id: 测点ID
            start_time: 开始时间
            end_time: 结束时间
            data_type: 数据类型
            use_cache: 是否使用缓存
            
        Returns:
            Dict: 测点数据
        """
        return asyncio.run(self.fetch_measurement_point_data(
            point_id, start_time, end_time, data_type, use_cache
        ))
    
    def sync_fetch_wind_farm_analysis(self, wind_farm_id: int,
                                       analysis_period: int = 30,
                                       use_cache: bool = True) -> Dict[str, Any]:
        """同步获取风场分析数据
        
        Args:
            wind_farm_id: 风场ID
            analysis_period: 分析周期（天）
            use_cache: 是否使用缓存
            
        Returns:
            Dict: 风场分析数据
        """
        return asyncio.run(self.fetch_wind_farm_analysis(
            wind_farm_id, analysis_period, use_cache
        ))
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict: 缓存统计信息
        """
        cache_files = list(self.cache.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'cache_count': len(cache_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'cache_dir': str(self.cache.cache_dir),
            'ttl_seconds': self.cache.ttl_seconds
        }