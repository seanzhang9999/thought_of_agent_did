重新定义EOC三件套
Caller = ANPTool的升级版（可靠的多协议调用器）
设计理念：提供统一、可靠的调用接口，支持多种协议，但不涉及LLM和智能决策

class UnifiedCaller:
    """统一调用器 - ANPTool的升级版"""
    
    def __init__(self, agent):
        self.agent = agent
        self.anp_tool = ANPTool(agent.anp_user.user_data)  # 复用现有ANPTool
        self.local_registry = LOCAL_METHODS_REGISTRY
    
    # 1. ANP协议调用 (现有能力)
    async def call_anp(self, did: str, api_path: str, **params):
        """ANP协议调用"""
        url = f"http://host:port/agent/api/{did}{api_path}"
        return await self.anp_tool.execute_with_two_way_auth(
            url=url, method="POST", body=params,
            caller_agent=self.agent.anp_user_id,
            target_agent=did,
            use_two_way_auth=True
        )
    
    # 2. 本地方法调用 (新增能力)
    async def call_local(self, method_name: str, **params):
        """本地方法调用"""
        method_key = f"{self.agent.anp_user_id}::{method_name}"
        if method_key in self.local_registry:
            method_info = self.local_registry[method_key]
            # 直接调用本地方法
            return await self._invoke_local_method(method_info, params)
        raise MethodNotFoundError(f"Local method not found: {method_name}")
    
    # 3. MCP协议调用 (新增能力)
    async def call_mcp(self, server: str, method: str, **params):
        """MCP协议调用"""
        # 实现MCP协议调用逻辑
        pass
    
    # 4. HTTP API调用 (新增能力)
    async def call_http(self, url: str, method: str = "POST", **params):
        """标准HTTP API调用"""
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=params) as response:
                return await response.json()
    
    # 5. 统一调用接口
    async def call(self, service_uri: str, **params):
        """统一调用接口 - 根据URI前缀路由到不同协议"""
        if service_uri.startswith("anp:"):
            did, path = self._parse_anp_uri(service_uri[4:])
            return await self.call_anp(did, path, **params)
        elif service_uri.startswith("local:"):
            method_name = service_uri[6:]
            return await self.call_local(method_name, **params)
        elif service_uri.startswith("mcp:"):
            server, method = self._parse_mcp_uri(service_uri[4:])
            return await self.call_mcp(server, method, **params)
        elif service_uri.startswith("http:") or service_uri.startswith("https:"):
            return await self.call_http(service_uri, **params)
        else:
            # 默认尝试本地调用
            return await self.call_local(service_uri, **params)

Orchestrator = ANPToolCrawler的升级版（LLM驱动的智能编排器）
设计理念：基于现有Crawler的LLM驱动能力，提供智能任务编排和执行

class ServiceOrchestrator:
    """服务编排器 - ANPToolCrawler的升级版"""
    
    def __init__(self, agent):
        self.agent = agent
        self.caller = UnifiedCaller(agent)  # 使用可靠的Caller进行实际调用
        self.llm_client = self._create_llm_client()
    
    async def orchestrate(self, task_description: str, context: dict = None):
        """智能任务编排 - 基于现有crawler逻辑"""
        
        # 1. 任务分析 (LLM驱动)
        task_plan = await self._analyze_task_with_llm(task_description, context)
        
        # 2. 服务发现 (基于现有crawler的发现能力)
        available_services = await self._discover_services(task_plan.required_services)
        
        # 3. 执行计划生成 (LLM驱动)
        execution_steps = await self._generate_execution_plan(task_plan, available_services)
        
        # 4. 步骤执行 (使用Caller进行可靠调用)
        results = []
        for step in execution_steps:
            try:
                result = await self.caller.call(step.service_uri, **step.params)
                results.append({"step": step.name, "result": result, "status": "success"})
            except Exception as e:
                results.append({"step": step.name, "error": str(e), "status": "failed"})
                # 根据错误类型决定是否继续
                if step.critical:
                    break
        
        return {
            "task": task_description,
            "plan": task_plan,
            "execution_results": results,
            "status": "completed" if all(r["status"] == "success" for r in results) else "partial"
        }
    
    async def _discover_services(self, required_services):
        """服务发现 - 复用现有crawler的发现逻辑"""
        discovered_services = {}
        
        for service_type in required_services:
            # 1. 本地服务发现
            local_services = self._find_local_services(service_type)
            if local_services:
                discovered_services[service_type] = local_services
                continue
            
            # 2. 网络服务发现 - 使用现有crawler逻辑
            discovery_task = f"寻找{service_type}类型的服务"
            crawler_result = await self._run_service_discovery_crawler(discovery_task)
            discovered_services[service_type] = crawler_result
        
        return discovered_services
    
    async def _run_service_discovery_crawler(self, discovery_task):
        """运行服务发现爬虫 - 基于现有ANPToolCrawler"""
        # 复用现有crawler的核心逻辑
        crawler = ANPToolCrawler()
        result = await crawler.run_crawler_demo(
            task_input=discovery_task,
            initial_url="http://localhost:9527/agents/list",
            task_type="function_query",
            use_two_way_auth=True,
            req_did=self.agent.anp_user_id
        )
        return result

