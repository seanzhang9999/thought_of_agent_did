logo
总结

MCP规范完整中译稿：2025-3-26版
【引】尽管AI 可以帮助我们顺利地理解MCP规范，但一份完整的MCP规范中译稿还是有意义的，可以进一步帮助我们理解MCP规范的来龙去脉，以及协议中细节的方方面面。如果希望希望极简入门的话， 可以阅读老码农的新作——
1.规范
模型上下文协议 (Model Context Protocol，MCP) 是一个开放的协议，支持 LLM 应用程序与外部数据源和工具之间的无缝集成。无论是构建基于 AI 的 IDE、增强聊天界面还是创建自定义 AI 工作流，MCP 都提供了一种标准化的方法来将 llm 与它们所需的上下文连接起来。

该规范基于 schema.ts 中的 TypeScript 模式定义了权威协议需求。

有关实现指南及示例，请浏览 modelcontextprotocol.io。

本文件中的关键词 “MUST”、“MUST NOT”、“REQUIRED”、“SHALL”、“SHALL NOT”、“SHOULD”、“SHOULD NOT”、“RECOMMENDED”、“NOT RECOMMENDED”、“MAY” 和 “OPTIONAL” 应按照 BCP 14 [RFC2119][RFC8174] 中的规定解释，如本文件所示，当且仅当它们出现在所有大写字母中时表示如上含义。

1.1 概览
MCP 为应用程序提供了一种标准化的方式：

与语言模型共享上下文信息
向人工智能系统公开工具和能力
构建可组合的集成和工作流
该协议使用 JSON-RPC 2.0 消息来建立以下组件之间的通信：

主机: 启动连接的 LLM 应用程序
客户端: 宿主应用程序中的连接器
服务器： 提供上下文和能力服务
MCP 从语言服务器协议 (Language Server Protocol) 中获得了一些灵感，该协议标准化了如何在整个开发工具生态系统中添加对编程语言的支持。以类似的方式，MCP 标准化了如何将其他上下文和工具集成到 AI 应用程序的生态系统中。

1.2 主要内容
1.2.1 基本协议
JSON-RPC 消息格式
有状态连接
服务器和客户端能力协商
1.2.2 特性
服务器向客户端提供以下特性：

资源： 上下文和数据，供用户或 AI 模型使用
提示词： 用户的模板化消息和工作流
工具： AI 模型要执行的函数
客户端可向服务器提供以下功能：

采样： 服务器发起的代理化行为和递归 的LLM 交互

额外公用设施

配置

进度跟踪

取消

错误报告

日志


1.3 安全性和信任及保护
模型上下文协议通过任意的数据访问和代码执行路径实现了强大的功能。这种能力带来了重大的安全和信任问题，所有实现者都必须仔细考虑这些问题。

1.3.1 主要原则
1. 用户同意及管制
用户必须明确同意并理解所有数据访问和操作
用户必须保留对共享哪些数据和采取哪些操作的控制
实现者应该为审查和授权活动提供清晰的用户界面

2. 数据私隐
在向服务器公开用户数据之前，主机必须获得用户的明确同意
未经用户同意，主机不得在其他地方传输资源数据
应使用适当的访问控制来保护用户数据
3. 工具安全
工具代表任意的代码执行，必须谨慎对待。
特别是，工具行为的描述 (如注释) 应该被认为是不可信的，除非从受信任的服务器获得。
在调用任何工具之前，主机必须获得明确的用户同意
在授权使用之前，用户应该了解每个工具的作用
4. 采样控制
用户必须显式批准任何 LLM 采样请求
使用者应控制：
是否进行取样
将要发送的实际提示词
服务器可以看到的结果
该协议有意将服务器的可见性限制为提示词  ##1.4 实现指南
虽然 MCP 本身不能在协议级别上强制执行这些安全原则，但实现者应该：

在其应用程序中构建健壮的批准和授权流
提供安全影响的清晰文档
实施适当的访问控制和数据保护
在它们的集成中遵循安全最佳实践
在他们的功能设计中考虑隐私问题
2.关键变更
本文档列出了自上一版本（ 2024-11-05 ）以来对模型上下文协议 (MCP) 规范所做的变更。

2.1 主要变化
增加了一个基于 OAuth 2.1 (PR # 133) 的全面授权框架
用更灵活的 Streamable HTTP 传输 (PR # 206) 取代了以前的 HTTP + SSE 传输
增加了对 JSON-RPC 批处理的支持 (PR # 228)
增加了全面的工具注释，以更好地描述工具的行为，如它是只读的还是破坏性的 (PR # 185) 
2.2  其他模式的变更
向 ProgressNotification 添加了消息字段以提供描述性状态更新
添加了对音频数据的支持，加入了现有的文本和图像的内容类型
添加了补全能力，以显式指示对参数自动补全建议的支持
有关更多详细信息，请参见更新的数据模式。

2.3 完整的变更记录
有关自上次协议修订以来所做的所有变更的完整列表，请参见 GitHub。

3.架构
模型上下文协议 (Model Context Protocol，MCP) 遵循客户端- 主机 - 服务器的架构模式，其中每个主机可以运行多个客户端实例。这种架构使用户能够在应用程序之间集成 AI 功能，同时保持清晰的安全边界和隔离关注点。MCP 建立在 JSON-RPC 之上，它提供了一个有状态的会话协议，主要关注客户端和服务器之间的上下文交换和采样协调。

3.1 核心组件
3.1.1 主机（Host）
主机进程充当容器和协调器：

创建并管理多个客户端实例
控制客户端连接权限和生命周期
执行安全策略和正式批准需求
处理用户授权决策
协调 AI/LLM 的集成和采样
管理跨客户端的上下文聚合
3.1.2 客户端（client）
每个客户端由主机创建，并维护一个独立的服务器连接：

为每个服务器建立一个有状态会话
处理协议协商和能力交换
支持双向的路由协议消息
管理订阅和通知
维护服务器之间的安全边界
主机应用程序创建并管理多个客户机，每个客户机与特定服务器具有 1:1 的关系。

3.1.3 服务器（Server）
服务器提供专门的环境和功能：

通过 MCP 原语公开资源、工具和提示词
独立工作，责任明确
通过客户端接口请求取样
必须尊循安全约束
可以是本地进程或远程服务
3.2 设计原则
MCP 建立在几个关键设计原则的基础上，这些原则为其架构和实施提供了参考信息：

3.2.1 服务器应该非常容易构建
主机应用程序负责处理复杂的业务流程
服务器侧重于特定的、定义良好的能力
简单接口并最小化实现开销
清晰的分离，支持可维护的代码
3.2.2 服务器应该是高度可组合的
每个服务器提供独立的重点功能

可以无缝地组合多个服务器

共享的协议支持互操作性

模块化设计支持可扩展性

3.2.3 服务器不能够读取整个会话，也不能 “看到” 其他服务器
服务器只接收必要的上下文信息
完整的会话历史保留在主机上
每个服务器连接保持隔离
跨服务器交互由主机控制
主机进程强制执行安全边界
3.2.4 功能特性可以逐步添加到服务器和客户端
核心协议提供了最低要求的功能
额外的能力可以根据需要进行协商
服务器和客户机是独立开发的
为将来的可扩展性而设计的协议
保持后向兼容性
3.3 能力协商
模型上下文协议使用一个基于能力的协商系统，客户端和服务器在初始化期间显式地声明它们支持的功能特性。能力决定哪些协议特性和原语在会话期间可用。

服务器声明诸如资源订阅、工具支持和提示模板等功能
客户端声明采样支持和通知处理等功能
在整个会话过程中，双方都必须遵循对方声明的能力
额外的功能可以通过协议的扩展来协商
每个功能解锁特定的协议特性，以便在会话期间使用。例如：

实现的服务器特性必须在服务器能力中公布
发出资源订阅通知需要服务器声明其支持订阅
工具调用要求服务器声明其工具的能力
采样要求客户端在其功能中声明支持
此能力协商确保客户端和服务器在维护协议可扩展性的同时清楚地理解所支持的功能。

4. 基本协议
修订于 2025 年 3 月 26 日

4.1 概览
模型上下文协议由几个协同工作的关键组成部分组成：

基本协议：核心 JSON-RPC 消息类型
生命周期管理： 连接初始化、能力协商和会话控制
服务器特性： 服务器公开的资源、提示词和工具
客户端特性： 客户端提供的取样和根目录列表
实用程序： 横切关注点，如日志记录和参数不全
所有的实现都必须支持基本协议和生命周期管理组件。其他组件可以根据应用程序的具体需要来实现。

这些协议层建立了清晰的关注点分离，同时实现了客户端和服务器之间的丰富交互。模块化设计允许实现完全支持它们需要的特性。

4.1.1 消息
MCP 客户端和服务器之间的所有消息必须遵循 JSON-RPC 2.0 规范，该协议定义了以下类型的消息。

4.1.1.1 请求
请求从客户端发送到服务器，反之亦然，以启动一个操作。

{
  jsonrpc: "2.0";
  id: string | number;
  method: string;
  params?: {
    [key: string]: unknown;
  };
}
请求必须包含一个字符串或整数 ID。
与基本 JSON-RPC 不同，ID 不能为空。
请求 ID 必须以前没有被请求者在同一个会话中使用过。
4.1.1.2 响应

响应是在回复请求时发送的，包含操作的结果或错误信息。

{
  jsonrpc: "2.0";
  id: string | number;
  result?: {
    [key: string]: unknown;
  }
  error?: {
    code: number;
    message: string;
    data?: unknown;
  }
}
响应必须包含与其对应的请求相同的 ID。
响应进一步细分为成功的结果或错误。必须设置结果或错误，一个响应不能同时设置成功和错误。
结果可以遵循任何 JSON 对象结构，而错误必须至少包含一个错误编码和消息。
错误编码码必须是整数。  ####通知
通知作为单向消息从客户机发送到服务器，反之亦然。接收者不能发送响应。

{
  jsonrpc: "2.0";
  method: string;
  params?: {
    [key: string]: unknown;
  };
}
通知不能包含 ID。

4.1.1.3 批处理
JSON-RPC 还定义了一种方法来批处理多个请求和通知，将它们发送到一个数组中。MCP 实现可能支持发送端的 JSON-RPC 批处理，但必须支持接收端的 JSON-RPC 批处理。

4.1.2 授权
MCP 提供了一个用于 HTTP 的授权框架。使用基于 http 传输的实现应该符合这个规范，而使用 STDIO 传输的实现不应该遵循这个规范，而应该从环境中检索凭证。

此外，客户端和服务器可以协商自己的自定义身份验证和授权策略。

欲了解更多关于 MCP 身份验证机制发展的讨论和贡献，请加入 GitHub 讨论，帮助塑造协议的未来！

4.1.3 Schema
协议的完整规范被定义为 TypeScript 模式。这是所有协议消息和结构的真实来源。

还有一个JSON Schema，它是从 TypeScript 可信真值源自动生成的，用于各种自动化工具。

4.2 生命周期
模型上下文协议 (Model Context Protocol，MCP) 为客户端 - 服务器连接定义了严格的生命周期，以确保适当的能力协商和状态管理。

初始化： 能力协商和协议版本认同
操作： 正常协议通信
Shutdown: 连接的正常终止
Image
4.2.1 生命周期阶段
4.2.1.1 初始化
初始化阶段必须是客户端和服务器之间的第一次交互。在这个阶段，客户端和服务器：

建立协议版本兼容性
交换和协商能力
共享实现细节
客户端必须通过发送包含以下内容的初始化请求来启动此阶段：

支持的协议版本
客户端能力
客户端的实现信息
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": {
        "listChanged": true
      },
      "sampling": {}
    },
    "clientInfo": {
      "name": "ExampleClient",
      "version": "1.0.0"
    }
  }
}
初始化请求不能成为 JSON-RPC 批处理的一部分，因为在初始化完成之前，其他请求和通知是不可能发出的。这还允许向后兼容不显式支持 JSON-RPC 批处理的以前协议版本。

