# Nacos MCP Router TypeScript ![NPM Version](https://img.shields.io/npm/v/nacos-mcp-router) ![NPM Downloads](https://img.shields.io/npm/d18m/nacos-mcp-router)

[English](./README.md) | 中文

基于 TypeScript 实现的 Nacos MCP Router，连接 Nacos 服务发现与模型上下文协议（MCP），为 AI 应用程序提供智能服务编排和工具调用能力。

## 概述

Nacos MCP Router TypeScript 是一个复杂的路由层，它将 Nacos 服务注册中心与兼容 MCP 的 AI 代理集成。提供智能服务发现、动态工具注册和自动化工作流编排能力。

### 核心能力

- **动态服务发现**：通过 Nacos 自动发现和注册 MCP 服务
- **智能路由**：基于服务能力和负载的智能请求路由
- **工具编排**：AI 代理与微服务之间的无缝集成
- **配置管理**：通过 Nacos 进行集中配置管理
- **实时监控**：服务健康监控和性能指标

## 架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI 代理       │    │  Nacos MCP       │    │   Nacos         │
│   (Claude,      │◄──►│  Router          │◄──►│   服务器        │
│   Cline, 等)    │    │  TypeScript      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   MCP 服务       │
                       │   (工具和资源)    │
                       └──────────────────┘
```

## 功能特性

- **Nacos 集成**：完整的 Nacos 集成，支持服务注册、发现和配置管理
- **MCP 协议支持**：完整的模型上下文协议实现，用于 AI 代理通信
- **服务编排**：基于能力的智能服务发现和路由
- **工具管理**：动态工具注册、发现和调用
- **健康监控**：实时服务健康检查和监控
- **负载均衡**：跨服务实例的智能请求分发
- **配置热重载**：无需服务重启的动态配置更新

## 前置要求

- Node.js 16+ 
- Nacos Server 3.0+
- TypeScript 4.5+

## 快速开始

### 安装

```bash
npm install nacos-mcp-router
# 或
yarn add nacos-mcp-router
```

### 基本用法

1. **配置环境变量**

```bash
export NACOS_SERVER_ADDR=localhost:8848
export NACOS_USERNAME=nacos
export NACOS_PASSWORD=nacos
export NACOS_NAMESPACE=public
```

2. **MCP 服务器配置**

在你的 MCP 客户端配置中添加：

```json
{
  "mcpServers": {
    "nacos-mcp-router": {
      "command": "npx",
      "args": ["nacos-mcp-router@latest"],
      "env": {
        "NACOS_SERVER_ADDR": "localhost:8848",
        "NACOS_USERNAME": "nacos", 
        "NACOS_PASSWORD": "nacos",
        "NACOS_NAMESPACE": "public"
      }
    }
  }
}
```

3. **程序化使用**

```typescript
import { NacosMcpRouter } from 'nacos-mcp-router';

const router = new NacosMcpRouter({
  nacos: {
    serverAddr: 'localhost:8848',
    username: 'nacos',
    password: 'nacospassword',
  },
  logLevel: 'info'
});