Exposer = 现有装饰器系统的统一封装
设计理念：统一现有的各种装饰器，提供一致的服务暴露接口

class ServiceExposer:
    """服务暴露器 - 统一现有装饰器系统"""
    
    def __init__(self, agent):
        self.agent = agent
    
    def expose(self, source: str, **kwargs):
        """统一暴露装饰器"""
        def decorator(func):
            if source == "api":
                # 使用现有的agent.api装饰器
                path = kwargs.get("path", f"/{func.__name__}")
                return self.agent._api(path)(func)
            
            elif source == "local":
                # 使用现有的local_method装饰器
                from anp_server_framework.local_service.local_methods_decorators import local_method
                description = kwargs.get("description", "")
                tags = kwargs.get("tags", [])
                return local_method(description, tags)(func)
            
            elif source == "message":
                # 使用现有的message_handler装饰器
                msg_type = kwargs.get("msg_type", "*")
                return self.agent._message_handler(msg_type)(func)
            
            else:
                raise ValueError(f"Unsupported source: {source}")
        
        return decorator

完整的EOC使用示例
# 1. 创建EOC组件
agent = create_agent("did:wba:localhost:9527:wba:user:abc123", "智能助手")
exposer = ServiceExposer(agent)
caller = UnifiedCaller(agent)
orchestrator = ServiceOrchestrator(agent)

# 2. 使用Exposer暴露服务
@exposer.expose(source="local", description="获取天气信息")
async def get_weather(location: str):
    return {"location": location, "temperature": "22°C", "condition": "晴天"}

@exposer.expose(source="api", path="/send_email")
async def send_email_api(request_data, request):
    to = request_data.get("to")
    content = request_data.get("content")
    # 发送邮件逻辑
    return {"status": "sent", "to": to}

# 3. 使用Caller进行可靠调用
async def test_caller():
    # 本地调用
    weather = await caller.call("local:get_weather", location="北京")
    
    # ANP调用
    result = await caller.call("anp:did:wba:other:agent/calculate", a=1, b=2)
    
    # HTTP调用
    api_result = await caller.call("https://api.example.com/service", param="value")

# 4. 使用Orchestrator进行智能编排
async def test_orchestrator():
    result = await orchestrator.orchestrate(
        "查询北京天气，如果是雨天就发送提醒邮件给用户",
        context={"user_email": "user@example.com"}
    )
    return result

实施路线图
第一阶段：Caller实现 (1周)
扩展ANPTool为UnifiedCaller
添加本地方法调用能力
添加HTTP/MCP协议支持
提供统一的call()接口
第二阶段：Exposer实现 (1周)
封装现有装饰器系统
提供统一的expose()装饰器
保持向下兼容
第三阶段：Orchestrator实现 (2周)
基于ANPToolCrawler实现智能编排
集成UnifiedCaller进行可靠调用
提供任务分析和执行计划能力
这样的设计：

Caller：可靠的多协议调用器，无LLM依赖
Orchestrator：智能的LLM驱动编排器，基于现有Crawler
Exposer：统一的服务暴露接口，基于现有装饰器




