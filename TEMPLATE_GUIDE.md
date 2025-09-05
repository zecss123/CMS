# CMS振动分析报告系统 - 模板使用指南

## 📋 模板概述

本系统支持自定义报告模板，允许用户根据不同的分析需求创建和管理专业的振动分析报告模板。模板采用Jinja2语法，支持动态内容填充和版本控制。

## 📁 模板存储结构

```
cms_vibration_rag/
├── knowledge/
│   └── report_templates/
│       ├── report/                    # 报告类型模板目录
│       │   ├── vibration_analysis.html    # 振动分析报告模板
│       │   ├── trend_analysis.html        # 趋势分析报告模板
│       │   └── maintenance_report.html    # 维护报告模板
│       ├── summary/                   # 摘要类型模板目录
│       │   ├── daily_summary.html         # 日报摘要模板
│       │   └── weekly_summary.html        # 周报摘要模板
│       └── metadata/                  # 模板元数据目录
│           ├── report_metadata.json       # 报告模板元数据
│           └── summary_metadata.json      # 摘要模板元数据
```

## 🔧 如何上传模板

### 方法一：直接文件放置

1. **准备模板文件**
   - 创建HTML格式的模板文件
   - 使用Jinja2语法编写动态内容
   - 确保文件编码为UTF-8

2. **放置模板文件**
   ```bash
   # 进入模板目录
   cd cms_vibration_rag/knowledge/report_templates/
   
   # 根据模板类型放入对应目录
   # 报告类型模板
   cp your_template.html report/
   
   # 摘要类型模板
   cp your_summary.html summary/
   ```

3. **更新元数据**
   - 编辑对应的metadata.json文件
   - 添加新模板的元数据信息

### 方法二：使用模板管理API

```python
from knowledge.template_manager import TemplateManager

# 初始化模板管理器
manager = TemplateManager()

# 读取模板内容
with open('your_template.html', 'r', encoding='utf-8') as f:
    template_content = f.read()

# 定义模板元数据
metadata = {
    "author": "张工程师",
    "description": "风机振动分析专用模板",
    "tags": ["振动分析", "风机", "专业报告"],
    "variables": [
        "turbine_id", "analysis_date", "rms_value", 
        "frequency_data", "conclusion", "charts"
    ]
}

# 保存模板
result = manager.save_template(
    name="custom_vibration_analysis",
    template_type="report",
    content=template_content,
    metadata=metadata
)

print(f"模板保存结果: {result}")
```

### 方法三：通过Web界面上传（如果启用）

1. 启动Streamlit应用
   ```bash
   streamlit run streamlit_app.py
   ```

2. 在侧边栏找到"模板管理"选项

3. 点击"上传新模板"

4. 填写模板信息并上传文件

## 📝 模板格式规范

### 基本HTML结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title | default('振动分析报告') }}</title>
    <style>
        /* CSS样式 */
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .section {
            margin: 20px 0;
        }
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report_title | default('振动分析报告') }}</h1>
        <p>设备编号: {{ turbine_id | default('未指定') }}</p>
        <p>分析日期: {{ analysis_date | default('未指定') }}</p>
    </div>
    
    <div class="section">
        <h2>1. 分析概述</h2>
        <p>{{ analysis_overview | default('暂无概述信息') }}</p>
    </div>
    
    <div class="section">
        <h2>2. 振动数据分析</h2>
        <p><strong>RMS值:</strong> {{ rms_value | default('N/A') }} mm/s</p>
        <p><strong>主频率:</strong> {{ main_frequency | default('N/A') }} Hz</p>
        
        {% if charts %}
        <div class="chart-container">
            {% for chart in charts %}
            <div>
                <h3>{{ chart.title }}</h3>
                <img src="data:image/png;base64,{{ chart.data }}" alt="{{ chart.title }}" style="max-width: 100%;">
                <p>{{ chart.description | default('') }}</p>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    
    <div class="section">
        <h2>3. 分析结论</h2>
        <p>{{ conclusion | default('暂无结论') }}</p>
    </div>
    
    <div class="section">
        <h2>4. 建议措施</h2>
        <ul>
        {% for recommendation in recommendations | default([]) %}
            <li>{{ recommendation }}</li>
        {% endfor %}
        </ul>
    </div>
    
    <div class="footer" style="margin-top: 40px; text-align: center; font-size: 12px; color: #666;">
        <p>报告生成时间: {{ generation_time | default('未指定') }}</p>
        <p>CMS振动分析报告系统 v2.1.0</p>
    </div>
