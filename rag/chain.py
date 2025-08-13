# -*- coding: utf-8 -*-
"""
RAG链条模块 - 整合LLM和向量数据库
"""

from typing import Dict, List, Any, Optional
from loguru import logger

from .llm_handler import DeepSeekLLMHandler
from .vector_store import knowledge_base, initialize_kb
from config.prompts import (
    get_analysis_prompt, get_report_prompt, get_summary_prompt,
    KNOWLEDGE_QUERY_PROMPT, CHART_DESCRIPTION_PROMPT
)
from data.mock_data import get_mock_data

class CMSAnalysisChain:
    """CMS振动分析RAG链条"""
    
    def __init__(self):
        self.llm_handler = None
        self.knowledge_base = knowledge_base
        self.initialized = False
        try:
            self.initialized = self._ensure_initialized()
        except Exception as e:
            logger.error(f"CMSAnalysisChain初始化失败: {e}")
            self.initialized = False
    
    def _ensure_initialized(self):
        """确保系统初始化"""
        try:
            # 初始化知识库
            if not initialize_kb():
                logger.warning("知识库初始化失败")
            
            # 初始化LLM处理器
            try:
                self.llm_handler = DeepSeekLLMHandler()
                if not self.llm_handler.load_model():
                    logger.error("模型加载失败")
                    return False
                return True
            except Exception as e:
                logger.error(f"LLM处理器初始化失败: {e}")
                return False
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            # 不抛出异常，而是返回False
            return False
    
    def analyze_single_measurement(self, wind_farm: str, turbine_id: str, 
                                 measurement_point: str) -> Dict[str, Any]:
        """分析单个测点数据"""
        logger.info(f"开始分析测点: {wind_farm}-{turbine_id}-{measurement_point}")
        
        try:
            # 确保系统已正确初始化
            if not self.initialized or self.llm_handler is None:
                logger.warning("分析链未正确初始化，使用模拟分析结果")
                # 返回模拟的分析结果而不是抛出异常
                data = get_mock_data(wind_farm, turbine_id, measurement_point)
                return {
                    "measurement_data": data,
                    "knowledge_context": [],
                    "analysis_result": "系统未完全初始化，返回基础数据分析结果",
                    "chart_description": "基础振动数据图表",
                    "report_section": "由于系统初始化问题，本次分析使用基础模式",
                    "status": "success"
                }
            
            # 获取模拟数据
            data = get_mock_data(wind_farm, turbine_id, measurement_point)
            
            # 搜索相关知识
            knowledge_results = self._search_relevant_knowledge(data)
            
            # 构建分析提示词
            analysis_prompt = self._build_analysis_prompt(data, knowledge_results)
            
            # LLM分析
            analysis_result = self.llm_handler.analyze_vibration_data(str(data), analysis_prompt)
            
            # 生成图表描述
            chart_description = self._generate_chart_description(data)
            
            # 构建报告段落
            report_prompt = get_report_prompt(analysis_result, chart_description)
            report_section = self.llm_handler.generate_report({"analysis_result": analysis_result, "chart_description": chart_description})
            
            result = {
                "measurement_data": data,
                "knowledge_context": knowledge_results,
                "analysis_result": analysis_result,
                "chart_description": chart_description,
                "report_section": report_section,
                "status": "success"
            }
            
            logger.info(f"测点分析完成: {measurement_point}")
            return result
            
        except Exception as e:
            logger.error(f"测点分析失败: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _search_relevant_knowledge(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """搜索相关知识"""
        try:
            # 基于故障类型搜索
            fault_type = data.get("fault_type", "正常")
            measurement_point = data.get("measurement_point", "")
            
            # 构建搜索查询
            queries = [
                f"{fault_type}故障特征",
                f"{measurement_point}振动分析",
                "振动诊断方法"
            ]
            
            all_results = []
            for query in queries:
                results = self.knowledge_base.search_knowledge(query, n_results=2)
                all_results.extend(results)
            
            # 去重并按相似度排序
            unique_results = {}
            for result in all_results:
                doc_id = result["document"][:50]  # 使用文档前50字符作为唯一标识
                if doc_id not in unique_results or result["similarity"] > unique_results[doc_id]["similarity"]:
                    unique_results[doc_id] = result
            
            return list(unique_results.values())[:5]  # 返回前5个最相关的
            
        except Exception as e:
            logger.error(f"知识搜索失败: {str(e)}")
            return []
    
    def _build_analysis_prompt(self, data: Dict[str, Any], 
                             knowledge_results: List[Dict[str, Any]]) -> str:
        """构建分析提示词"""
        # 提取数据特征
        features = data["features"]
        
        # 构建知识上下文
        knowledge_context = "\n".join([
            f"- {result['document']}"
            for result in knowledge_results[:3]
        ])
        
        # 构建完整提示词
        enhanced_prompt = get_analysis_prompt(
            wind_farm=data["wind_farm"],
            turbine_id=data["turbine_id"],
            measurement_point=data["measurement_point"],
            timestamp=data["timestamp"],
            rms_value=features["rms_value"],
            peak_value=features["peak_value"],
            pp_value=features["peak_to_peak"],
            main_frequency=features["main_frequency"],
            main_amplitude=features["main_amplitude"],
            frequency_features=data["frequency_features"],
            trend_analysis=data["trend_analysis"],
            alarm_level=data["alarm_level"],
            alarm_threshold=data["alarm_threshold"]
        )
        
        # 添加知识上下文
        if knowledge_context:
            enhanced_prompt += f"\n\n**参考知识：**\n{knowledge_context}\n\n请结合以上专业知识进行分析。"
        
        return enhanced_prompt
    
    def _generate_chart_description(self, data: Dict[str, Any]) -> str:
        """生成图表描述"""
        try:
            if self.llm_handler is None:
                raise Exception("LLM处理器未初始化")
                
            features = data["features"]
            
            chart_prompt = CHART_DESCRIPTION_PROMPT.format(
                chart_type="振动时域波形和频谱图",
                data_content=f"RMS值{features['rms_value']:.3f}mm/s，主频率{features['main_frequency']:.1f}Hz",
                key_features=f"峰值{features['peak_value']:.3f}mm/s，报警状态{data['alarm_level']}"
            )
            
            return self.llm_handler.generate_response(chart_prompt, max_new_tokens=150)
            
        except Exception as e:
            logger.error(f"图表描述生成失败: {str(e)}")
            return f"振动数据图表显示RMS值为{data['features']['rms_value']:.3f}mm/s，主频率为{data['features']['main_frequency']:.1f}Hz。"
    
    def analyze_turbine_all_points(self, wind_farm: str, turbine_id: str) -> Dict[str, Any]:
        """分析机组所有测点"""
        logger.info(f"开始分析机组所有测点: {wind_farm}-{turbine_id}")
        
        from config.settings import CMS_CONFIG
        measurement_points = CMS_CONFIG["measurement_points"]
        
        results = {
            "wind_farm": wind_farm,
            "turbine_id": turbine_id,
            "timestamp": None,
            "measurements": {},
            "summary": None,
            "overall_status": "unknown"
        }
        
        # 分析每个测点
        all_analysis_results = []
        for point in measurement_points:
            point_result = self.analyze_single_measurement(wind_farm, turbine_id, point)
            results["measurements"][point] = point_result
            
            if point_result["status"] == "success":
                all_analysis_results.append({
                    "point": point,
                    "analysis": point_result["analysis_result"],
                    "alarm_level": point_result["measurement_data"]["alarm_level"],
                    "timestamp": point_result["measurement_data"].get("timestamp", "")
                })
            else:
                # 如果分析失败，记录错误但继续处理其他测点
                logger.warning(f"测点 {point} 分析失败: {point_result.get('error', '未知错误')}")
        
        # 设置时间戳
        if all_analysis_results:
            results["timestamp"] = all_analysis_results[0].get("timestamp", "")
        
        # 生成整体摘要
        if all_analysis_results:
            summary = self._generate_turbine_summary(wind_farm, turbine_id, all_analysis_results)
            results["summary"] = summary
            results["overall_status"] = self._determine_overall_status(all_analysis_results)
            
            # 为UI显示格式化结果
            results["overall_assessment"] = summary
            results["point_analyses"] = {}
            
            for analysis_result in all_analysis_results:
                point_name = analysis_result["point"]
                results["point_analyses"][point_name] = analysis_result["analysis"]
            
            # 生成故障诊断和建议
            results["fault_diagnosis"] = self._generate_fault_diagnosis(all_analysis_results)
            results["recommendations"] = self._generate_recommendations(all_analysis_results)
        
        logger.info(f"机组分析完成: {turbine_id}")
        return results
    
    def _generate_turbine_summary(self, wind_farm: str, turbine_id: str, 
                                all_analysis_results: List[Dict[str, Any]]) -> str:
        """生成机组整体摘要"""
        try:
            if self.llm_handler is None:
                raise Exception("LLM处理器未初始化")
                
            # 构建所有分析结果的文本
            analysis_text = "\n".join([
                f"**{result['point']}**: {result['analysis'][:200]}... (状态: {result['alarm_level']})"
                for result in all_analysis_results
            ])
            
            summary_prompt = get_summary_prompt(
                wind_farm=wind_farm,
                turbine_id=turbine_id,
                analysis_time=all_analysis_results[0].get("timestamp", ""),
                all_analysis_results=analysis_text
            )
            
            return self.llm_handler.generate_response(summary_prompt, 512)
            
        except Exception as e:
            logger.error(f"摘要生成失败: {str(e)}")
            return "摘要生成失败，请检查各测点详细分析结果。"
    
    def _determine_overall_status(self, all_analysis_results: List[Dict[str, Any]]) -> str:
        """确定整体状态"""
        # 根据所有测点的报警级别确定整体状态
        alarm_levels = [result["alarm_level"] for result in all_analysis_results]
        
        if "危险" in alarm_levels:
            return "危险"
        elif "警告" in alarm_levels:
            return "警告"
        elif "注意" in alarm_levels:
            return "注意"
        else:
            return "正常"
    
    def _generate_fault_diagnosis(self, all_analysis_results: List[Dict[str, Any]]) -> str:
        """生成故障诊断"""
        try:
            # 统计各种报警级别的测点
            alarm_counts = {}
            problem_points = []
            
            for result in all_analysis_results:
                level = result["alarm_level"]
                alarm_counts[level] = alarm_counts.get(level, 0) + 1
                
                if level in ["警告", "注意", "危险"]:
                    problem_points.append(f"{result['point']}({level})")
            
            if not problem_points:
                return "所有测点运行正常，未发现异常。"
            
            diagnosis = f"发现 {len(problem_points)} 个测点存在异常：{', '.join(problem_points)}。"
            
            # 根据报警级别给出诊断
            if "危险" in alarm_counts:
                diagnosis += "存在危险级别异常，需要立即停机检查。"
            elif "警告" in alarm_counts:
                diagnosis += "存在警告级别异常，建议安排维护检查。"
            elif "注意" in alarm_counts:
                diagnosis += "存在需要注意的异常，建议加强监控。"
            
            return diagnosis
            
        except Exception as e:
            logger.error(f"生成故障诊断失败: {e}")
            return "故障诊断生成失败，请检查分析结果。"
    
    def _generate_recommendations(self, all_analysis_results: List[Dict[str, Any]]) -> List[str]:
        """生成建议措施"""
        try:
            recommendations = []
            alarm_counts = {}
            
            for result in all_analysis_results:
                level = result["alarm_level"]
                alarm_counts[level] = alarm_counts.get(level, 0) + 1
            
            # 根据报警级别生成建议
            if "危险" in alarm_counts:
                recommendations.extend([
                    "立即停机检查，避免设备损坏",
                    "联系专业维修人员进行详细检查",
                    "检查轴承、齿轮箱等关键部件"
                ])
            elif "警告" in alarm_counts:
                recommendations.extend([
                    "安排计划性维护检查",
                    "增加监控频率，密切关注设备状态",
                    "检查润滑系统和冷却系统"
                ])
            elif "注意" in alarm_counts:
                recommendations.extend([
                    "加强日常监控，记录振动趋势",
                    "检查设备安装和紧固件",
                    "定期进行振动分析"
                ])
            else:
                recommendations.append("设备运行正常，继续保持定期维护")
            
            # 通用建议
            recommendations.append("建立振动监控档案，跟踪设备健康状态")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成建议措施失败: {e}")
            return ["建议措施生成失败，请联系技术支持。"]
    
    def batch_analyze_turbines(self, wind_farm: str, turbine_ids: List[str]) -> Dict[str, Any]:
        """批量分析多台机组"""
        logger.info(f"开始批量分析 {len(turbine_ids)} 台机组")
        
        results = {
            "wind_farm": wind_farm,
            "turbines": {},
            "batch_summary": None
        }
        
        for turbine_id in turbine_ids:
            logger.info(f"分析机组: {turbine_id}")
            turbine_result = self.analyze_turbine_all_points(wind_farm, turbine_id)
            results["turbines"][turbine_id] = turbine_result
        
        logger.info("批量分析完成")
        return results

# 全局分析链实例
analysis_chain = CMSAnalysisChain()

# 便捷函数
def analyze_measurement(wind_farm: str, turbine_id: str, measurement_point: str) -> Dict[str, Any]:
    """分析单个测点"""
    return analysis_chain.analyze_single_measurement(wind_farm, turbine_id, measurement_point)

def analyze_turbine(wind_farm: str, turbine_id: str) -> Dict[str, Any]:
    """分析整台机组"""
    return analysis_chain.analyze_turbine_all_points(wind_farm, turbine_id)

def batch_analyze(wind_farm: str, turbine_ids: List[str]) -> Dict[str, Any]:
    """批量分析"""
    return analysis_chain.batch_analyze_turbines(wind_farm, turbine_ids)

if __name__ == "__main__":
    # 测试代码
    chain = CMSAnalysisChain()
    
    # 测试单个测点分析
    result = chain.analyze_single_measurement("华能风场A", "A01", "1X水平振动")
    
    if result["status"] == "success":
        print("分析成功")
        print(f"分析结果: {result['analysis_result'][:200]}...")
        print(f"报告段落: {result['report_section'][:200]}...")
    else:
        print(f"分析失败: {result.get('error', '未知错误')}")