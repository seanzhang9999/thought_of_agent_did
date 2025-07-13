# 技术上下文

## 技术栈概览

### 核心技术选型

#### 1. 编程语言与框架
```
主要语言：Python 3.8+
Web框架：FastAPI (异步优先)
AI集成：LangChain + 自研DIKIWI框架
异步库：asyncio, aiohttp, httpx
```

**选择理由**：
- **Python**：AI生态丰富，开发效率高，社区活跃
- **FastAPI**：现代异步框架，自动API文档，类型安全
- **异步优先**：适合I/O密集型的智能体通信场景

#### 2. 数据存储
```
结构化数据：PostgreSQL
图数据：Neo4j (知识图谱)
缓存：Redis
文件存储：本地文件系统 + 对象存储
```

**存储策略**：
- **PostgreSQL**：配置、用户数据、交互历史
- **Neo4j**：DIKIWI知识图谱、Agent关系网络
- **Redis**：路由缓存、会话状态、实时数据
- **文件系统**：Agent配置、日志文件

#### 3. 前端技术
```
框架：React 18 + TypeScript
状态管理：Zustand
UI组件：Ant Design / Tailwind CSS
构建工具：Vite
```

**设计考虑**：
- **TypeScript**：类型安全，减少运行时错误
- **React 18**：并发特性，适合实时交互
- **Vite**：快速开发构建，热重载体验好

#### 4. 部署与运维
```
容器化：Docker + Docker Compose
编排：Kubernetes (生产环境)
监控：Prometheus + Grafana
日志：ELK Stack (Elasticsearch + Logstash + Kibana)
```

## 开发环境配置

### 1. 本地开发环境

#### Python环境
```bash
# Python版本管理
pyenv install 3.11.0
pyenv local 3.11.0

# 虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 依赖管理
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 核心依赖
```python
# requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
httpx>=0.25.0
aiofiles>=23.0.0
langchain>=0.1.0
openai>=1.0.0
anthropic>=0.7.0
neo4j>=5.0.0
redis>=5.0.0
```

#### 开发工具依赖
```python
# requirements-dev.txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.5.0
pre-commit>=3.0.0
```

### 2. 配置管理

#### 环境配置文件
```yaml
# config/development.yaml
anp_sdk:
  host: "localhost"
  port: 9527
  debug_mode: true
  log_level: "DEBUG"

database:
  postgresql:
    host: "localhost"
    port: 5432
    database: "anp_dev"
    username: "anp_user"
    password: "dev_password"
  
  neo4j:
    uri: "bolt://localhost:7687"
    username: "neo4j"
    password: "dev_password"
  
  redis:
    host: "localhost"
    port: 6379
    db: 0

mcp_servers:
  crawler:
    command: ["python", "-m", "anp_crawler_mcp"]
    env:
      PYTHONPATH: "."
```

#### Docker开发环境
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: anp_dev
      POSTGRES_USER: anp_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  neo4j:
    image: neo4j:5.0
    environment:
      NEO4J_AUTH: neo4j/dev_password
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  neo4j_data:
  redis_data:
```

### 3. 代码质量工具

#### Pre-commit配置
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

#### 测试配置
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    --verbose
    --tb=short
    --cov=anp_open_sdk
    --cov-report=html
    --cov-report=term-missing