## 回调机制的双层架构

### 第一层：Caller的临时回调端点分配

__Caller负责__：为每次调用动态创建临时回调URL

```python
class UnifiedCaller:
    async def call_with_callback(self, service_uri: str, callback_handler, **params):
        """Caller创建临时回调端点"""
        
        # 1. 生成唯一回调ID
        callback_id = str(uuid.uuid4())
        callback_path = f"/callback/{callback_id}"
        
        # 2. 在当前agent上注册临时回调路由
        callback_url = f"http://localhost:9527/agent/api/{self.agent.anp_user_id}{callback_path}"
        
        # 3. 将回调处理器注册到Exposer
        self.exposer.register_dynamic_callback(callback_path, callback_handler)
        
        # 4. 发起调用，传入回调URL
        return await self.call(service_uri, callback_url=callback_url, **params)
```

### 第二层：Exposer的动态回调接口实现

__Exposer负责__：提供实际的回调接口，并支持动态指定响应服务

```python
class ServiceExposer:
    def __init__(self, agent):
        self.agent = agent
        self.dynamic_callbacks = {}  # 存储动态回调处理器
        self.callback_services = {}  # 存储回调服务配置
        
        # 注册通用回调接口
        self._register_universal_callback_endpoint()
    
    def _register_universal_callback_endpoint(self):
        """注册通用回调接口"""
        @self.agent._api("/callback/<callback_id>")
        async def universal_callback_handler(request_data, request):
            """通用回调处理器 - 支持动态服务调用"""
            
            # 1. 提取回调ID
            callback_id = request.path_params.get("callback_id")
            callback_path = f"/callback/{callback_id}"
            
            # 2. 获取回调配置
            callback_config = self.dynamic_callbacks.get(callback_path)
            if not callback_config:
                return {"error": "Callback not found", "callback_id": callback_id}
            
            # 3. 动态调用指定的响应服务
            return await self._execute_dynamic_callback(callback_config, request_data)
    
    async def _execute_dynamic_callback(self, callback_config, request_data):
        """执行动态回调 - 核心功能"""
        
        callback_handler = callback_config["handler"]
        service_config = callback_config.get("service_config", {})
        
        # 支持多种动态响应服务
        if service_config.get("type") == "llm":
            # 调用LLM服务处理回调
            return await self._handle_callback_with_llm(callback_handler, request_data, service_config)
        
        elif service_config.get("type") == "anp_service":
            # 调用其他ANP服务处理回调
            return await self._handle_callback_with_anp_service(callback_handler, request_data, service_config)
        
        elif service_config.get("type") == "orchestrator":
            # 调用编排器处理回调
            return await self._handle_callback_with_orchestrator(callback_handler, request_data, service_config)
        
        else:
            # 默认直接调用处理器
            return await callback_handler(request_data)
    
    def register_dynamic_callback(self, callback_path: str, callback_handler, 
                                service_type: str = "direct", **service_config):
        """注册动态回调处理器"""
        self.dynamic_callbacks[callback_path] = {
            "handler": callback_handler,
            "service_config": {
                "type": service_type,
                **service_config
            },
            "created_at": datetime.now()
        }
    
    async def _handle_callback_with_llm(self, callback_handler, request_data, service_config):
        """使用LLM处理回调"""
        
        # 1. 构建LLM提示
        llm_prompt = service_config.get("prompt_template", "").format(
            callback_data=request_data,
            context=service_config.get("context", {})
        )
        
        # 2. 调用LLM
        llm_client = self._get_llm_client()
        llm_response = await llm_client.chat.completions.create(
            model=service_config.get("model", "gpt-4"),
            messages=[
                {"role": "system", "content": service_config.get("system_prompt", "")},
                {"role": "user", "content": llm_prompt}
            ]
        )
        
        # 3. 处理LLM响应
        llm_result = llm_response.choices[0].message.content
        
        # 4. 调用原始回调处理器，传入LLM结果
        enhanced_data = {
            **request_data,
            "llm_analysis": llm_result,
            "llm_config": service_config
        }
        
        return await callback_handler(enhanced_data)
```