</body>
</html>
```

### 支持的模板变量

#### 基础信息变量
- `{{ report_title }}` - 报告标题
- `{{ turbine_id }}` - 设备编号
- `{{ analysis_date }}` - 分析日期
- `{{ generation_time }}` - 报告生成时间
- `{{ analyst_name }}` - 分析师姓名

#### 振动数据变量
- `{{ rms_value }}` - RMS有效值
- `{{ peak_value }}` - 峰值
- `{{ main_frequency }}` - 主频率
- `{{ frequency_data }}` - 频域数据数组
- `{{ time_data }}` - 时域数据数组

#### 分析结果变量
- `{{ analysis_overview }}` - 分析概述
- `{{ conclusion }}` - 分析结论
- `{{ alarm_level }}` - 报警级别
- `{{ recommendations }}` - 建议措施列表

#### 图表变量
- `{{ charts }}` - 图表数据列表
  - `{{ chart.title }}` - 图表标题
  - `{{ chart.data }}` - Base64编码的图片数据
  - `{{ chart.description }}` - 图表描述
  - `{{ chart.type }}` - 图表类型

### Jinja2语法示例

#### 条件判断
```html
{% if rms_value %}
    <p>RMS值: {{ rms_value }} mm/s</p>
{% else %}
    <p>RMS值: 数据缺失</p>
{% endif %}

{% if alarm_level == 'danger' %}
    <div style="color: red; font-weight: bold;">⚠️ 危险警告</div>
{% elif alarm_level == 'warning' %}
    <div style="color: orange; font-weight: bold;">⚠️ 注意警告</div>
{% else %}
    <div style="color: green;">✅ 状态正常</div>
{% endif %}
```

#### 循环遍历
```html
{% for chart in charts %}
<div class="chart-item">
    <h3>{{ loop.index }}. {{ chart.title }}</h3>
    <img src="data:image/png;base64,{{ chart.data }}" alt="{{ chart.title }}">
    {% if chart.description %}
        <p>{{ chart.description }}</p>
    {% endif %}
</div>
{% endfor %}

{% for recommendation in recommendations %}
<li>{{ recommendation }}</li>
{% empty %}
<li>暂无建议</li>
{% endfor %}
```

#### 过滤器使用
```html
<!-- 默认值 -->
<p>设备: {{ turbine_id | default('未知设备') }}</p>

<!-- 日期格式化 -->
<p>日期: {{ analysis_date | strftime('%Y年%m月%d日') }}</p>

<!-- 数值格式化 -->
<p>RMS值: {{ rms_value | round(2) }} mm/s</p>

<!-- 字符串处理 -->
<p>标题: {{ report_title | upper }}</p>
<p>描述: {{ description | truncate(100) }}</p>
```

## 📊 模板元数据格式

每个模板都需要对应的元数据文件，格式如下：

```json
{
  "templates": {
    "vibration_analysis": {
      "name": "振动分析报告模板",
      "description": "标准振动分析报告模板，适用于风机设备",
      "author": "系统管理员",
      "version": "1.0.0",
      "created_at": "2024-08-19T10:00:00Z",
      "updated_at": "2024-08-19T10:00:00Z",
      "tags": ["振动分析", "风机", "标准报告"],
      "variables": [
        {
          "name": "turbine_id",
          "type": "string",
          "description": "设备编号",
          "required": true
        },
        {
          "name": "rms_value",
          "type": "float",
          "description": "RMS有效值",
          "required": false
        },
        {
          "name": "charts",
          "type": "array",
          "description": "图表数据列表",
          "required": false
        }
      ],
      "output_formats": ["html", "pdf"],
      "file_path": "report/vibration_analysis.html"
    }
  }
}
```

## 🔍 模板验证

### 语法验证
```python
from knowledge.template_manager import TemplateManager
from jinja2 import Template, TemplateSyntaxError

def validate_template(template_content):
    try:
        template = Template(template_content)
        print("✅ 模板语法正确")
        return True
    except TemplateSyntaxError as e:
        print(f"❌ 模板语法错误: {e}")
        return False

