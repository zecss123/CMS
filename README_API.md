# CMS振动分析系统 - API服务文档

## 概述

CMS振动分析系统API服务提供RESTful接口，支持振动分析报告生成、智能问答等功能。基于FastAPI框架构建，提供高性能、易用的API服务。

## 功能特性

- 🚀 **高性能**: 基于FastAPI和异步处理，支持高并发请求
- 📊 **多格式报告**: 支持PDF、HTML、DOCX格式，智能图表匹配
- 🤖 **智能问答**: 集成RAG技术的聊天机器人功能
- 🔐 **安全认证**: API密钥认证机制，支持多级权限控制
- 📈 **图表生成**: 自动生成振动分析图表，支持中文字体
- 🔄 **异步处理**: 后台任务处理，支持长时间运行和进度查询
- 📝 **完整文档**: 自动生成Swagger/OpenAPI文档
- 🎯 **智能匹配**: 分析结论与图表智能匹配算法
- 💾 **缓存优化**: 多级缓存提升响应速度
- 🔍 **实时监控**: 完整的日志记录和性能监控

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装API服务依赖
pip install -r requirements.txt

# 验证安装
python -c "import fastapi, uvicorn; print('Dependencies installed successfully')"
```

### 2. 配置系统

```bash
# 复制配置文件
cp config.yaml.example config.yaml

# 编辑配置文件，设置模型路径和API密钥
vim config.yaml
```

### 3. 启动服务

```bash
# 使用启动脚本（推荐）
python start_api_server.py

# 或直接运行
python cms_api_server.py

# 开发模式（支持热重载）
python start_api_server.py --host 0.0.0.0 --port 8000 --reload

# 生产模式（多进程）
uvicorn cms_api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 访问服务

- **API文档**: http://localhost:8000/docs (Swagger UI)
- **备用文档**: http://localhost:8000/redoc (ReDoc)
- **健康检查**: http://localhost:8000/health
- **服务状态**: http://localhost:8000/
- **系统信息**: http://localhost:8000/system-info

## API接口

### 认证

所有API请求需要在Header中包含认证信息：

```http
Authorization: Bearer cms-api-key-2024
```

### 核心接口

#### 1. 服务状态