## 动态LLM回调的完整示例

### 使用场景：智能数据分析回调

```python
# 1. 定义回调处理器
async def intelligent_analysis_callback(callback_data):
    """智能分析回调处理器"""
    
    # 获取LLM分析结果
    llm_analysis = callback_data.get("llm_analysis", "")
    original_result = callback_data.get("result", {})
    
    print(f"原始分析结果: {original_result}")
    print(f"LLM智能解读: {llm_analysis}")
    
    # 根据LLM分析决定下一步行动
    if "异常" in llm_analysis or "警告" in llm_analysis:
        # 触发警报流程
        await orchestrator.orchestrate("发送数据异常警报给管理员")
    
    return {
        "status": "callback_processed",
        "original_result": original_result,
        "intelligent_analysis": llm_analysis,
        "action_taken": "alert_sent" if "异常" in llm_analysis else "normal_processing"
    }

# 2. 使用Caller发起带LLM回调的调用
result = await caller.call_with_callback(
    service_uri="anp:data_service/analyze_large_dataset",
    callback_handler=intelligent_analysis_callback,
    # 指定使用LLM处理回调
    callback_service_type="llm",
    llm_config={
        "model": "gpt-4",
        "system_prompt": "你是一个数据分析专家，请分析数据处理结果并提供专业见解",
        "prompt_template": """
        数据分析任务已完成，请分析以下结果：
        
        回调数据：{callback_data}
        
        请提供：
        1. 结果质量评估
        2. 是否发现异常数据
        3. 建议的后续行动
        4. 风险评估
        """,
        "context": {"dataset_type": "sales", "analysis_type": "trend"}
    },
    # 原始任务参数
    dataset="sales_2024.csv",
    analysis_type="comprehensive"
)
```

### Caller的增强实现

```python
class UnifiedCaller:
    async def call_with_callback(self, service_uri: str, callback_handler, 
                               callback_service_type: str = "direct", **params):
        """增强的回调调用 - 支持动态服务指定"""
        
        # 1. 提取回调服务配置
        callback_service_config = {}
        llm_config = params.pop("llm_config", {})
        anp_config = params.pop("anp_config", {})
        orchestrator_config = params.pop("orchestrator_config", {})
        
        if callback_service_type == "llm":
            callback_service_config = llm_config
        elif callback_service_type == "anp_service":
            callback_service_config = anp_config
        elif callback_service_type == "orchestrator":
            callback_service_config = orchestrator_config
        
        # 2. 创建临时回调端点
        callback_id = str(uuid.uuid4())
        callback_path = f"/callback/{callback_id}"
        
        # 3. 在Exposer中注册动态回调
        self.exposer.register_dynamic_callback(
            callback_path=callback_path,
            callback_handler=callback_handler,
            service_type=callback_service_type,
            **callback_service_config
        )
        
        # 4. 构建回调URL
        callback_url = f"http://localhost:9527/agent/api/{self.agent.anp_user_id}{callback_path}"
        
        # 5. 发起调用
        return await self.call(service_uri, callback_url=callback_url, **params)
```

## 支持的动态回调服务类型

### 1. LLM回调服务

```python
# 使用LLM智能处理回调
await caller.call_with_callback(
    "anp:service/task",
    callback_handler=my_handler,
    callback_service_type="llm",
    llm_config={
        "model": "gpt-4",
        "system_prompt": "你是专业的任务分析师",
        "prompt_template": "分析任务结果: {callback_data}"
    }
)
```

### 2. ANP服务回调

```python
# 使用其他ANP服务处理回调
await caller.call_with_callback(
    "anp:service/task",
    callback_handler=my_handler,
    callback_service_type="anp_service",
    anp_config={
        "target_service": "anp:analysis_service/process_callback",
        "auth_required": True
    }
)
```

### 3. Orchestrator回调

```python
# 使用编排器处理复杂回调逻辑
await caller.call_with_callback(
    "anp:service/task",
    callback_handler=my_handler,
    callback_service_type="orchestrator",
    orchestrator_config={
        "workflow_template": "callback_processing_workflow",
        "context": {"priority": "high"}
    }
)
```