# 验证模板文件
with open('your_template.html', 'r', encoding='utf-8') as f:
    content = f.read()
    
validate_template(content)
```

### 变量检查
```python
import re

def extract_template_variables(template_content):
    # 提取所有模板变量
    pattern = r'{{\s*([^}|\s]+)(?:\s*\|[^}]*)?\s*}}'
    variables = re.findall(pattern, template_content)
    
    # 提取循环变量
    loop_pattern = r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}'
    loop_vars = re.findall(loop_pattern, template_content)
    
    return list(set(variables)), loop_vars

# 检查模板变量
variables, loops = extract_template_variables(content)
print(f"模板变量: {variables}")
print(f"循环变量: {loops}")
```

## 📚 模板示例库

### 1. 简单振动报告模板
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ turbine_id }} 振动报告</title>
</head>
<body>
    <h1>设备 {{ turbine_id }} 振动分析</h1>
    <p>分析时间: {{ analysis_date }}</p>
    <p>RMS值: {{ rms_value }} mm/s</p>
    <p>状态: {{ alarm_level }}</p>
    <p>结论: {{ conclusion }}</p>
</body>
</html>
```

### 2. 详细分析报告模板
```html
<!DOCTYPE html>
<html>
<head>
    <title>详细振动分析报告</title>
    <style>
        .warning { color: orange; }
        .danger { color: red; }
        .normal { color: green; }
    </style>
</head>
<body>
    <h1>{{ report_title }}</h1>
    
    <section>
        <h2>设备信息</h2>
        <ul>
            <li>设备编号: {{ turbine_id }}</li>
            <li>位置: {{ location | default('未指定') }}</li>
            <li>型号: {{ model | default('未指定') }}</li>
        </ul>
    </section>
    
    <section>
        <h2>振动数据</h2>
        <table border="1">
            <tr><th>参数</th><th>数值</th><th>单位</th></tr>
            <tr><td>RMS值</td><td>{{ rms_value }}</td><td>mm/s</td></tr>
            <tr><td>峰值</td><td>{{ peak_value }}</td><td>mm/s</td></tr>
            <tr><td>主频率</td><td>{{ main_frequency }}</td><td>Hz</td></tr>
        </table>
    </section>
    
    <section>
        <h2>图表分析</h2>
        {% for chart in charts %}
        <div>
            <h3>{{ chart.title }}</h3>
            <img src="data:image/png;base64,{{ chart.data }}" style="max-width: 600px;">
        </div>
        {% endfor %}
    </section>
    
    <section>
        <h2>分析结论</h2>
        <p class="{{ alarm_level }}">{{ conclusion }}</p>
    </section>
</body>
</html>
```

## 🛠️ 常见问题

### Q1: 模板上传后不显示？
**A:** 检查以下几点：
- 文件编码是否为UTF-8
- 元数据文件是否正确更新
- 模板语法是否正确
- 文件权限是否正确

### Q2: 模板变量不显示内容？
**A:** 确认：
- 变量名是否正确
- 数据是否正确传递
- 是否使用了正确的Jinja2语法

### Q3: 中文显示乱码？
**A:** 确保：
- HTML文件使用UTF-8编码
- HTML头部包含正确的charset声明
- 使用支持中文的字体

### Q4: 图片不显示？
**A:** 检查：
- 图片数据是否为Base64格式
- img标签的src属性格式是否正确
- 图片数据是否完整

## 📋 最佳实践

1. **命名规范**
   - 使用有意义的模板名称
   - 避免特殊字符和空格
   - 使用小写字母和下划线

2. **版本管理**
   - 每次修改都更新版本号
   - 保留重要版本的备份
   - 记录详细的修改日志

3. **性能优化**
   - 避免过于复杂的循环和条件
   - 合理使用CSS样式
   - 优化图片大小和格式

4. **兼容性**
   - 测试不同浏览器的显示效果
   - 确保移动端适配
   - 考虑打印样式

5. **安全性**
   - 避免在模板中包含敏感信息
   - 对用户输入进行适当转义
   - 定期检查模板安全性

---

**注意**: 模板修改后建议先在测试环境验证，确认无误后再部署到生产环境。