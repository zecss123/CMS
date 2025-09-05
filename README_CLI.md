# CMS振动分析系统 - 命令行版本

这是CMS振动分析系统的命令行版本，无需前端界面，通过主函数启动，接收用户信息并返回分析报告。

## 功能特性

- 🔧 **真实API集成**: 基于example.ipynb中的API模式，调用真实的振动数据接口
- 📊 **数据分析**: 获取和分析振动数据，生成统计报告
- 🤖 **模型运行**: 执行分析模型，获取智能分析结果
- 📈 **可视化图表**: 自动生成振动数据可视化图表
- 💬 **智能对话**: 支持自然语言交互（可选功能）
- 📄 **报告生成**: 自动生成详细的分析报告
- ⚡ **高性能处理**: 支持并发数据处理和缓存优化
- 🔄 **批量处理**: 支持多任务批量分析
- 📝 **详细日志**: 完整的操作日志和错误追踪
- 🛡️ **错误恢复**: 自动重试机制和异常处理
- 🎯 **智能匹配**: RAG增强的振动模式识别
- 📊 **多格式输出**: 支持JSON、CSV、PDF等多种输出格式

## 环境要求

- Python 3.8+
- 内存: 建议8GB以上
- 存储: 至少2GB可用空间
- 网络: 能够访问API服务器

## 安装依赖

### 基础安装
```bash
# 创建虚拟环境（推荐）
python -m venv cms_cli_env
source cms_cli_env/bin/activate  # Linux/Mac
# 或 cms_cli_env\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements_cli.txt

# 验证安装
python -c "import torch, transformers, requests; print('安装成功')"
```

### 开发环境安装
```bash
# 安装开发依赖
pip install -r requirements_cli.txt
pip install pytest pytest-cov black flake8
```

## 使用方法

### 1. 交互模式（推荐）

```bash
python cms_cli_app.py --mode interactive
```

启动后可以使用以下命令：

- `analyze <region> <station> <position> <point> <start_time> <end_time>` - 分析振动数据
- `chat <message>` - 智能对话
- `help` - 显示帮助信息
- `quit` - 退出程序

#### 示例：
```
请输入命令 > analyze A08 1003 8 AI_CMS024 "2025-01-12 00:00:00" "2025-01-13 00:00:00"
请输入命令 > chat 请分析最近的振动趋势
```

### 2. 批处理模式

```bash
python cms_cli_app.py --mode batch \
  --region A08 \
  --station 1003 \
  --position 8 \
  --point AI_CMS024 \
  --start-time "2025-01-12 00:00:00" \
  --end-time "2025-01-13 00:00:00" \
  --output report.txt
```

### 3. 高级用法

#### 批量分析多个测点
```bash
# 使用配置文件批量处理
python cms_cli_app.py --mode batch --config batch_config.json

# 并发处理（提高效率）
python cms_cli_app.py --mode batch --workers 4 --config batch_config.json
```

#### 自定义输出格式
```bash
# 生成JSON格式报告
python cms_cli_app.py --mode batch --output-format json --output results.json

# 生成CSV数据文件
python cms_cli_app.py --mode batch --output-format csv --output data.csv

# 生成PDF报告
python cms_cli_app.py --mode batch --output-format pdf --output report.pdf
```

#### 调试和日志控制
```bash
# 启用详细日志
python cms_cli_app.py --mode interactive --log-level DEBUG

# 指定日志文件
python cms_cli_app.py --mode batch --log-file /path/to/custom.log

# 静默模式（仅错误输出）
python cms_cli_app.py --mode batch --quiet
```

## 配置管理

### API配置

在使用前，请确保API配置正确：

1. **API端点**: 默认为 `http://172.16.253.39/api/model/services`
2. **认证令牌**: 需要在 `CMSAPIClient` 类中配置正确的Authorization token
3. **网络连接**: 确保能够访问API服务器

### 环境变量配置

```bash
# 设置API配置
export CMS_API_BASE_URL="http://172.16.253.39/api/model/services"
export CMS_API_TOKEN="your_auth_token_here"
export CMS_LOG_LEVEL="INFO"
export CMS_CACHE_DIR="./cache"
export CMS_OUTPUT_DIR="./outputs"
```

