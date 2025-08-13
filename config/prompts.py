# -*- coding: utf-8 -*-
"""
CMS振动分析系统提示词模板
"""

# 系统提示词
SYSTEM_PROMPT = """
你是一位专业的风电设备振动分析专家，具有丰富的CMS（状态监测系统）数据分析经验。
你的任务是分析风电机组的振动数据，并提供专业的诊断结论和建议。

请遵循以下原则：
1. 基于提供的振动数据进行客观分析
2. 结合振动分析理论和实际经验
3. 提供明确的设备状态评估
4. 给出具体的维护建议
5. 使用专业但易懂的语言
"""

# 振动数据分析提示词模板
VIBRATION_ANALYSIS_PROMPT = """
请分析以下风电机组振动数据：

**机组信息：**
- 风场：{wind_farm}
- 机组号：{turbine_id}
- 测点：{measurement_point}
- 采集时间：{timestamp}

**振动数据：**
- 有效值（RMS）：{rms_value:.3f} mm/s
- 峰值：{peak_value:.3f} mm/s
- 峰峰值：{pp_value:.3f} mm/s
- 主频率：{main_frequency:.1f} Hz
- 主频幅值：{main_amplitude:.3f} mm/s

**频谱特征：**
{frequency_features}

**历史趋势：**
{trend_analysis}

**报警状态：**
当前状态：{alarm_level}
报警阈值：{alarm_threshold:.3f} mm/s

请从以下几个方面进行分析：
1. **振动水平评估**：评估当前振动水平是否正常
2. **频谱分析**：分析主要频率成分及其可能原因
3. **趋势分析**：评估振动趋势变化
4. **故障诊断**：识别可能的故障类型和原因
5. **维护建议**：提供具体的维护措施和建议

请以专业、简洁的方式提供分析结论，字数控制在300-500字。
"""

# 报告生成提示词模板
REPORT_GENERATION_PROMPT = """
请基于以下振动分析结果，生成一份专业的CMS振动分析报告段落：

**分析结果：**
{analysis_result}

**图表说明：**
{chart_description}

请生成一个结构化的报告段落，包含：
1. **测点概述**：简要说明测点位置和监测目的
2. **数据分析**：总结主要发现和关键指标
3. **诊断结论**：明确的设备状态评估
4. **建议措施**：具体的维护建议

要求：
- 语言专业、准确
- 结构清晰、逻辑性强
- 与图表内容呼应
- 字数控制在200-300字
"""

# 知识库查询提示词
KNOWLEDGE_QUERY_PROMPT = """
基于以下振动特征，请从知识库中查找相关的故障模式和诊断经验：

振动特征：
- RMS值：{rms_value:.3f} mm/s
- 主频率：{main_frequency:.1f} Hz
- 频谱特征：{spectrum_features}
- 测点位置：{measurement_point}

请查找相关的：
1. 类似故障案例
2. 频率特征对应的故障类型
3. 该测点常见的故障模式
4. 相应的处理措施
"""

# 报告摘要生成提示词
SUMMARY_GENERATION_PROMPT = """
请基于以下多个测点的分析结果，生成机组整体状态摘要：

**机组信息：**
- 风场：{wind_farm}
- 机组号：{turbine_id}
- 分析时间：{analysis_time}

**各测点分析结果：**
{all_analysis_results}

请生成包含以下内容的摘要：
1. **整体状态评估**：机组总体健康状况
2. **主要发现**：关键问题和异常
3. **风险等级**：整体风险评估
4. **优先建议**：最重要的维护措施

要求简洁明了，字数控制在150-250字。
"""

# 图表描述生成提示词
CHART_DESCRIPTION_PROMPT = """
请为以下振动分析图表生成专业的描述文字：

**图表类型：**{chart_type}
**数据内容：**{data_content}
**关键特征：**{key_features}

请生成一段50-100字的图表描述，说明：
1. 图表显示的主要信息
2. 关键数据点和趋势
3. 需要关注的异常特征

描述应该专业、准确，便于读者理解图表内容。
"""

def get_analysis_prompt(wind_farm, turbine_id, measurement_point, timestamp, 
                       rms_value, peak_value, pp_value, main_frequency, 
                       main_amplitude, frequency_features, trend_analysis, 
                       alarm_level, alarm_threshold):
    """获取格式化的振动分析提示词"""
    return VIBRATION_ANALYSIS_PROMPT.format(
        wind_farm=wind_farm,
        turbine_id=turbine_id,
        measurement_point=measurement_point,
        timestamp=timestamp,
        rms_value=rms_value,
        peak_value=peak_value,
        pp_value=pp_value,
        main_frequency=main_frequency,
        main_amplitude=main_amplitude,
        frequency_features=frequency_features,
        trend_analysis=trend_analysis,
        alarm_level=alarm_level,
        alarm_threshold=alarm_threshold
    )

def get_report_prompt(analysis_result, chart_description):
    """获取格式化的报告生成提示词"""
    return REPORT_GENERATION_PROMPT.format(
        analysis_result=analysis_result,
        chart_description=chart_description
    )

def get_summary_prompt(wind_farm, turbine_id, analysis_time, all_analysis_results):
    """获取格式化的摘要生成提示词"""
    return SUMMARY_GENERATION_PROMPT.format(
        wind_farm=wind_farm,
        turbine_id=turbine_id,
        analysis_time=analysis_time,
        all_analysis_results=all_analysis_results
    )