**GET /** - 根路径状态检查

```bash
curl -X GET "http://localhost:8000/"
```

**GET /health** - 健康检查

```bash
curl -X GET "http://localhost:8000/health"
```

#### 2. 报告生成

**POST /generate-report** - 生成振动分析报告

```bash
curl -X POST "http://localhost:8000/generate-report" \
  -H "Authorization: Bearer cms-api-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "振动分析报告",
    "basic_info": {
      "wind_farm": "测试风场",
      "turbine_id": "WT001",
      "measurement_date": "2024-01-20",
      "operator": "张三",
      "equipment_status": "运行中"
    },
    "measurement_results": [
      {
        "measurement_point": "主轴承DE",
        "rms_value": 2.5,
        "peak_value": 8.2,
        "main_frequency": 25.5,
        "alarm_level": "normal"
      }
    ],
    "output_format": "pdf",
    "include_charts": true
  }'
```

**GET /report-status/{task_id}** - 查询报告生成状态

```bash
curl -X GET "http://localhost:8000/report-status/your-task-id" \
  -H "Authorization: Bearer cms-api-key-2024"
```

**GET /download-report/{task_id}** - 下载生成的报告

```bash
curl -X GET "http://localhost:8000/download-report/your-task-id" \
  -H "Authorization: Bearer cms-api-key-2024" \
  -o report.pdf
```

#### 3. 智能问答

**POST /chat** - 与系统进行对话

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Authorization: Bearer cms-api-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "如何分析振动数据？",
    "session_id": "optional-session-id",
    "context": {
      "equipment_type": "wind_turbine",
      "measurement_point": "main_bearing"
    }
  }'
```

**POST /chat/stream** - 流式对话（支持实时响应）

```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Authorization: Bearer cms-api-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "详细解释振动分析的步骤",
    "session_id": "stream-session-001"
  }'
```

#### 4. 数据分析

**POST /analyze-data** - 分析振动数据

```bash
curl -X POST "http://localhost:8000/analyze-data" \
  -H "Authorization: Bearer cms-api-key-2024" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@vibration_data.csv" \
  -F "analysis_config={
    \"sampling_rate\": 25600,
    \"analysis_types\": [\"time\", \"frequency\", \"envelope\"],
    \"equipment_info\": {
      \"type\": \"wind_turbine\",
      \"model\": \"V90-2.0MW\"
    }
  }"
```

**GET /analysis-result/{analysis_id}** - 获取分析结果

```bash
curl -X GET "http://localhost:8000/analysis-result/your-analysis-id" \
  -H "Authorization: Bearer cms-api-key-2024"
```

#### 5. 图表生成

**POST /generate-charts** - 生成分析图表

```bash
curl -X POST "http://localhost:8000/generate-charts" \
  -H "Authorization: Bearer cms-api-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": "your-analysis-id",
    "chart_types": ["waveform", "spectrum", "waterfall"],
    "output_format": "png",
    "chart_config": {
      "dpi": 300,
      "figsize": [12, 8],
      "style": "professional"
    }
  }'
```

#### 6. 系统管理

**DELETE /cleanup-reports** - 清理旧报告文件

```bash
curl -X DELETE "http://localhost:8000/cleanup-reports" \
  -H "Authorization: Bearer cms-api-key-2024" \
  -d '{"days_old": 7}'
```

**GET /system-info** - 获取系统信息

```bash
curl -X GET "http://localhost:8000/system-info" \
  -H "Authorization: Bearer cms-api-key-2024"
```

**POST /reload-config** - 重新加载配置

```bash
curl -X POST "http://localhost:8000/reload-config" \
  -H "Authorization: Bearer cms-api-key-2024"
```

## 数据模型

### ReportRequest（报告请求）

```json
{
  "title": "报告标题",
  "basic_info": {
    "wind_farm": "风场名称",
    "turbine_id": "风机编号",
    "measurement_date": "测量日期",
    "operator": "操作员",
    "equipment_status": "设备状态",
    "report_date": "报告日期（可选）"
  },
  "executive_summary": "执行摘要（可选）",
  "measurement_results": [
    {
      "measurement_point": "测量点",
      "rms_value": 2.5,
      "peak_value": 8.2,
      "main_frequency": 25.5,
      "alarm_level": "normal|warning|alarm"
    }
  ],
  "analysis_conclusion": "分析结论（可选）",
  "recommendations": ["建议1", "建议2"],
  "output_format": "pdf|html|docx",
  "include_charts": true,
  "template_type": "vibration_analysis"
}
```

### ChatRequest（对话请求）

```json
{
  "message": "用户消息内容",
  "session_id": "会话ID（可选）",
  "context": {
    "equipment_type": "设备类型",
    "measurement_point": "测量点",
    "analysis_context": "分析上下文"
  },
  "stream": false,
  "max_tokens": 1000,
  "temperature": 0.7
}
```

### AnalysisRequest（分析请求）

```json
{
  "file_data": "base64编码的文件数据或文件路径",
  "analysis_config": {
    "sampling_rate": 25600,
    "analysis_types": ["time", "frequency", "envelope", "order"],
    "frequency_range": [0, 1000],
    "filter_config": {
      "enable_filtering": true,
      "filter_type": "bandpass",
      "low_freq": 2,
      "high_freq": 1000
    }
  },
  "equipment_info": {
    "type": "wind_turbine",
    "model": "V90-2.0MW",
    "rated_power": 2000,
    "rotor_speed": 16.9
  },
  "measurement_info": {
    "point": "main_bearing_de",
    "direction": "radial",
    "sensor_type": "accelerometer",
    "sensitivity": 100
  }
}
```

### ChartRequest（图表请求）

```json
{
  "analysis_id": "分析任务ID",
  "chart_types": ["waveform", "spectrum", "waterfall", "trend", "overview"],
  "output_format": "png",
  "chart_config": {
    "dpi": 300,
    "figsize": [12, 8],
    "style": "professional",
    "color_scheme": "default",
    "font_size": 12,
    "title_config": {
      "show_title": true,
      "custom_title": "自定义标题"
    },
    "axis_config": {
      "x_label": "时间 (s)",
      "y_label": "幅值 (mm/s)",
      "grid": true
    }
  }
}
```

### APIResponse（API响应）

```json
{
  "success": true,
  "message": "响应消息",
  "data": {
    "key": "value"
  },
  "error": null,
  "timestamp": "2024-01-20T10:30:00Z",
  "request_id": "req_123456789",
  "processing_time": 1.23
}
```

### TaskStatus（任务状态）

```json
{
  "task_id": "task_123456789",
  "status": "pending|running|completed|failed",
  "progress": 75,
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:32:15Z",
  "estimated_completion": "2024-01-20T10:35:00Z",
  "result": {
    "file_path": "/reports/report_123.pdf",
    "file_size": 2048576,
    "download_url": "/download-report/task_123456789"
  },
  "error_details": null
}
```

## 使用示例

### Python客户端示例

```python
import requests
import json

class CMSAPIClient:
    def __init__(self, base_url="http://localhost:8000", api_key="cms-api-key-2024"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_report(self, report_data):
        response = requests.post(
            f"{self.base_url}/generate-report",
            headers=self.headers,
            json=report_data
        )
        return response.json()
    
    def get_report_status(self, task_id):
        response = requests.get(
            f"{self.base_url}/report-status/{task_id}",
            headers=self.headers
        )
        return response.json()
    
    def download_report(self, task_id, save_path):
        response = requests.get(
            f"{self.base_url}/download-report/{task_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        return False

# 使用示例
client = CMSAPIClient()

# 生成报告
report_data = {
    "title": "测试报告",
    "basic_info": {
        "wind_farm": "测试风场",
        "turbine_id": "WT001",
        "measurement_date": "2024-01-20",
        "operator": "测试员"
    },
    "measurement_results": [
        {
            "measurement_point": "主轴承",
            "rms_value": 2.5,
            "peak_value": 8.2,
            "main_frequency": 25.5,
            "alarm_level": "normal"
        }
    ],
    "output_format": "pdf"
}

result = client.generate_report(report_data)
if result["success"]:
    task_id = result["data"]["task_id"]
    print(f"任务ID: {task_id}")
    
    # 等待完成并下载
    import time
    while True:
        status = client.get_report_status(task_id)
        if status["data"]["status"] == "completed":
            client.download_report(task_id, "report.pdf")
            break
        time.sleep(2)
```

### JavaScript客户端示例

```javascript
class CMSAPIClient {
    constructor(baseUrl = 'http://localhost:8000', apiKey = 'cms-api-key-2024') {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async generateReport(reportData) {
        const response = await fetch(`${this.baseUrl}/generate-report`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(reportData)
        });
        return await response.json();
    }
    
    async getReportStatus(taskId) {
        const response = await fetch(`${this.baseUrl}/report-status/${taskId}`, {
            headers: this.headers
        });
        return await response.json();
    }
    
    async downloadReport(taskId) {
        const response = await fetch(`${this.baseUrl}/download-report/${taskId}`, {
            headers: this.headers
        });
        return await response.blob();
    }
}

// 使用示例
const client = new CMSAPIClient();

const reportData = {
    title: '测试报告',
    basic_info: {
        wind_farm: '测试风场',
        turbine_id: 'WT001',
        measurement_date: '2024-01-20',
        operator: '测试员'
    },
    measurement_results: [{
        measurement_point: '主轴承',
        rms_value: 2.5,
        peak_value: 8.2,
        main_frequency: 25.5,
        alarm_level: 'normal'
    }],
    output_format: 'pdf'
};
# 使用示例
client.generateReport(reportData)
    .then(result => {
        if (result.success) {
            console.log('任务ID:', result.data.task_id);
            // 轮询任务状态
            return pollTaskStatus(result.data.task_id);
        }
    })
    .then(finalResult => {
        console.log('报告生成完成:', finalResult);
    })
    .catch(error => {
        console.error('生成失败:', error);
    });

// 轮询任务状态的辅助函数
function pollTaskStatus(taskId) {
    return new Promise((resolve, reject) => {
        const checkStatus = async () => {
            try {
                const status = await client.getReportStatus(taskId);
                if (status.data.status === 'completed') {
                    resolve(status.data);
                } else if (status.data.status === 'failed') {
                    reject(new Error(status.data.error_details));
                } else {
                    setTimeout(checkStatus, 2000); // 2秒后重试
                }
            } catch (error) {
                reject(error);
            }
        };
        checkStatus();
    });
}
```

## 高级用法

### 批量处理

```python
import asyncio
import aiohttp
from typing import List, Dict

class AsyncCMSClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def batch_generate_reports(self, report_requests: List[Dict]) -> List[Dict]:
        """批量生成报告"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for request in report_requests:
                task = self._generate_single_report(session, request)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
    
    async def _generate_single_report(self, session: aiohttp.ClientSession, request: Dict) -> Dict:
        """生成单个报告"""
        async with session.post(
            f"{self.base_url}/generate-report",
            headers=self.headers,
            json=request
        ) as response:
            return await response.json()

# 使用示例
async def main():
    client = AsyncCMSClient("http://localhost:8000", "cms-api-key-2024")
    
    # 准备多个报告请求
    requests = [
        {"title": f"报告{i}", "basic_info": {...}, ...}
        for i in range(10)
    ]
    
    # 批量处理
    results = await client.batch_generate_reports(requests)
    print(f"成功生成 {len([r for r in results if not isinstance(r, Exception)])} 个报告")

# 运行
asyncio.run(main())
```

### 流式处理

```python
import requests
import json

def stream_chat(message: str, api_key: str):
    """流式对话处理"""
    url = "http://localhost:8000/chat/stream"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "message": message,
        "stream": True
    }
    
    with requests.post(url, headers=headers, json=data, stream=True) as response:
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    if 'content' in chunk:
                        print(chunk['content'], end='', flush=True)
                except json.JSONDecodeError:
                    continue
        print()  # 换行

# 使用示例
stream_chat("详细解释振动分析的原理和方法", "cms-api-key-2024")
```

### 错误重试机制

```python
import time
import random
from functools import wraps

def retry_on_failure(max_retries=3, backoff_factor=1.0):
    """错误重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        # 指数退避
                        delay = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                        print(f"请求失败，{delay:.1f}秒后重试... (尝试 {attempt + 1}/{max_retries + 1})")
                        time.sleep(delay)
                    else:
                        print(f"所有重试都失败了，最后错误: {e}")
            
            raise last_exception
        return wrapper
    return decorator

class RobustCMSClient(CMSAPIClient):
    @retry_on_failure(max_retries=3, backoff_factor=2.0)
    def generate_report_with_retry(self, report_data):
        """带重试机制的报告生成"""
        return self.generate_report(report_data)
    
    @retry_on_failure(max_retries=5, backoff_factor=1.0)
    def wait_for_completion(self, task_id, timeout=300):
        """等待任务完成，带超时和重试"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_report_status(task_id)
            
            if status["data"]["status"] == "completed":
                return status["data"]
            elif status["data"]["status"] == "failed":
                raise Exception(f"任务失败: {status['data'].get('error_details', '未知错误')}")
            
            time.sleep(2)
        
        raise TimeoutError(f"任务 {task_id} 在 {timeout} 秒内未完成")
```

## 测试

### 运行测试脚本

```bash
# 完整功能测试
python test_api_client.py

# 指定测试类型
python test_api_client.py --test connection
python test_api_client.py --test health
python test_api_client.py --test report
python test_api_client.py --test chat
python test_api_client.py --test analysis
python test_api_client.py --test charts

# 自定义服务地址
python test_api_client.py --url http://your-server:8000 --key your-api-key

# 压力测试
python test_api_client.py --test stress --concurrent 10 --requests 100
```

### 单元测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-mock

# 运行测试
pytest tests/test_api/ -v

# 运行特定测试
pytest tests/test_api/test_report_generation.py -v

# 生成覆盖率报告
pytest tests/test_api/ --cov=cms_api_server --cov-report=html
```

### 性能测试

```bash
# 使用locust进行负载测试
pip install locust
locust -f tests/load_test.py --host=http://localhost:8000

# 使用ab进行简单压测
ab -n 1000 -c 10 -H "Authorization: Bearer cms-api-key-2024" http://localhost:8000/health
```

## 部署

### 开发环境

```bash
# 启动开发服务器（支持热重载）
python start_api_server.py --reload
```

### 生产环境

```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn cms_api_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 使用Docker部署
docker build -t cms-api .
docker run -p 8000:8000 cms-api
```

### 环境变量配置

```bash
# 设置环境变量
export CMS_API_HOST=0.0.0.0
export CMS_API_PORT=8000
export CMS_API_WORKERS=4
export CMS_LOG_LEVEL=info
```

## 配置

### API密钥管理

在生产环境中，建议通过环境变量或配置文件管理API密钥：

```python
# 环境变量方式
import os
VALID_API_KEYS = {
    os.getenv('CMS_API_KEY', 'default-key'): 'production'
}

# 配置文件方式
import yaml
with open('api_config.yaml') as f:
    config = yaml.safe_load(f)
    VALID_API_KEYS = config['api_keys']
```

### 日志配置

```python
# 自定义日志配置
from loguru import logger

logger.add(
    "logs/api_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)
```

## 错误处理

### 常见错误码

- `400`: 请求参数错误
- `401`: 认证失败
- `404`: 资源不存在
- `500`: 服务器内部错误

### 错误响应格式

```json
{
  "success": false,
  "message": "错误描述",
  "error": "详细错误信息",
  "data": null
}
```

## 性能优化

### 并发处理

- 使用异步处理提高并发性能
- 后台任务处理避免阻塞
- 支持多进程部署

### 缓存策略

- 报告模板缓存
- 图表生成缓存
- 配置信息缓存

### 资源管理

- 自动清理过期文件
- 内存使用监控
- 磁盘空间管理

## 监控和日志

### 日志文件

- `logs/api_server.log`: 主服务日志
- `logs/access.log`: 访问日志
- `logs/error.log`: 错误日志

### 监控指标

- 请求响应时间
- 错误率统计
- 资源使用情况
- 任务处理状态

## 安全考虑

### 认证授权

- API密钥认证
- 请求频率限制
- IP白名单控制

### 数据安全

- 敏感信息加密
- 文件访问控制
- 日志脱敏处理

## 常见问题

### Q: 如何修改API端口？
A: 使用启动参数 `--port 9000` 或修改环境变量 `CMS_API_PORT`

### Q: 报告生成失败怎么办？
A: 检查日志文件，确认依赖包安装完整，验证输入数据格式

### Q: 如何增加新的API密钥？
A: 修改 `VALID_API_KEYS` 字典或使用配置文件管理

### Q: 支持HTTPS吗？
A: 支持，使用反向代理（如Nginx）配置SSL证书

## 更新日志

### v1.0.0
- 初始版本发布
- 支持PDF/HTML/DOCX报告生成
- 集成智能问答功能
- 提供完整API文档

## 联系支持

如有问题或建议，请联系开发团队或查看项目文档。