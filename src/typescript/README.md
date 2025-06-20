# Nacos MCP Router TypeScript ![NPM Version](https://img.shields.io/npm/v/nacos-mcp-router) ![NPM Downloads](https://img.shields.io/npm/d18m/nacos-mcp-router)

English | [中文](./README_zh.md)

A TypeScript implementation of Nacos MCP Router that bridges Nacos service discovery with the Model Context Protocol (MCP), enabling intelligent service orchestration and tool invocation for AI applications.

## Overview

Nacos MCP Router TypeScript is a sophisticated routing layer that integrates Nacos service registry with MCP-compatible AI agents. It provides intelligent service discovery, dynamic tool registration, and automated workflow orchestration capabilities.

### Key Capabilities

- **Dynamic Service Discovery**: Automatically discover and register MCP services through Nacos
- **Intelligent Routing**: Smart request routing based on service capabilities and load
- **Tool Orchestration**: Seamless integration between AI agents and microservices
- **Configuration Management**: Centralized configuration through Nacos
- **Real-time Monitoring**: Service health monitoring and performance metrics

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Agent      │    │  Nacos MCP       │    │   Nacos         │
│   (Claude,      │◄──►│  Router          │◄──►│   Server        │
│   Cline, etc.)  │    │  TypeScript      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   MCP Services   │
                       │   (Tools &       │
                       │   Resources)     │
                       └──────────────────┘
```

## Features

- **Nacos Integration**: Full integration with Nacos for service registration, discovery, and configuration management
- **MCP Protocol Support**: Complete Model Context Protocol implementation for AI agent communication
- **Service Orchestration**: Intelligent service discovery and routing based on capabilities
- **Tool Management**: Dynamic tool registration, discovery, and invocation
- **Health Monitoring**: Real-time service health checks and monitoring
- **Load Balancing**: Intelligent request distribution across service instances
- **Configuration Hot-reload**: Dynamic configuration updates without service restart

## Prerequisites

- Node.js 16+ 
- Nacos Server 3.0+
- TypeScript 4.5+

## Quick Start

### Installation

```bash
npm install nacos-mcp-router
# or
yarn add nacos-mcp-router
```

### Basic Usage

1. **Configure Environment Variables**

```bash
export NACOS_SERVER_ADDR=localhost:8848
export NACOS_USERNAME=nacos
export NACOS_PASSWORD=nacos
export NACOS_NAMESPACE=public
```

2. **MCP Server Configuration**

Add to your MCP client configuration:

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

3. **Programmatic Usage**

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

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NACOS_SERVER_ADDR` | Nacos server address | `localhost:8848` |
| `NACOS_USERNAME` | Nacos username | `nacos` |
| `NACOS_PASSWORD` | Nacos password | `nacos` |
| `NACOS_NAMESPACE` | Nacos namespace | `public` |
| `NACOS_GROUP` | Service group | `DEFAULT_GROUP` |
| `LOG_LEVEL` | Logging level | `info` |
| `PORT` | MCP server port | `3000` |

### Configuration File

Create a `nacos-mcp-config.json` file:

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
  "port": 3000, // common port, used if ssePort/streamablePort are not specified
  "logLevel": "info"
}
```

- `mode`: startup mode, supports `stdio` (default), `sse`, `streamable`
- `port`: common port, used if ssePort/streamablePort are not specified
- `ssePort`: port for SSE mode
- `streamablePort`: port for Streamable HTTP mode

## Available Tools

### Service Discovery Tools

#### SearchMcpServer
Discover MCP services based on capabilities and requirements.

```typescript
// Parameters
{
  "task_description": "string",  // Task description
  "keywords": "string[]",        // Search keywords (optional)
  "capabilities": "string[]"     // Required capabilities (optional)
}
```

#### ListMcpServers
List all available MCP services.

```typescript
// Returns
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

### Service Management Tools

#### AddMcpServer
Register a new MCP service.

```typescript
// Parameters
{
  "name": "string",           // Service name
  "url": "string",            // Service URL
  "description": "string",    // Service description
  "capabilities": "string[]", // Service capabilities
  "metadata": "object"        // Additional metadata (optional)
}
```

#### RemoveMcpServer
Unregister an MCP service.

```typescript
// Parameters
{
  "name": "string"  // Service name
}
```

### Tool Execution

#### UseTool
Execute tools on registered MCP services.

```typescript
// Parameters
{
  "server_name": "string",    // Target server name
  "tool_name": "string",      // Tool name
  "arguments": "object",      // Tool arguments
  "timeout": "number"         // Timeout in seconds (optional)
}
```

## Use Cases

### 1. AI Agent Service Discovery

```typescript
// AI agent searching for database services
const dbServices = await router.searchMcpServer({
  task_description: "I need to query customer data from database",
  keywords: ["database", "sql", "customer"],
  capabilities: ["query", "read"]
});
```

### 2. Dynamic Tool Registration

```typescript
// Register a new microservice as MCP tool
await router.addMcpServer({
  name: "payment-service",
  url: "http://payment-service:8080/mcp",
  description: "Payment processing service",
  capabilities: ["payment", "transaction", "refund"],
  metadata: {
    version: "1.0.0",
    team: "finance"
  }
});
```

### 3. Cross-Service Orchestration

```typescript
// AI agent orchestrating multiple services
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

## Development

### Project Structure

```
src/
├── index.ts                # Application entry point
├── router.ts               # MCP routing and tool registration
├── nacos_http_client.ts    # Nacos HTTP client
├── mcp_manager.ts          # MCP service management
├── router_types.ts         # Type definitions and utilities
└── logger.ts               # Logging module
test/                       # Test cases
example/
└── simpleSseServer.ts      # Simple SSE server implementation
```

### Build and Test

```bash
# Install dependencies
npm install

# Build
npm run build

# Test
npm test

# Development mode
npm run dev

# Lint
npm run lint

# Type check
npm run type-check
```

### Docker Support

[Dockerfile](./Dockerfile)

## Monitoring and Observability

### Health Checks

The router provides health check endpoints:

- `GET /health` - Basic health status
- `GET /health/detailed` - Detailed health information
- `GET /metrics` - Prometheus metrics

### Logging

Structured logging with configurable levels:

```typescript
import { logger } from './utils/logger';

logger.info('Service registered', { 
  serviceName: 'payment-service',
  instances: 3 
});
```

### Metrics

Built-in metrics collection:

- Request count and latency
- Service discovery performance
- Tool execution statistics
- Error rates and types

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Apache License 2.0

## Related Projects

- [Nacos MCP Router (Python)](https://github.com/nacos-group/nacos-mcp-router) - Original Python implementation
- [Nacos](https://nacos.io/) - Dynamic naming and configuration service  
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification

## Support

- [Documentation](https://nacos.io/docs/)
- [Issues](https://github.com/nacos-group/nacos-mcp-router-typescript/issues)
- [Discussions](https://github.com/nacos-group/nacos-mcp-router-typescript/discussions)