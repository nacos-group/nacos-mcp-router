import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { NacosHttpClient } from "./nacos_http_client";
import { McpManager } from "./mcp_manager";
import { logger } from "./logger";
import { z } from "zod";
import { ErrorCode, McpError } from "@modelcontextprotocol/sdk/types.js";
import { VectorDB, NacosMcpServer } from "./router_types";
// import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";

const MCP_SERVER_NAME = "nacos-mcp-router";

export interface RouterConfig {
  nacos: {
    serverAddr: string;
    username: string;
    password: string;
  };
  mcp: {
    host: string;
    port: number;
    authToken?: string;
  };
}

interface ServiceInfo {
  name: string;
  description: string;
}

export class Router {
  private nacosClient: NacosHttpClient;
  private mcpManager: McpManager | undefined;
  private vectorDB: VectorDB | undefined;
  private mcpServer: McpServer | undefined;

  constructor(config: RouterConfig) {
    const {serverAddr, username, password} = config.nacos;
    this.nacosClient = new NacosHttpClient(serverAddr, username, password);
  }

  private async registerMcpTools() {
    if (!this.mcpServer) {
      throw new McpError(ErrorCode.InternalError, "MCP server not initialized");
    }
    try {
      this.mcpServer.tool(
        "SearchMcpServer",
        `根据任务描述及关键字搜索mcp server，制定完成任务的步骤;Args:task_description: 用户任务描述，使用中文;key_words: 字符串数组，用户任务关键字，使用中文,可以为多个，最多为2个`,
        { taskDescription: z.string(), keyWords: z.string().array().nonempty({
          message: "Can't be empty!",
        }).max(2) },
        async ({ taskDescription, keyWords }) => {
          try {
            const mcpServers1: NacosMcpServer[] = [];
            
            // 根据关键字搜索MCP服务器
            for (const keyWord of keyWords) {
              const mcps = await this.mcpManager!.searchMcpByKeyword(keyWord);
              if (mcps.length > 0) {
                mcpServers1.push(...mcps);
              }
            }

            // 如果找到的服务器数量少于5个，使用任务描述进行从向量库补充搜索
            if (mcpServers1.length < 5) {
              const additionalServers = await this.mcpManager!.getMcpServer(taskDescription, 5 - mcpServers1.length);
              mcpServers1.push(...additionalServers);
            }

            // 构建结果
            const result: Record<string, { name: string; description: string }> = {};
            for (const mcpServer of mcpServers1) {
              result[mcpServer.getName()] = {
                name: mcpServer.getName(),
                description: mcpServer.getDescription()
              };
            }

            const content = JSON.stringify(result, null, 2);
            const jsonString = `## 获取${taskDescription}的步骤如下：
### 1. 当前可用的mcp server列表为：
${content}
### 2. 从当前可用的mcp server列表中选择你需要的mcp server调AddMcpServer工具安装mcp server`;

            return {
              content: [{
                type: "text",
                text: jsonString
              }]
            };
          } catch (error) {
            logger.warn(`failed to search_mcp_server: ${taskDescription}`, error);
            return {
              content: [{
                type: "text",
                text: `failed to search mcp server for ${taskDescription}`
              }]
            };
          }
        }
      );
      this.mcpServer.tool(
        "UseTool",
        '使用指定MCP服务器上的工具。需要先通过AddMcpServer安装MCP服务器，然后才能使用其工具。',
        { mcpServerName: z.string(), toolName: z.string(), params: z.record(z.string(), z.any()) },
        async ({ mcpServerName, toolName, params }) => {
          try {
            const result = await this.mcpManager!.useTool(mcpServerName, toolName, params);
            return {
              content: [{
                type: "text",
                text: JSON.stringify(result)
              }]
            };
          } catch (error) {
            logger.error(`Failed to use tool ${toolName} from server ${mcpServerName}:`, error);
            // throw new McpError(ErrorCode.InternalError, `Failed to use tool ${toolName} from server ${mcpServerName}`);
            return {
              content: [{
                type: "text",
                text: `Failed to use tool ${toolName} from server ${mcpServerName}`
              }]
            };
          }
        }
      );
      this.mcpServer.tool(
        "AddMcpServer",
        `安装指定的mcp server, return mcp server安装结果`,
        { mcpServerName: z.string() },
        async ({ mcpServerName }) => {
          try {
            const result = await this.mcpManager!.addMcpServer(mcpServerName);
            return {
              content: [{
                type: "text",
                text: JSON.stringify(result)
              }]
            };
          } catch (error) {
            logger.error(`Failed to add mcp server ${mcpServerName}:`, error);
            throw new McpError(ErrorCode.InternalError, `Failed to add mcp server ${mcpServerName}`);
          }
        }
      );
    } catch (error) {
      logger.error("Failed to register MCP tools:", error);
      throw new McpError(ErrorCode.InternalError, "Failed to register MCP tools:", error);
    }
  }

  public async start(replaceTransport?: Transport) {
    try {
      // const modelName = "all-MiniLM-L6-v2";
      // const defaultEF = new DefaultEmbeddingFunction({ model: modelName });
      // console.log(`defaultEF: ${defaultEF}`);

      const { env } = await import("@xenova/transformers");
      (env as any).remoteHost = "https://hf-mirror.com";
      if (!this.vectorDB) {
        this.vectorDB = new VectorDB();
        await this.vectorDB.start();
        await this.vectorDB.isReady();
        logger.info(`vectorDB is ready, collectionId: ${this.vectorDB._collectionId}`);
      }
      const isReady = await this.nacosClient.isReady();
      if (!isReady) {
        throw new McpError(ErrorCode.InternalError, "Nacos client is not ready or not connected, please check the nacos server conifg");
      }
      logger.info(`nacosClient is ready: ${isReady}`);
      if (!this.mcpManager) {
        this.mcpManager = new McpManager(this.nacosClient, this.vectorDB, 5000);
      }
      if (!this.mcpServer) {
        this.mcpServer = new McpServer({
          name: MCP_SERVER_NAME,
          version: "1.0.0",
        });
      }

      logger.info(`registerMcpTools`);
      this.registerMcpTools();
      if (replaceTransport) {
        this.mcpServer!.connect(replaceTransport);
      } else {
        const transport = new StdioServerTransport();
        logger.info(`transport: ${transport}`);
        await this.mcpServer!.connect(transport);
        logger.info(`mcpServer is connected, transport: ${JSON.stringify(transport)}`);
      }
    } catch (error) {
      logger.error("Failed to start Nacos MCP Router:", error);
      // throw error;
    }
  }
}
