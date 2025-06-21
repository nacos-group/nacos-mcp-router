# SearchMcpServer 技术文档

## 目录
- [1. 接口概述](#1-接口概述)
- [2. 数据流分析](#2-数据流分析)
  - [2.1 接口定义与注册](#21-接口定义与注册)
  - [2.2 数据加载流程](#22-数据加载流程)
  - [2.3 索引建立](#23-索引建立)
  - [2.4 搜索与结果返回](#24-搜索与结果返回)
- [3. 关键数据结构](#3-关键数据结构)
  - [3.1 NacosMcpServer](#31-nacosmcpserver)
  - [3.2 NacosMcpServerConfig](#32-nacosmcpserverconfig)
- [4. 核心代码位置](#4-核心代码位置)
- [5. 数据流总结](#5-数据流总结)

## 1. 接口概述

SearchMcpServer 是一个 MCP 工具接口，用于根据任务描述和关键字搜索 MCP 服务器。主要实现在 `src/router.ts` 的 `registerMcpTools` 方法中注册。

## 2. 数据流分析

### 2.1 接口定义与注册

```typescript
// src/router.ts
this.mcpServer.tool(
  "SearchMcpServer",
  `根据任务描述及关键字搜索mcp server...`,
  { 
    taskDescription: z.string(), 
    keyWords: z.string().array().nonempty().max(2) 
  },
  async ({ taskDescription, keyWords }) => {
    // 处理逻辑
  }
);
```

### 2.2 数据加载流程

1. **数据来源**：
   - MCP 服务器信息存储在 Nacos 配置中心
   - 通过 `NacosHttpClient` 类与 Nacos 交互

2. **数据加载**：
   - 系统启动时，`McpManager` 会初始化并加载 MCP 服务器信息
   - 通过 `updateNow` 方法定期更新 MCP 服务器列表

### 2.3 索引建立

1. **向量数据库**：
   - 使用 `VectorDB` 类进行向量检索
   - 在 `Router.start()` 中初始化 VectorDB

```typescript
// src/router.ts
if (!this.vectorDB) {
  this.vectorDB = new VectorDB();
  await this.vectorDB.start();
  await this.vectorDB.isReady();
}
```

2. **索引过程**：
   - MCP 服务器信息被转换为向量并存储在 VectorDB 中
   - 使用 `@xenova/transformers` 进行文本嵌入

### 2.4 搜索与结果返回

1. **搜索流程**：
   - 接收用户输入的 `taskDescription` 和 `keyWords`
   - 调用 `mcpManager.getMcpServer` 进行搜索

```typescript
// src/mcp_manager.ts
async getMcpServer(queryTexts: string, count: number): Promise<NacosMcpServer[]> {
  const result = await this.vectorDbService.query(queryTexts, count);
  // 处理并返回结果
}
```

2. **结果处理**：
   - 从 VectorDB 获取相似度最高的结果
   - 格式化返回给用户

## 3. 关键数据结构

### 3.1 NacosMcpServer

```typescript
// src/router_types.ts
export class NacosMcpServer {
  name: string;
  description: string;
  mcpConfigDetail: NacosMcpServerConfigImpl | null;
  agentConfig: Record<string, any>;
  
  // 方法
  getName(): string
  getDescription(): string
  getAgentConfig(): Record<string, any>
  toDict(): Record<string, any>
}
```

### 3.2 NacosMcpServerConfig

```typescript
// src/nacos_mcp_server_config.ts
export interface NacosMcpServerConfig {
  name: string;
  protocol: string;
  description: string | null;
  version: string;
  remoteServerConfig: RemoteServerConfig;
  localServerConfig: Record<string, any>;
  enabled: boolean;
  capabilities: string[];
  backendEndpoints: BackendEndpoint[];
  toolSpec: ToolSpec;
  getToolDescription(): string;
}
```

## 4. 核心代码位置

1. **接口注册**：
   - `src/router.ts` - `Router.registerMcpTools()`

2. **MCP 服务器管理**：
   - `src/mcp_manager.ts` - `McpManager` 类
   - `src/nacos_http_client.ts` - `NacosHttpClient` 类

3. **数据结构**：
   - `src/router_types.ts` - 核心数据模型
   - `src/nacos_mcp_server_config.ts` - 配置相关结构

4. **向量检索**：
   - `VectorDB` 类实现（在代码库中可能在其他文件）

## 5. 数据流总结

1. **初始化阶段**：
   - 启动时加载 MCP 服务器信息到内存
   - 初始化向量数据库

2. **搜索阶段**：
   - 接收用户查询
   - 将查询转换为向量
   - 在向量数据库中执行相似度搜索
   - 返回最匹配的 MCP 服务器列表

3. **更新阶段**：
   - 定期从 Nacos 同步 MCP 服务器信息
   - 更新本地缓存和向量索引

这个设计允许系统高效地根据自然语言描述和关键词搜索 MCP 服务器，同时保持数据的实时性。