### 配置文件示例

创建 `config.yaml`：
```yaml
api:
  base_url: "http://172.16.253.39/api/model/services"
  timeout: 30
  retry_times: 3
  retry_delay: 1

logging:
  level: INFO
  file: cms_cli.log
  max_size: 10MB
  backup_count: 5

processing:
  workers: 2
  batch_size: 100
  cache_enabled: true
  cache_ttl: 3600

output:
  default_format: json
  include_charts: true
  chart_format: png
  report_template: default
```

## 配置文件

系统会尝试加载以下配置：
- `config/config_loader.py` - 主配置加载器
- 默认配置包括区域、风场、位置等参数

## API接口说明

系统集成了三个主要API接口：

1. **数据获取API** (`6853afa7540afad16e5114f8`)
   - 获取指定时间范围的振动数据
   - 支持多种振动特征参数

2. **模型运行API** (`681c0f2e016a0cd2dd73295f`)
   - 执行振动分析模型
   - 返回分析结果和执行时间

3. **图表生成API** (`6879cd88540afad16e77dbc3`)
   - 生成振动数据可视化图表
   - 返回base64编码的图片数据

## 输出文件

- **分析报告**: 包含数据统计、模型结果和建议
- **可视化图表**: PNG格式的振动数据图表
- **日志文件**: `cms_cli.log` - 系统运行日志

## 故障排除

### 常见问题

1. **API连接失败**
   ```bash
   # 测试API连接
   curl -X GET "http://172.16.253.39/api/model/services/health"
   
   # 检查网络连通性
   ping 172.16.253.39
   ```
   - 检查网络连接和防火墙设置
   - 验证API端点和认证信息
   - 确认服务器状态和负载

2. **模块导入失败**
   ```bash
   # 检查Python环境
   python --version
   pip list | grep -E "torch|transformers|requests"
   
   # 重新安装依赖
   pip install --upgrade -r requirements_cli.txt
   ```
   - 确保Python版本3.8+
   - 检查虚拟环境是否激活
   - 验证包版本兼容性

3. **数据解析错误**
   ```bash
   # 启用调试模式查看详细错误
   python cms_cli_app.py --mode batch --log-level DEBUG
   ```
   - 检查API返回数据格式
   - 验证时间格式（YYYY-MM-DD HH:MM:SS）
   - 确认测点参数正确性

4. **内存不足错误**
   ```bash
   # 监控内存使用
   python cms_cli_app.py --mode batch --memory-limit 4GB
   
   # 减少批处理大小
   python cms_cli_app.py --mode batch --batch-size 50
   ```
   - 减少并发worker数量
   - 启用数据流式处理
   - 清理缓存文件

5. **模型加载失败**
   ```bash
   # 检查模型文件
   ls -la models/
   
   # 重新下载模型
   python -c "from transformers import AutoModel; AutoModel.from_pretrained('model_name')"
   ```
   - 检查模型文件完整性
   - 验证网络连接（下载模型）
   - 确认磁盘空间充足

### 日志分析

```bash
# 实时查看日志
tail -f cms_cli.log

# 查看错误日志
grep "ERROR" cms_cli.log

# 查看最近的警告
grep "WARNING" cms_cli.log | tail -20

# 分析性能日志
grep "PERFORMANCE" cms_cli.log | awk '{print $3, $4}'
```

### 性能优化

#### 系统级优化
```bash
# 设置环境变量优化
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false

# 使用GPU加速（如果可用）
export CUDA_VISIBLE_DEVICES=0
```

#### 应用级优化
```bash
# 启用缓存
python cms_cli_app.py --mode batch --enable-cache

# 调整批处理大小
python cms_cli_app.py --mode batch --batch-size 200

# 使用多进程
python cms_cli_app.py --mode batch --workers 8
```

#### 内存优化
```bash
# 启用内存映射
python cms_cli_app.py --mode batch --memory-map

# 设置内存限制
python cms_cli_app.py --mode batch --memory-limit 6GB

# 启用垃圾回收优化
python cms_cli_app.py --mode batch --gc-optimize
```

