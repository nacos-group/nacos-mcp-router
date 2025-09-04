import { SearchProvider } from "../../types/search";
import { NacosMcpServer } from "../../types/nacos_mcp_server";
import { logger } from "../../logger";
import { NacosMcpServer as BaseNacosMcpServer } from "../../router_types";

/**
 * COMPASS API search provider implementation that adapts to NacosMcpServer
 */
export class CompassSearchProvider implements SearchProvider {
  private apiBase: string;
  private defaultAgentConfig: Record<string, any>;

  /**
   * Create a new CompassSearchProvider
   * @param apiBase Base URL for the COMPASS API
   * @param defaultAgentConfig Default agent configuration for created NacosMcpServer instances
   */
  constructor(apiBase: string, defaultAgentConfig: Record<string, any> = {}) {
    if (!apiBase.endsWith('/')) {
      apiBase = apiBase + '/';
    }
    this.apiBase = apiBase;
    this.defaultAgentConfig = defaultAgentConfig;
    logger.info(`CompassSearchProvider initialized with API base: ${this.apiBase}`);
  }

  /**
   * Search for MCP servers using the COMPASS API and convert results to NacosMcpServer
   * @param params Search parameters including task description and optional filters
   * @returns Promise with array of NacosMcpServer instances
   */
  async search(params: Parameters<SearchProvider['search']>[0]): ReturnType<SearchProvider['search']> {
    const query = [
      params.taskDescription, 
      ...(params.keywords || []), 
      ...(params.capabilities || [])
    ].join(' ').trim();
    
    try {
      logger.debug(`Searching COMPASS API with query: ${query}`);
      const requestUrl = `${this.apiBase}recommend?description=${encodeURIComponent(query)}`;

      const response = await fetch(requestUrl);

      if (!response.ok) {
        const errorMsg = `COMPASS API request failed with status ${response.status}`;
        const error = new Error(errorMsg);
        logger.error(errorMsg, {
          status: response.status,
          statusText: response.statusText,
          url: requestUrl,
        });
        throw error;
      }

      const data = await response.json() as Array<{
        title: string;
        description: string;
        github_url: string;
        score: number;
      }>;

      logger.debug(`Received ${data.length} results from COMPASS API`);
      
      // Convert MCPServerResponse to NacosMcpServer
      const results: NacosMcpServer[] = [];
      for (const item of data) {
        try {
          // First create a base NacosMcpServer instance
          const baseServer = new BaseNacosMcpServer(
            item.title,
            item.description,
            {
              ...this.defaultAgentConfig,
              source: 'compass',
              sourceUrl: item.github_url,
              categories: [],
              tags: []
            }
          );
          
          // Then enhance it with search-specific properties
          const nacosServer = Object.assign(baseServer, {
            providerName: 'compass',
            similarity: item.score,
            score: item.score
          });
          results.push(nacosServer);
        } catch (error) {
          logger.error('Error converting COMPASS result to NacosMcpServer:', {
            error,
            item,
          });
        }
      }

      return results;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      logger.error(`Error in CompassSearchProvider: ${message}`, {
        error,
        query,
        apiBase: this.apiBase,
      });
      throw error;
    }
  }
}
