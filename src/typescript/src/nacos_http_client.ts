import axios, { AxiosInstance } from 'axios';
import { NacosMcpServer } from './router_types';
import { logger } from './logger';
import { NacosMcpServerConfigImpl, Tool } from './nacos_mcp_server_config';
import { ErrorCode, McpError } from '@modelcontextprotocol/sdk/types.js';

export class NacosHttpClient {
  private readonly nacosAddr: string;
  private readonly userName: string;
  private readonly passwd: string;
  private client: AxiosInstance;

  constructor(nacosAddr: string, userName: string, passwd: string) {
    if (!nacosAddr) {
      throw new Error('nacosAddr cannot be an empty string');
    }
    if (!userName) {
      throw new Error('userName cannot be an empty string');
    }
    if (!passwd) {
      throw new Error('passwd cannot be an empty string');
    }

    this.nacosAddr = nacosAddr;
    this.userName = userName;
    this.passwd = passwd;

    this.client = axios.create({
      baseURL: `http://${this.nacosAddr}`,
      headers: {
        'Content-Type': 'application/json',
        'charset': 'utf-8',
        'userName': this.userName,
        'password': this.passwd
      }
    });
  }

  async isReady(): Promise<boolean> {
    return new Promise((resolve) => {
      this.client.get('/nacos/v3/admin/ai/mcp/list').then((response) => {
        if (response.status === 200) {
          resolve(true);
        } else {
          resolve(false);
        }
      });
    });
  }

  async getMcpServerByName(name: string): Promise<NacosMcpServer> {
    const url = `/nacos/v3/admin/ai/mcp?mcpName=${name}`;
    const mcpServer = new NacosMcpServer(name, '', {});

    try {
      const response = await this.client.get(url);
      if (response.status === 200) {
        const data = response.data.data;
        const config = NacosMcpServerConfigImpl.fromDict(data);
        const server = new NacosMcpServer(
          config.name,
          config.description || '',
          config.localServerConfig
        );
        server.mcpConfigDetail = config;

        if (config.protocol !== 'stdio' && config.backendEndpoints.length > 0) {
          const endpoint = config.backendEndpoints[0];
          const httpSchema = endpoint.port === 443 ? 'https' : 'http';
          let url = `${httpSchema}://${endpoint.address}:${endpoint.port}${config.remoteServerConfig.exportPath}`;
          
          if (!config.remoteServerConfig.exportPath.startsWith('/')) {
            url = `${httpSchema}://${endpoint.address}:${endpoint.port}/${config.remoteServerConfig.exportPath}`;
          }

          if (!server.agentConfig.mcpServers) {
            server.agentConfig.mcpServers = {};
          }

          server.agentConfig.mcpServers[server.name] = {
            name: server.name,
            description: server.description,
            url: url
          };
        }
        return server;
      }
    } catch (error) {
      logger.warning(`failed to get mcp server ${name}, response: ${error}`);
    }
    return mcpServer;
  }

  async getMcpServers(): Promise<NacosMcpServer[]> {
    const mcpServers: NacosMcpServer[] = [];
    try {
      const pageSize = 100;
      const pageNo = 1;
      const url = `/nacos/v3/admin/ai/mcp/list?pageNo=${pageNo}&pageSize=${pageSize}`;
      
      const response = await this.client.get(url);
      if (response.status !== 200) {
        logger.warning(`failed to get mcp server list, url ${url}, response: ${response.data}`);
        return [];
      }

      for (const mcpServerDict of response.data.data.pageItems) {
        if (mcpServerDict.enabled) {
          const mcpName = mcpServerDict.name;
          const mcpServer = await this.getMcpServerByName(mcpName);

          if (mcpServer.description) {
            mcpServers.push(mcpServer);
          }
        }
      }
    } catch (error) {
      logger.error('Error getting mcp servers:', error);
      throw new McpError(ErrorCode.InternalError, `Failed to get mcp servers: ${error}`)
    }
    return mcpServers;
  }

  async updateMcpTools(mcpName: string, tools: Tool[]): Promise<boolean> {
    try {
      const url = `/nacos/v3/admin/ai/mcp?mcpName=${mcpName}`;
      const response = await this.client.get(url);

      if (response.status === 200) {
        const data = response.data.data;
        const toolList = tools.map(tool => ({
          name: tool.name,
          description: tool.description,
          inputSchema: tool.inputSchema
        }));

        const endpointSpecification: Record<string, any> = {};
        if (data.protocol !== 'stdio') {
          endpointSpecification.data = data.remoteServerConfig.serviceRef;
          endpointSpecification.type = 'REF';
        }

        if (!data.toolSpec) {
          data.toolSpec = {};
        }

        data.toolSpec.tools = toolList;
        const params: Record<string, any> = {
          mcpName: mcpName
        };

        const toolSpecification = data.toolSpec;
        delete data.toolSpec;
        delete data.backendEndpoints;

        params.serverSpecification = JSON.stringify(data);
        params.endpointSpecification = JSON.stringify(endpointSpecification);
        params.toolSpecification = JSON.stringify(toolSpecification);

        logger.info(`update mcp tools, params ${JSON.stringify(params)}`);

        const updateUrl = `http://${this.nacosAddr}/nacos/v3/admin/ai/mcp?`;
        const updateResponse = await axios.put(updateUrl, params, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'charset': 'utf-8',
            'userName': this.userName,
            'password': this.passwd
          }
        });

        if (updateResponse.status === 200) {
          return true;
        } else {
          logger.warning(`failed to update mcp tools list, caused: ${updateResponse.data}`);
          return false;
        }
      } else {
        logger.warning(`failed to update mcp tools list, caused: ${response.data}`);
        return false;
      }
    } catch (error) {
      logger.error('Error updating mcp tools:', error);
      return false;
    }
  }
}