## 开发说明

### 项目结构
```
cms_vibration_rag/
├── cms_cli_app.py          # 主应用文件
├── requirements_cli.txt    # 依赖包列表
├── README_CLI.md          # 使用说明
├── config/                # 配置文件目录
│   ├── config_loader.py   # 配置加载器
│   ├── config.yaml        # 主配置文件
│   └── batch_config.json  # 批处理配置
├── chat/                  # 对话功能模块
│   ├── __init__.py
│   ├── chat_handler.py    # 对话处理器
│   └── rag_engine.py      # RAG引擎
├── knowledge/             # 知识库模块
│   ├── __init__.py
│   ├── vector_store.py    # 向量存储
│   └── embeddings.py      # 嵌入模型
├── api/                   # API客户端模块
│   ├── __init__.py
│   ├── cms_client.py      # CMS API客户端
│   └── retry_handler.py   # 重试处理器
├── utils/                 # 工具模块
│   ├── __init__.py
│   ├── logger.py          # 日志工具
│   ├── cache.py           # 缓存管理
│   └── validators.py      # 数据验证
├── models/                # 模型文件目录
├── cache/                 # 缓存目录
├── outputs/               # 输出目录
├── tests/                 # 测试文件
│   ├── test_api.py
│   ├── test_chat.py
│   └── test_utils.py
└── cms_cli.log           # 运行日志
```

### 核心类设计

#### CMSCLIApp 类
```python
class CMSCLIApp:
    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.api_client = CMSAPIClient(self.config)
        self.chat_handler = ChatHandler(self.config)
        self.logger = setup_logger(self.config)
    
    def run_interactive(self):
        """交互模式主循环"""
        pass
    
    def run_batch(self, params: dict):
        """批处理模式"""
        pass
```

#### CMSAPIClient 类
```python
class CMSAPIClient:
    def __init__(self, config: dict):
        self.base_url = config['api']['base_url']
        self.timeout = config['api']['timeout']
        self.retry_handler = RetryHandler(config)
    
    async def get_vibration_data(self, params: dict):
        """获取振动数据"""
        pass
    
    async def run_analysis_model(self, data: dict):
        """运行分析模型"""
        pass
```

### 扩展开发

#### 添加新的API接口
```python
# 在 api/cms_client.py 中添加
class CMSAPIClient:
    async def get_equipment_status(self, equipment_id: str):
        """获取设备状态"""
        endpoint = f"/equipment/{equipment_id}/status"
        return await self._make_request('GET', endpoint)
```

#### 添加新的命令
```python
# 在 cms_cli_app.py 中添加
class CMSCLIApp:
    def handle_status_command(self, args: list):
        """处理status命令"""
        if len(args) < 1:
            print("用法: status <equipment_id>")
            return
        
        equipment_id = args[0]
        status = await self.api_client.get_equipment_status(equipment_id)
        print(f"设备 {equipment_id} 状态: {status}")
```

#### 自定义输出格式
```python
# 在 utils/ 中创建 formatters.py
class ReportFormatter:
    @staticmethod
    def to_json(data: dict) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def to_csv(data: dict) -> str:
        # CSV格式化逻辑
        pass
    
    @staticmethod
    def to_pdf(data: dict, template: str = 'default') -> bytes:
        # PDF生成逻辑
        pass
```

### 测试指南

#### 单元测试
```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_api.py -v

# 运行覆盖率测试
pytest --cov=. --cov-report=html
```

#### 集成测试
```bash
# 测试API连接
python -m pytest tests/test_integration.py::test_api_connection

# 测试完整流程
python -m pytest tests/test_integration.py::test_full_workflow
```

#### 性能测试
```bash
# 使用pytest-benchmark
pytest tests/test_performance.py --benchmark-only

# 内存使用测试
python -m memory_profiler cms_cli_app.py --mode batch
```

## 附录

### 命令行参数完整列表

