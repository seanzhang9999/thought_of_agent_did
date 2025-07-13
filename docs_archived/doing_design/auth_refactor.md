# ANP SDK 认证系统重构行动方案

## 一、概述

### 1.1 重构目标

- __清晰化__：分离认证策略、降级逻辑、存储管理
- __结构化__：采用分层架构，职责单一
- __可扩展__：支持新认证方式的灵活添加
- __可观测__：完善的日志和监控机制

### 1.2 核心改进

- ✅ 统一的认证上下文和结果模型
- ✅ 策略模式实现多种认证方式
- ✅ 智能降级机制（双向→单向→Token）
- ✅ Token 生命周期管理
- ✅ 认证事件监控和告警

## 二、架构设计

### 2.1 整体架构图

### 2.2 认证降级流程

### 2.3 认证级别定义

| 级别 | 名称           | 安全性 | 使用场景                 |
|------|----------------|--------|--------------------------|
| 30   | DID双向认证    | 最高   | 敏感操作、首次建立信任   |
| 20   | DID单向认证    | 中等   | 一般API调用、降级场景    |
| 10   | Bearer Token   | 较低   | 频繁调用、性能优先       |
| 0    | 无认证         | 无     | 公开接口、健康检查       |

## 三、实施步骤

### 第一阶段：基础框架搭建

#### 步骤 1.1：创建核心数据模型

```bash
# 创建目录结构
anp_open_sdk/adapter_auth/
├── core/
│   ├── __init__.py
│   ├── context.py      # 认证上下文
│   ├── result.py       # 认证结果
│   └── levels.py       # 认证级别
├── strategies/
│   ├── __init__.py
│   ├── base.py         # 策略基类
│   ├── bearer.py       # Token策略
│   ├── did_wba.py      # DID策略
│   └── fallback.py     # 降级策略
├── storage/
│   ├── __init__.py
│   ├── token_store.py  # Token存储
│   └── cache.py        # 缓存管理
├── middleware/
│   ├── __init__.py
│   └── auth_middleware.py
├── client/
│   ├── __init__.py
│   └── enhanced_client.py
└── monitoring/
    ├── __init__.py
    └── fallback_monitor.py
```

#### 步骤 1.2：实现核心模型

__文件：`auth/core/context.py`__

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class AuthContext:
    """统一的认证上下文"""
    caller_did: Optional[str] = None
    target_did: Optional[str] = None
    request_url: str = ""
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    auth_type: Optional[str] = None
    use_two_way_auth: bool = True
    domain: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

__文件：`auth/core/result.py`__

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any

class AuthStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    EXPIRED = "expired"

@dataclass
class AuthResult:
    """认证结果"""
    status: AuthStatus
    authenticated: bool
    caller_did: Optional[str] = None
    target_did: Optional[str] = None
    token: Optional[str] = None
    auth_header: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

__文件：`auth/core/levels.py`__

```python
from enum import IntEnum

class AuthLevel(IntEnum):
    """认证级别，数值越高安全性越高"""
    NONE = 0
    BEARER_TOKEN = 10
    DID_ONE_WAY = 20
    DID_TWO_WAY = 30
    
    def can_downgrade_to(self, target_level: 'AuthLevel') -> bool:
        """判断是否可以降级到目标级别"""
        return target_level < self
```

### 第二阶段：实现认证策略

#### 步骤 2.1：策略基类

__文件：`auth/strategies/base.py`__

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional
from fastapi import Request
from ..core.context import AuthContext
from ..core.result import AuthResult

class AuthStrategy(ABC):
    """认证策略基类"""
    
    @abstractmethod
    async def authenticate(self, request: Request, context: AuthContext) -> AuthResult:
        """执行认证"""
        pass
    
    @abstractmethod
    async def generate_response(self, auth_result: AuthResult, context: AuthContext) -> Dict:
        """生成认证响应"""
        pass
    
    @abstractmethod
    def can_handle(self, request: Request) -> bool:
        """判断是否可以处理该请求"""
        pass

class ClientAuthStrategy(ABC):
    """客户端认证策略基类"""
    
    @abstractmethod
    async def authenticate(self, context: AuthContext) -> 'AuthResponse':
        """执行客户端认证"""
        pass
    
    @abstractmethod
    def can_handle(self, context: AuthContext) -> bool:
        """判断是否可以处理该上下文"""
        pass
```

#### 步骤 2.2：Bearer Token 策略

__文件：`auth/strategies/bearer.py`__

```python
import logging
from typing import Dict
from fastapi import Request
from datetime import datetime, timezone
from .base import AuthStrategy
from ..core.context import AuthContext
from ..core.result import AuthResult, AuthStatus
from ..storage.token_store import TokenStore
from ...anp_sdk_agent import LocalAgent

logger = logging.getLogger(__name__)