## 技术优势

1. __动态灵活__：回调处理逻辑可以根据需要动态指定
2. __智能增强__：LLM可以对回调数据进行智能分析和处理
3. __服务解耦__：回调处理与原始服务完全解耦
4. __可扩展性__：支持多种回调服务类型，易于扩展
5. __上下文保持__：回调处理器可以访问完整的调用上下文

这样的设计真正实现了"Exposer提供接口，Caller分配端点，动态指定响应服务"的灵活架构，特别是LLM回调服务的支持，为智能化的异步协作提供了强大的基础。



现有Crawler就是Workflow系统
从anp_tool.py中可以看到的workflow模式
# 现有的ANPToolCrawler已经支持多种workflow
async def run_crawler_demo(self, task_input: str, initial_url: str,
                         task_type: str = "code_generation"):
    
    # 不同的task_type就是不同的workflow
    if task_type == "weather_query":
        prompt_template = self._create_weather_search_prompt_template()
        agent_name = "天气查询爬虫"
        max_documents = 10
    elif task_type == "root_query":
        prompt_template = self._create_root_search_prompt_template()
        agent_name = "多智能体搜索爬虫"
        max_documents = 120
    elif task_type == "function_query":
        prompt_template = self._create_function_search_prompt_template()
        agent_name = "功能搜索爬虫"
        max_documents = 10
    else:
        prompt_template = self._create_code_search_prompt_template()
        agent_name = "代码生成爬虫"
        max_documents = 10

这些task_type本质上就是预定义的workflow模板！

Orchestrator = Crawler + Workflow管理
基于现有Crawler的Orchestrator设计
class ServiceOrchestrator:
    """服务编排器 - ANPToolCrawler的升级版"""
    
    def __init__(self, agent):
        self.agent = agent
        self.crawler = ANPToolCrawler()  # 复用现有crawler
        self.caller = UnifiedCaller(agent)
        self.workflow_templates = self._load_workflow_templates()
    
    def _load_workflow_templates(self):
        """加载工作流模板 - 基于现有crawler的task_type"""
        return {
            # 现有的crawler workflow
            "weather_search": {
                "task_type": "weather_query",
                "prompt_template": self.crawler._create_weather_search_prompt_template(),
                "max_documents": 10,
                "agent_name": "天气查询工作流"
            },
            "multi_agent_search": {
                "task_type": "root_query", 
                "prompt_template": self.crawler._create_root_search_prompt_template(),
                "max_documents": 120,
                "agent_name": "多智能体搜索工作流"
            },
            "function_discovery": {
                "task_type": "function_query",
                "prompt_template": self.crawler._create_function_search_prompt_template(),
                "max_documents": 10,
                "agent_name": "功能发现工作流"
            },
            
            # 新增的workflow模板
            "data_analysis": {
                "task_type": "data_analysis",
                "prompt_template": self._create_data_analysis_workflow_template(),
                "max_documents": 15,
                "agent_name": "数据分析工作流"
            },
            "email_automation": {
                "task_type": "email_automation", 
                "prompt_template": self._create_email_workflow_template(),
                "max_documents": 8,
                "agent_name": "邮件自动化工作流"
            }
        }
    
    async def orchestrate(self, task_description: str, workflow_type: str = "auto", **context):
        """执行工作流编排"""
        
        # 1. 自动选择或指定workflow
        if workflow_type == "auto":
            workflow_type = await self._auto_select_workflow(task_description)
        
        # 2. 获取workflow模板
        workflow_template = self.workflow_templates.get(workflow_type)
        if not workflow_template:
            # 回退到通用搜索workflow
            workflow_template = self.workflow_templates["multi_agent_search"]
        
        # 3. 使用现有crawler执行workflow
        result = await self.crawler.run_crawler_demo(
            task_input=task_description,
            initial_url=context.get("initial_url", "http://localhost:9527/agents/list"),
            task_type=workflow_template["task_type"],
            use_two_way_auth=context.get("use_two_way_auth", True),
            req_did=self.agent.anp_user_id
        )
        
        # 4. 后处理和回调支持
        return await self._post_process_workflow_result(result, workflow_type, context)

