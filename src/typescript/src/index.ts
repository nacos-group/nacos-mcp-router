#!/usr/bin/env node

import { Router, RouterConfig } from "./router";
import { logger } from "./logger";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import fs from "fs";
import deepmerge from "deepmerge";
import express from "express";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

async function main() {
  // 解析命令行参数
  const argv = await yargs(hideBin(process.argv))
    .option("config", {
      alias: "c",
      type: "string",
      description: "配置文件路径（json）",
    })
    .help()
    .parse();

  let fileConfig = {};
  if (argv.config) {
    try {
      const fileContent = fs.readFileSync(argv.config, "utf-8");
      fileConfig = JSON.parse(fileContent);
    } catch (e) {
      logger.error(`读取配置文件失败: ${argv.config}`, e);
      process.exit(1);
    }
  }

  // 从 env 构建 config
  const envConfig = {
    nacos: {
      serverAddr: process.env.NACOS_SERVER_ADDR || "localhost:8848",
      username: process.env.NACOS_USERNAME || "nacos",
      password: process.env.NACOS_PASSWORD || "nacos_password",
    },
    logLevel: process.env.LOG_LEVEL || "info",
    // 支持 sse/streamable 端口
    port: process.env.PORT ? Number(process.env.PORT) : undefined,
    ssePort: process.env.SSE_PORT ? Number(process.env.SSE_PORT) : undefined,
    streamablePort: process.env.STREAMABLE_PORT ? Number(process.env.STREAMABLE_PORT) : undefined,
    mode: process.env.MODE || "stdio",
  };

  // 合并优先级：config json > env
  const mergedConfig = deepmerge(envConfig, fileConfig);

  // 根据 mode 启动不同 server
  const mode = mergedConfig.mode;
  if (mode === "sse") {
    // SSE模式
    const app = express();
    app.use(express.json());
    const transports: Record<string, SSEServerTransport> = {};
    app.get("/sse", async (req, res) => {
      try {
        const transport = new SSEServerTransport("/messages", res);
        const sessionId = transport.sessionId;
        transports[sessionId] = transport;
        transport.onclose = () => {
          delete transports[sessionId];
        };
        const router = new Router(mergedConfig as RouterConfig);
        await router.start(transport);
      } catch (error) {
        logger.error("Error establishing SSE stream:", error);
        if (!res.headersSent)
          res.status(500).send("Error establishing SSE stream");
      }
    });
    app.post("/messages", async (req, res) => {
      logger.info("Received POST request to /messages");
      const sessionId = req.query.sessionId as string | undefined;
      if (!sessionId) {
        logger.error("No session ID provided in request URL");
        res.status(400).send("Missing sessionId parameter");
        return;
      }
      const transport = transports[sessionId];
      if (!transport) {
        logger.error(`No active transport found for session ID: ${sessionId}`);
        res.status(404).send("Session not found");
        return;
      }
      try {
        await transport.handlePostMessage(req, res, req.body);
      } catch (error) {
        logger.error("Error handling request:", error);
        if (!res.headersSent) res.status(500).send("Error handling request");
      }
    });
    const port = mergedConfig.ssePort || mergedConfig.port || 3001;
    app.listen(port, () => {
      logger.info(`SSE Server listening on port ${port}`);
    });
    return;
  } else if (mode === "streamable") {
    // Streamable HTTP模式，参考 simpleStreamableHttp.ts
    const app = express();
    app.use(express.json());
    const transports: { [sessionId: string]: StreamableHTTPServerTransport } = {};
    app.post("/mcp", async (req, res) => {
      try {
        const sessionId = req.headers["mcp-session-id"] as string | undefined;
        let transport: StreamableHTTPServerTransport;
        if (sessionId && transports[sessionId]) {
          // 复用已存在的 transport
          transport = transports[sessionId];
        } else if (!sessionId && req.body && req.body.method === "initialize") {
          // 新会话初始化
          transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: () => Math.random().toString(36).slice(2),
            // 可加 eventStore/onsessioninitialized
          });
          transport.onclose = () => {
            const sid = transport.sessionId;
            if (sid && transports[sid]) {
              logger.info(`Transport closed for session ${sid}, removing from map`);
              delete transports[sid];
            }
          };
          // 连接 router
          const router = new Router(mergedConfig as RouterConfig);
          await router.start(transport);
          // 存储 transport
          if (transport.sessionId) {
            transports[transport.sessionId] = transport;
          }
          await transport.handleRequest(req, res, req.body);
          return;
        } else {
          res.status(400).json({
            jsonrpc: "2.0",
            error: { code: -32000, message: "Bad Request: No valid session ID provided" },
            id: null,
          });
          return;
        }
        // 已有 transport，直接处理
        await transport.handleRequest(req, res, req.body);
      } catch (error) {
        logger.error("Error handling MCP request:", error);
        if (!res.headersSent) {
          res.status(500).json({
            jsonrpc: "2.0",
            error: { code: -32603, message: "Internal server error" },
            id: null,
          });
        }
      }
    });
    // Handle GET requests for SSE streams (using built-in support from StreamableHTTP)
    app.get("/mcp", async (req, res) => {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;
      if (!sessionId || !transports[sessionId]) {
        res.status(400).send("Invalid or missing session ID");
        return;
      }
      const transport = transports[sessionId];
      await transport.handleRequest(req, res);
    });
    // Handle DELETE requests for session termination (according to MCP spec)
    app.delete("/mcp", async (req, res) => {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;
      if (!sessionId || !transports[sessionId]) {
        res.status(400).send("Invalid or missing session ID");
        return;
      }
      try {
        const transport = transports[sessionId];
        await transport.handleRequest(req, res);
      } catch (error) {
        logger.error("Error handling session termination:", error);
        if (!res.headersSent) {
          res.status(500).send("Error processing session termination");
        }
      }
    });
    const port = mergedConfig.streamablePort || mergedConfig.port || 3002;
    app.listen(port, () => {
      logger.info(`MCP Streamable HTTP Server listening on port ${port}`);
    });
    // 优雅关闭
    process.on("SIGINT", async () => {
      logger.info("Shutting down server...");
      for (const sessionId in transports) {
        try {
          logger.info(`Closing transport for session ${sessionId}`);
          await transports[sessionId].close();
          delete transports[sessionId];
        } catch (error) {
          logger.error(`Error closing transport for session ${sessionId}:`, error);
        }
      }
      logger.info("Server shutdown complete");
      process.exit(0);
    });
    return;
  } else {
    // stdio 模式
    try {
      const router = new Router(mergedConfig as RouterConfig);
      logger.info(`nacos mcp router start`);
      await router.start();
      logger.info("Nacos MCP Router started successfully");
    } catch (error) {
      logger.error("Failed to start Nacos MCP Router:", error);
      process.exit(1);
    }
  }
}

// 只有当这个文件是主入口文件时才执行 main() 函数
if (require.main === module) {
  (async () => {
    await main();
  })();
}

type NacosMcpRouterConfig = RouterConfig;

export type { NacosMcpRouterConfig };

export const NacosMcpRouter = Router;