class BearerTokenStrategy(AuthStrategy):
    """Bearer Token 认证策略"""
    
    def __init__(self, token_store: TokenStore):
        self.token_store = token_store
    
    def can_handle(self, request: Request) -> bool:
        auth_header = request.headers.get("Authorization", "")
        return auth_header.startswith("Bearer ")
    
    async def authenticate(self, request: Request, context: AuthContext) -> AuthResult:
        auth_header = request.headers.get("Authorization", "")
        token = auth_header[7:]  # Remove "Bearer "
        
        try:
            # 尝试从本地存储验证
            resp_agent = LocalAgent.from_did(context.target_did)
            token_info = resp_agent.contact_manager.get_token_to_remote(context.caller_did)
            
            if token_info:
                # 检查token状态
                if token_info.get("is_revoked"):
                    return AuthResult(
                        status=AuthStatus.FAILED,
                        authenticated=False,
                        error="Token has been revoked"
                    )
                
                # 检查过期时间
                expires_at = datetime.fromisoformat(token_info["expires_at"])
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                
                if datetime.now(timezone.utc) > expires_at:
                    return AuthResult(
                        status=AuthStatus.EXPIRED,
                        authenticated=False,
                        error="Token has expired"
                    )
                
                # 验证token匹配
                if token != token_info["token"]:
                    return AuthResult(
                        status=AuthStatus.FAILED,
                        authenticated=False,
                        error="Invalid token"
                    )
                
                return AuthResult(
                    status=AuthStatus.SUCCESS,
                    authenticated=True,
                    caller_did=context.caller_did,
                    target_did=context.target_did,
                    token=token,
                    metadata={"auth_method": "bearer_cached"}
                )
            
            # 使用公钥验证
            validation_result = await self.token_store.validate_token(
                token, context.caller_did, context.target_did
            )
            
            if validation_result.is_valid:
                return AuthResult(
                    status=AuthStatus.SUCCESS,
                    authenticated=True,
                    caller_did=context.caller_did,
                    target_did=context.target_did,
                    token=token,
                    metadata={"auth_method": "bearer_verified"}
                )
            else:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    authenticated=False,
                    error=validation_result.error
                )
                
        except Exception as e:
            logger.error(f"Bearer token authentication error: {e}")
            return AuthResult(
                status=AuthStatus.FAILED,
                authenticated=False,
                error=str(e)
            )
    
    async def generate_response(self, auth_result: AuthResult, context: AuthContext) -> Dict:
        # Bearer Token 认证通常不需要额外的响应头
        return {}
```

#### 步骤 2.3：DID WBA 策略

__文件：`auth/strategies/did_wba.py`__

```python
import json
import logging
from typing import Dict
from fastapi import Request
from .base import AuthStrategy
from ..core.context import AuthContext
from ..core.result import AuthResult, AuthStatus
from ..core.levels import AuthLevel
from ..storage.token_store import TokenStore
from ...auth.did_auth_wba import WBADIDAuthenticator

logger = logging.getLogger(__name__)