具体的Workflow示例
天气查询Workflow
# 现有的weather_query就是一个完整的workflow
async def weather_workflow_example():
    orchestrator = ServiceOrchestrator(agent)
    
    result = await orchestrator.orchestrate(
        task_description="查询北京明天的天气，如果下雨就发送提醒",
        workflow_type="weather_search",  # 使用现有的weather_query workflow
        initial_url="http://localhost:9527/agents/list",
        callback_url="http://localhost:9527/agent/api/my_agent/weather_callback"
    )
    
    # 这个workflow会自动：
    # 1. 发现天气服务
    # 2. 理解API使用方法
    # 3. 查询天气数据
    # 4. 分析天气条件
    # 5. 如果需要，发送提醒

通用查询Workflow
# 现有的root_query就是最强大的通用workflow
async def general_query_workflow_example():
    orchestrator = ServiceOrchestrator(agent)
    
    result = await orchestrator.orchestrate(
        task_description="帮我分析销售数据，生成报告，并发送给团队",
        workflow_type="multi_agent_search",  # 使用现有的root_query workflow
        initial_url="http://localhost:9527/agents/list"
    )
    
    # 这个workflow会自动：
    # 1. 搜索所有可用的智能体
    # 2. 分析每个智能体的能力
    # 3. 找到数据分析相关的服务
    # 4. 找到报告生成服务
    # 5. 找到邮件发送服务
    # 6. 按顺序执行整个流程

Orchestrator的增强功能
1. Workflow模板管理
# 可以动态添加新的workflow模板
orchestrator.add_workflow_template("custom_workflow", {
    "task_type": "custom_task",
    "prompt_template": custom_prompt,
    "max_documents": 20,
    "agent_name": "自定义工作流",
    "pre_processors": [data_validator],
    "post_processors": [result_formatter, callback_handler]
})

2. 智能Workflow选择
async def _auto_select_workflow(self, task_description: str):
    """基于任务描述自动选择最适合的workflow"""
    
    # 使用LLM分析任务类型
    analysis_prompt = f"""
    分析以下任务，选择最适合的工作流类型：
    任务：{task_description}
    
    可选工作流：
    - weather_search: 天气相关查询
    - multi_agent_search: 复杂的多步骤任务
    - function_discovery: 寻找特定功能
    - data_analysis: 数据分析任务
    - email_automation: 邮件相关任务
    
    返回最适合的工作流类型：
    """
    
    # 调用LLM进行分析
    workflow_type = await self._call_llm_for_analysis(analysis_prompt)
    return workflow_type

3. Workflow组合和链式执行
async def orchestrate_chain(self, workflow_chain: List[Dict]):
    """执行工作流链"""
    
    results = []
    context = {}
    
    for workflow_step in workflow_chain:
        # 每个步骤可以使用前一步的结果
        workflow_step["context"].update(context)
        
        result = await self.orchestrate(
            task_description=workflow_step["task"],
            workflow_type=workflow_step["type"],
            **workflow_step["context"]
        )
        
        results.append(result)
        context.update(result.get("context", {}))
    
    return {"chain_results": results, "final_context": context}

# 使用示例
workflow_chain = [
    {
        "task": "查询北京天气",
        "type": "weather_search",
        "context": {}
    },
    {
        "task": "根据天气情况生成外出建议",
        "type": "function_discovery", 
        "context": {"weather_data": "{{previous_result}}"}
    },
    {
        "task": "将建议发送给用户",
        "type": "email_automation",
        "context": {"recipient": "user@example.com"}
    }
]

result = await orchestrator.orchestrate_chain(workflow_chain)

总结
您的理解完全正确：

现有Crawler已经是Workflow系统：不同的task_type就是不同的预定义workflow
Orchestrator是Crawler的升级：增加workflow管理、模板系统、链式执行等功能
搜索天气、通用查询都是workflow：它们都有完整的"发现→分析→执行→结果处理"流程
这样的设计既充分利用了现有代码的强大能力，又提供了更灵活的workflow管理和编排功能。Orchestrator本质上就是一个增强版的ANPToolCrawler，支持更多的workflow模板和更智能的任务编排。