await router.start();
```

## 配置

### 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `NACOS_SERVER_ADDR` | Nacos 服务器地址 | `localhost:8848` |
| `NACOS_USERNAME` | Nacos 用户名 | `nacos` |
| `NACOS_PASSWORD` | Nacos 密码 | `nacos` |
| `NACOS_NAMESPACE` | Nacos 命名空间 | `public` |
| `NACOS_GROUP` | 服务组 | `DEFAULT_GROUP` |
| `LOG_LEVEL` | 日志级别 | `info` |
| `MCP_PORT` | MCP 服务器端口 | `3000` |

### 配置文件

创建 `nacos-mcp-config.json` 文件：

```json
{
  "nacos": {
    "serverAddr": "localhost:8848",
    "username": "nacos",
    "password": "nacos",
    "namespace": "public",
    "group": "MCP_GROUP"
  },
  "mode": "stdio",
  "port": 3000,
  "logLevel": "info"
}
```

## 可用工具

### 服务发现工具

#### SearchMcpServer
基于能力和需求发现 MCP 服务。

```typescript
// 参数
{
  "task_description": "string",  // 任务描述
  "keywords": "string[]",        // 搜索关键词（可选）
  "capabilities": "string[]"     // 所需能力（可选）
}
```

#### ListMcpServers
列出所有可用的 MCP 服务。

```typescript
// 返回值
{
  "services": [
    {
      "name": "string",
      "description": "string", 
      "capabilities": "string[]",
      "status": "string",
      "instances": "number"
    }
  ]
}
```

### 服务管理工具

#### AddMcpServer
注册新的 MCP 服务。

```typescript
// 参数
{
  "name": "string",           // 服务名称
  "url": "string",            // 服务 URL
  "description": "string",    // 服务描述
  "capabilities": "string[]", // 服务能力
  "metadata": "object"        // 附加元数据（可选）
}
```

#### RemoveMcpServer
注销 MCP 服务。

```typescript
// 参数
{
  "name": "string"  // 服务名称
}
```

### 工具执行

#### UseTool
在注册的 MCP 服务上执行工具。

```typescript
// 参数
{
  "server_name": "string",    // 目标服务器名称
  "tool_name": "string",      // 工具名称
  "arguments": "object",      // 工具参数
  "timeout": "number"         // 超时时间（秒，可选）
}
```

## 使用场景

### 1. AI 代理服务发现

```typescript
// AI 代理搜索数据库服务
const dbServices = await router.searchMcpServer({
  task_description: "我需要从数据库查询客户数据",
  keywords: ["database", "sql", "customer"],
  capabilities: ["query", "read"]
});
```

### 2. 动态工具注册

```typescript
// 将新的微服务注册为 MCP 工具
await router.addMcpServer({
  name: "payment-service",
  url: "http://payment-service:8080/mcp",
  description: "支付处理服务",
  capabilities: ["payment", "transaction", "refund"],
  metadata: {
    version: "1.0.0",
    team: "finance"
  }
});
```

### 3. 跨服务编排

```typescript
// AI 代理编排多个服务
const orderResult = await router.useTool({
  server_name: "order-service",
  tool_name: "create_order",
  arguments: { customerId: 123, items: [...] }
});

const paymentResult = await router.useTool({
  server_name: "payment-service", 
  tool_name: "process_payment",
  arguments: { orderId: orderResult.orderId, amount: orderResult.total }
});
```

## 开发

### 项目结构

```
src/
├── index.ts                # 应用入口点
├── router.ts               # MCP 路由和工具注册
├── nacos_http_client.ts    # Nacos HTTP 客户端
├── mcp_manager.ts          # MCP 服务管理
├── router_types.ts         # 类型定义和工具
└── logger.ts               # 日志模块
test/                       # 测试用例
example/
└── simpleSseServer.ts      # 简单 SSE 服务器实现
```

### 构建和测试

```bash
# 安装依赖
npm install

# 构建
npm run build

# 测试
npm test

# 开发模式
npm run dev

# 代码检查
npm run lint

# 类型检查
npm run type-check
```

### Docker 支持

[Dockerfile](./Dockerfile)

## 监控和可观察性

### 健康检查

路由器提供健康检查端点：

- `GET /health` - 基本健康状态
- `GET /health/detailed` - 详细健康信息
- `GET /metrics` - Prometheus 指标

### 日志

结构化日志，支持可配置级别：

```typescript
import { logger } from './utils/logger';

logger.info('服务已注册', { 
  serviceName: 'payment-service',
  instances: 3 
});
```

### 指标

内置指标收集：

- 请求计数和延迟
- 服务发现性能
- 工具执行统计
- 错误率和类型

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解指南。

### 开发设置

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 添加测试
5. 提交拉取请求

## 许可证

Apache License 2.0

## 相关项目

- [Nacos MCP Router (Python)](https://github.com/nacos-group/nacos-mcp-router) - 原始 Python 实现
- [Nacos](https://nacos.io/) - 动态命名和配置服务
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 规范

## 支持

- [文档](https://nacos.io/docs/)
- [问题](https://github.com/nacos-group/nacos-mcp-router-typescript/issues)
- [讨论](https://github.com/nacos-group/nacos-mcp-router-typescript/discussions)
