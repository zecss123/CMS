# -*- coding: utf-8 -*-
"""
数据库模型 - 定义风场、机组、测点等数据结构
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional, List

Base = declarative_base()


class WindFarm(Base):
    """风场模型"""
    __tablename__ = 'wind_farms'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment='风场名称')
    code = Column(String(50), nullable=False, unique=True, comment='风场编码')
    location = Column(String(200), comment='风场位置')
    capacity = Column(Float, comment='装机容量(MW)')
    turbine_count = Column(Integer, comment='机组数量')
    description = Column(Text, comment='风场描述')
    status = Column(String(20), default='active', comment='状态: active/inactive')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    turbines = relationship('Turbine', back_populates='wind_farm', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<WindFarm(id={self.id}, name='{self.name}', code='{self.code}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'location': self.location,
            'capacity': self.capacity,
            'turbine_count': self.turbine_count,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }


class Turbine(Base):
    """机组模型"""
    __tablename__ = 'turbines'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wind_farm_id = Column(Integer, ForeignKey('wind_farms.id'), nullable=False, comment='所属风场ID')
    turbine_id = Column(String(50), nullable=False, comment='机组编号')
    model = Column(String(100), comment='机组型号')
    manufacturer = Column(String(100), comment='制造商')
    rated_power = Column(Float, comment='额定功率(kW)')
    hub_height = Column(Float, comment='轮毂高度(m)')
    rotor_diameter = Column(Float, comment='叶轮直径(m)')
    installation_date = Column(DateTime, comment='安装日期')
    commissioning_date = Column(DateTime, comment='投运日期')
    status = Column(String(20), default='active', comment='状态: active/inactive/maintenance')
    location_x = Column(Float, comment='X坐标')
    location_y = Column(Float, comment='Y坐标')
    description = Column(Text, comment='机组描述')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    wind_farm = relationship('WindFarm', back_populates='turbines')
    measurement_points = relationship('MeasurementPoint', back_populates='turbine', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Turbine(id={self.id}, turbine_id='{self.turbine_id}', wind_farm_id={self.wind_farm_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'wind_farm_id': self.wind_farm_id,
            'turbine_id': self.turbine_id,
            'model': self.model,
            'manufacturer': self.manufacturer,
            'rated_power': self.rated_power,
            'hub_height': self.hub_height,
            'rotor_diameter': self.rotor_diameter,
            'installation_date': self.installation_date.isoformat() if self.installation_date is not None else None,
            'commissioning_date': self.commissioning_date.isoformat() if self.commissioning_date is not None else None,
            'status': self.status,
            'location_x': self.location_x,
            'location_y': self.location_y,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }


class MeasurementPoint(Base):
    """测点模型"""
    __tablename__ = 'measurement_points'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    turbine_id = Column(Integer, ForeignKey('turbines.id'), nullable=False, comment='所属机组ID')
    point_id = Column(String(50), nullable=False, comment='测点编号')
    point_name = Column(String(100), nullable=False, comment='测点名称')
    component = Column(String(50), comment='部件名称: gearbox/generator/main_bearing等')
    location = Column(String(100), comment='测点位置描述')
    sensor_type = Column(String(50), comment='传感器类型: accelerometer/velocity/displacement')
    measurement_direction = Column(String(20), comment='测量方向: X/Y/Z/radial/axial/tangential')
    sampling_frequency = Column(Float, comment='采样频率(Hz)')
    frequency_range_min = Column(Float, comment='频率范围最小值(Hz)')
    frequency_range_max = Column(Float, comment='频率范围最大值(Hz)')
    unit = Column(String(20), comment='单位: m/s²/mm/s/μm等')
    alarm_level_1 = Column(Float, comment='注意报警阈值')
    alarm_level_2 = Column(Float, comment='警告报警阈值')
    alarm_level_3 = Column(Float, comment='危险报警阈值')
    is_active = Column(Boolean, default=True, comment='是否激活')
    api_endpoint = Column(String(200), comment='数据获取API端点')
    api_params = Column(JSON, comment='API参数配置')
    description = Column(Text, comment='测点描述')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    turbine = relationship('Turbine', back_populates='measurement_points')
    
    def __repr__(self):
        return f"<MeasurementPoint(id={self.id}, point_id='{self.point_id}', turbine_id={self.turbine_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'turbine_id': self.turbine_id,
            'point_id': self.point_id,
            'point_name': self.point_name,
            'component': self.component,
            'location': self.location,
            'sensor_type': self.sensor_type,
            'measurement_direction': self.measurement_direction,
            'sampling_frequency': self.sampling_frequency,
            'frequency_range_min': self.frequency_range_min,
            'frequency_range_max': self.frequency_range_max,
            'unit': self.unit,
            'alarm_level_1': self.alarm_level_1,
            'alarm_level_2': self.alarm_level_2,
            'alarm_level_3': self.alarm_level_3,
            'is_active': self.is_active,
            'api_endpoint': self.api_endpoint,
            'api_params': self.api_params,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }
    
    def get_alarm_level(self, value: float) -> str:
        """根据数值获取报警等级"""
        # 获取实际的阈值数值
        level_1 = getattr(self, 'alarm_level_1', None)
        level_2 = getattr(self, 'alarm_level_2', None) 
        level_3 = getattr(self, 'alarm_level_3', None)
        
        if level_1 is None or value <= level_1:
            return 'normal'
        elif level_2 is None or value <= level_2:
            return 'warning'
        elif level_3 is None or value <= level_3:
            return 'alarm'
        else:
            return 'critical'


class AnalysisResult(Base):
    """分析结果模型"""
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    turbine_id = Column(Integer, ForeignKey('turbines.id'), nullable=False, comment='机组ID')
    measurement_point_id = Column(Integer, ForeignKey('measurement_points.id'), nullable=False, comment='测点ID')
    analysis_type = Column(String(50), nullable=False, comment='分析类型: trend/spectrum/envelope等')
    analysis_time = Column(DateTime, nullable=False, comment='分析时间')
    data_start_time = Column(DateTime, comment='数据开始时间')
    data_end_time = Column(DateTime, comment='数据结束时间')
    rms_value = Column(Float, comment='RMS值')
    peak_value = Column(Float, comment='峰值')
    alarm_level = Column(String(20), comment='报警等级')
    fault_diagnosis = Column(Text, comment='故障诊断结果')
    recommendations = Column(Text, comment='维护建议')
    analysis_data = Column(JSON, comment='详细分析数据')
    chart_data = Column(JSON, comment='图表数据')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关联关系
    turbine = relationship('Turbine')
    measurement_point = relationship('MeasurementPoint')
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, turbine_id={self.turbine_id}, analysis_type='{self.analysis_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'turbine_id': self.turbine_id,
            'measurement_point_id': self.measurement_point_id,
            'analysis_type': self.analysis_type,
            'analysis_time': self.analysis_time.isoformat() if self.analysis_time is not None else None,
            'data_start_time': self.data_start_time.isoformat() if self.data_start_time is not None else None,
            'data_end_time': self.data_end_time.isoformat() if self.data_end_time is not None else None,
            'rms_value': self.rms_value,
            'peak_value': self.peak_value,
            'alarm_level': self.alarm_level,
            'fault_diagnosis': self.fault_diagnosis,
            'recommendations': self.recommendations,
            'analysis_data': self.analysis_data,
            'chart_data': self.chart_data,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None
        }


class KnowledgeDocument(Base):
    """知识库文档模型"""
    __tablename__ = 'knowledge_documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment='文档标题')
    document_type = Column(String(50), nullable=False, comment='文档类型: template/manual/standard等')
    category = Column(String(50), comment='文档分类')
    file_path = Column(String(500), comment='文件路径')
    file_name = Column(String(200), comment='文件名')
    file_size = Column(Integer, comment='文件大小(bytes)')
    file_hash = Column(String(64), comment='文件哈希值')
    content_text = Column(Text, comment='文档文本内容')
    document_metadata = Column(JSON, comment='文档元数据')
    tags = Column(String(500), comment='标签，逗号分隔')
    version = Column(String(20), default='1.0', comment='版本号')
    is_active = Column(Boolean, default=True, comment='是否激活')
    upload_user = Column(String(100), comment='上传用户')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, title='{self.title}', type='{self.document_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'document_type': self.document_type,
            'category': self.category,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'content_text': self.content_text,
            'document_metadata': self.document_metadata,
            'tags': self.tags,
            'version': self.version,
            'is_active': self.is_active,
            'upload_user': self.upload_user,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }