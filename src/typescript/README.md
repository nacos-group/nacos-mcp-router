# nacos-mcp-router-typescript

## 项目简介

`nacos-mcp-router-typescript` 是基于 TypeScript 实现的 Nacos MCP Router。它用于对接 Nacos 配置中心，实现多模型上下文协议（MCP）的服务注册、管理与工具调用，支持通过关键字和任务描述智能检索和调度 MCP 服务。

## 主要功能

- **Nacos 配置对接**：通过 HTTP 客户端与 Nacos 服务端交互，支持服务注册、发现与配置管理。
- **MCP 服务管理**：集成 MCP 协议，支持服务的注册、检索、安装与工具调用。
- **智能检索与调度**：支持通过关键字和任务描述，智能检索可用的 MCP 服务，并自动补全推荐。
- **工具注册与调用**：内置 `SearchMcpServer`、`AddMcpServer`、`UseTool` 等工具，便于自动化流程编排。
- **日志与监控**：集成 winston 日志系统，支持日志分级与按天轮转。

## 安装与依赖

### 环境要求
- Node.js 16+
- Nacos 服务端


## 使用方法

- 配置mcp server
```json
{
  "mcpServers": {
    "nacos-mcp-router": {
      "command": "npx",
      "args": [
        "nacos-mcp-router@latest"
      ],
      "env": {
        "NACOS_USERNAME": "nacos",
        "NACOS_PASSWORD": "nacos_password",
        "NACOS_SERVER_ADDR": "localhost:8848"
      }
    }
  }
}
```

### 配置环境变量

可通过 `.env` 文件或环境变量配置 Nacos 相关参数：

- `NACOS_SERVER_ADDR`：Nacos 服务地址（默认：localhost:8848）
- `NACOS_USERNAME`：Nacos 用户名（默认：nacos）
- `NACOS_PASSWORD`：Nacos nacos_password

## 目录结构

- `src/`：核心源码
  - `index.ts`：项目入口
  - `router.ts`：MCP 路由与工具注册
  - `nacos_http_client.ts`：Nacos HTTP 客户端
  - `mcp_manager.ts`：MCP 服务管理
  - `router_types.ts`：类型定义与辅助
  - `simpleSseServer.ts`：简单 SSE 服务
  - `logger.ts`：日志模块
- `test/`：测试用例

## 主要接口与工具

- `SearchMcpServer`：根据任务描述和关键字检索 MCP 服务
- `AddMcpServer`：安装指定的 MCP 服务
- `UseTool`：调用指定 MCP 服务上的工具

## 许可证

ISC 