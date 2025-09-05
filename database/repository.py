# -*- coding: utf-8 -*-
"""
数据库仓库 - 提供各个模型的CRUD操作
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger

from .models import WindFarm, Turbine, MeasurementPoint, AnalysisResult, KnowledgeDocument
from .database import get_database_manager


class BaseRepository:
    """基础仓库类"""
    
    def __init__(self, model_class):
        """初始化仓库
        
        Args:
            model_class: 模型类
        """
        self.model_class = model_class
        self.db_manager = get_database_manager()
    
    def get_session(self) -> Optional[Session]:
        """获取数据库会话"""
        return self.db_manager.get_session()
    
    def close_session(self, session: Session) -> None:
        """关闭数据库会话"""
        self.db_manager.close_session(session)


class WindFarmRepository(BaseRepository):
    """风场仓库"""
    
    def __init__(self):
        super().__init__(WindFarm)
    
    def create(self, wind_farm_data: Dict[str, Any]) -> Optional[WindFarm]:
        """创建风场
        
        Args:
            wind_farm_data: 风场数据字典
            
        Returns:
            WindFarm: 创建的风场对象，失败时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            wind_farm = WindFarm(**wind_farm_data)
            session.add(wind_farm)
            session.commit()
            session.refresh(wind_farm)
            logger.info(f"风场创建成功: {wind_farm.name}")
            return wind_farm
        except Exception as e:
            session.rollback()
            logger.error(f"风场创建失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_id(self, wind_farm_id: int) -> Optional[WindFarm]:
        """根据ID获取风场
        
        Args:
            wind_farm_id: 风场ID
            
        Returns:
            WindFarm: 风场对象，不存在时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            return session.query(WindFarm).filter(WindFarm.id == wind_farm_id).first()
        except Exception as e:
            logger.error(f"获取风场失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_name(self, name: str) -> Optional[WindFarm]:
        """根据名称获取风场
        
        Args:
            name: 风场名称
            
        Returns:
            WindFarm: 风场对象，不存在时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            return session.query(WindFarm).filter(WindFarm.name == name).first()
        except Exception as e:
            logger.error(f"获取风场失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_code(self, code: str) -> Optional[WindFarm]:
        """根据编码获取风场
        
        Args:
            code: 风场编码
            
        Returns:
            WindFarm: 风场对象，不存在时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            return session.query(WindFarm).filter(WindFarm.code == code).first()
        except Exception as e:
            logger.error(f"获取风场失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_all(self, status: Optional[str] = None) -> List[WindFarm]:
        """获取所有风场
        
        Args:
            status: 状态过滤，None表示获取所有状态
            
        Returns:
            List[WindFarm]: 风场列表
        """
        session = self.get_session()
        if not session:
            return []
        
        try:
            query = session.query(WindFarm)
            if status:
                query = query.filter(WindFarm.status == status)
            return query.all()
        except Exception as e:
            logger.error(f"获取风场列表失败: {e}")
            return []
        finally:
            self.close_session(session)
    
    def update(self, wind_farm_id: int, update_data: Dict[str, Any]) -> Optional[WindFarm]:
        """更新风场
        
        Args:
            wind_farm_id: 风场ID
            update_data: 更新数据字典
            
        Returns:
            WindFarm: 更新后的风场对象，失败时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            wind_farm = session.query(WindFarm).filter(WindFarm.id == wind_farm_id).first()
            if not wind_farm:
                logger.warning(f"风场不存在: {wind_farm_id}")
                return None
            
            for key, value in update_data.items():
                if hasattr(wind_farm, key):
                    setattr(wind_farm, key, value)
            
            session.commit()
            session.refresh(wind_farm)
            logger.info(f"风场更新成功: {wind_farm.name}")
            return wind_farm
        except Exception as e:
            session.rollback()
            logger.error(f"风场更新失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def delete(self, wind_farm_id: int) -> bool:
        """删除风场
        
        Args:
            wind_farm_id: 风场ID
            
        Returns:
            bool: 删除是否成功
        """
        session = self.get_session()
        if not session:
            return False
        
        try:
            wind_farm = session.query(WindFarm).filter(WindFarm.id == wind_farm_id).first()
            if not wind_farm:
                logger.warning(f"风场不存在: {wind_farm_id}")
                return False
            
            session.delete(wind_farm)
            session.commit()
            logger.info(f"风场删除成功: {wind_farm.name}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"风场删除失败: {e}")
            return False
        finally:
            self.close_session(session)


class TurbineRepository(BaseRepository):
    """机组仓库"""
    
    def __init__(self):
        super().__init__(Turbine)
    
    def create(self, turbine_data: Dict[str, Any]) -> Optional[Turbine]:
        """创建机组
        
        Args:
            turbine_data: 机组数据字典
            
        Returns:
            Turbine: 创建的机组对象，失败时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            turbine = Turbine(**turbine_data)
            session.add(turbine)
            session.commit()
            session.refresh(turbine)
            logger.info(f"机组创建成功: {turbine.turbine_id}")
            return turbine
        except Exception as e:
            session.rollback()
            logger.error(f"机组创建失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_id(self, turbine_id: int) -> Optional[Turbine]:
        """根据ID获取机组
        
        Args:
            turbine_id: 机组ID
            
        Returns:
            Turbine: 机组对象，不存在时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            return session.query(Turbine).filter(Turbine.id == turbine_id).first()
        except Exception as e:
            logger.error(f"获取机组失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_turbine_id(self, turbine_id: str, wind_farm_id: Optional[int] = None) -> Optional[Turbine]:
        """根据机组编号获取机组
        
        Args:
            turbine_id: 机组编号
            wind_farm_id: 风场ID，用于进一步过滤
            
        Returns:
            Turbine: 机组对象，不存在时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            query = session.query(Turbine).filter(Turbine.turbine_id == turbine_id)
            if wind_farm_id:
                query = query.filter(Turbine.wind_farm_id == wind_farm_id)
            return query.first()
        except Exception as e:
            logger.error(f"获取机组失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_wind_farm(self, wind_farm_id: int, status: Optional[str] = None) -> List[Turbine]:
        """获取风场下的所有机组
        
        Args:
            wind_farm_id: 风场ID
            status: 状态过滤
            
        Returns:
            List[Turbine]: 机组列表
        """
        session = self.get_session()
        if not session:
            return []
        
        try:
            query = session.query(Turbine).filter(Turbine.wind_farm_id == wind_farm_id)
            if status:
                query = query.filter(Turbine.status == status)
            return query.all()
        except Exception as e:
            logger.error(f"获取机组列表失败: {e}")
            return []
        finally:
            self.close_session(session)
    
    def update(self, turbine_id: int, update_data: Dict[str, Any]) -> Optional[Turbine]:
        """更新机组
        
        Args:
            turbine_id: 机组ID
            update_data: 更新数据字典
            
        Returns:
            Turbine: 更新后的机组对象，失败时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            turbine = session.query(Turbine).filter(Turbine.id == turbine_id).first()
            if not turbine:
                logger.warning(f"机组不存在: {turbine_id}")
                return None
            
            for key, value in update_data.items():
                if hasattr(turbine, key):
                    setattr(turbine, key, value)
            
            session.commit()
            session.refresh(turbine)
            logger.info(f"机组更新成功: {turbine.turbine_id}")
            return turbine
        except Exception as e:
            session.rollback()
            logger.error(f"机组更新失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def delete(self, turbine_id: int) -> bool:
        """删除机组
        
        Args:
            turbine_id: 机组ID
            
        Returns:
            bool: 删除是否成功
        """
        session = self.get_session()
        if not session:
            return False
        
        try:
            turbine = session.query(Turbine).filter(Turbine.id == turbine_id).first()
            if not turbine:
                logger.warning(f"机组不存在: {turbine_id}")
                return False
            
            session.delete(turbine)
            session.commit()
            logger.info(f"机组删除成功: {turbine.turbine_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"机组删除失败: {e}")
            return False
        finally:
            self.close_session(session)


class MeasurementPointRepository(BaseRepository):
    """测点仓库"""
    
    def __init__(self):
        super().__init__(MeasurementPoint)
    
    def create(self, point_data: Dict[str, Any]) -> Optional[MeasurementPoint]:
        """创建测点
        
        Args:
            point_data: 测点数据字典
            
        Returns:
            MeasurementPoint: 创建的测点对象，失败时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            point = MeasurementPoint(**point_data)
            session.add(point)
            session.commit()
            session.refresh(point)
            logger.info(f"测点创建成功: {point.point_id}")
            return point
        except Exception as e:
            session.rollback()
            logger.error(f"测点创建失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_id(self, point_id: int) -> Optional[MeasurementPoint]:
        """根据ID获取测点
        
        Args:
            point_id: 测点ID
            
        Returns:
            MeasurementPoint: 测点对象，不存在时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            return session.query(MeasurementPoint).filter(MeasurementPoint.id == point_id).first()
        except Exception as e:
            logger.error(f"获取测点失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_point_id(self, point_id: str, turbine_id: Optional[int] = None) -> Optional[MeasurementPoint]:
        """根据测点编号获取测点
        
        Args:
            point_id: 测点编号
            turbine_id: 机组ID，用于进一步过滤
            
        Returns:
            MeasurementPoint: 测点对象，不存在时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            query = session.query(MeasurementPoint).filter(MeasurementPoint.point_id == point_id)
            if turbine_id:
                query = query.filter(MeasurementPoint.turbine_id == turbine_id)
            return query.first()
        except Exception as e:
            logger.error(f"获取测点失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_turbine(self, turbine_id: int, is_active: Optional[bool] = None) -> List[MeasurementPoint]:
        """获取机组下的所有测点
        
        Args:
            turbine_id: 机组ID
            is_active: 是否激活过滤
            
        Returns:
            List[MeasurementPoint]: 测点列表
        """
        session = self.get_session()
        if not session:
            return []
        
        try:
            query = session.query(MeasurementPoint).filter(MeasurementPoint.turbine_id == turbine_id)
            if is_active is not None:
                query = query.filter(MeasurementPoint.is_active == is_active)
            return query.all()
        except Exception as e:
            logger.error(f"获取测点列表失败: {e}")
            return []
        finally:
            self.close_session(session)
    
    def get_by_component(self, component: str, turbine_id: Optional[int] = None) -> List[MeasurementPoint]:
        """根据部件获取测点
        
        Args:
            component: 部件名称
            turbine_id: 机组ID，用于进一步过滤
            
        Returns:
            List[MeasurementPoint]: 测点列表
        """
        session = self.get_session()
        if not session:
            return []
        
        try:
            query = session.query(MeasurementPoint).filter(MeasurementPoint.component == component)
            if turbine_id:
                query = query.filter(MeasurementPoint.turbine_id == turbine_id)
            return query.all()
        except Exception as e:
            logger.error(f"获取测点列表失败: {e}")
            return []
        finally:
            self.close_session(session)
    
    def update(self, point_id: int, update_data: Dict[str, Any]) -> Optional[MeasurementPoint]:
        """更新测点
        
        Args:
            point_id: 测点ID
            update_data: 更新数据字典
            
        Returns:
            MeasurementPoint: 更新后的测点对象，失败时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            point = session.query(MeasurementPoint).filter(MeasurementPoint.id == point_id).first()
            if not point:
                logger.warning(f"测点不存在: {point_id}")
                return None
            
            for key, value in update_data.items():
                if hasattr(point, key):
                    setattr(point, key, value)
            
            session.commit()
            session.refresh(point)
            logger.info(f"测点更新成功: {point.point_id}")
            return point
        except Exception as e:
            session.rollback()
            logger.error(f"测点更新失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def delete(self, point_id: int) -> bool:
        """删除测点
        
        Args:
            point_id: 测点ID
            
        Returns:
            bool: 删除是否成功
        """
        session = self.get_session()
        if not session:
            return False
        
        try:
            point = session.query(MeasurementPoint).filter(MeasurementPoint.id == point_id).first()
            if not point:
                logger.warning(f"测点不存在: {point_id}")
                return False
            
            session.delete(point)
            session.commit()
            logger.info(f"测点删除成功: {point.point_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"测点删除失败: {e}")
            return False
        finally:
            self.close_session(session)


class AnalysisResultRepository(BaseRepository):
    """分析结果仓库"""
    
    def __init__(self):
        super().__init__(AnalysisResult)
    
    def create(self, result_data: Dict[str, Any]) -> Optional[AnalysisResult]:
        """创建分析结果
        
        Args:
            result_data: 分析结果数据字典
            
        Returns:
            AnalysisResult: 创建的分析结果对象，失败时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            result = AnalysisResult(**result_data)
            session.add(result)
            session.commit()
            session.refresh(result)
            logger.info(f"分析结果创建成功: {result.id}")
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"分析结果创建失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_turbine(self, turbine_id: int, limit: Optional[int] = None) -> List[AnalysisResult]:
        """获取机组的分析结果
        
        Args:
            turbine_id: 机组ID
            limit: 限制返回数量
            
        Returns:
            List[AnalysisResult]: 分析结果列表
        """
        session = self.get_session()
        if not session:
            return []
        
        try:
            query = session.query(AnalysisResult).filter(AnalysisResult.turbine_id == turbine_id)
            query = query.order_by(AnalysisResult.analysis_time.desc())
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"获取分析结果失败: {e}")
            return []
        finally:
            self.close_session(session)
    
    def get_by_measurement_point(self, measurement_point_id: int, limit: Optional[int] = None) -> List[AnalysisResult]:
        """获取测点的分析结果
        
        Args:
            measurement_point_id: 测点ID
            limit: 限制返回数量
            
        Returns:
            List[AnalysisResult]: 分析结果列表
        """
        session = self.get_session()
        if not session:
            return []
        
        try:
            query = session.query(AnalysisResult).filter(AnalysisResult.measurement_point_id == measurement_point_id)
            query = query.order_by(AnalysisResult.analysis_time.desc())
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"获取分析结果失败: {e}")
            return []
        finally:
            self.close_session(session)


class KnowledgeDocumentRepository(BaseRepository):
    """知识库文档仓库"""
    
    def __init__(self):
        super().__init__(KnowledgeDocument)
    
    def create(self, doc_data: Dict[str, Any]) -> Optional[KnowledgeDocument]:
        """创建知识库文档
        
        Args:
            doc_data: 文档数据字典
            
        Returns:
            KnowledgeDocument: 创建的文档对象，失败时返回None
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            doc = KnowledgeDocument(**doc_data)
            session.add(doc)
            session.commit()
            session.refresh(doc)
            logger.info(f"知识库文档创建成功: {doc.title}")
            return doc
        except Exception as e:
            session.rollback()
            logger.error(f"知识库文档创建失败: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_by_type(self, document_type: str, is_active: Optional[bool] = None) -> List[KnowledgeDocument]:
        """根据类型获取文档
        
        Args:
            document_type: 文档类型
            is_active: 是否激活过滤
            
        Returns:
            List[KnowledgeDocument]: 文档列表
        """
        session = self.get_session()
        if not session:
            return []
        
        try:
            query = session.query(KnowledgeDocument).filter(KnowledgeDocument.document_type == document_type)
            if is_active is not None:
                query = query.filter(KnowledgeDocument.is_active == is_active)
            return query.all()
        except Exception as e:
            logger.error(f"获取知识库文档失败: {e}")
            return []
        finally:
            self.close_session(session)
    
    def search_by_content(self, search_text: str, limit: Optional[int] = None) -> List[KnowledgeDocument]:
        """根据内容搜索文档
        
        Args:
            search_text: 搜索文本
            limit: 限制返回数量
            
        Returns:
            List[KnowledgeDocument]: 文档列表
        """
        session = self.get_session()
        if not session:
            return []
        
        try:
            query = session.query(KnowledgeDocument).filter(
                or_(
                    KnowledgeDocument.title.contains(search_text),
                    KnowledgeDocument.content_text.contains(search_text),
                    KnowledgeDocument.tags.contains(search_text)
                )
            )
            query = query.filter(KnowledgeDocument.is_active == True)
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"搜索知识库文档失败: {e}")
            return []
        finally:
            self.close_session(session)