服务器必须用自己的能力和信息进行响应：

{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "logging": {},
      "prompts": {
        "listChanged": true
      },
      "resources": {
        "subscribe": true,
        "listChanged": true
      },
      "tools": {
        "listChanged": true
      }
    },
    "serverInfo": {
      "name": "ExampleServer",
      "version": "1.0.0"
    },
    "instructions": "Optional instructions for the client"
  }
}
初始化成功后，客户端必须发送一个初始化通知，表明它已准备好开始正常操作：

{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
在服务器响应初始化请求之前，客户端不应该发送 ping 以外的请求。

在接收到初始化通知之前，服务器不应该发送 ping 和日志以外的请求。

4.2.1.2 版本协商
在初始化请求中，客户端必须发送它支持的协议版本。这应该是客户端支持的最新版本。

如果服务器支持请求的协议版本，它必须用相同的版本响应。否则，服务器必须使用其支持的另一个协议版本进行响应。这应该是服务器支持的最新版本。

如果客户端不支持服务器响应中的版本，它应该断开连接。

4.2.1.3 能力协商
客户端和服务器功能确定在会话期间哪些可选协议的特性可用。

主要能力包括：

类别
能力
描述
Client
roots 
提供文件系统根的能力
Client
sampling 
支持 LLM 采样请求
Client
experimental 
描述对非标准实验特性的支持
Server
prompts 
提供提示词模板
Server
resources 
提供可读的资源
Server
tools 
公开可调用的工具
Server
logging 
发出结构化的日志消息
Server
experimental 
描述对非标准实验特性的支持
能力对象可以像这样描述其子能力：

listChanged: 支持列表更改通知 (用于提示、资源和工具)
subscribe： 支持订阅单个项目的更改 (仅限参考资料)

4.2.1.4 操作
在操作阶段，客户端和服务器根据协商的能力交换消息。

双方应该：

遵循协议的版本
只使用成功协商的能力  
4.2.1.5 shutdown
在关闭阶段，一方 (通常是客户端) 干净地终止协议连接。没有定义特定的关闭消息ーー相反，应该使用底层传输机制来发送连接终止信号：

stdio
对于 stdio 传输，客户端应该通过以下方式启动关闭：

1.首先，关闭子进程 (服务器) 的输入流

2. 等待服务器退出，如果服务器没有在合理的时间内退出，则发送 SIGTERM

3. 如果服务器没有在 SIGTERM 之后的合理时间内退出，则发送 SIGKILL

服务器可以通过关闭其到客户端的输出流并退出来启动关闭。

HTTP
对于 HTTP 传输，通过关闭相关的 HTTP 连接来指示关闭。

4.2.1.6 超时
实现应该为所有发送的请求建立超时，以防止挂起连接和资源耗尽。当请求在超时期间内没有收到成功或错误响应时，发送方应该为该请求发出取消通知，并停止等待响应。

SDK和其他中间件应该允许根据每个请求配置这些超时。

实现可能在接收到相应请求的进度通知时选择重置超时时钟，这意味着工作实际上正在发生。但是，无论进度通知如何，实现都应该强制执行最大超时，以限制行为不当的客户端或服务器的影响。

4.2.1.7 错误处理
应该准备好实现来处理这些错误情况：

协议版本不匹配
未能就所需能力完成协商
请求超时
初始化的错误示例：
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Unsupported protocol version",
    "data": {
      "supported": ["2024-11-05"],
      "requested": "1.0.0"
    }
  }
}
4.3 传输
MCP 使用 JSON-RPC 编码消息。 JSON-RPC 消息必须是 utf-8 编码。

该协议目前定义了客户端 - 服务器通信的两种标准传输机制：

STDIO：标准输入和标准输出的通信
Streamable HTTP
客户端应该尽可能支持 stdio。

客户端和服务器也可以以可插拔的方式实现自定义传输。

4.3.1 STDIO
在STDIO的传输中：

客户端将 MCP 服务器作为子进程启动。
服务器从其标准输入 (stdin) 中读取 JSON-RPC 消息，并将消息发送到其标准输出 (stdout)。
消息可以是 JSON-RPC 请求、通知、响应ーー或包含一个或多个请求和 / 或通知的 JSON-RPC 批处理。
消息由换行符分隔，并且不能(MUST NOT)包含嵌入的换行符。
服务器可以将 utf-8 字符串写入其标准错误 (stderr) ，以便记日志。客户端可以捕获、转发或忽略此日志记录。

服务器不能写入任何非有效 MCP 消息的标准输出。

客户端不能向服务器的 stdin 写入非有效 MCP 消息的内容。


Image
4.3.2 Streamable HTTP
这取代了协议 2024-11-05 版本中的 HTTP + SSE传输。

在 Streamable HTTP传输中，服务器作为独立进程运行，可以处理多个客户端连接。此传输使用 HTTP POST 和 GET 请求。服务器可以选择性地使用SSE来流化多个服务器消息。这为基本的 MCP 服务器和支持流的服务器提供了更多丰富的功能，并支持服务器到客户端的通知和请求。

服务器必须提供一个同时支持 POST 和 GET 方法的 HTTP 端点路径 (以下称为 MCP 端点)。例如，这可能是一个类似于 https://example.com/mcp 的 URL。

4.3.2.1 安全警告
实现流式 HTTP 传输时：

服务器必须在所有传入连接上验证初始的HTTP头，以防止 DNS 重新绑定攻击
在本地运行时，服务器应该只绑定到本地主机 (127.0.0.1) ，而不是绑定到网络接口 (0.0.0.0) 
服务器应该为所有连接实现正确的身份验证
如果没有这些保护，攻击者可以使用 DNS 重新绑定来与远程站点的本地 MCP 服务器交互。

4.3.2.2 向服务器发送消息
从客户端发送的每个 JSON-RPC 消息都必须是对 MCP 端点的新HTTP POST 请求。

客户端必须使用HTTP POST 将 JSON-RPC 消息发送到 MCP 端点。
客户机必须包含一个 Accept 头，列出将application/json 和 text/event-stream 作为支持的内容类型。
POST 请求的正文MUST必须列情况之一：
单个 JSON-RPC 请求、通知或响应
批处理一个或多个请求和 / 或通知的数组
批处理一个或多个响应的数组
如果输入仅由 (任意数量的) JSON-RPC 组成响应或者通知:
如果服务器接受输入，则服务器必须返回 HTTP 状态码 202 Accepted，而不接受任何正文。
如果服务器不能接受输入，它必须返回一个 HTTP 错误状态码 (例如，400 Bad Request)。HTTP 响应的正文可能包含一个没有 id 的 JSON-RPC 错误响应。
如果输入包含任意数量的 JSON-RPC 请求，服务器必须返回 Content-Type: text/event-stream 来初始化 SSE 流，或者返回 Content-Type: application/JSON 来返回一个 JSON 对象。客户端必须同时支持这两种情况。

如果服务器启动 SSE 流：

断开连接不应被解释为客户端取消其请求。
若要取消其请求，客户端应显式发送 MCP CancelledNotification。
为了避免由于断开连接而导致的消息丢失，服务器可以恢复流传输。
SSE 流最终应该为 POST 主体中发送的每个 JSON-RPC 请求包含一个 JSON-RPC 响应。这些响应可以是批处理形式。
在发送 JSON-RPC 响应之前，服务器可能会发送 JSON-RPC 请求和通知。这些消息应该与原始客户端的请求相关。这些请求和通知可以被批处理。
服务器不应该在为每个接收到的 JSON-RPC 请求发送一个 JSON-RPC 响应之前关闭 SSE 流，除非会话过期。
在发送了所有 JSON-RPC 响应之后，服务器应该关闭 SSE 流。 断开连接可以发生在任何时间 (例如，由于网络条件)，因此：
4.3.2.3 侦听来自服务器的消息
客户端可以向 MCP 端点发出HTTP GET请求。这可以用来打开一个 SSE 流，允许服务器与客户端通信，而不需要客户机首先通过 HTTP POST 发送数据。
客户端必须包含一个 Accept 头，将text/event-stream 列为受支持的内容类型。
服务器必须返回 Content-Type: text/event-stream 来响应这个 HTTP GET，或者返回 HTTP 405 Method Not Allowed，表明服务器没有在这个端点提供 SSE 流。
如果服务器启动了 SSE 流：
服务器可以在流上发送 JSON-RPC 请求和通知。这些请求和通知可以被批处理。
这些消息应该与来自客户端的任何并发运行的 JSON-RPC 请求无关。
服务器不能在流上发送 JSON-RPC 响应，除非恢复与以前的客户端请求相关联的流。
服务器可以在任何时候关闭 SSE 流。
客户端可以在任何时候关闭 SSE 流。
4.3.2.4 多连接
客户端可以同时保持与多个 SSE 流的连接。
服务器必须只在一个已连接的流上发送它的每个 JSON-RPC 消息；也就是说，它绝对不能跨多个流广播相同的消息。
可以通过使流可恢复来降低消息丢失的风险。
4.3.2.5 可恢复性和重新发送
为了支持恢复中断的连接，并重新发送可能丢失的消息：

服务器可以附上一个id字段并添加到它们的 SSE 事件，像SSE 标准描述的那样：

如果存在该 ID ，则必须在该会话内的所有流之间是全局唯一的ーー或者在不使用会话管理的情况下在具有该特定客户端的所有流之间是全局唯一的。
如果客户端希望在断开连接后恢复，则它应该向 MCP 端点发出一个 HTTP GET请求， 并将使用Last-Event-ID 头来指示它接收的最后一个事件 ID。

服务器可以使用这个头来重播在最后一个事件 ID 之后发送的消息，并在断开连接的流上从该点恢复流。
服务器一定不能重播在不同流上传递的消息。
换句话说，服务器应该根据每个流分配这些事件 id，作为该特定流中的游标。

4.3.2.6 会话管理
一个MCP “会话” 由客户端和服务器之间逻辑上相关的交互组成，从初始化阶段开始。未来支持希望建立有状态会话的服务器：

使用流式 HTTP 传输的服务器可以在初始化时分配会话 ID，方法是将其HTTP 响应头Mcp-Session-Id header中包含InitializeResult.

会话 ID 应该是全局唯一的，并且具有加密安全性 (例如，安全生成的 UUID、 JWT 或加密散列)。
会话 ID 必须只包含可见的 ASCII 字符 (范围从 0x21 到 0x7e)。
如果服务器在初始化期间返回Mcp-Session-Id ，客户端使用流式 HTTP 传输时必须在所有后续 HTTP 请求头中包含Mcp-Session-Id 。

需要会话 ID 的服务器应该使用 HTTP 400 Bad Request 来响应没有 Mcp-Session-Id 头的请求 (初始化除外)。
服务器可以在任何时候终止会话，之后它必须用 HTTP 404 Not Found 响应包含该会话 ID 的请求。

当客户端响应包含 Mcp-Session-Id 的请求而收到 HTTP 404 时，它必须通过发送一个没有附加会话 ID 的新 InitializeRequest 来启动一个新会话。

不再需要特定会话的客户端 (例如，因为用户即将离开客户端应用)应该发送 HTTP DELETE到MCP端点，并使用Mcp-Session-Id 头以显式终止会话。

服务器可能用 HTTP 405 Method Not Allowed 响应此请求，表示服务器不允许客户端终止会话。  
Image
4.3.2.7 向后兼容性
客户端和服务器可以维护与 HTTP+ SSE传输 (来自协议版本 2024-11-05) 的向后兼容性，如下所示：

希望支持老客户端的服务器应该：

继续承载旧传输的 SSE 和 POST 端点，以及为 Streamable HTTP 传输定义的新 “MCP 端点”。
也可以组合旧的 POST 端点和新的 MCP 端点，但是这可能会引入不必要的复杂性。
希望支持旧服务器的客户端应该：

接受来自用户的 MCP 服务器 URL，该 URL 可以指向使用旧传输协议或新传输协议的服务器。
试图POST 一个InitializeRequest到服务器 URL，使用如上所述的Accept 头：
客户端向服务器 URL 发出 GET 请求，期望这将打开一个 SSE 流并返回一个endpoint事件作为第一个事件。
当endpoint事件到达时，客户端可以假设这是一个运行旧 HTTP + SSE 传输的服务器，并且应该将该传输用于所有后续通信。  ####4.3.2.8 定制传输
如果成功，客户端可以假设这是一个支持新的 Streamable HTTP 传输的服务器。
如果失败，服务器使用了 HTTP 4xx 的状态代码 (例如，405 Method Not Allowed 或 404 Not Found) :
客户短和服务器可以实现额外的自定义传输机制，以满足它们的特定需求。该协议是传输无关的，可以在任何支持双向消息交换的信道上完成实现。

选择支持自定义传输的实现者必须确保它们保留由 MCP 定义的 JSON-RPC 消息格式和生命周期需求。自定义传输应该记录其特定的连接建立和消息交换模式，以帮助实现互操作性。

4.4 鉴权
4.4.1. 简介
4.4.1.1 目标及范围
模型上下文协议在传输级别提供鉴权功能，使 MCP 客户短能够代表资源所有者向受限 MCP 服务器发出请求。本规范定义了基于 HTTP传输的授权流程。

4.4.1.2 协议要求
对于 MCP 实现，鉴权是可选的。当支持鉴权时：

使用基于HTTP传输的实现应该符合此规范。
使用 STDIO 传输的实现不应该遵循此规范，而应该从环境中检索凭据。
使用替代传输的实现必须遵循其协议的既定安全最佳实践。
4.4.1.3 遵守标准
这种鉴权机制基于下列既定规范，但实现了其特性的一个选定子集，以确保安全性和互操作性，同时保持简单：

OAuth 2.1 IETF DRAFT
OAuth 2.0 Authorization Server Metadata (RFC8414)
OAuth 2.0 Dynamic Client Registration Protocol (RFC7591)
4.4.2. 鉴权流程
4.4.2.1 概览
MCP鉴权实现必须实现 OAuth 2.1，并为私密客户端和公共客户端提供适当的安全措施。

MCP auth 实现应该支持 OAuth 2.0 动态客户端注册协议 (RFC7591)。

MCP 服务器应该和 MCP 客户端必须实现 OAuth 2.0 鉴权服务器元数据协议(RFC8414)。不支持元数据协议的服务器必须遵循默认 URI Schema。

OAuth 授权类型
OAuth 指定不同的流或授权类型，这是获得访问令牌的不同方式。每个目标都有不同的用例和场景。

MCP 服务器应该支持 OAuth 授权类型，这种授权类型最适合目标用户。例如：

鉴权码： 当客户短代表 (人类) 最终用户行事时非常有用。
例如，Agent调用由 SaaS 系统实现的 MCP 工具。
客户端凭据： 客户端是另一个应用程序 (不是人)
例如，Agent调用一个安全 MCP 工具来检查特定商店的库存,不需要模拟最终用户。
4.4.2.2 示例： 鉴权码授予
这里演示了用于用户身份验证的鉴权码授予类型的 OAuth 2.1 流。

注意： 下面的示例假定 MCP 服务器也作为授权服务器运行。但是，可以将授权服务器部署为其自己的特定服务。

人类用户通过 web 浏览器完成 OAuth 流程，获得一个访问令牌，该令牌可以识别用户，并允许客户端代表用户进行操作。

当需要鉴权且客户端尚未证明授权时，服务器必须响应HTTP 401 Unauthorized。

客户端在收到 HTTP 401 Unauthorized 之后启动 OAuth 2.1 IETF DRAFT 鉴权流程。

下图展示了使用 PKCE 公共客户端的基本 OAuth 2.1流程。


Image
4.4.2.3 服务器元数据发现
对于服务器能力发现而言：

MCP 客户端必须遵循RFC8414中定义的 OAuth 2.0 Authorization Server Metadata 协议。
MCP 服务器应该遵循 OAuth 2.0 Authorization Server Metadata 协议。
不支持 OAuth 2.0 Authorization Server Metadata 协议的 MCP 服务器必须支持会退URL。
发现流程如下：


Image
4.4.2.3.1 服务器元数据发现的HTTP头
MCP 客户端应该在服务器元数据发现期间包含头 MCP-protocol-version: ，以允许 MCP 服务器基于MCP的协议版本进行响应。

例如： MCP-Protocol-Version: 2024-11-05

4.4.2.3.2 鉴权的基URL
通过丢弃任何当前的路径元素，鉴权的基 URL 必须从 MCP 服务器 URL 中确定。例如：

如果 MCP 服务器 URL 是 https://api.example.com/v1/MCP ，那么：

鉴权的基URL 是 https://api.example.com
元数据端点必须在 https://api.example.com/.well-known/oauth-authorization-server
这确保鉴权端点始终位于承载 MCP 服务器的域名的根级别，而不管 MCP 服务器 URL 中的其他路径元素如何。

4.4.2.3.3 服务器未支持元数据发现的的后备方案
对于没有实现 OAuth 2.0 Authorization Server Metadata 协议的服务器，客户端必须使用相对于鉴权的基 URL (在 2.3.2 节中定义) 的以下默认端点路径：

端点
默认路径
描述




鉴权端点
/authorize/ 
用于鉴权请求
令牌端点

/token/ 

用于令牌交换和刷新
注册端点

/register/ 

用于动态客户端注册
例如，当 MCP 服务器托管在 https://api.example.com/v1/MCP 时，默认端点为：

https://api.example.com/authorize
https://api.example.com/token
https://api.example.com/register

客户端必须首先尝试通过元数据文档发现端点，然后再回到默认路径。当使用默认路径时，所有其他协议要求保持不变。

4.4.2.4 动态客户端注册
MCP 客户端和服务器应该支持 OAuth 2.0 动态客户端注册协议，以允许 MCP 客户端在没有用户交互的情况下获得 OAuth 客户端ID。这为客户端自动向新服务器注册提供了一种标准化的方法，对于 MCP 至关重要，因为：

客户端不能预先知道所有可能的服务器
手动注册会给用户带来不便
客户端支持与新服务器的无缝连接
服务器可以实现自己的注册策略
任何不支持动态客户端注册的 MCP 服务器都需要提供获取客户端 ID 以及 (如果适用的话) 客户端保密的替代方法。对于其中一台服务器，MCP 客户端必须满足以下条件之一：

专门为 MCP 服务器硬编码客户端 ID (如果适用，还有客户端密钥) ，或者
在注册 OAuth 客户端之后 ，为用户提供一个允许他们输入这些细节的 UI(例如，通过服务器托管的配置接口)。
4.4.2.5 鉴权的流程步骤
完整的鉴权流程如下：


Image
4.4.2.5.1 决策流程概述
Image
4.4.2.6 访问令牌的使用
4.4.2.6.1 令牌要求
访问令牌的处理必须符合 OAuth 2.1 第 5 部分对资源请求的要求，特别是：

1. MCP 客户端必须使用OAuth 2.1中 5.1.1 节的鉴权请求头字段：
Authorization: Bearer <access-token>
请注意，从客户端到服务器的每个 HTTP 请求中都必须包含鉴权，即使它们是同一逻辑会话的一部分。

2. 访问令牌不能包含在 URI 的查询字符串中 请求示例：
GET /v1/contexts HTTP/1.1
Host: mcp.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
4.4.2.6.2 令牌处理
资源服务器必须验证访问令牌，如OAuth 2.1的第 5.2 节所述。如果验证失败，服务器必须根据 5.3 节的错误处理要求进行响应。无效或过期的令牌必须接收一个HTTP 401 响应。

4.4.2.7 安全性考量
必须执行下列安全性要求：

客户端必须按照 OAuth 2.0 最佳实践安全地存储令牌
服务器应该强制令牌过期和轮换
所有鉴权端点必须通过 HTTPS 提供服务
服务器必须验证重定向的URI以防止打开重定向漏洞
重定向 URI必须是本地主机 URL或 HTTPS URL
4.4.2.8 错误处理
服务器必须为鉴权错误返回适当的 HTTP 状态码：


状态代码
描述
用法
401
Unauthorized

需要鉴权或令牌无效
403
Forbidden
无效范围或权限不足
400

Bad Request

格式错误的授权请求


4.4.2.9 实施规定
具体实现必须遵循 OAuth 2.1 安全最佳实践
所有客户端都需要 PKCE
为了增强安全性，应该实现令牌轮换
令牌生存周期应该根据安全需求进行限制
4.4.2.10 第三方鉴权流程
4.4.2.10.1 概览
MCP 服务器可以通过第三方鉴权服务器支持委托鉴权。在这个流程中，MCP 服务器既充当 OAuth 客户端(对于第三方身份验证服务器) ，又充当 OAuth 鉴权服务器 (对于 MCP 客户端)。

4.4.2.10.2 流程描述
第三方鉴权流程包括以下步骤：

MCP 客户端与 MCP 服务器初始化标准 OAuth 流程
MCP 服务器将用户请求重定向到第三方鉴权服务器
使用第三方服务器进行用户授权
第三方服务器使用鉴权重定向回 MCP 服务器
MCP 服务器为第三方访问令牌交换鉴权码
MCP 服务器生成自己绑定到第三方会话的访问令牌
MCP 服务器使用 MCP 客户端完成初始的 OAuth 流程
4.4.2.10.3 会话绑定要求
实现第三方授权的 MCP 服务器必须：

维护第三方令牌与已发布 MCP 令牌之间的安全映射
在承认 MCP 令牌之前验证第三方令牌的状态
实现适当的令牌生命周期管理
处理第三方令牌的过期和更新
Image

4.4.2.10.4 安全性考量
在实施第三方授权时，服务器必须：

验证所有重定向URI
安全地存储第三方凭据
实现适当的会话超时处理
考虑令牌链的安全性影响
为第三方身份鉴权失败实现正确的错误处理
4.4.3 最佳实践
4.4.3.1 本地客户端作为公共 OAuth 2.1 客户端
我们强烈建议本地客户端将 OAuth 2.1 作为公共客户端实现：

对鉴权请求使用PKCE以防止拦截攻击
实现适合本地系统的安全令牌存储
遵循令牌刷新的最佳实践来维护会话
正确处理令牌的过期和更新  
4.4.3.2 鉴权元数据的发现
我们强烈建议所有客户端都实现元数据发现。这减少了用户手动提供端点或客户端回退到预定义默认值的需要。

4.4.3.3 动态客户端注册
由于客户端事先不知道 MCP 服务器的集合，我们强烈建议实现动态客户端注册。这允许应用程序自动向 MCP 服务器注册，并消除了用户手动获取客户机 id 的需要。

4.5 实用程序
4.5.1 取消请求
模型上下文协议支持通过通知消息可选地取消正在进行的请求。任何一方都可以发送取消通知，表明以前发出的请求应该终止。

4.5.1.1 取消流程
当一方希望取消一个正在进行的请求时，它会发送一个 notifications/cancelled 通知，其中包括：

要取消的请求 ID
可以记录或显示可选的原因字符串
{
  "jsonrpc": "2.0",
  "method": "notifications/cancelled",
  "params": {
    "requestId": "123",
    "reason": "User requested cancellation"
  }
}
4.5.1.2 行为要求
取消通知必须只有请求：

先前已向同一方向发出
确信仍在进行中
客户端不能取消初始化请求

取消通知的接收方应该:

停止处理取消的请求
释放相关资源
不为取消的请求发送响应
接收方可以忽略取消通知，如果：

引用的请求未知
处理工作已经完成
请求无法取消
取消通知的发送方应该忽略对随后到达请求的任何响应

4.5.1.3 时机的考量
由于网络延迟，取消通知可能在请求处理完成之后到达，并且可能在响应已经发送之后到达。

双方都必须妥善处理这些竞争条件：


Image
4.5.1.4 实施说明
为了调试，双方都应该记录请求取消原因
应用程序的UI应该指示何时请求取消  ####4.5.1.5 错误处理
无效的取消通知应该被忽略：

未知的请求ID
已经处理完成的请求
格式错误的通知
这保持了通知的 “发送和忘记” 特性，同时允许异步通信中的竞态条件。

4.5.2 Ping
模型上下文协议包含一个可选的 ping 机制，允许任何一方验证对方是否仍然响应，以及连接是否存在。

4.5.2.1 概览
Ping 功能是通过简单的请求 / 响应模式实现的。客户端或服务器都可以通过发送 ping 请求来初始化一个 ping。

4.5.2.2 消息格式
Ping 请求是一个没有参数的标准 JSON-RPC 请求：

{
  "jsonrpc": "2.0",
  "id": "123",
  "method": "ping"
}
4.5.2.3 行为要求
接收方必须立即作出一个空响应：


{
"jsonrpc": "2.0",
"id": "123",
"result": {}
}

如果在合理的超时期限内没有收到响应，则发送方可以:

考虑连接是否过期
终止连接
尝试重新连接
4.5.2.4 使用模式
Image
4.5.2.5 实现的考量
实现应该周期性发出 ping 以检测连接的健康状况
Ping 的频率应该是可配置的
超时应适用于网络环境
应该避免过多的 ping 以减少网络开销

4.5.2.6 错误处理
超时应被视为连接失败

多个失败的 ping 可能触发连接复位

具体实现应该记录诊断失败的日志

4.5.3 进度
模型上下文协议支持以通知消息对长时间运行的操作执行可选的进度跟踪。任何一方都可以发送进度通知，以提供有关操作状态的更新。

4.5.3.1 进度流程
当一方希望接收请求的进度更新时，它会在请求元数据中包含 progressToken。

进度令牌必须是字符串或整数值
发送方可以使用任何方法选择进度令牌，但是在所有进行的请求中必须是唯一的。
        {
          "jsonrpc": "2.0",
          "id": 1,
          "method": "some_method",
          "params": {
            "_meta": {
              "progressToken": "abc123"
            }
          }
        }

然后，接收方可以发送进度通知，内容包括：

* 原始进度令牌
* 迄今为止的当前进度值
* 一个可选的 “total” 值
* 一个可选的 “message” 值

{
  "jsonrpc": "2.0",
  "method": "notifications/progress",
  "params": {
    "progressToken": "abc123",
    "progress": 50,
    "total": 100,
    "message": "Reticulating splines..."
  }
}
进度值必须随着每次通知而增加，即使总数是未知的。
进度值和总值可以是浮点数。
消息字段应该提供相关的人类可读的进度信息。  
 


4.5.3.2 行为要求


进度通知必须只引用以下令牌：

在主动请求中提供
与正在进行的操作关联
进度请求的接收方可以：

选择不发送任何进度通知
以他们认为合适的频率发送通知
如果未知，则省略总值
Image

4.5.3.3 实施指南
发送方和接收方应该跟踪活动的进度令牌
双方应实行限速，以防止通知泛滥
进度通知必须在完成后停止发送
5 客户端特性
5.1 根目录
模型上下文协议为客户端向服务器公开文件系统的 “根目录” 提供了一种标准化的方法。Root 定义了服务器可以在文件系统中操作的边界，允许服务器理解它们可以访问哪些目录和文件。服务器可以从支持的客户端中请求根目录的列表，并在该列表发生更改时接收通知。

5.1.1 用户交互模型
MCP 中的根通常通过工作区或项目配置接口公开。

例如，实现可以提供一个工作区 / 项目选择器，允许用户选择服务器应该访问的目录和文件。这可以与来自版本控制系统或项目文件的自动工作区检测相结合。

然而，具体实现可以自由地通过任何符合其需要的接口模式来公开“根”，协议本身并不要求任何特定的用户交互模型。

5.1.2 能力
支持根目录的客户端必须在初始化期间声明根目录的能力：

{
  "capabilities": {
    "roots": {
      "listChanged": true
    }
  }
}
listChanged 指示当根列表发生更改时，客户端是否发出通知。

5.1.3 协议消息
5.1.3.1 Listing Roots
为了检索根目录，服务器发送一个roots/list请求。

请求：

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "roots/list"
}
响应：

{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "roots": [
      {
        "uri": "file:///home/user/projects/myproject",
        "name": "My Project"
      }
    ]
  }
}
5.1.3.2 Root List 变更
当根发生变更时，支持 listChanged 的客户端必须发送一个通知。

{
        "jsonrpc": "2.0",
"method": "notifications/roots/list_changed"
}

5.1.4 消息流程
Image
5.1.5 数据类型
5.1.5.1 Root
根的定义包括：

URI: root 的唯一标识符，必须是当前规范中的文件：//URI。
名称：用于显示目的的人类可读名称(可选)。

不同用例的root示例：

项目目录
{
  "uri": "file:///home/user/projects/myproject",
  "name": "My Project"
}
多储存库
[
  {
    "uri": "file:///home/user/repos/frontend",
    "name": "Frontend Repository"
  },
  {
    "uri": "file:///home/user/repos/backend",
    "name": "Backend Repository"
  }
]
5.1.6 错误处理
对于常见的失败情况，客户端应该返回标准的 JSON-RPC 错误：

客户端不支持 root:-32601 (未找到方法)
内部错误：-32603
错误示例：

{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Roots not supported",
    "data": {
      "reason": "Client does not have roots capability"
    }
  }
}
5.1.7 安全事宜
1. 客户端必须：

仅暴露具有适当权限的根
验证所有 root URI 以防止路径遍历
实现正确的访问控制
监控 root 的可访问性
2. 服务器应该：

处理根不可用的情况
在操作过程中遵守根的范围边界
根据提供的根验证所有路径
5.1.8 实施指南
客户端应该：

在将 root 暴露给服务器之前提示用户同意
为 root 管理提供清晰的用户界面
在暴露之前验证 root 的可访问性
监控 root 变更
服务器应该：

使用前请检查 root 功能
优雅地处理根列表变更
在操作中遵守根的边界
适当缓存根信息
5.2 采样
模型上下文协议为服务器通过客户端从语言模型请求 LLM 采样 (“补全” 或 “代替”) 提供了一种标准化的方法。此流程允许客户端维护对模型访问、选择和权限的控制，同时允许服务器利用 AI 功能ーー不需要服务器 API 密钥。服务器可以请求基于文本、音频或图像的交互，还可以在提示词中包含来自 MCP 服务器的上下文。

5.2.1 用户交互模型
MCP 中的采样允许服务器实现智能体行为，允许 LLM 调用嵌套在其他 MCP 服务器的功能。

具体实现可以自由地通过任何适合其需要的接口模式公开采样，协议本身并不要求任何特定的用户交互模型。

为了信任、保密和安全性，应该总是有一个人工行为在循环中有能力拒绝采样请求。

应用应该：

提供用户界面，使其更容易和直观地审查采样请求
允许用户在发送之前查看和编辑提示词
提供生成的响应，以便在交付前进行审查  ###5.2.2 能力
支持采样的客户端必须在初始化期间声明采样能力：

{
  "capabilities": {
    "sampling": {}
  }
}
5.2.3 协议消息
5.2.3.1 创建消息
为了请求语言模型的一个生成结果，服务器发送一个sampling/createMessage 请求：

请求：

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "sampling/createMessage",
  "params": {
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "What is the capital of France?"
        }
      }
    ],
    "modelPreferences": {
      "hints": [
        {
          "name": "claude-3-sonnet"
        }
      ],
      "intelligencePriority": 0.8,
      "speedPriority": 0.5
    },
    "systemPrompt": "You are a helpful assistant.",
    "maxTokens": 100
  }
}
响应：

{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "role": "assistant",
    "content": {
      "type": "text",
      "text": "The capital of France is Paris."
    },
    "model": "claude-3-sonnet-20240307",
    "stopReason": "endTurn"
  }
}
5.2.4 消息流程
Image
5.2.5 数据类型
5.2.5.1 消息
采样信息可以包含：

文字内容
{
  "type": "text",
  "text": "The message content"
}
图片内容
{
  "type": "image",
  "data": "base64-encoded-image-data",
  "mimeType": "image/jpeg"
}
音频内容
{
  "type": "audio",
  "data": "base64-encoded-audio-data",
  "mimeType": "audio/wav"
}
5.2.6 模型偏好设置
MCP 中的模型选择需要仔细的抽象，因为服务器和客户端可能使用不同的 AI 提供者提供不同的模型。服务器不能简单地通过名称请求特定的模型，因为客户端可能无法访问该确切的模型，或者可能更喜欢使用不同提供者的等价模型。

为了解决这个问题，MCP 实现了一个偏好设置系统，将抽象的能力优先级与可选的模型引导结合起来。

5.2.6.1 能力优先级
服务器通过三个规范化的优先级值 (0-1) 来表达它们的需求：

成本优先： 最小化成本的重要程度？ 更高的值倾向于更便宜的模型。
速度优先: 低延迟的重要程度？ 更高的值倾向于更快的模型。
智能优先: 智能的程度？ 更高的值倾向于更有能力的模型。
5.2.6.2 模型引导
虽然优先级有助于根据特征选择模型，但引导允许服务器建议特定的模型或模型家族：

引导被视为可以灵活匹配模型名称的子字符串
按偏好顺序计算多个引导词
客户端可以将引导词映射到来自不同提供者的等效模型
提示是建议性的ーー最终由客户端选择模型
例如：

{
  "hints": [
    { "name": "claude-3-sonnet" }, // Prefer Sonnet-class models
    { "name": "claude" } // Fall back to any Claude model
  ],
  "costPriority": 0.3, // Cost is less important
  "speedPriority": 0.8, // Speed is very important
  "intelligencePriority": 0.5 // Moderate capability needs
}
客户端处理这些偏好项以从其可用选项中选择适当的模型。例如，如果客户端没有访问 Claude 模型，但有 Gemini，它可能会基于类似的功能将sonnet引导映射到 Gemini-1.5-pro。

5.2.7 错误处理
对于常见的故障情况，客户端应该返回错误：

错误示例：

{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -1,
    "message": "User rejected sampling request"
  }
}
5.2.7 安全事宜
客户端应实现用户审批控制
双方都应该验证消息内容
客户端应该遵循模型的偏好引导
客户端应实施速率限制
双方必须适当地处理敏感数据
6. 服务器特性
6.1 概览
服务器提供了通过 MCP 向语言模型添加上下文的基本构建块。这些原语支持客户端、服务器和语言模型之间的丰富交互：

提示词： 指导语言模型交互的预定义模板或指令
资源： 为模型提供附加上下文的结构化数据或内容
工具： 允许模型执行操作或检索信息的可执行函数
每个原语可以归纳为以下的控制层次结构：


原语
管制
描述
例子

提示词

用户控制

由用户选择调用的交互式模板

斜杠命令，菜单选项

资源

应用控制

由客户端附加和管理的上下文数据

文件内容，git 历史

工具
模型控制

公开给 LLM 以执行操作的函数

API POST 请求，文件写入
以下更详细地探讨这些关键原语：提示词、资源和工具。

6.2 提示词
模型上下文协议 (Model Context Protocol，MCP) 为服务器向客户机公开提示模板提供了一种标准化的方法。提示允许服务器提供与语言模型交互的结构化消息和指令。客户机可以发现可用的提示，检索它们的内容，并提供参数来定制它们。

6.2.1 用户交互模型
提示词被设计为由用户控制，这意味着它们从服务器公开给客户端，用户可以显式地选择它们来使用。

通常，提示词将通过用户界面中由用户发起的命令触发，这允许用户自然地发现和调用可用的提示次。例如，作为斜杠命令。

然而，实现者可以自由地通过任何适合他们需要的接口模式公开提示词ーー协议本身并不要求任何特定的用户交互模型。

6.2.2 能力
支持提示词的服务器必须在初始化期间声明提示词功能：

{
  "capabilities": {
    "prompts": {
      "listChanged": true
    }
  }
}
listChanged 指示了当可用提示词列表发生更改时，服务器是否发出通知。

6.2.3 协议消息
6.2.3.1 对提示词进行检索
为了检索可用的提示词，客户端发送一个 prompts/list请求。此操作支持分页。

请求：

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "prompts/list",
  "params": {
    "cursor": "optional-cursor-value"
  }
}
响应：

{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "prompts": [
      {
        "name": "code_review",
        "description": "Asks the LLM to analyze code quality and suggest improvements",
        "arguments": [
          {
            "name": "code",
            "description": "The code to review",
            "required": true
          }
        ]
      }
    ],
    "nextCursor": "next-page-cursor"
  }
}


6.2.3.2 获得提示词
为了检索特定的提示词，客户端发送一个prompts/get请求。参数可以通过完整的API 自动完成。

请求：

{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "prompts/get",
  "params": {
    "name": "code_review",
    "arguments": {
      "code": "def hello():\n    print('world')"
    }
  }
}
响应：

{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "description": "Code review prompt",
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "Please review this Python code:\ndef hello():\n    print('world')"
        }
      }
    ]
  }
}
6.2.3.3 变更通知
当可用提示词列表发生更改时，声明 listChanged 能力的服务器应发送通知：

{
  "jsonrpc": "2.0",
  "method": "notifications/prompts/list_changed"
}
6.2.4 消息流
Image
6.2.5 数据类型
6.2.5.1 提示词
一个提示词的定义包括：

名称：提示词的唯一标识符
说明：可选的人类可读说明
参数：可选的自定义参数列表  ####6.2.5.2 提示词消息
一个提示词中的消息可以包含：

角色：指代说话者是 “用户” 或 “助手”
内容：以下内容类型之一：

文字内容
文本内容表示纯文本消息：

{
  "type": "text",
  "text": "The text content of the message"
}
这是用于自然语言交互的最常见内容类型。

图片内容
图像内容允许在消息中包含视觉信息：

{
  "type": "image",
  "data": "base64-encoded-image-data",
  "mimeType": "image/png"
}
图像数据必须是 base64 编码，并且包含有效的 MIME 类型。这使得多模态交互在视觉上下文很重要的地方成为可能。

音频内容
音频内容允许在消息中包含音频信息：

{
  "type": "audio",
  "data": "base64-encoded-audio-data",
  "mimeType": "audio/wav"
}
音频数据必须是 base64 编码，并且包含有效的 MIME 类型。这使得在音频上下文很重要的情况下进行多模态交互成为可能。

嵌入式资源
嵌入式资源允许在消息中直接引用服务器端资源：

{
  "type": "resource",
  "resource": {
    "uri": "resource://example",
    "mimeType": "text/plain",
    "text": "Resource content"
  }
}
资源可以包含文本或二进制 (blob) 数据，必须包括：

有效的资源 URI
适当的 MIME 类型
文本内容或 base64 编码的 blob 数据
嵌入式资源允许提示词将服务器管理的内容 (如文档、代码示例或其他参考资料) 无缝地直接合并到会话流中。

6.2.6 错误处理
对于常见的故障情况，服务器应该返回标准的 JSON-RPC 错误：

无效提示词名称：-32602 (Invalid params)
缺少所需参数： -32602 (Invalid params)
内部错误： -32603 (Internal error)

6.2.7 实施考虑
服务器在处理前验证提示参数
客户端应该处理大型提示词列表的分页
双方应该遵循能力协商 
6.2.8 安全性
具体实现必须仔细验证所有提示词的输入和输出，以防止注入攻击或未经授权的资源访问。

6.3 资源
模型上下文协议为服务器向客户端公开资源提供了一种标准化的方法。资源允许服务器共享为语言模型提供上下文的数据，例如文件、数据库模式或特定于应用程序的信息。每个资源都由一个 URI 唯一标识。

6.3.1 用户交互模型
MCP 中的资源被设计为由应用程序所驱动，由主机应用程序根据自己的需要确定如何合并上下文。

例如，应用程序可以：

在树视图或列表视图中，通过 UI 元素公开资源以进行显式选择
允许用户搜索和筛选可用资源
基于启发式或人工智能模型的选择。实现自动上下文包含
然而，具体实现可以通过任何适合其需要的接口模式自由地公开资源ーー协议本身并不强制任何特定的用户交互模型。

6.3.3 能力
支持资源的服务器必须声明资源能力：

{
  "capabilities": {
    "resources": {
      "subscribe": true,
      "listChanged": true
    }
  }
}
该能力支持两个可选特性：

Subscribe： 客户端是否可以订阅以获得单个资源更改的通知。
listChanged: 当可用资源列表发生更改时，服务器是否发出通知。
Subscribe 和 listChanged 都是可选的ーー服务器可以不支持它们，也可以支持它们中的一个，或者两者都支持：

{
  "capabilities": {
    "resources": {} // Neither feature supported
  }
}


{
  "capabilities": {
    "resources": {
      "subscribe": true // Only subscriptions supported
    }
  }
}


{
  "capabilities": {
    "resources": {
      "listChanged": true // Only list change notifications supported
    }
  }
}
6.3.4 协议消息
6.3.4.1 资源的检索
为了发现可用的资源，客户端发送一个resources/list请求。此操作支持分页。

请求：

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list",
  "params": {
    "cursor": "optional-cursor-value"
  }
}
响应：

{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resources": [
      {
        "uri": "file:///project/src/main.rs",
        "name": "main.rs",
        "description": "Primary application entry point",
        "mimeType": "text/x-rust"
      }
    ],
    "nextCursor": "next-page-cursor"
  }
}
6.3.4.2 读取资源
为了检索资源内容，客户端发送一个resources/read 请求。

请求：

{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/read",
  "params": {
    "uri": "file:///project/src/main.rs"
  }
}
响应：

{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "contents": [
      {
        "uri": "file:///project/src/main.rs",
        "mimeType": "text/x-rust",
        "text": "fn main() {\n    println!(\"Hello world!\");\n}"
      }
    ]
  }
}
6.3.4.3 资源模板
资源模板允许服务器使用 URI 模板公开参数化的资源。参数可以通过 API 自动补全。

请求：

{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/templates/list"
}
响应：

{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "resourceTemplates": [
      {
        "uriTemplate": "file:///{path}",
        "name": "Project Files",
        "description": "Access files in the project directory",
        "mimeType": "application/octet-stream"
      }
    ]
  }
}
6.3.4.4 名单更改通知
当可用资源列表发生更改时，声明 listChanged 功能的服务器应发送通知。

{
  "jsonrpc": "2.0",
  "method": "notifications/resources/list_changed"
}
6.3.4.5 订阅
该协议支持对资源更改的可选订阅。客户端可以订阅特定的资源，并在资源更改时接收通知。

订阅请求：

{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/subscribe",
  "params": {
    "uri": "file:///project/src/main.rs"
  }
}
更新通知：

{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "file:///project/src/main.rs"
  }
}
6.3.5 消息流程
Image
6.3.6 数据类型
6.3.6.1 资源
一个资源定义包括：

Uri: 资源的唯一标识符
名称：人类可读的名称
描述： 可选的描述
mimeType: 可选的 MIME 类型
Size: 可选的大小 (字节)  ####6.3.6.2 资源内容
资源可以包含文本数据或二进制数据：

文字内容
{
  "uri": "file:///example.txt",
  "mimeType": "text/plain",
  "text": "Resource content"
}
二进制内容
{
  "uri": "file:///example.png",
  "mimeType": "image/png",
  "blob": "base64-encoded-data"
}
6.3.6.3 常见的 URI 方案
该协议定义了几个标准的 URI 模式。这个列表并不详尽，具体实现总是可以自由地使用额外的、自定义的 URI 模式。

https://
用于表示 web 上可用的资源。

只有当客户端能够自己直接从 web 获取和加载资源时，服务器才应该使用这种方案ーー也就是说，它不需要通过 MCP 服务器读取资源。

对于其他用例，服务器应该优先使用另一个 URI 方案，或者定义一个自定义 URI 方案，即使服务器本身将通过 internet 下载资源内容。

file://
用于标识行为类似于文件系统的资源。但是，资源不需要映射到实际的物理文件系统。

MCP 服务器可以使用 XDG MIME 类型标识 file:// 资源，比如 inode/directory，来表示没有标准 MIME 类型的非常规文件 (比如目录)。

git://
Git 版本控制集成。

6.3.7 错误处理
对于常见的故障情况，服务器应该返回标准的 JSON-RPC 错误：

未找到资源：-32002
内部错误：-32603
错误示例：

{
  "jsonrpc": "2.0",
  "id": 5,
  "error": {
    "code": -32002,
    "message": "Resource not found",
    "data": {
      "uri": "file:///nonexistent.txt"
    }
  }
}


6.3.8 安全事宜
服务器必须验证所有资源的URI
应对敏感资源实施访问控制
二进制数据必须正确编码
操作前应检查资源权限
6.4 工具
模型上下文协议允许服务器公开可由语言模型调用的工具。工具使模型能够与外部系统交互，例如查询数据库、调用 api 或执行计算。每个工具都由名称唯一标识，并包含描述其模式的元数据。

6.4.1 用户交互模型
MCP 中的工具被设计为由模型控制，这意味着语言模型可以根据其上下文理解和用户的提示词自动发现和调用工具。

然而，具体实现可以通过任何适合其需要的接口模式自由地公开工具ーー协议本身并不强制要求任何特定的用户交互模型。

为了信任、保密和安全性，在循环中应该始终有一个人工操控有能力拒绝工具调用。

应用应该：

提供用户界面，清楚地说明哪些工具将公开给 AI 模型
在调用工具时插入清晰的可视化指示词
确认当前提示给用户进行操作，以确保有人可以在操作循环中  ### 6.4.2 能力
支持工具的服务器必须声明工具能力：

{
  "capabilities": {
    "tools": {
      "listChanged": true
    }
  }
}
listChanged 指示当可用工具列表发生更改时，服务器是否发出通知。

6.4.3 协议消息
6.4.3.1 对工具的检索
为了发现可用的工具，客户端发送一个tools/list请求。这个操作支持分页。

请求：

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {
    "cursor": "optional-cursor-value"
  }
}
响应：

{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_weather",
        "description": "Get current weather information for a location",
        "inputSchema": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "City name or zip code"
            }
          },
          "required": ["location"]
        }
      }
    ],
    "nextCursor": "next-page-cursor"
  }
}


6.4.3.2 调用工具
要调用工具，客户端发送一个tools/call请求：

请求：

{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {
      "location": "New York"
    }
  }
}
响应：

{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Current weather in New York:\nTemperature: 72°F\nConditions: Partly cloudy"
      }
    ],
    "isError": false
  }
}
6.4.3.3 更改通知
当可用工具列表发生更改时，声明 listChanged 功能的服务器应该发送一个通知：

{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
6.4.4 消息流程
Image
6.4.5 数据类型
6.4.5.1 工具
一个工具定义包括：

名字： 工具唯一标识符
描述： 人类可读的功能描述
inputSchema: 定义预期参数的 json schema
注释： 描述工具行为的可选属性
为了信任、保密和安全性，客户端必须认为工具注释是不可信的，除非它们来自受信任的服务器。

6.4.5.2 工具结果
工具结果可以包含不同类型的多个内容项：

文本内容
{
  "type": "text",
  "text": "Tool result text"
}
图片内容
{
  "type": "image",
  "data": "base64-encoded-data",
  "mimeType": "image/png"
}
音频内容
{
  "type": "audio",
  "data": "base64-encoded-audio-data",
  "mimeType": "audio/wav"
}
嵌入式资源
可以将资源嵌入到 URI 后面，以提供额外的上下文或数据，客户端以后可以订阅或再次获取这些 URI:

{
  "type": "resource",
  "resource": {
    "uri": "resource://example",
    "mimeType": "text/plain",
    "text": "Resource content"
  }
}
6.4.6 错误处理
工具使用两种错误报告机制。

6.4.6.1 协议错误
协议错误是 标准的 JSON-RPC 错误，例如：

Unknown tools：未知工具
Invalid arguments：无效的参数
Server errors：服务器错误
协议错误示例：

{
  "jsonrpc": "2.0",
  "id": 3,
  "error": {
    "code": -32602,
    "message": "Unknown tool: invalid_tool_name"
  }
}
6.4.6.2 工具执行错误
工具执行错误在工具结果中使用 isError: true 报告：

API failures：API 失败
Invalid input data：无效的输入数据
Business logic errors：业务逻辑错误
工具执行错误示例：

{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Failed to fetch weather data: API rate limit exceeded"
      }
    ],
    "isError": true
  }
}
6.4.7 安全事宜
1. 服务器必须：
验证所有的工具输入
实施适当的访问控制
工具调用的速率限制
清理工具输出
2 客户端应该：
提示用户确认敏感操作
在调用服务器之前向用户显示工具输入，以避免恶意或意外的数据溢出
在传递给 LLM 之前验证工具结果
实现工具调用的超时
为审计目的记录工具的使用情况
6.5 实用程序
6.5.1 补全
模型上下文协议为服务器提供了一种标准化的方法，用于为提示词和资源 uri 提供参数的自动补全建议。这使得用户可以在输入参数值时接收上下文建议，从而获得丰富的类 ide 体验。

6.5.1.1 用户交互模型
MCP 中的补全设计用于支持类似于 IDE 代码补全的交互式用户体验。

例如，当用户输入时，应用程序可以在下拉菜单或弹出菜单中显示补全建议，并具有从可用选项中进行筛选和选择的能力。

然而，具体实现可以自由地通过任何适合其需要的接口模式公开补全的能力，协议本身并不要求任何特定的用户交互模型。

6.5.1.2 能力
支持补全的服务器必须声明补全的能力：

{
  "capabilities": {
    "completions": {}
  }
}


6.5.1.3 协议消息
补全的请求
为了获得全建议，客户端通过参考类型发送一个completion/complete 请求，并指定正在完成的内容。

