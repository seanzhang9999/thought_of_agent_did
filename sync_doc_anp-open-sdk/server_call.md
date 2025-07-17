## 当前架构分析

从 `anp_server/router/router_agent.py` 可以看到，当前已经有了类似的远程调用机制：

1. __已有的远程调用模式__：

   - 当前代码已经支持转发到 `framework_server` (端口9528)
   - 使用 `aiohttp.ClientSession` 进行HTTP调用
   - 有完整的错误处理和回退机制

2. __现有的配置支持__：

   - `use_framework_server`: 是否启用框架服务器
   - `framework_server_url`: 框架服务器地址
   - `fallback_to_local`: 失败时是否回退到本地处理

## 实现方案

要支持调用另一台服务器的 `route_request`，只需要在现有基础上扩展：

### 方案一：扩展现有配置（推荐）

在配置中添加远程服务器列表：

```yaml
anp_sdk:
  use_framework_server: true
  framework_server_url: "http://localhost:9528"
  
  # 新增：远程服务器配置
  remote_servers:
    - name: "server_a"
      url: "http://server-a.example.com:9527"
      priority: 1
    - name: "server_b" 
      url: "http://server-b.example.com:9527"
      priority: 2
  
  # 路由策略
  routing_strategy: "local_first"  # local_first, remote_first, load_balance
  fallback_to_local: true
```

### 方案二：修改 route_request 方法

在 `AgentRouter.route_request` 方法中添加远程调用逻辑：

```python
async def route_request(self, req_did: str, resp_did: str, request_data: Dict, request: Request) -> Any:
    # 1. 尝试本地处理
    local_agent = self.find_agent_with_domain_priority(resp_did, domain, port)
    
    if local_agent:
        # 本地处理
        return await local_agent.handle_request(req_did, request_data, request)
    
    # 2. 尝试远程服务器
    config = get_global_config()
    remote_servers = getattr(config.anp_sdk, "remote_servers", [])
    
    for server in sorted(remote_servers, key=lambda x: x.get('priority', 999)):
        try:
            result = await self._call_remote_route_request(
                server['url'], req_did, resp_did, request_data, request
            )
            if result:
                return result
        except Exception as e:
            self.logger.warning(f"远程服务器 {server['name']} 调用失败: {e}")
            continue
    
    # 3. 都失败了
    raise ValueError(f"未找到智能体: {resp_did}")
```

### 方案三：实现远程调用方法

```python
async def _call_remote_route_request(self, server_url: str, req_did: str, resp_did: str, 
                                   request_data: Dict, request: Request) -> Any:
    """调用远程服务器的 route_request"""
    try:
        async with aiohttp.ClientSession() as session:
            # 构造远程调用URL - 直接调用 /agent/api/ 端点
            target_url = f"{server_url}/agent/api/{resp_did}/{request_data.get('path', '').lstrip('/')}"
            
            # 准备请求数据
            remote_request_data = {
                **request_data,
                "req_did": req_did,
                "remote_call": True  # 标记为远程调用
            }
            
            async with session.post(
                target_url,
                json=remote_request_data,
                params=dict(request.query_params),
                timeout=30  # 设置超时
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.debug(f"✅ 远程调用成功: {server_url} -> {resp_did}")
                    return result
                else:
                    error_text = await response.text()
                    self.logger.error(f"❌ 远程服务器返回错误: {response.status} - {error_text}")
                    return None
                    
    except Exception as e:
        self.logger.error(f"❌ 远程调用失败: {server_url} - {e}")
        return None
```

## 复杂度评估

__实现复杂度：低到中等__

### 简单的部分：

1. __HTTP调用机制__：已有 aiohttp 基础设施
2. __配置系统__：已有完整的配置管理
3. __错误处理__：已有回退机制模板
4. __路由逻辑__：核心路由逻辑已经存在

### 需要考虑的部分：

1. __服务发现__：如何知道哪些服务器有哪些Agent
2. __负载均衡__：多个远程服务器的选择策略
3. __故障转移__：远程调用失败的处理
4. __认证授权__：跨服务器调用的安全性
5. __性能优化__：连接池、超时设置等

## 推荐实施步骤

1. __第一阶段__：基础远程调用

   - 扩展配置文件支持远程服务器列表
   - 实现基础的远程 route_request 调用
   - 添加简单的错误处理和日志

2. __第二阶段__：增强功能

   - 添加服务健康检查
   - 实现负载均衡策略
   - 优化连接管理

3. __第三阶段__：生产就绪

   - 添加认证机制
   - 实现监控和指标
   - 性能优化和压力测试
