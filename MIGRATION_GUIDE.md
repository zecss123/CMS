# CMS振动分析系统 - 用户迁移指南

本文档指导用户如何调整系统配置、切换大模型接口、迁移数据和自定义系统参数。

## 目录

- [新手快速入门](#新手快速入门)
- [配置文件说明](#配置文件说明)
- [大模型接口配置](#大模型接口配置)
- [API接口调整](#api接口调整)
- [数据库迁移](#数据库迁移)
- [知识库迁移](#知识库迁移)
- [模板自定义](#模板自定义)
- [性能参数调优](#性能参数调优)
- [环境变量配置](#环境变量配置)
- [常见迁移场景](#常见迁移场景)
- [故障排除](#故障排除)

## 新手快速入门

### 🚀 我想要做什么？

#### 1. 我想换个大模型（比如从OpenAI换到DeepSeek）

**步骤：**
1. 打开 `config.yaml` 文件
2. 找到 `llm:` 部分
3. 修改 `provider: "deepseek"` 
4. 在 `deepseek:` 部分填入你的API密钥
5. 重启应用

**完整示例：**
```yaml
llm:
  provider: "deepseek"  # 改这里
  deepseek:
    api_key: "sk-你的deepseek密钥"  # 改这里
    base_url: "https://api.deepseek.com/v1"
    model: "deepseek-chat"
    temperature: 0.7
    max_tokens: 2048
```

**⚠️ 注意事项：**
- 修改后需要重启所有应用（Streamlit、Gradio、API服务器）
- 确保你有对应平台的API密钥
- 不同模型的响应格式可能略有差异

#### 2. 我想启动网页界面

**Streamlit界面（推荐新手）：**
```bash
cd /path/to/cms_vibration_rag
python -m streamlit run streamlit_app.py
```
访问：http://localhost:8501

**Gradio界面：**
```bash
cd /path/to/cms_vibration_rag
python gradio_app.py
```
访问：http://localhost:7860

**⚠️ 启动前检查：**
- 确保 `config.yaml` 中模型配置正确
- 确保API密钥已设置
- 确保依赖包已安装：`pip install -r requirements.txt`

#### 3. 我想启动API服务器

**启动API服务器：**
```bash
cd /path/to/cms_vibration_rag
python api/main.py
```

**API文档地址：**
- Swagger文档：http://localhost:8000/docs
- ReDoc文档：http://localhost:8000/redoc

**测试API：**
```bash
# 健康检查
curl http://localhost:8000/health

# 聊天接口测试
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "session_id": "test"}'
```

#### 4. 我想修改数据库配置

**从SQLite换到PostgreSQL：**

1. **安装PostgreSQL依赖：**
```bash
pip install psycopg2-binary
```

2. **修改config.yaml：**
```yaml
vector_db:
  provider: "chromadb"  # 或者 "pinecone"
  chromadb:
    persist_directory: "./data/vector_db"
    collection_name: "cms_knowledge"
```

3. **重新初始化数据库：**
```bash
python -c "
from knowledge.knowledge_manager import KnowledgeManager
km = KnowledgeManager()
km.initialize_database()
print('数据库初始化完成')
"
```

**⚠️ 配套修改：**
- 确保数据库服务已启动
- 确保数据库和用户已创建
- 备份原数据（如果需要）

### 🔧 常见配置修改

#### 修改日志级别
```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "cms_system.log"
```

#### 修改处理线程数
```yaml
processing:
  max_workers: 4  # 根据CPU核心数调整
  batch_size: 100  # 根据内存大小调整
```

#### 启用/禁用缓存
```yaml
processing:
  cache_enabled: true  # true启用，false禁用
  cache_ttl: 3600
```

## 系统配置

### 📝 日志配置（调试和监控）

**我想调整日志级别和输出：**

**开发环境（详细日志）：**
```yaml
logging:
  level: "DEBUG"  # 显示所有调试信息
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    - type: "console"  # 控制台输出
      level: "DEBUG"
    - type: "file"
      filename: "logs/cms_vibration_debug.log"
      level: "DEBUG"
      max_bytes: 10485760  # 10MB
      backup_count: 5
```

**生产环境（精简日志）：**
```yaml
logging:
  level: "INFO"  # 只显示重要信息
  format: "%(asctime)s - %(levelname)s - %(message)s"
  handlers:
    - type: "file"
      filename: "logs/cms_vibration.log"
      level: "INFO"
      max_bytes: 52428800  # 50MB
      backup_count: 10
```

**⚠️ 日志配置配套修改：**
1. 创建日志目录：
   ```bash
   mkdir -p logs
   ```
2. 设置日志文件权限：
   ```bash
   chmod 755 logs
   ```
3. 重启应用以应用新配置
4. 监控日志文件大小，避免磁盘空间不足

### 🚀 缓存配置（提升性能）

**我想配置缓存系统：**

**选项1：内存缓存（简单，适合单机）**
```yaml
cache:
  type: "memory"
  config:
    max_size: 1000  # 最大缓存条目数
    ttl: 3600  # 默认过期时间（秒）
```

**选项2：Redis缓存（推荐，支持分布式）**
```yaml
cache:
  type: "redis"
  config:
    host: "localhost"  # Redis服务器地址
    port: 6379
    db: 0  # 数据库编号
    password: null  # 如果有密码则填写
    ttl: 3600  # 默认过期时间（秒）
    max_connections: 10
```

**⚠️ Redis缓存配套修改：**
1. 安装Redis服务器：
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # CentOS/RHEL
   sudo yum install redis
   
   # 或使用Docker
   docker run -d --name redis -p 6379:6379 redis:latest
   ```

2. 安装Python Redis客户端：
   ```bash
   pip install redis
   ```

3. 启动Redis服务：
   ```bash
   sudo systemctl start redis
   sudo systemctl enable redis
   ```

4. 测试Redis连接：
   ```bash
   redis-cli ping
   # 期望返回：PONG
   ```

### ⚡ 性能配置

**我想优化系统性能：**

```yaml
performance:
  # 并发配置
  max_workers: 4  # 工作进程数（建议为CPU核心数）
  max_concurrent_requests: 100  # 最大并发请求数
  
  # 内存配置
  max_memory_usage: "2GB"  # 最大内存使用量
  gc_threshold: 0.8  # 垃圾回收阈值
  
  # 超时配置
  request_timeout: 30  # 请求超时时间（秒）
  llm_timeout: 60  # LLM调用超时时间（秒）
  db_timeout: 10  # 数据库查询超时时间（秒）
```

**⚠️ 性能优化配套修改：**
1. 监控系统资源使用：
   ```bash
   # 查看CPU和内存使用
   htop
   
   # 查看进程状态
   ps aux | grep python
   ```

2. 调整系统限制：
   ```bash
   # 增加文件描述符限制
   ulimit -n 65536
   ```

3. 重启应用以应用新配置

### 🔒 安全配置

**我想加强系统安全：**

```yaml
security:
  # API安全
  enable_cors: true  # 启用跨域请求
  allowed_origins:
    - "http://localhost:3000"
    - "https://yourdomain.com"
  
  # 请求限制
  rate_limit:
    enabled: true
    requests_per_minute: 60  # 每分钟最大请求数
    burst_size: 10  # 突发请求数
  
  # 文件上传安全
  upload:
    max_file_size: "10MB"  # 最大文件大小
    allowed_extensions: [".pdf", ".txt", ".docx"]  # 允许的文件类型
    scan_uploads: true  # 扫描上传文件
```

**⚠️ 安全配置配套修改：**
1. 安装安全相关依赖：
   ```bash
   pip install python-multipart aiofiles
   ```

2. 配置防火墙规则：
   ```bash
   # 只允许必要端口
   sudo ufw allow 8000/tcp  # API端口
   sudo ufw allow 8501/tcp  # Streamlit端口
   ```

3. 定期更新依赖包：
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

### 📋 修改参数后的检查清单

**修改大模型后：**
- [ ] 重启所有应用
- [ ] 测试聊天功能
- [ ] 检查日志是否有错误
- [ ] 验证API响应格式

**修改数据库后：**
- [ ] 运行数据库初始化脚本
- [ ] 测试数据读写
- [ ] 备份原数据
- [ ] 检查连接配置

**修改API配置后：**
- [ ] 重启API服务器
- [ ] 测试API端点
- [ ] 检查认证配置
- [ ] 验证响应格式

### 🆘 出问题了怎么办？

**常见错误及解决方案：**

1. **"API密钥无效"**
   - 检查 `config.yaml` 中的API密钥是否正确
   - 确认密钥格式（通常以 `sk-` 开头）
   - 检查网络连接

2. **"模块未找到"**
   ```bash
   pip install -r requirements.txt
   ```

3. **"向量数据库连接失败"**
   - 检查向量数据库目录是否存在
   - 验证连接参数
   - 重新初始化数据库

4. **"端口被占用"**
   ```bash
   # 查看端口占用
   lsof -i :8501  # Streamlit
   lsof -i :7860  # Gradio
   lsof -i :8000  # API服务器
   
   # 杀死进程
   kill -9 <进程ID>
   ```

5. **"内存不足"**
   - 启用模型量化：`load_in_4bit: true`
   - 减少批处理大小：`batch_size: 16`
   - 减少最大worker数：`max_workers: 2`

## 配置文件说明

### 主配置文件 (config.yaml)

系统的核心配置文件位于项目根目录：

```yaml
# CMS振动分析系统配置文件
api:
  # CMS数据API配置
  cms_base_url: "http://172.16.253.39/api/model/services"
  timeout: 30
  retry_times: 3
  retry_delay: 1
  
  # 认证配置
  auth_token: "your_auth_token_here"
  api_key: "your_api_key_here"

# 大语言模型配置
llm:
  # 模型提供商: openai, deepseek, qwen, local
  provider: "deepseek"
  
  # OpenAI配置
  openai:
    api_key: "sk-your-openai-key"
    base_url: "https://api.openai.com/v1"
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 2048
  
  # DeepSeek配置
  deepseek:
    api_key: "sk-your-deepseek-key"
    base_url: "https://api.deepseek.com/v1"
    model: "deepseek-chat"
    temperature: 0.7
    max_tokens: 2048
  
  # 通义千问配置
  qwen:
    api_key: "sk-your-qwen-key"
    base_url: "https://dashscope.aliyuncs.com/api/v1"
    model: "qwen-turbo"
    temperature: 0.7
    max_tokens: 2048
  
  # 本地模型配置
  local:
    model_path: "/root/autodl-tmp/models/deepseek-7b"
    device: "cuda"
    max_memory: "8GB"
    load_in_8bit: false
    load_in_4bit: true

# 嵌入模型配置
embedding:
  # 模型类型: sentence_transformers, openai, local
  provider: "sentence_transformers"
  
  # SentenceTransformers配置
  sentence_transformers:
    model_name: "all-MiniLM-L6-v2"
    device: "cuda"
    batch_size: 32
  
  # OpenAI嵌入配置
  openai:
    api_key: "sk-your-openai-key"
    model: "text-embedding-ada-002"
  
  # 本地嵌入模型
  local:
    model_path: "/root/autodl-tmp/models/embeddings/bge-large-zh"
    device: "cuda"

# 向量数据库配置
vector_db:
  # 数据库类型: chromadb, faiss, pinecone
  provider: "chromadb"
  
  # ChromaDB配置
  chromadb:
    persist_directory: "./data/vector_db"
    collection_name: "cms_knowledge"
  
  # Pinecone配置
  pinecone:
    api_key: "your-pinecone-key"
    environment: "us-west1-gcp"
    index_name: "cms-vibration"

# 数据处理配置
processing:
  # 并发处理
  max_workers: 4
  batch_size: 100
  
  # 缓存配置
  cache_enabled: true
  cache_ttl: 3600
  cache_dir: "./cache"
  
  # 内存管理
  max_memory_usage: "6GB"
  gc_threshold: 0.8

# 日志配置
logging:
  level: "INFO"
  file: "cms_system.log"
  max_size: "10MB"
  backup_count: 5
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 输出配置
output:
  # 默认输出格式
  default_format: "json"
  
  # 报告配置
  reports:
    template_dir: "./report_templates"
    output_dir: "./output"
    include_charts: true
    chart_format: "png"
    chart_dpi: 300
  
  # 图表配置
  charts:
    font_family: "SimHei"
    figure_size: [12, 8]
    color_scheme: "default"
    style: "seaborn"
```

### 应用特定配置

#### Streamlit配置 (.streamlit/config.toml)
```toml
[server]
port = 8501
headless = true
enableCORS = false
enableXsrfProtection = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

#### Gradio配置
```python
# 在gradio_app.py中修改
import gradio as gr

# 基础配置
GRADIO_CONFIG = {
    "server_name": "0.0.0.0",
    "server_port": 7860,
    "share": False,
    "debug": False,
    "auth": None,  # 或 ("username", "password")
    "ssl_keyfile": None,
    "ssl_certfile": None,
    "ssl_keyfile_password": None
}
```

## 大模型接口配置

### 🔄 API版本兼容性说明

**重要提醒：** 修改大模型配置不会影响API服务器的版本和接口格式。API服务器作为中间层，会自动适配不同的大模型提供商，对外提供统一的接口格式。

**API兼容性保证：**
- ✅ 聊天接口 `/chat` 格式保持不变
- ✅ 报告生成接口 `/generate_report` 格式保持不变
- ✅ 知识检索接口 `/search` 格式保持不变
- ✅ 客户端代码无需修改

### 1. 切换到OpenAI

**配置文件方式：**
```yaml
# 在config.yaml中修改
model:
  type: "openai"  # 关键配置
  openai:
    api_key: "sk-your-openai-api-key"  # 必须修改
    base_url: "https://api.openai.com/v1"
    model: "gpt-4"  # 可选：gpt-3.5-turbo, gpt-4, gpt-4-turbo
    temperature: 0.7  # 创造性：0-2，越高越有创意
    max_tokens: 2048  # 最大输出长度
```

**环境变量方式：**
```bash
# 在.env文件中设置
CMS_MODEL_TYPE=openai
CMS_OPENAI_API_KEY=sk-your-openai-api-key
CMS_OPENAI_BASE_URL=https://api.openai.com/v1
```

**⚠️ 配套修改清单：**
1. 确保网络能访问OpenAI API
2. 检查API密钥余额
3. 重启所有服务：
   ```bash
   # 重启Streamlit
   pkill -f streamlit
   python streamlit_app.py
   
   # 重启API服务器
   pkill -f "python.*api"
   python start_api_server.py
   ```
4. 测试聊天功能是否正常

### 2. 切换到DeepSeek

**配置文件方式：**
```yaml
model:
  type: "deepseek_api"  # 关键配置
  deepseek_api:
    api_key: "sk-your-deepseek-key"  # 必须修改
    base_url: "https://api.deepseek.com/v1"
    model: "deepseek-chat"  # 推荐模型
    temperature: 0.7
    max_tokens: 2048
```

**环境变量方式：**
```bash
# 在.env文件中设置
CMS_MODEL_TYPE=deepseek_api
CMS_DEEPSEEK_API_KEY=sk-your-deepseek-key
```

**⚠️ DeepSeek特殊说明：**
- DeepSeek API相对便宜，适合大量使用
- 支持中文对话，效果较好
- 需要科学上网访问（部分地区）

**配套修改：**
1. 注册DeepSeek账号获取API密钥
2. 检查网络连接
3. 重启服务并测试

### 3. 使用本地模型

**配置文件方式：**
```yaml
model:
  type: "local"  # 关键配置
  local:
    model_path: "/root/autodl-tmp/models/deepseek-7b"  # 模型路径
    device: "cuda"  # GPU加速，CPU用"cpu"
    max_memory: "8GB"  # 根据显存调整
    load_in_8bit: false
    load_in_4bit: true  # 4bit量化节省内存
    trust_remote_code: true
```

**⚠️ 本地模型特殊说明：**
- 需要下载模型文件（通常几GB到几十GB）
- 需要足够的显存（推荐8GB以上）
- 首次加载较慢，后续使用快
- 无需网络连接

**配套修改清单：**
1. **下载模型：**
   ```bash
   # 使用huggingface-cli下载
   pip install huggingface_hub
   huggingface-cli download deepseek-ai/deepseek-llm-7b-chat --local-dir /root/autodl-tmp/models/deepseek-7b
   ```

2. **检查显存：**
   ```bash
   nvidia-smi  # 查看GPU显存
   ```

3. **调整量化设置：**
   - 显存不足时启用：`load_in_4bit: true`
   - 显存充足时禁用：`load_in_4bit: false`

4. **测试加载：**
   ```bash
   python -c "
   from chat.llm_client import LLMClient
   from config.config_loader import get_config
   config = get_config()
   client = LLMClient(config.get_model_config())
   print('模型加载成功')
   "
   ```

### 4. 使用自定义API

**配置文件方式：**
```yaml
model:
  type: "custom"  # 关键配置
  custom:
    api_key: "your-custom-api-key"  # 必须修改
    base_url: "https://your-api.com/v1"  # 必须修改
    model: "your-model-name"
    temperature: 0.7
    max_tokens: 2048
```

**适用场景：**
- 企业内部API
- 其他兼容OpenAI格式的API
- 代理服务

**配套修改：**
1. 确认API格式兼容OpenAI
2. 测试API连通性
3. 验证认证方式

**代码中的调整：**

在 `chat/llm_client.py` 中添加新的模型支持：

```python
class LLMClient:
    def __init__(self, config):
        self.config = config
        self.provider = config['llm']['provider']
        
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "deepseek":
            self._init_deepseek()
        elif self.provider == "qwen":
            self._init_qwen()
        elif self.provider == "local":
            self._init_local_model()
    
    def _init_openai(self):
        import openai
        openai_config = self.config['llm']['openai']
        self.client = openai.OpenAI(
            api_key=openai_config['api_key'],
            base_url=openai_config.get('base_url')
        )
    
    def _init_deepseek(self):
        import openai
        deepseek_config = self.config['llm']['deepseek']
        self.client = openai.OpenAI(
            api_key=deepseek_config['api_key'],
            base_url=deepseek_config['base_url']
        )
    
    def _init_local_model(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM
        local_config = self.config['llm']['local']
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            local_config['model_path'],
            trust_remote_code=local_config.get('trust_remote_code', True)
        )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            local_config['model_path'],
            device_map="auto",
            max_memory={0: local_config.get('max_memory', '8GB')},
            load_in_8bit=local_config.get('load_in_8bit', False),
            load_in_4bit=local_config.get('load_in_4bit', True),
            trust_remote_code=local_config.get('trust_remote_code', True)
        )
```

## API接口调整

### 🔧 外部API配置（连接CMS系统）

**我想连接到CMS系统获取真实数据：**

1. **修改config.yaml：**
```yaml
external_api:
  enabled: true  # 启用外部API
  cms_api:
    base_url: "http://172.16.253.39/api/model/services"  # CMS系统地址
    api_key: "your_cms_api_key"  # 必须修改
    timeout: 30
    retry_count: 3
```

2. **环境变量方式：**
```bash
# 在.env文件中设置
CMS_EXTERNAL_API_ENABLED=true
CMS_CMS_API_KEY=your_cms_api_key
CMS_CMS_API_URL=http://172.16.253.39/api/model/services
```

**⚠️ 配套修改清单：**
1. 确保网络能访问CMS系统
2. 获取有效的API密钥
3. 测试API连通性：
   ```bash
   curl -H "Authorization: Bearer your_api_key" \
        "http://172.16.253.39/api/model/services/health"
   ```
4. 重启API服务器

### 🚀 启动API服务器的不同方式

**方式1：直接启动（推荐新手）**
```bash
cd /root/autodl-tmp/cms_vibration_rag
python start_api_server.py
```

**方式2：使用FastAPI命令**
```bash
cd /root/autodl-tmp/cms_vibration_rag
uvicorn cms_api_server:app --host 0.0.0.0 --port 8000 --reload
```

**方式3：后台运行**
```bash
cd /root/autodl-tmp/cms_vibration_rag
nohup python start_api_server.py > api.log 2>&1 &
```

### 📡 API接口说明

**核心接口列表：**

| 接口路径 | 方法 | 功能 | 是否需要认证 |
|---------|------|------|-------------|
| `/health` | GET | 健康检查 | ❌ |
| `/chat` | POST | 智能对话 | ❌ |
| `/generate_report` | POST | 生成报告 | ❌ |
| `/search` | POST | 知识检索 | ❌ |
| `/upload` | POST | 文件上传 | ❌ |

**接口测试示例：**

1. **健康检查：**
```bash
curl http://localhost:8000/health
# 期望返回：{"status": "healthy"}
```

2. **智能对话：**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "分析一下1号风机的振动情况",
    "session_id": "test_session"
  }'
```

3. **生成报告：**
```bash
curl -X POST "http://localhost:8000/generate_report" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "WTG001",
    "report_type": "comprehensive",
    "time_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  }'
```

### 🔌 添加新的API端点

**如果你想添加自定义API接口：**

1. **在cms_api_server.py中添加：**
```python
@app.post("/custom/analysis")
async def custom_analysis(request: dict):
    """自定义分析接口"""
    try:
        # 你的自定义逻辑
        result = await perform_custom_analysis(request)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

2. **重启API服务器：**
```bash
pkill -f "python.*api"
python start_api_server.py
```

3. **测试新接口：**
```bash
curl -X POST "http://localhost:8000/custom/analysis" \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
```

**⚠️ API修改注意事项：**
- 修改API后需要重启服务器
- 新接口会自动出现在Swagger文档中
- 保持接口格式的一致性
- 添加适当的错误处理

### CMS数据API配置

修改 `api/real_cms_client.py`：

```python
class RealCMSClient:
    def __init__(self, config=None):
        if config:
            self.base_url = config['api']['cms_base_url']
            self.auth_token = config['api']['auth_token']
            self.timeout = config['api']['timeout']
        else:
            # 从环境变量读取
            self.base_url = os.getenv('CMS_API_BASE_URL', 'http://172.16.253.39/api/model/services')
            self.auth_token = os.getenv('CMS_AUTH_TOKEN')
            self.timeout = int(os.getenv('CMS_API_TIMEOUT', '30'))
        
        self.headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
```

### 添加新的API端点

```python
# 在api/real_cms_client.py中添加
class RealCMSClient:
    def get_equipment_list(self, region=None):
        """获取设备列表"""
        endpoint = "/equipment/list"
        params = {'region': region} if region else {}
        return self._make_request('GET', endpoint, params=params)
    
    def get_alarm_history(self, equipment_id, start_time, end_time):
        """获取报警历史"""
        endpoint = f"/equipment/{equipment_id}/alarms"
        params = {
            'start_time': start_time,
            'end_time': end_time
        }
        return self._make_request('GET', endpoint, params=params)
```

## 数据库配置

### 🗄️ 向量数据库配置（存储文档向量）

**我想更换向量数据库类型：**

**选项1：Chroma（推荐新手，轻量级）**
```yaml
vector_db:
  type: "chroma"
  config:
    persist_directory: "./data/chroma_db"  # 数据存储位置
    collection_name: "cms_vibration_docs"  # 集合名称
    embedding_dimension: 1536  # 向量维度（与embedding模型匹配）
```

**选项2：FAISS（高性能，适合大数据量）**
```yaml
vector_db:
  type: "faiss"
  config:
    index_path: "./data/faiss_index"  # 索引文件路径
    dimension: 1536
    index_type: "IVF"  # 索引类型
```

**选项3：Milvus（企业级，分布式）**
```yaml
vector_db:
  type: "milvus"
  config:
    host: "localhost"
    port: 19530
    collection_name: "cms_vibration_docs"
    dimension: 1536
```

**⚠️ 更换向量数据库配套修改：**
1. 安装对应依赖：
   ```bash
   # Chroma
   pip install chromadb
   
   # FAISS
   pip install faiss-cpu  # 或 faiss-gpu
   
   # Milvus
   pip install pymilvus
   ```
2. 重新构建向量索引：
   ```bash
   python scripts/rebuild_vector_index.py
   ```
3. 测试向量检索功能

### 🏪 关系数据库配置（存储结构化数据）

**我想更换关系数据库：**

**选项1：SQLite（推荐新手，无需安装）**
```yaml
database:
  type: "sqlite"
  config:
    database_path: "./data/cms_vibration.db"  # 数据库文件路径
    timeout: 30
```

**选项2：PostgreSQL（推荐生产环境）**
```yaml
database:
  type: "postgresql"
  config:
    host: "localhost"  # 数据库服务器地址
    port: 5432
    username: "cms_user"  # 必须修改
    password: "cms_password"  # 必须修改
    database: "cms_vibration"  # 数据库名
    pool_size: 10
```

**选项3：MySQL**
```yaml
database:
  type: "mysql"
  config:
    host: "localhost"
    port: 3306
    username: "cms_user"  # 必须修改
    password: "cms_password"  # 必须修改
    database: "cms_vibration"
    charset: "utf8mb4"
```

**⚠️ 更换关系数据库配套修改：**

1. **安装数据库驱动：**
   ```bash
   # PostgreSQL
   pip install psycopg2-binary
   
   # MySQL
   pip install pymysql
   ```

2. **创建数据库和用户：**
   ```sql
   -- PostgreSQL
   CREATE DATABASE cms_vibration;
   CREATE USER cms_user WITH PASSWORD 'cms_password';
   GRANT ALL PRIVILEGES ON DATABASE cms_vibration TO cms_user;
   
   -- MySQL
   CREATE DATABASE cms_vibration CHARACTER SET utf8mb4;
   CREATE USER 'cms_user'@'localhost' IDENTIFIED BY 'cms_password';
   GRANT ALL PRIVILEGES ON cms_vibration.* TO 'cms_user'@'localhost';
   ```

3. **运行数据库迁移：**
   ```bash
   python scripts/init_database.py
   ```

4. **测试数据库连接：**
   ```bash
   python scripts/test_db_connection.py
   ```

### 🔄 数据库迁移步骤

**从SQLite迁移到PostgreSQL：**

1. **备份现有数据：**
   ```bash
   python scripts/backup_database.py --source sqlite --output backup.sql
   ```

2. **修改配置文件：**
   ```yaml
   # 将database.type从"sqlite"改为"postgresql"
   database:
     type: "postgresql"
     config:
       host: "localhost"
       # ... 其他配置
   ```

3. **恢复数据：**
   ```bash
   python scripts/restore_database.py --target postgresql --input backup.sql
   ```

4. **验证迁移：**
   ```bash
   python scripts/verify_migration.py
   ```

### 📊 数据库性能优化

**如果数据库查询很慢：**

1. **调整连接池大小：**
   ```yaml
   database:
     config:
       pool_size: 20  # 增加连接池
       max_overflow: 30
   ```

2. **添加数据库索引：**
   ```bash
   python scripts/create_indexes.py
   ```

3. **启用查询缓存：**
   ```yaml
   database:
     config:
       enable_cache: true
       cache_ttl: 3600  # 缓存1小时
   ```

## 数据库迁移

### SQLite到PostgreSQL

1. **安装PostgreSQL依赖：**
```bash
pip install psycopg2-binary
```

2. **修改数据库配置：**
```yaml
# config.yaml
database:
  type: "postgresql"
  postgresql:
    host: "localhost"
    port: 5432
    database: "cms_vibration"
    username: "cms_user"
    password: "your_password"
    pool_size: 10
    max_overflow: 20
```

3. **数据迁移脚本：**
```python
# migrate_database.py
import sqlite3
import psycopg2
from sqlalchemy import create_engine

def migrate_sqlite_to_postgresql():
    # SQLite连接
    sqlite_conn = sqlite3.connect('data/cms_data.db')
    
    # PostgreSQL连接
    pg_engine = create_engine(
        'postgresql://cms_user:password@localhost:5432/cms_vibration'
    )
    
    # 迁移数据
    tables = ['reports', 'analysis_results', 'user_sessions']
    
    for table in tables:
        df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
        df.to_sql(table, pg_engine, if_exists='replace', index=False)
    
    sqlite_conn.close()
    print("数据库迁移完成")

if __name__ == "__main__":
    migrate_sqlite_to_postgresql()
```

### 向量数据库迁移

#### 从ChromaDB迁移到Pinecone

```python
# migrate_vector_db.py
import chromadb
import pinecone
from tqdm import tqdm

def migrate_chromadb_to_pinecone():
    # 初始化ChromaDB
    chroma_client = chromadb.PersistentClient(path="./data/vector_db")
    collection = chroma_client.get_collection("cms_knowledge")
    
    # 初始化Pinecone
    pinecone.init(
        api_key="your-pinecone-key",
        environment="us-west1-gcp"
    )
    
    # 创建索引
    if "cms-vibration" not in pinecone.list_indexes():
        pinecone.create_index(
            "cms-vibration",
            dimension=384,  # 根据嵌入模型维度调整
            metric="cosine"
        )
    
    index = pinecone.Index("cms-vibration")
    
    # 获取所有数据
    results = collection.get(include=['embeddings', 'metadatas', 'documents'])
    
    # 批量上传到Pinecone
    batch_size = 100
    for i in tqdm(range(0, len(results['ids']), batch_size)):
        batch_ids = results['ids'][i:i+batch_size]
        batch_embeddings = results['embeddings'][i:i+batch_size]
        batch_metadata = results['metadatas'][i:i+batch_size]
        
        vectors = [
            {
                'id': batch_ids[j],
                'values': batch_embeddings[j],
                'metadata': batch_metadata[j]
            }
            for j in range(len(batch_ids))
        ]
        
        index.upsert(vectors=vectors)
    
    print("向量数据库迁移完成")

if __name__ == "__main__":
    migrate_chromadb_to_pinecone()
```

## 知识库迁移

### 知识库结构

```
knowledge_base/
├── documents/          # 原始文档
│   ├── manuals/       # 设备手册
│   ├── standards/     # 行业标准
│   └── cases/         # 案例文档
├── embeddings/        # 向量嵌入
├── metadata/          # 元数据
└── templates/         # 报告模板
```

### 知识库迁移脚本

```python
# migrate_knowledge.py
import os
import shutil
from pathlib import Path

def migrate_knowledge_base(old_path, new_path):
    """迁移知识库"""
    old_kb = Path(old_path)
    new_kb = Path(new_path)
    
    # 创建新目录结构
    new_kb.mkdir(parents=True, exist_ok=True)
    (new_kb / "documents").mkdir(exist_ok=True)
    (new_kb / "embeddings").mkdir(exist_ok=True)
    (new_kb / "metadata").mkdir(exist_ok=True)
    (new_kb / "templates").mkdir(exist_ok=True)
    
    # 复制文档
    if (old_kb / "documents").exists():
        shutil.copytree(
            old_kb / "documents",
            new_kb / "documents",
            dirs_exist_ok=True
        )
    
    # 重新生成嵌入（因为可能使用不同的嵌入模型）
    from knowledge.knowledge_manager import KnowledgeManager
    
    km = KnowledgeManager(str(new_kb))
    km.rebuild_embeddings()
    
    print(f"知识库迁移完成: {old_path} -> {new_path}")

def update_knowledge_config(config_path, new_kb_path):
    """更新配置文件中的知识库路径"""
    import yaml
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    config['knowledge'] = {
        'base_path': new_kb_path,
        'auto_update': True,
        'chunk_size': 1000,
        'chunk_overlap': 200
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"配置文件已更新: {config_path}")

if __name__ == "__main__":
    migrate_knowledge_base(
        "./old_knowledge_base",
        "./knowledge_base"
    )
    update_knowledge_config("config.yaml", "./knowledge_base")
```

## 模板自定义

### 报告模板配置

在 `report_templates/` 目录下创建自定义模板：

```python
# report_templates/custom/my_template.py
from knowledge.template_manager import BaseTemplate

class MyCustomTemplate(BaseTemplate):
    def __init__(self):
        super().__init__()
        self.template_name = "my_custom_template"
        self.description = "我的自定义报告模板"
    
    def generate_structure(self, data):
        return {
            "title": "自定义振动分析报告",
            "sections": [
                {
                    "name": "概述",
                    "content": self._generate_overview(data)
                },
                {
                    "name": "详细分析",
                    "content": self._generate_analysis(data)
                },
                {
                    "name": "建议措施",
                    "content": self._generate_recommendations(data)
                }
            ]
        }
    
    def _generate_overview(self, data):
        # 自定义概述生成逻辑
        pass
    
    def _generate_analysis(self, data):
        # 自定义分析生成逻辑
        pass
    
    def _generate_recommendations(self, data):
        # 自定义建议生成逻辑
        pass
```

### 注册自定义模板

```python
# 在knowledge/template_manager.py中注册
from report_templates.custom.my_template import MyCustomTemplate

class TemplateManager:
    def __init__(self):
        self.templates = {
            "default": DefaultTemplate(),
            "comprehensive": ComprehensiveTemplate(),
            "maintenance": MaintenanceTemplate(),
            "my_custom": MyCustomTemplate(),  # 添加自定义模板
        }
```

## 性能参数调优

### 内存优化配置

```yaml
# config.yaml
performance:
  # 内存管理
  memory:
    max_usage: "8GB"
    gc_threshold: 0.8
    clear_cache_interval: 3600
  
  # 模型优化
  model:
    use_quantization: true
    quantization_bits: 4
    use_flash_attention: true
    gradient_checkpointing: true
  
  # 并发处理
  concurrency:
    max_workers: 4
    batch_size: 32
    queue_size: 100
  
  # 缓存策略
  cache:
    enabled: true
    ttl: 3600
    max_size: "2GB"
    compression: true
```

### GPU配置优化

```python
# utils/gpu_optimizer.py
import torch
import os

def optimize_gpu_settings():
    """优化GPU设置"""
    if torch.cuda.is_available():
        # 设置内存分配策略
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
        
        # 启用cudnn优化
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        
        # 设置内存增长策略
        torch.cuda.empty_cache()
        
        print(f"GPU优化完成，可用显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    else:
        print("未检测到GPU，使用CPU模式")

def set_mixed_precision(enabled=True):
    """设置混合精度训练"""
    if enabled and torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        print("混合精度已启用")
```

## 环境变量配置

### 创建环境配置文件

项目现在支持`.env`文件配置，可以通过环境变量覆盖`config.yaml`中的设置。首先复制示例文件：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
vim .env
```

`.env`文件内容示例：

```bash
# LLM配置
CMS_MODEL_TYPE=deepseek_api
CMS_OPENAI_API_KEY=sk-your-openai-key
CMS_OPENAI_BASE_URL=https://api.openai.com/v1
CMS_DEEPSEEK_API_KEY=sk-your-deepseek-key
CMS_LOCAL_MODEL_PATH=/path/to/local/model
CMS_CUSTOM_API_KEY=your-custom-api-key
CMS_CUSTOM_BASE_URL=https://your-custom-api.com/v1

# 嵌入模型配置
CMS_EMBEDDING_TYPE=huggingface
CMS_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CMS_EMBEDDING_CACHE_DIR=./cache/embeddings

# 数据库配置
CMS_DB_TYPE=sqlite
CMS_DB_PATH=./data/cms_vibration.db
CMS_DB_HOST=localhost
CMS_DB_PASSWORD=your_db_password

# 外部API配置
CMS_EXTERNAL_API_ENABLED=true
CMS_CMS_API_KEY=your_cms_api_key
CMS_CMS_API_URL=http://172.16.253.39/api/model/services

# Streamlit配置
CMS_STREAMLIT_ENABLED=true
CMS_STREAMLIT_PORT=8501
CMS_STREAMLIT_HOST=0.0.0.0

# 系统配置
CMS_LOG_LEVEL=INFO
CMS_DEBUG=false
```

### 环境变量加载

项目已集成环境变量加载功能，配置加载器会自动：

1. 加载`.env`文件中的环境变量
2. 使用环境变量覆盖`config.yaml`中的对应配置
3. 支持类型转换（字符串、布尔值、数字）

```python
# 使用配置加载器（自动加载.env文件）
from config.config_loader import get_config

# 获取配置
config = get_config()
model_config = config.get_model_config()
database_config = config.get_database_config()

# 检查配置
print(f"当前模型类型: {model_config['type']}")
print(f"数据库类型: {database_config['type']}")
print(f"调试模式: {config.is_debug_mode()}")
```

### 环境变量映射

系统支持以下环境变量映射到配置文件：

| 环境变量 | 配置路径 | 说明 |
|---------|---------|------|
| `CMS_MODEL_TYPE` | `model.type` | 模型类型 |
| `CMS_OPENAI_API_KEY` | `model.openai.api_key` | OpenAI API密钥 |
| `CMS_DEEPSEEK_API_KEY` | `model.deepseek_api.api_key` | DeepSeek API密钥 |
| `CMS_DB_TYPE` | `database.type` | 数据库类型 |
| `CMS_DB_PATH` | `database.sqlite.path` | SQLite数据库路径 |
| `CMS_LOG_LEVEL` | `system.logging.level` | 日志级别 |
| `CMS_DEBUG` | `development.debug` | 调试模式 |

## 常见迁移场景

### 🚀 测试环境到生产环境

**我要将系统部署到生产环境：**

1. **配置文件调整**
   ```yaml
   # 生产环境配置要点
   logging:
     level: "INFO"  # 从DEBUG改为INFO
   
   database:
     type: "postgresql"  # 从sqlite改为postgresql
     config:
       host: "prod-db-server"
       # ... 生产数据库配置
   
   model:
     openai:
       api_key: "${OPENAI_API_KEY}"  # 使用环境变量
   ```

2. **性能优化**
   ```yaml
   performance:
     max_workers: 8  # 增加工作进程
     max_concurrent_requests: 200
   
   cache:
     type: "redis"  # 启用Redis缓存
     config:
       host: "redis-cluster"
   ```

3. **安全加固**
   ```bash
   # 配置HTTPS
   sudo certbot --nginx -d yourdomain.com
   
   # 配置防火墙
   sudo ufw enable
   sudo ufw allow 443/tcp
   sudo ufw allow 80/tcp
   ```

### 🎮 GPU服务器切换

**我要在GPU服务器上运行：**

1. **检查GPU环境**
   ```bash
   # 检查GPU状态
   nvidia-smi
   
   # 检查CUDA版本
   nvcc --version
   
   # 测试PyTorch GPU支持
   python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}, Device count: {torch.cuda.device_count()}')"
   ```

2. **安装GPU版本依赖**
   ```bash
   # 安装GPU版PyTorch（根据CUDA版本选择）
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   
   # 安装GPU版FAISS
   pip install faiss-gpu
   
   # 安装其他GPU加速库
   pip install cupy-cuda11x  # 可选
   ```

3. **修改配置启用GPU**
   ```yaml
   model:
     device: "cuda"  # 启用GPU
     gpu_memory_fraction: 0.8  # 使用80%显存
     
   embedding:
     device: "cuda"
     batch_size: 32  # GPU可以处理更大批次
   
   vector_db:
     config:
       use_gpu: true  # 如果支持GPU加速
   ```

4. **GPU性能监控**
   ```bash
   # 实时监控GPU使用
   watch -n 1 nvidia-smi
   
   # 查看GPU内存使用
   python -c "import torch; print(f'GPU Memory: {torch.cuda.memory_allocated()/1024**3:.2f}GB / {torch.cuda.memory_reserved()/1024**3:.2f}GB')"
   ```

### 🏢 多租户部署

**我要为多个客户部署独立实例：**

1. **配置隔离策略**
   ```bash
   # 为每个租户创建独立目录
   mkdir -p /opt/cms_rag/tenant_a
   mkdir -p /opt/cms_rag/tenant_b
   
   # 复制配置模板
   cp config/config.yaml /opt/cms_rag/tenant_a/config.yaml
   cp config/config.yaml /opt/cms_rag/tenant_b/config.yaml
   ```

2. **数据库隔离**
   ```yaml
   # tenant_a/config.yaml
   database:
     config:
       database: "cms_vibration_tenant_a"
   
   vector_db:
     config:
       collection_name: "docs_tenant_a"
   
   # tenant_b/config.yaml
   database:
     config:
       database: "cms_vibration_tenant_b"
   
   vector_db:
     config:
       collection_name: "docs_tenant_b"
   ```

3. **端口和服务隔离**
   ```bash
   # 租户A - 端口8000
   cd /opt/cms_rag/tenant_a
   python start_api_server.py --port 8000 --config config.yaml
   
   # 租户B - 端口8001
   cd /opt/cms_rag/tenant_b
   python start_api_server.py --port 8001 --config config.yaml
   ```

4. **资源限制配置**
   ```yaml
   # 每个租户的资源限制
   performance:
     max_workers: 2  # 限制工作进程数
     max_concurrent_requests: 50  # 限制并发请求
     max_memory_usage: "1GB"  # 限制内存使用
   
   security:
     rate_limit:
       requests_per_minute: 30  # 限制请求频率
   ```

## 🆘 常见问题解答（FAQ）

### Q1: 启动时提示"模块未找到"错误

**A:** 检查依赖安装和Python路径
```bash
# 重新安装依赖
pip install -r requirements.txt

# 检查Python路径
echo $PYTHONPATH
export PYTHONPATH=/root/autodl-tmp/cms_vibration_rag:$PYTHONPATH

# 或使用相对导入
cd /root/autodl-tmp/cms_vibration_rag
python -m streamlit run streamlit_app.py
```

### Q2: API调用超时或连接失败

**A:** 检查网络和API配置
```bash
# 测试网络连通性
curl -I https://api.openai.com

# 检查API密钥
echo $OPENAI_API_KEY

# 测试API调用
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     "https://api.openai.com/v1/models"
```

### Q3: 向量数据库检索结果不准确

**A:** 重建向量索引和调整参数
```bash
# 清理旧索引
rm -rf data/chroma_db/*

# 重新构建索引
python scripts/rebuild_vector_index.py

# 调整检索参数
# 在config.yaml中修改：
vector_db:
  config:
    similarity_threshold: 0.7  # 降低阈值
    max_results: 10  # 增加结果数量
```

### Q4: 内存使用过高导致系统卡顿

**A:** 优化内存配置
```yaml
# 在config.yaml中调整
performance:
  max_memory_usage: "1GB"  # 限制内存使用
  gc_threshold: 0.6  # 降低垃圾回收阈值

model:
  max_tokens: 2048  # 减少token数量
  batch_size: 1  # 减少批处理大小
```

### Q5: 数据库连接失败

**A:** 检查数据库配置和连接
```bash
# 测试SQLite
ls -la data/cms_vibration.db

# 测试PostgreSQL
psql -h localhost -U cms_user -d cms_vibration -c "SELECT 1;"

# 检查数据库服务状态
sudo systemctl status postgresql
```

### Q6: 文件上传失败

**A:** 检查文件权限和大小限制
```bash
# 检查上传目录权限
ls -la data/uploads/
chmod 755 data/uploads/

# 检查文件大小限制
# 在config.yaml中调整：
security:
  upload:
    max_file_size: "50MB"  # 增加文件大小限制
```

## 🔧 故障排除步骤

### 1. 系统无法启动

**排查步骤：**
```bash
# 1. 检查Python环境
python --version
which python

# 2. 检查依赖
pip list | grep -E "streamlit|fastapi|openai"

# 3. 检查配置文件
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# 4. 查看详细错误
python streamlit_app.py --debug
```

### 2. API响应缓慢

**排查步骤：**
```bash
# 1. 检查系统资源
htop
df -h

# 2. 检查网络延迟
ping api.openai.com

# 3. 查看日志
tail -f logs/cms_vibration.log

# 4. 测试API性能
time curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### 3. 数据检索不准确

**排查步骤：**
```bash
# 1. 检查向量数据库
ls -la data/chroma_db/

# 2. 测试embedding
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2'); print(model.encode(['test']))"

# 3. 重建索引
python scripts/rebuild_vector_index.py --verbose

# 4. 调整检索参数
# 修改config.yaml中的similarity_threshold
```

## 故障排除

### 配置验证脚本

```python
# validate_config.py
import yaml
import os
from pathlib import Path

def validate_config(config_path="config.yaml"):
    """验证配置文件"""
    errors = []
    warnings = []
    
    # 检查配置文件是否存在
    if not Path(config_path).exists():
        errors.append(f"配置文件不存在: {config_path}")
        return errors, warnings
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"配置文件格式错误: {e}")
        return errors, warnings
    
    # 验证必需的配置项
    required_sections = ['api', 'llm', 'embedding', 'vector_db']
    for section in required_sections:
        if section not in config:
            errors.append(f"缺少必需的配置节: {section}")
    
    # 验证API配置
    if 'api' in config:
        api_config = config['api']
        if not api_config.get('cms_base_url'):
            errors.append("缺少API基础URL配置")
        if not api_config.get('auth_token'):
            warnings.append("未配置API认证令牌")
    
    # 验证LLM配置
    if 'llm' in config:
        llm_config = config['llm']
        provider = llm_config.get('provider')
        if not provider:
            errors.append("未指定LLM提供商")
        elif provider not in ['openai', 'deepseek', 'qwen', 'local']:
            errors.append(f"不支持的LLM提供商: {provider}")
        
        # 验证提供商特定配置
        if provider in llm_config:
            provider_config = llm_config[provider]
            if provider != 'local' and not provider_config.get('api_key'):
                errors.append(f"缺少{provider}的API密钥")
    
    # 验证路径
    paths_to_check = [
        ('knowledge_base', config.get('knowledge', {}).get('base_path')),
        ('cache_dir', config.get('processing', {}).get('cache_dir')),
        ('output_dir', config.get('output', {}).get('reports', {}).get('output_dir'))
    ]
    
    for name, path in paths_to_check:
        if path and not Path(path).exists():
            warnings.append(f"{name}路径不存在: {path}")
    
    return errors, warnings

def fix_common_issues(config_path="config.yaml"):
    """修复常见配置问题"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 创建缺失的目录
    dirs_to_create = [
        config.get('processing', {}).get('cache_dir', './cache'),
        config.get('output', {}).get('reports', {}).get('output_dir', './output'),
        './data/vector_db',
        './knowledge_base'
    ]
    
    for dir_path in dirs_to_create:
        if dir_path:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"创建目录: {dir_path}")
    
    print("常见问题修复完成")

if __name__ == "__main__":
    errors, warnings = validate_config()
    
    if errors:
        print("配置错误:")
        for error in errors:
            print(f"  ❌ {error}")
    
    if warnings:
        print("配置警告:")
        for warning in warnings:
            print(f"  ⚠️ {warning}")
    
    if not errors and not warnings:
        print("✅ 配置验证通过")
    
    if errors or warnings:
        fix_common_issues()
```

### 常见问题解决

#### 1. 模型加载失败

**问题：** `OSError: Can't load tokenizer`

**解决方案：**
```bash
# 清理模型缓存
rm -rf ~/.cache/huggingface/

# 重新下载模型
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('your-model-name')"
```

#### 2. API连接超时

**问题：** `requests.exceptions.Timeout`

**解决方案：**
```yaml
# 增加超时时间
api:
  timeout: 60
  retry_times: 5
  retry_delay: 2
```

#### 3. 内存不足

**问题：** `CUDA out of memory`

**解决方案：**
```yaml
# 启用模型量化
llm:
  local:
    load_in_4bit: true
    max_memory: "6GB"

# 减少批处理大小
processing:
  batch_size: 16
```

#### 4. 向量数据库连接失败

**问题：** `chromadb.errors.InvalidDimensionException`

**解决方案：**
```python
# 重建向量数据库
python -c "
from knowledge.knowledge_manager import KnowledgeManager
km = KnowledgeManager()
km.rebuild_embeddings()
"
```

### 迁移检查清单

- [ ] 备份原始配置和数据
- [ ] 验证新环境的系统要求
- [ ] 更新配置文件中的API端点
- [ ] 配置新的认证信息
- [ ] 迁移知识库和向量数据库
- [ ] 测试模型加载和推理
- [ ] 验证API连接和数据获取
- [ ] 运行端到端测试
- [ ] 检查日志输出
- [ ] 性能基准测试
- [ ] 监控系统资源使用
- [ ] 文档更新

---

**版本**: 1.0.0  
**最后更新**: 2025-01-14  
**维护者**: CMS开发团队

如需更多帮助，请联系技术支持团队。