```bash
python cms_cli_app.py [OPTIONS]

选项:
  --mode {interactive,batch}     运行模式 (默认: interactive)
  --config PATH                  配置文件路径
  --region TEXT                  区域代码
  --station TEXT                 风场代码
  --position TEXT                位置代码
  --point TEXT                   测点代码
  --start-time TEXT              开始时间 (YYYY-MM-DD HH:MM:SS)
  --end-time TEXT                结束时间 (YYYY-MM-DD HH:MM:SS)
  --output PATH                  输出文件路径
  --output-format {json,csv,pdf} 输出格式 (默认: json)
  --workers INTEGER              并发worker数量 (默认: 2)
  --batch-size INTEGER           批处理大小 (默认: 100)
  --log-level {DEBUG,INFO,WARNING,ERROR} 日志级别 (默认: INFO)
  --log-file PATH                日志文件路径
  --memory-limit TEXT            内存限制 (如: 4GB)
  --enable-cache                 启用缓存
  --cache-ttl INTEGER            缓存TTL秒数 (默认: 3600)
  --quiet                        静默模式
  --help                         显示帮助信息
```

### 批处理配置文件示例

创建 `batch_config.json`：
```json
{
  "tasks": [
    {
      "name": "风机A08-1003分析",
      "region": "A08",
      "station": "1003",
      "position": "8",
      "point": "AI_CMS024",
      "start_time": "2025-01-12 00:00:00",
      "end_time": "2025-01-13 00:00:00",
      "output": "reports/A08_1003_report.json"
    },
    {
      "name": "风机A08-1004分析",
      "region": "A08",
      "station": "1004",
      "position": "8",
      "point": "AI_CMS025",
      "start_time": "2025-01-12 00:00:00",
      "end_time": "2025-01-13 00:00:00",
      "output": "reports/A08_1004_report.json"
    }
  ],
  "global_settings": {
    "workers": 4,
    "batch_size": 200,
    "enable_cache": true,
    "output_format": "json",
    "include_charts": true
  }
}
```

### 最佳实践

#### 1. 性能优化建议
- 使用适当的worker数量（通常为CPU核心数的1-2倍）
- 启用缓存以避免重复API调用
- 合理设置批处理大小，避免内存溢出
- 在生产环境中使用配置文件而非命令行参数

#### 2. 错误处理策略
- 始终检查API响应状态
- 实现指数退避重试机制
- 记录详细的错误日志用于调试
- 设置合理的超时时间

#### 3. 安全考虑
- 不要在命令行中直接传递敏感信息
- 使用环境变量或配置文件存储API密钥
- 定期轮换API访问令牌
- 限制日志中的敏感信息输出

#### 4. 监控和维护
- 定期检查日志文件大小，实施日志轮转
- 监控API调用频率，避免超出限制
- 定期清理缓存和临时文件
- 建立健康检查机制

### 常见使用场景

#### 场景1：日常巡检分析
```bash
# 分析昨天的数据
python cms_cli_app.py --mode batch \
  --region A08 --station 1003 --position 8 --point AI_CMS024 \
  --start-time "$(date -d 'yesterday' '+%Y-%m-%d 00:00:00')" \
  --end-time "$(date -d 'yesterday' '+%Y-%m-%d 23:59:59')" \
  --output "daily_reports/$(date -d 'yesterday' '+%Y%m%d')_report.json"
```

#### 场景2：批量健康检查
```bash
# 使用配置文件批量检查多个风机
python cms_cli_app.py --mode batch \
  --config health_check_config.json \
  --workers 8 \
  --output-format pdf
```

#### 场景3：故障诊断分析
```bash
# 详细分析特定时间段的异常
python cms_cli_app.py --mode interactive \
  --log-level DEBUG \
  --enable-cache
```

### 技术支持

如遇到问题，请提供以下信息：
1. 完整的错误日志
2. 使用的命令和参数
3. 系统环境信息（Python版本、操作系统等）
4. API响应示例（如适用）

## 许可证

本项目仅供内部使用，请勿外传。

---

**版本**: 1.0.0  
**最后更新**: 2025-01-14  
**维护者**: CMS开发团队