```

## 技术约束与限制

### 1. 性能约束

#### 响应时间要求
```
API响应时间：< 200ms (P95)
DIKIWI处理：< 3秒 (单次)
知识检索：< 100ms
Agent通信：< 500ms
```

#### 并发处理能力
```
单实例并发：1000+ 连接
Agent数量：支持10000+ Agent
MCP工具调用：100+ QPS
数据库连接池：50-100 连接
```

#### 内存使用限制
```
单Agent内存：< 100MB
知识图谱缓存：< 1GB
总内存使用：< 4GB (单实例)
```

### 2. 安全约束

#### 认证与授权
```python
# DID认证要求
- 支持去中心化身份验证
- 双向认证机制
- JWT Token有效期管理
- 权限细粒度控制
```

#### 数据安全
```
- 敏感数据加密存储
- 传输层TLS加密
- API访问频率限制
- 审计日志完整记录
```

#### 隐私保护
```
- 用户数据本地化存储
- 可选的数据匿名化
- GDPR合规性支持
- 数据删除权实现
```

### 3. 兼容性约束

#### Python版本兼容
```
最低版本：Python 3.8
推荐版本：Python 3.11+
异步特性：完全支持asyncio
类型提示：支持最新typing特性
```

#### 操作系统支持
```
开发环境：macOS, Linux, Windows
生产环境：Linux (Ubuntu 20.04+, CentOS 8+)
容器环境：Docker 20.10+, Kubernetes 1.20+
```

#### 浏览器兼容
```
Chrome：90+
Firefox：88+
Safari：14+
Edge：90+
```

### 4. 扩展性约束

#### 水平扩展
```python
# 无状态设计要求
- Agent状态外部化存储
- 会话状态Redis管理
- 配置热重载支持
- 负载均衡友好
```

#### 垂直扩展
```
CPU密集型：DIKIWI处理、AI推理
内存密集型：知识图谱、缓存
I/O密集型：网络通信、文件操作
```

## 依赖管理策略

### 1. 核心依赖版本锁定

#### 关键依赖版本策略
```python
# 严格版本锁定
fastapi==0.104.1        # API框架
pydantic==2.4.2         # 数据验证
uvicorn==0.24.0         # ASGI服务器

# 兼容版本范围
httpx>=0.25.0,<0.26.0   # HTTP客户端
langchain>=0.1.0,<0.2.0 # AI框架
openai>=1.0.0,<2.0.0    # OpenAI SDK
```

#### 依赖更新策略
```bash
# 定期依赖检查
pip-audit                # 安全漏洞检查
pip list --outdated      # 过期包检查
dependabot              # 自动依赖更新PR
```

### 2. 可选依赖管理

#### 功能模块化依赖
```python
# setup.py extras_require
extras_require={
    "neo4j": ["neo4j>=5.0.0"],
    "redis": ["redis>=5.0.0"],
    "monitoring": ["prometheus-client>=0.17.0"],
    "dev": ["pytest>=7.0.0", "black>=23.0.0"],
    "all": ["neo4j>=5.0.0", "redis>=5.0.0", "prometheus-client>=0.17.0"]
}
```

## 开发工作流

### 1. Git工作流

#### 分支策略
```
main: 生产就绪代码
develop: 开发集成分支
feature/*: 功能开发分支
hotfix/*: 紧急修复分支
release/*: 发布准备分支
```

#### 提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建工具、依赖更新
```

### 2. CI/CD流程

#### GitHub Actions配置
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest
      - name: Run linting
        run: |
          black --check .
          isort --check-only .
          flake8 .
          mypy .
```

### 3. 代码审查标准

#### 审查检查清单
```
□ 代码符合项目编码规范
□ 单元测试覆盖率 > 80%
□ 文档字符串完整
□ 类型提示正确
□ 异常处理适当
□ 性能影响评估
□ 安全性考虑
□ 向后兼容性
```

## 监控与调试

### 1. 日志系统

#### 日志配置
```python
# logging配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "level": "INFO"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/anp.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "loggers": {
        "anp_open_sdk": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}
```

### 2. 性能监控

#### 指标收集
```python
# Prometheus指标
from prometheus_client import Counter, Histogram, Gauge

# 请求计数
REQUEST_COUNT = Counter('anp_requests_total', 'Total requests', ['method', 'endpoint'])

# 响应时间
REQUEST_DURATION = Histogram('anp_request_duration_seconds', 'Request duration')

# 活跃Agent数量
ACTIVE_AGENTS = Gauge('anp_active_agents', 'Number of active agents')

# DIKIWI处理时间
DIKIWI_PROCESSING_TIME = Histogram('anp_dikiwi_processing_seconds', 'DIKIWI processing time')
```

### 3. 调试工具

#### 开发调试
```python
# 调试配置
DEBUG_TOOLS = {
    "pdb": "内置调试器",
    "ipdb": "增强调试器", 
    "pytest-xdist": "并行测试",
    "pytest-cov": "测试覆盖率",
    "memory-profiler": "内存分析",
    "py-spy": "性能分析"
}
```

这个技术上下文为项目提供了完整的技术指导，确保开发团队能够在统一的技术标准下高效协作。