class DIDWBAStrategy(AuthStrategy):
    """支持降级的 DID WBA 认证策略"""
    
    def __init__(self, authenticator: WBADIDAuthenticator, token_store: TokenStore):
        self.authenticator = authenticator
        self.token_store = token_store
    
    def can_handle(self, request: Request) -> bool:
        auth_header = request.headers.get("Authorization", "")
        return "did:wba:" in auth_header
    
    async def authenticate(self, request: Request, context: AuthContext) -> AuthResult:
        auth_level = context.metadata.get('auth_level', AuthLevel.DID_TWO_WAY)
        
        if auth_level == AuthLevel.DID_TWO_WAY:
            return await self._try_two_way_auth(request, context)
        elif auth_level == AuthLevel.DID_ONE_WAY:
            return await self._try_one_way_auth(request, context)
        else:
            return AuthResult(
                status=AuthStatus.FAILED,
                authenticated=False,
                error="Invalid adapter_auth level for DID WBA"
            )
    
    async def _try_two_way_auth(self, request: Request, context: AuthContext) -> AuthResult:
        """尝试双向认证"""
        context.use_two_way_auth = True
        auth_header = request.headers.get("Authorization", "")
        
        try:
            success, msg = await self.authenticator.verify_response(auth_header, context)
            
            if success:
                token = await self.token_store.create_token(
                    context.caller_did,
                    context.target_did,
                    expires_in=3600
                )
                
                return AuthResult(
                    status=AuthStatus.SUCCESS,
                    authenticated=True,
                    caller_did=context.caller_did,
                    target_did=context.target_did,
                    token=token,
                    metadata={
                        'auth_method': 'did_wba_two_way',
                        'auth_level': AuthLevel.DID_TWO_WAY
                    }
                )
            else:
                # 双向认证失败，返回PARTIAL状态以触发降级
                return AuthResult(
                    status=AuthStatus.PARTIAL,
                    authenticated=False,
                    error=f"Two-way adapter_auth failed: {msg}",
                    metadata={'should_downgrade': True}
                )
                
        except Exception as e:
            logger.error(f"Two-way adapter_auth error: {e}")
            return AuthResult(
                status=AuthStatus.PARTIAL,
                authenticated=False,
                error=str(e),
                metadata={'should_downgrade': True}
            )
    
    async def _try_one_way_auth(self, request: Request
```

继续

**Checkpoint

Compare

Restore

API Request$0.0000

### 步骤 2.3：DID WBA 策略（续）

```python
    async def _try_one_way_auth(self, request: Request, context: AuthContext) -> AuthResult:
        """尝试单向认证"""
        context.use_two_way_auth = False
        auth_header = request.headers.get("Authorization", "")
        
        try:
            success, msg = await self.authenticator.verify_response(auth_header, context)
            
            if success:
                token = await self.token_store.create_token(
                    context.caller_did,
                    context.target_did,
                    expires_in=3600
                )
                
                return AuthResult(
                    status=AuthStatus.SUCCESS,
                    authenticated=True,
                    caller_did=context.caller_did,
                    target_did=context.target_did,
                    token=token,
                    metadata={
                        'auth_method': 'did_wba_one_way',
                        'auth_level': AuthLevel.DID_ONE_WAY,
                        'downgraded': True
                    }
                )
            else:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    authenticated=False,
                    error=f"One-way adapter_auth failed: {msg}"
                )
                
        except Exception as e:
            logger.error(f"One-way adapter_auth error: {e}")
            return AuthResult(
                status=AuthStatus.FAILED,
                authenticated=False,
                error=str(e)
            )
    
    async def generate_response(self, auth_result: AuthResult, context: AuthContext) -> Dict:
        """生成认证响应"""
        if not auth_result.authenticated:
            return {}
        
        from ...anp_sdk_agent import LocalAgent
        from ...auth.token_nonce_auth import create_access_token
        
        try:
            resp_agent = LocalAgent.from_did(context.target_did)
            
            # 存储token到联系人管理器
            if auth_result.token:
                resp_agent.contact_manager.store_token_to_remote(
                    context.caller_did,
                    auth_result.token,
                    3600
                )
            
            # 生成响应认证头（如果是双向认证）
            resp_auth_header = None
            if context.use_two_way_auth:
                from ...agent_connect_hotpatch.authentication.did_wba_auth_header import DIDWbaAuthHeader
                
                auth_client = DIDWbaAuthHeader(
                    did_document_path=str(resp_agent.did_document_path),
                    private_key_path=str(resp_agent.private_key_path)
                )
                
                resp_auth_header = auth_client.get_auth_header_two_way(
                    "http://virtual.WBAback:9999",
                    context.caller_did
                )
            
            return {
                "Authorization": json.dumps([{
                    "access_token": auth_result.token,
                    "token_type": "bearer",
                    "req_did": context.caller_did,
                    "resp_did": context.target_did,
                    "resp_did_auth_header": resp_auth_header
                }])
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {}
```

### 第三阶段：实现降级策略

#### 步骤 3.1：降级策略管理器

__文件：`auth/strategies/fallback.py`__

```python
import logging
from typing import Dict, List, Optional
from ..core.context import AuthContext
from ..core.result import AuthResult, AuthStatus
from ..core.levels import AuthLevel
from .base import AuthStrategy

logger = logging.getLogger(__name__)

class FallbackStrategy:
    """认证降级策略"""
    
    def __init__(self, fallback_chain: Optional[List[AuthLevel]] = None):
        self.fallback_chain = fallback_chain or [
            AuthLevel.DID_TWO_WAY,
            AuthLevel.DID_ONE_WAY,
            AuthLevel.BEARER_TOKEN
        ]
        self.max_retries = 3
    
    async def execute_with_fallback(
        self,
        request: 'Request',
        context: AuthContext,
        strategies: Dict[AuthLevel, AuthStrategy]
    ) -> AuthResult:
        """执行带降级的认证"""
        
        last_error = None
        attempted_levels = []
        
        for level in self.fallback_chain:
            if level not in strategies:
                continue
            
            strategy = strategies[level]
            
            # 检查策略是否能处理该请求
            if not strategy.can_handle(request):
                continue
            
            attempted_levels.append(level)
            
            try:
                # 更新上下文中的认证级别
                context.metadata['auth_level'] = level
                context.metadata['attempted_levels'] = attempted_levels
                
                logger.info(f"尝试认证级别: {level.name}")
                result = await strategy.authenticate(request, context)
                
                if result.status == AuthStatus.SUCCESS:
                    # 认证成功
                    result.metadata['final_auth_level'] = level
                    result.metadata['fallback_occurred'] = len(attempted_levels) > 1
                    
                    if len(attempted_levels) > 1:
                        logger.warning(
                            f"认证降级成功: {attempted_levels} -> {level.name}"
                        )
                    
                    return result
                
                elif result.status == AuthStatus.PARTIAL:
                    # 需要降级
                    last_error = result.error
                    logger.info(f"认证级别 {level.name} 失败，尝试降级: {result.error}")
                    continue
                
                else:
                    # 彻底失败，不再尝试
                    logger.error(f"认证级别 {level.name} 彻底失败: {result.error}")
                    return result
                    
            except Exception as e:
                logger.error(f"认证策略 {level.name} 执行异常: {e}")
                last_error = str(e)
                continue
        
        # 所有策略都失败
        return AuthResult(
            status=AuthStatus.FAILED,
            authenticated=False,
            error=last_error or "All authentication strategies failed",
            metadata={
                'attempted_levels': [level.name for level in attempted_levels]
            }
        )
```

### 第四阶段：实现认证中间件

#### 步骤 4.1：认证中间件

__文件：`auth/middleware/auth_middleware.py`__

```python
import fnmatch
import logging
from typing import List, Dict, Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from ..core.context import AuthContext
from ..core.levels import AuthLevel
from ..strategies.base import AuthStrategy
from ..strategies.fallback import FallbackStrategy
from ..strategies.bearer import BearerTokenStrategy
from ..strategies.did_wba import DIDWBAStrategy
from ..storage.token_store import TokenStore
from ..monitoring.fallback_monitor import FallbackMonitor

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """统一的认证中间件"""
    
    EXEMPT_PATHS = [
        "/docs", "/redoc", "/openapi.json", "/favicon.ico",
        "/", "/health", "/metrics",
        "/wba/hostuser/*", "/wba/user/*",
        "/publisher/agents", "/agent/group/*"
    ]
    
    def __init__(
        self,
        token_store: TokenStore,
        authenticator: 'WBADIDAuthenticator',
        monitor: Optional[FallbackMonitor] = None
    ):
        self.token_store = token_store
        self.authenticator = authenticator
        self.monitor = monitor or FallbackMonitor()
        
        # 初始化策略
        self.strategies = {
            AuthLevel.BEARER_TOKEN: BearerTokenStrategy(token_store),
            AuthLevel.DID_ONE_WAY: DIDWBAStrategy(authenticator, token_store),
            AuthLevel.DID_TWO_WAY: DIDWBAStrategy(authenticator, token_store)
        }
        
        self.fallback_strategy = FallbackStrategy()
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """中间件主逻辑"""
        
        # 检查豁免路径
        if self._is_exempt(request.url.path):
            return await call_next(request)
        
        # 构建认证上下文
        context = self._build_context(request)
        
        # 特殊处理 /wba/adapter_auth 端点
        if request.url.path == "/wba/adapter_auth":
            return await self._handle_auth_endpoint(request, context)
        
        try:
            # 执行降级认证
            result = await self.fallback_strategy.execute_with_fallback(
                request, context, self.strategies
            )
            
            if result.authenticated:
                # 认证成功
                request.state.auth_result = result
                request.state.headers = dict(request.headers)
                
                # 记录降级事件
                if result.metadata.get('fallback_occurred'):
                    await self._record_fallback(result, context)
                
                # 继续处理请求
                response = await call_next(request)
                
                # 添加认证响应头
                for level, strategy in self.strategies.items():
                    if result.metadata.get('auth_method', '').startswith(level.name.lower()):
                        auth_response = await strategy.generate_response(result, context)
                        for key, value in auth_response.items():
                            response.headers[key] = value
                        break
                
                return response
            else:
                # 认证失败
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": result.error or "Authentication failed",
                        "attempted_methods": result.metadata.get('attempted_levels', [])
                    }
                )
                
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal authentication error"}
            )
    
    def _is_exempt(self, path: str) -> bool:
        """检查路径是否豁免认证"""
        for pattern in self.EXEMPT_PATHS:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False
    
    def _build_context(self, request: Request) -> AuthContext:
        """构建认证上下文"""
        headers = dict(request.headers)
        
        # 从不同来源获取 DID
        req_did = (
            headers.get("req_did") or
            request.query_params.get("req_did") or
            "demo_caller"
        )
        
        resp_did = (
            headers.get("resp_did") or
            request.query_params.get("resp_did") or
            self._extract_did_from_path(request.url.path)
        )
        
        return AuthContext(
            caller_did=req_did,
            target_did=resp_did,
            request_url=str(request.url),
            method=request.method,
            headers=headers,
            domain=request.url.hostname
        )
    
    def _extract_did_from_path(self, path: str) -> Optional[str]:
        """从路径中提取 DID"""
        # 实现路径解析逻辑
        import re
        patterns = [
            r"/agent/api/([^/]+)",
            r"/agent/message/([^/]+)",
            r"/wba/user/([^/]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, path)
            if match:
                return match.group(1)
        
        return None
    
    async def _handle_auth_endpoint(self, request: Request, context: AuthContext) -> Response:
        """处理 /wba/adapter_auth 认证端点"""
        # 这是一个特殊端点，用于获取认证令牌
        result = await self.fallback_strategy.execute_with_fallback(
            request, context, self.strategies
        )
        
        if result.authenticated:
            # 生成认证响应
            response_data = {
                "access_token": result.token,
                "token_type": "bearer",
                "req_did": result.caller_did,
                "resp_did": result.target_did,
                "auth_level": result.metadata.get('final_auth_level', 'unknown')
            }
            
            # 如果有响应认证头，添加到响应中
            for level, strategy in self.strategies.items():
                if result.metadata.get('auth_method', '').startswith(level.name.lower()):
                    auth_response = await strategy.generate_response(result, context)
                    if auth_response:
                        response_data.update(auth_response)
                    break
            
            return JSONResponse(content=response_data)
        else:
            return JSONResponse(
                status_code=401,
                content={"error": result.error or "Authentication failed"}
            )
    
    async def _record_fallback(self, result: AuthResult, context: AuthContext):
        """记录降级事件"""
        if self.monitor and result.metadata.get('fallback_occurred'):
            attempted = result.metadata.get('attempted_levels', [])
            final = result.metadata.get('final_auth_level')
            
            if len(attempted) > 1 and final:
                await self.monitor.record_fallback(
                    from_level=attempted[0],
                    to_level=final,
                    did=context.caller_did
                )
```

### 第五阶段：实现客户端

#### 步骤 5.1：增强的认证客户端

__文件：`auth/client/enhanced_client.py`__

```python
import logging
from typing import Optional, Dict, Tuple, Any
from dataclasses import dataclass
import aiohttp
from ..core.context import AuthContext
from ..core.levels import AuthLevel
from ..strategies.fallback import FallbackStrategy
from ..storage.cache import TokenCache
from ...auth.schemas import DIDCredentials
from ...anp_sdk_agent import LocalAgent

logger = logging.getLogger(__name__)

@dataclass
class AuthResponse:
    """认证响应"""
    success: bool
    status_code: int = 200
    token: Optional[str] = None
    auth_header: Optional[str] = None
    response_data: Optional[Any] = None
    error: Optional[str] = None
    auth_level: Optional[AuthLevel] = None
    metadata: Dict[str, Any] = None

class EnhancedAuthClient:
    """增强的认证客户端"""
    
    def __init__(self):
        self.token_cache = TokenCache()
        self.fallback_strategy = FallbackStrategy()
    
    async def authenticate(
        self,
        caller_did: str,
        target_did: str,
        request_url: str,
        method: str = "GET",
        body: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        prefer_cached_token: bool = True
    ) -> Tuple[int, str, str, bool]:
        """
        执行认证请求
        
        返回: (
```

继续

**Checkpoint

Compare

Restore

API Request$0.0000

### 步骤 5.1：增强的认证客户端（续）

```python
        """
        执行认证请求
        
        返回: (status_code, response_data, message, success)
        """
        context = AuthContext(
            caller_did=caller_did,
            target_did=target_did,
            request_url=request_url,
            method=method,
            body=body,
            headers=headers or {}
        )
        
        # 1. 尝试使用缓存的 token
        if prefer_cached_token:
            cached_response = await self._try_cached_token(context)
            if cached_response.success:
                return (
                    cached_response.status_code,
                    cached_response.response_data,
                    "使用缓存 Token 认证成功",
                    True
                )
            elif cached_response.status_code in [401, 403]:
                # Token 失效，清除缓存
                logger.info(f"缓存 Token 失效，清除并尝试 DID 认证")
                await self.token_cache.invalidate(caller_did, target_did)
        
        # 2. 执行 DID 认证（带降级）
        auth_response = await self._authenticate_with_fallback(context)
        
        # 3. 处理认证结果
        if auth_response.success:
            # 缓存新 token
            if auth_response.token:
                await self.token_cache.store(
                    caller_did,
                    target_did,
                    auth_response.token,
                    3600  # 默认1小时
                )
            
            message = self._build_success_message(auth_response)
            return (
                auth_response.status_code,
                auth_response.response_data,
                message,
                True
            )
        else:
            return (
                auth_response.status_code,
                auth_response.response_data or "",
                auth_response.error or "认证失败",
                False
            )
    
    async def _try_cached_token(self, context: AuthContext) -> AuthResponse:
        """尝试使用缓存的 token"""
        token = await self.token_cache.get_valid_token(
            context.caller_did,
            context.target_did
        )
        
        if not token:
            return AuthResponse(success=False, error="No cached token")
        
        # 使用 token 发送请求
        headers = context.headers.copy()
        headers.update({
            "Authorization": f"Bearer {token}",
            "req_did": context.caller_did,
            "resp_did": context.target_did
        })
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=context.method,
                    url=context.request_url,
                    headers=headers,
                    json=context.body
                ) as response:
                    status = response.status
                    
                    if status == 200:
                        data = await response.json()
                        return AuthResponse(
                            success=True,
                            status_code=status,
                            response_data=data,
                            token=token,
                            auth_level=AuthLevel.BEARER_TOKEN
                        )
                    else:
                        return AuthResponse(
                            success=False,
                            status_code=status,
                            error=f"Token adapter_auth failed with status {status}"
                        )
                        
        except Exception as e:
            logger.error(f"Token request error: {e}")
            return AuthResponse(
                success=False,
                error=str(e)
            )
    
    async def _authenticate_with_fallback(self, context: AuthContext) -> AuthResponse:
        """执行带降级的 DID 认证"""
        from ...auth.did_auth_wba import WBADIDAuthenticator, WBAAuth
        from ...anp_sdk_user_data import LocalUserDataManager
        
        # 获取调用方凭证
        user_data_manager = LocalUserDataManager()
        user_data = user_data_manager.get_user_data(context.caller_did)
        if not user_data:
            return AuthResponse(
                success=False,
                status_code=401,
                error=f"Caller DID {context.caller_did} not found"
            )
        
        credentials = DIDCredentials.from_paths(
            did_document_path=user_data.did_doc_path,
            private_key_path=str(user_data.did_private_key_file_path)
        )
        
        # 创建认证器
        from ...auth.did_auth_wba import (
            WBADIDResolver, WBADIDSigner, WBAAuthHeaderBuilder
        )
        
        authenticator = WBADIDAuthenticator(
            resolver=WBADIDResolver(),
            signer=WBADIDSigner(),
            header_builder=WBAAuthHeaderBuilder(),
            base_auth=WBAAuth()
        )
        
        # 尝试双向认证
        context.use_two_way_auth = True
        try:
            status, auth_header, response_data = await authenticator.authenticate_request(
                context, credentials
            )
            
            if status in [401, 403]:
                # 降级到单向认证
                logger.info("双向认证失败，降级到单向认证")
                context.use_two_way_auth = False
                status, auth_header, response_data = await authenticator.authenticate_request(
                    context, credentials
                )
            
            # 处理响应
            if status not in [401, 403]:
                # 提取 token
                token = self._extract_token_from_response(auth_header)
                
                # 验证响应方认证头（如果是双向认证）
                if context.use_two_way_auth and auth_header:
                    verified = await self._verify_response_header(auth_header)
                    if not verified:
                        return AuthResponse(
                            success=False,
                            status_code=401,
                            error="Response DID verification failed"
                        )
                
                # 存储 token
                if token:
                    caller_agent = LocalAgent.from_did(context.caller_did)
                    caller_agent.contact_manager.store_token_from_remote(
                        context.target_did, token
                    )
                
                return AuthResponse(
                    success=True,
                    status_code=status,
                    response_data=response_data,
                    token=token,
                    auth_level=(
                        AuthLevel.DID_TWO_WAY if context.use_two_way_auth
                        else AuthLevel.DID_ONE_WAY
                    ),
                    metadata={
                        'downgraded': not context.use_two_way_auth
                    }
                )
            else:
                return AuthResponse(
                    success=False,
                    status_code=status,
                    error="DID authentication failed"
                )
                
        except Exception as e:
            logger.error(f"DID authentication error: {e}")
            return AuthResponse(
                success=False,
                status_code=500,
                error=str(e)
            )
    
    def _extract_token_from_response(self, auth_header: Dict) -> Optional[str]:
        """从响应头中提取 token"""
        if not auth_header:
            return None
        
        try:
            import json
            auth_data = auth_header.get("Authorization")
            if isinstance(auth_data, str):
                auth_data = json.loads(auth_data)
            
            if isinstance(auth_data, list) and len(auth_data) > 0:
                return auth_data[0].get("access_token")
            elif isinstance(auth_data, dict):
                return auth_data.get("access_token")
            
        except Exception as e:
            logger.error(f"Error extracting token: {e}")
        
        return None
    
    async def _verify_response_header(self, auth_header: Dict) -> bool:
        """验证响应方的 DID 认证头"""
        from ...auth.did_auth_wba import check_response_DIDAtuhHeader
        
        try:
            import json
            auth_data = auth_header.get("Authorization")
            if isinstance(auth_data, str):
                auth_data = json.loads(auth_data)
            
            if isinstance(auth_data, list) and len(auth_data) > 0:
                resp_header = auth_data[0].get("resp_did_auth_header")
                if resp_header:
                    return await check_response_DIDAtuhHeader(
                        resp_header.get("Authorization")
                    )
            
        except Exception as e:
            logger.error(f"Error verifying response header: {e}")
        
        return False
    
    def _build_success_message(self, auth_response: AuthResponse) -> str:
        """构建成功消息"""
        if auth_response.auth_level == AuthLevel.BEARER_TOKEN:
            return "使用缓存 Token 认证成功"
        elif auth_response.auth_level == AuthLevel.DID_TWO_WAY:
            return "DID 双向认证成功"
        elif auth_response.auth_level == AuthLevel.DID_ONE_WAY:
            if auth_response.metadata.get('downgraded'):
                return "DID 单向认证成功（从双向降级）"
            else:
                return "DID 单向认证成功"
        else:
            return "认证成功"
```

### 第六阶段：实现存储和监控

#### 步骤 6.1：Token 存储

__文件：`auth/storage/token_store.py`__

```python
import jwt
import logging
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from ...config import get_global_config

logger = logging.getLogger(__name__)

@dataclass
class TokenValidationResult:
    is_valid: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TokenStore(ABC):
    """Token 存储接口"""
    
    @abstractmethod
    async def create_token(
        self,
        caller_did: str,
        target_did: str,
        expires_in: int
    ) -> str:
        """创建新 token"""
        pass
    
    @abstractmethod
    async def validate_token(
        self,
        token: str,
        caller_did: str,
        target_did: str
    ) -> TokenValidationResult:
        """验证 token"""
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str):
        """撤销 token"""
        pass

class JWTTokenStore(TokenStore):
    """基于 JWT 的 Token 存储实现"""
    
    def __init__(self):
        self.config = get_global_config()
        self.algorithm = self.config.anp_sdk.jwt_algorithm
    
    async def create_token(
        self,
        caller_did: str,
        target_did: str,
        expires_in: int
    ) -> str:
        """创建 JWT token"""
        from ...anp_sdk_agent import LocalAgent
        from ...auth.token_nonce_auth import get_jwt_private_key
        
        try:
            # 获取目标智能体
            target_agent = LocalAgent.from_did(target_did)
            
            # 获取私钥
            private_key = get_jwt_private_key(target_agent.jwt_private_key_path)
            if not private_key:
                raise ValueError("Failed to load private key")
            
            # 创建 payload
            now = datetime.now(timezone.utc)
            payload = {
                "req_did": caller_did,
                "resp_did": target_did,
                "iat": now,
                "exp": now + timedelta(seconds=expires_in),
                "comments": f"Token for {caller_did}"
            }
            
            # 生成 token
            token = jwt.encode(
                payload,
                private_key,
                algorithm=self.algorithm
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Error creating token: {e}")
            raise
    
    async def validate_token(
        self,
        token: str,
        caller_did: str,
        target_did: str
    ) -> TokenValidationResult:
        """验证 JWT token"""
        from ...anp_sdk_agent import LocalAgent
        from ...auth.token_nonce_auth import get_jwt_public_key
        
        try:
            # 获取目标智能体
            target_agent = LocalAgent.from_did(target_did)
            
            # 获取公钥
            public_key = get_jwt_public_key(target_agent.jwt_public_key_path)
            if not public_key:
                return TokenValidationResult(
                    is_valid=False,
                    error="Failed to load public key"
                )
            
            # 验证 token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[self.algorithm]
            )
            
            # 验证 DID
            if payload.get("req_did") != caller_did:
                return TokenValidationResult(
                    is_valid=False,
                    error="req_did mismatch"
                )
            
            if payload.get("resp_did") != target_did:
                return TokenValidationResult(
                    is_valid=False,
                    error="resp_did mismatch"
                )
            
            return TokenValidationResult(
                is_valid=True,
                metadata=payload
            )
            
        except jwt.ExpiredSignatureError:
            return TokenValidationResult(
                is_valid=False,
                error="Token expired"
            )
        except jwt.InvalidTokenError as e:
            return TokenValidationResult(
                is_valid=False,
                error=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return TokenValidationResult(
                is_valid=False,
                error=str(e)
            )
    
    async def revoke_token(self, token: str):
        """撤销 token（JWT 无法真正撤销，需要黑名单机制）"""
        # 这里可以实现黑名单机制
        logger.warning("JWT token revocation not implemented (requires blacklist)")
```

#### 步骤 6.2：Token 缓存

__文件：`auth/storage/cache.py`__

```python
import asyncio
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

@dataclass
class CachedToken:
    token: str
    expires_at: datetime
    created_at: datetime

class TokenCache:
    """客户端 Token 缓存"""
    
    def __init__(self):
        self._cache: Dict[str, CachedToken] = {}
        self._lock = asyncio.Lock()
    
    async def get_valid_token(
        self,
        caller_did: str,
        target_did: str
    ) -> Optional[str]:
        """获取有效的缓存 token"""
        key = f"{caller_did}:{target_did}"
        
        async with self._lock:
            cached = self._cache.get(key)
            
            if not cached:
                return None
            
            # 检查是否过期（提前5分钟）
            now = datetime.now(timezone.utc)
            if now >= cached.expires_at - timedelta(minutes=5):
                # Token 即将过期，删除
                del self._cache[key]
                return None
            
            return cached.token
    
    async def store(
        self,
        caller_did: str,
        target_did: str,
        token: str,
        expires_in: int
    ):
        """存储 token 到缓存"""
        key = f"{caller_did}:{target_did}"
        now = datetime.now(timezone.utc)
        
        async with self._lock:
            self._cache[key] = CachedToken(
                token=token,
                expires_at=now + timedelta(seconds=expires_in),
                created_at=now
            )
    
    async def invalidate(self, caller_did: str, target_did: str):
        """使缓存失效"""
        key = f"{caller_did}:{target_did}"
        
        async with self._lock:
            self._cache.pop(key, None)
    
    async def clear(self):
        """清空所有缓存"""
        async with self._lock:
            self._cache.clear()
```

#### 步骤 6.3：降级监控

__文件：`auth/monitoring/fallback_monitor.py`__

```python
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List
from ..core.levels import AuthLevel

logger = logging.getLogger(__name__)

class FallbackMonitor:
    """降级监控器"""
    
    def __init__(self, alert_threshold: int = 10):
        self.fallback_stats = defaultdict(int)
        self.fallback_history: List[Dict] = []
        self.alert_threshold = alert_threshold
    
    async def record_fallback(
        self,
        from_level: AuthLevel,
        to_level: AuthLevel,
        did: str
    ):
        """记录降级事件"""
        key = f"{from_level.name}->{to_level.name}"
        self.fallback_stats[key] += 1
        
        # 记录历史
        event = {
            "timestamp": datetime.now().isoformat(),
            "from_level": from_level.name,
            "to_level": to_level.name,
            "did": did,
            "count": self.fallback_stats[key]
        }
        self.fallback_history.append(event)
        
        # 保持历史记录在合理范围内
        if len(self.fallback_history) > 1000:
            self.fallback_history = self.fallback_history[-500:]
        
        # 检查是否需要告警
        if self.fallback_stats[key] >= self.alert_threshold:
            await self._send_alert(from_level, to_level, did, self.fallback_stats[key])
    
    async def _send_alert(
        self,
        from_level: AuthLevel,
        to_level: AuthLevel,
        did: str,
        count: int
    ):
        """发送降级告警"""
        alert_msg = (
            f"认证降级告警: {from_level.name} -> {to_level.name} "
            f"已发生 {count} 次，最近 DID: {did}"
        )
        
        logger.warning(alert_msg)
        
        # TODO: 集成告警系统（邮件、Slack、钉钉等）
        # await self.alert_service.send_alert(alert_msg)
    
    def get_stats(self) -> Dict[str, int]:
        """获取降级统计"""
        return dict(self.fallback_stats)
    
    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """获取最近的降级事件"""
        return self.fallback_history[-limit:]
    
    def reset_stats(self):
        """重置统计"""
        self.fallback_stats.clear()
        self.fallback_history.clear()
```

### 第七阶段：集成和配置

#### 步骤 7.1：更新 `anp_sdk.py`

__修改 `anp_open_sdk/anp_sdk.py` 的认证中间件部分：__

```python
# 在 __init__ 方法中
from anp_open_sdk.auth.middleware.auth_middleware import AuthMiddleware
from anp_open_sdk.auth.storage.token_store import JWTTokenStore
from anp_open_sdk.auth.monitoring.fallback_monitor import FallbackMonitor

# 初始化认证组件
self.token_store = JWTTokenStore()
self.fallback_monitor = FallbackMonitor()

# 创建认证中间件
@self.app.middleware("http")
async def auth_middleware_wrapper(request, call_next):
    # 创建认证器
    from anp_open_sdk.auth.did_auth_wba import (
        WBADIDResolver, WBADIDSigner, 
        WBAAuthHeaderBuilder, WBADIDAuthenticator, WBAAuth
    )
    
    authenticator = WBADIDAuthenticator(
        resolver=WBADIDResolver(),
        signer=WBADIDSigner(),
        header_builder=WBAAuthHeaderBuilder(),
        base_auth=WBAAuth()
    )
    
    # 创建中间件实例
    middleware = AuthMiddleware(
        token_store=self.token_store,
        authenticator=authenticator,
        monitor=self.fallback_monitor
    )
    
    return await middleware(request, call_next)
```

#### 步骤 7.2：更新客户端调用

__修改 `anp_open_sdk/auth/auth_client.py` 的 `agent_auth_request` 函数：__

```python
from anp_open_sdk.auth.client.enhanced_client import EnhancedAuthClient

async def agent_auth_request(
    caller_agent: str,
    target_agent: str,
    request_url: str,
    method: str = "GET",
    json_data: Optional[Dict] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    use_two_way_auth: bool = True,
    auth_method: str = "wba"
) -> Tuple[int, str, str, bool]:
    """
    通用认证函数，支持智能降级
    
    返回: (status_code, response_data, message, success)
    """
    client = EnhancedAuthClient()
    
    return await client.authenticate(
        caller_did=caller_agent,
        target_did=target_agent,
        request_url=request_url,
        method=method,
        body=json_data,
        headers=custom_headers,
        prefer_cached_token=True  # 优先使用缓存 token
    )
```

### 第八阶段：测试和文档

#### 步骤 8.1：创建测试文件

__文件：`test/test_auth_fallback.py`__

```python
import pytest
import asyncio
from anp_open_sdk.auth.core.levels import AuthLevel
from anp_open_sdk.auth.client.enhanced_client import EnhancedAuthClient
from anp_open_sdk.auth.monitoring.fallback_monitor import FallbackMonitor

class TestAuthFallback:
    """测试认证降级机制"""
    
    @pytest.mark.asyncio
    async def test_token_cache(self):
        """测试 Token 缓存"""
        client = EnhancedAuthClient()
        
        # 第一次调用，应该使用 DID 认证
        status1, data1, msg1, success1 = await client.authenticate(
            caller_did="did:wba:localhost:9527:user:test1",
            target_did="did:wba:localhost:9528:user:test2",
            request_url="http://localhost:9528/api/test"
        )
        
        assert success1
        assert "DID" in msg1
        
        # 第二次调用，应该使用缓存 Token
        status2, data2, msg2, success2 = await client.authenticate(
            caller_did="did:wba:localhost:9527:user:test1",
            target_did="did:wba:localhost:9528:user:test2",
            request_url="http://localhost:9528/api/test"
        )
        
        assert success2
        assert "缓存 Token" in msg2
    
    @pytest.mark.asyncio
    async def test_auth_downgrade(self):
        """测试认证降级"""
        # 模拟双向认证失败的场景
        # 这需要配置测试环境
        pass
    
    @pytest.mark.asyncio
    async def test_fallback_monitor(self):
        """测试降级监控"""
        monitor = FallbackMonitor(alert_threshold=3)
        
        # 记录降级事件
        for i in range(5):
            await monitor.record_fallback(
                AuthLevel.DID_TWO_WAY,
                AuthLevel.DID_ONE_WAY,
                f"did:wba:test:{i}"
            )
        
        # 检查统计
        stats = monitor.get_stats()
        assert stats["DID_TWO_WAY->DID_ONE_WAY"] == 5
        
        # 检查历史
        events = monitor.get_recent_events(3)
        assert len(events) == 3
```

#### 步骤 8.2：创建使用文档

__文件：`docs/auth_system_guide.md`__

````markdown
# ANP SDK 认证系统使用指南

## 概述

新的认证系统提供了智能的认证降级机制，支持从高安全级别自动降级到低安全级别，确保服务的可用性。

## 认证级别

1. **DID 双向认证**（最高安全级别）
   - 双方互相验证身份
   - 适用于首次建立信任关系
   - 提供最强的安全保证

2. **DID 单向认证**（中等安全级别）
   - 仅验证请求方身份
   - 双向认证失败时的降级选择
   - 平衡安全性和可用性

3. **Bearer Token**（基础安全级别）
   - 使用预先颁发的令牌
   - 适用于频繁的 API 调用
   - 提供最佳性能

## 使用示例

### 基础使用

```python
from anp_open_sdk.auth.auth_client import agent_auth_request

# 发起认证请求
status, data, message, success = await agent_auth_request(
    caller_agent="did:wba:localhost:9527:user:alice",
    target_agent="did:wba:localhost:9528:user:bob",
    request_url="http://localhost:9528/api/data",
    method="GET"
)

if success:
    print(f"认证成功: {message}")
    print(f"响应数据: {data}")
else:
    print(f"认证失败: {message}")
````

### 配置降级策略

```python
from anp_open_sdk.auth.strategies.fallback import FallbackStrategy
from anp_open_sdk.auth.core.levels import AuthLevel

# 自定义降级链
custom_fallback = FallbackStrategy(
    fallback_chain=[
        AuthLevel.DID_TWO_WAY,
        AuthLevel.BEARER_TOKEN  # 跳过单向认证
    ]
)
```

### 监控降级事件

```python
from anp_open_sdk.anp_sdk import ANPSDK

sdk = ANPSDK()

# 获取降级统计
stats = sdk.fallback_monitor.get_stats()
print(f"降级统计: {stats}")

# 获取最近的降级事件
events = sdk.fallback_monitor.get_recent_events(10)
for event in events:
    print(f"{event['timestamp']}: {event['from_level']} -> {event['to_level']}")
```

## 最佳实践

1. __优先使用缓存 Token__

   - 减少网络往返
   - 提高响应速度
   - 降低服务器负载

2. __合理设置告警阈值__

   - 监控降级频率
   - 及时发现认证问题
   - 避免告警疲劳

3. __定期轮换密钥__

   - 增强安全性
   - 限制密钥泄露影响
   - 遵循安全最佳实践

## 故障排查

### 常见问题

1. __频繁降级到单向认证__

   - 检查双向认证配置
   - 验证 DID 文档完整性
   - 查看网络连接状态

2. __Token 频繁失效__

   - 检查时钟同步
   - 验证 Token 过期时间设置
   - 查看是否有主动撤销

3. __认证完全失败__

   - 检查 DID 是否正确
   - 验证密钥文件存在
   - 查看详细错误日志

### 调试模式

```python
import logging

# 启用详细日志
logging.getLogger("anp_open_sdk.adapter_auth").setLevel(logging.DEBUG)
```

```javascript

## 总结

这个重构方案实现了：

1. **清晰的分层架构**
   - 核心层：统一的数据模型
   - 策略层：可扩展的认证策略
   - 存储层：Token 生命周期管理
   - 监控层：降级事件追踪

2. **智能降级机制**
   - 自动从高到低尝试
   - 记录降级事件
   - 支持自定义降级链

3. **性能优化**
   - Token 缓存机制
   - 减少网络请求
   - 快速认证路径

4. **可观测性**
   - 详细的日志记录
   - 降级事件监控
   - 统计和告警机制

5. **向后兼容**
   - 保持原有接口
   - 平滑迁移路径
   - 配置化切换

现在您可以切换到 Act Mode 来执行这个重构方案。
```