请求：

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "completion/complete",
  "params": {
    "ref": {
      "type": "ref/prompt",
      "name": "code_review"
    },
    "argument": {
      "name": "language",
      "value": "py"
    }
  }
}
响应：

{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "completion": {
      "values": ["python", "pytorch", "pyside"],
      "total": 10,
      "hasMore": true
    }
  }
}
参考类型
该协议支持两种类型的补全：


类别
描述
例子
ref/prompt

通过名称的参考提示词
{"type": "ref/prompt", "name": "code_review"}
ref/resource

参考资源 URI
{"type": "ref/resource", "uri": "file:///{path}"}


完成结果
服务器返回一个按相关性排序的补全值的数组，其中包括：

每次回复最多 100 个项
可选的可用匹配项总数
指示是否存在其他结果的布尔值

6.5.1.4 消息流程
Image
6.5.1.5 数据类型
CompleteRequest
ref: 一个PromptReference 或 ResourceReference

argument: 对象包含

Name: 参数名称
Value: 当前值  

CompleteResult
completion: 对象包含

values: 建议数组 (最大值 100)
total: 可选的匹配总数
hasMore: 附加结果标志  
6.5.1.6 错误处理
错误处理 对于常见的故障情况，服务器应该返回标准的 JSON-RPC 错误：
未找到方法：-32601 (Capability not supported)

无效提示词名称：-32602 (Invalid params)

缺少必需的参数：-32602 (Invalid params)

内部错误： -32603 (Internal error)-32603 

6.5.1.7 实施考虑
服务器应该：
——按相关性排序返回建议
——在适当的地方实现模糊匹配
——补全请求速率限制
——验证所有输入

2. 客户端应该：

能够快速取消补全请求
在适当的地方缓存补全结果
优雅地处理缺失或部分结果

6.5.1.8 安全性
具体实施必须:

验证所有补全输入

实施适当的速率限制

控制对敏感建议的访问

防止基于补全的信息披露

6.5.2 日志
模型上下文协议为服务器向客户端发送结构化日志消息提供了一种标准化方法。客户端可以通过设置最低日志级别来控制日志记录的详细程度，服务器发送包含严重级别、可选日志名称和任意可序列化 json 数据的通知。

6.5.2.1 用户交互模型
具体实现可以自由地通过任何符合其需要的接口模式公开日志记录，协议本身并不要求任何特定的用户交互模型。

6.5.2.2 能力
发出日志消息通知的服务器必须声明日志记录能力：

{
  "capabilities": {
    "logging": {}
  }
}
6.5.2.3 日志级别
该协议遵循 RFC 5424 规定的标准 syslog 的日志严重级别：


日志级别
描述
示例

debug

详细的调试信息

函数入口 / 出口点

info

一般信息
操作进度更新

notice

正常但重要的事件

配置变更

warning
警告条件

不推荐的特性使用

error
错误条件
操作故障
critical
临界条件

系统组件故障

alert

必须立即采取行动

检测到数据损坏
emergency
系统无法使用
补全系统发生故障

6.5.2.4 协议消息
设置日志级别
要配置最低日志级别，客户端可以发送一个logging/setLevel 请求 。

请求：

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "logging/setLevel",
  "params": {
    "level": "info"
  }
}


日志消息通知
服务器使用notifications/message发送日志消息：

{
  "jsonrpc": "2.0",
  "method": "notifications/message",
  "params": {
    "level": "error",
    "logger": "database",
    "data": {
      "error": "Connection failed",
      "details": {
        "host": "localhost",
        "port": 5432
      }
    }
  }
}


6.5.2.5 消息流程
Image
6.5.2.6 错误处理
对于常见的故障情况，服务器应该返回标准的 JSON-RPC 错误：

无效日志级别：-32602 (Invalid params)
配置错误：-32603 (Internal error)  #### 6.5.2.7 实施考虑
1. 服务器应该：
日志消息的速率限制
在数据字段中包含相关上下文
使用一致的日志记录名称
删除敏感信息
2.客户可以：
在 UI 中显示日志消息
实现日志过滤 / 搜索
直观地显示严重程度
持久化日志消息
6.5.2.8 安全性
1. 日志消息不能包含：
证书或密钥
个人身份信息
可能被攻击的内部系统细节
2. 具体实现应该：
速率限制信息
验证所有数据字段
控制日志访问
监视敏感内容
6.5.3 分页
模型上下文协议支持可能返回大型结果集的分页列表操作。分页能够允许服务器以更小的块产生结果，而不是一次产生所有结果。

当通过互联网连接到外部服务时，分页尤其重要，而且对于本地集成也很有用，可以避免大型数据集的性能问题。

6.5.3.1 分页模型
MCP 中的分页使用不透明的基于游标的方法，而不是编号页。

游标是不透明的字符串标记，表示结果集中的位置
页面大小由服务器决定，客户端不能采用固定的页面大小  #### 6.5.3.2 响应格式
当服务器发送包含以下内容的响应时，开始分页：

结果的当前页
如果存在更多结果，则为可选的 nextCursor 字段

{
"jsonrpc": "2.0",
"id": "123",
"result": {
"resources": [...],
"nextCursor": "eyJwYWdlIjogM30="
}
}

6.5.3.3 请求格式
接收到游标后，客户端可以通过发出包括该游标在内的请求来继续分页：

{
  "jsonrpc": "2.0",
  "method": "resources/list",
  "params": {
    "cursor": "eyJwYWdlIjogMn0="
  }
}
6.5.3.4 分页流程
Image

6.5.3.5 支持分页的操作
下列 MCP 操作支持分页：

Resources/List - 列出可用的资源
Resources/templates/List - 列出资源模板
prompts/list - 列出可用的提示词
tools/list - 列出可用的工具 
6.5.3.5 实施指引
1. 服务器应该：
提供稳定的游标
优雅地处理无效游标
2. 客户应该
将缺少的 nextCursor 视为结果的末尾
支持分页和非分页的流
3. 客户端必须将游标视为不透明的令牌：
不要对游标的格式做任何假设
不要尝试解析或修改游标
不要跨会话持久化游标  #### 6.5.3.7 错误处理 无效的游标应导致代码 -32602 错误 (Invalid params).。
7. 资源
7.1 版本控制
模型上下文协议使用符合 YYYY-MM-DD 格式的基于字符串的版本标识符，以指示向后不兼容更改的最后日期。

协议版本不会在协议更新时增加，只需更改保持向后兼容。这允许在保持互操作性的同时进行增量改进。

7.1.1 修订版
修订内容可标示如下：

Draft: 进行中的规范，尚未准备好应用。
Current: 当前协议版本，已准备好使用，并可能继续接收向后兼容的更改。
Final: 过去，完整的规范将不会改变。
Current协议版本是 2025-03-26。

7.1.2 协商
版本协商发生在初始化过程中。客户端和服务器可以同时支持多个协议版本，但是它们必须同意在会话中使用一个版本。

如果版本协商失败，该协议提供适当的错误处理，允许客户端在找不到与服务器兼容的版本时正常地终止连接。

7.2 社区贡献
参见github。





【参考资料与关联阅读】

https://modelcontextprotocol.io/specification/2025-03-26

大模型应用系列：两万字解读MCP

拆解OpenAI最大对手的杀手锏：为什么会是MCP？

智能体间协作的"巴别塔困境"如何破解？解读Agent通信4大协议：MCP/ACP/A2A/ANP

大模型应用系列：两万字解读MCP

大模型应用的10种架构模式

7B？13B？175B？解读大模型的参数

大模型应用系列：从Ranking到Reranking

大模型应用系列：Query 变换的示例浅析

从零构建大模型之Transformer公式解读

如何选择Embedding Model？关于嵌入模型的10个思考

解读文本嵌入：语义表达的练习

解读知识图谱的自动构建

“提示工程”的技术分类

大模型系列：提示词管理

提示工程中的10个设计模式

解读：基于图的大模型提示技术

大模型微调：RHLF与DPO浅析

Chunking：基于大模型RAG系统中的文档分块

大模型应用框架：LangChain与LlamaIndex的对比选择

解读大模型应用的可观测性

大模型系列之解读MoE

在大模型RAG系统中应用知识图谱

面向知识图谱的大模型应用

让知识图谱成为大模型的伴侣

如何构建基于大模型的App
Qcon2023: 大模型时代的技术人成长（简）

论文学习笔记：增强学习应用于OS调度

《深入浅出Embedding》随笔

LLM的工程实践思考

大模型应用设计的10个思考

基于大模型（LLM）的Agent 应用开发

解读大模型的微调

解读向量数据库

解读向量索引

解读ChatGPT中的RLHF

解读大模型（LLM）的token

解读提示词工程（Prompt Engineering）

解读Toolformer

解读TaskMatrix.AI

解读LangChain

解读LoRA

解读RAG

大模型应用框架之Semantic Kernel

浅析多模态机器学习

大模型应用于数字人

深度学习架构的对比分析

老码农眼中的大模型（LLM）

