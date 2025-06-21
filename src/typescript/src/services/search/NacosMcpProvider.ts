import { NacosMcpServer } from '../../router_types';
import { McpManager } from '../../mcp_manager';
import { SearchParams, SearchProvider } from '../../types/search';

/**
 * Default implementation backed by the existing {@link McpManager} logic that
 * queries Nacos and the in-memory vector DB.
 */
export class NacosMcpProvider implements SearchProvider {
  private readonly mcpManager: McpManager;

  constructor(mcpManager: McpManager) {
    this.mcpManager = mcpManager;
  }

  async search(params: SearchParams): Promise<NacosMcpServer[]> {
    const { taskDescription, keywords = [] } = params;

    const candidates: NacosMcpServer[] = [];

    // 1. Keyword search (exact / fuzzy match in cache)
    for (const keyword of keywords) {
      const byKeyword = await this.mcpManager.searchMcpByKeyword(keyword);
      if (byKeyword.length > 0) {
        candidates.push(...byKeyword);
      }
    }

    // 2. Vector DB semantic search if results are fewer than 5
    if (candidates.length < 5) {
      const additional = await this.mcpManager.getMcpServer(
        taskDescription,
        5 - candidates.length,
      );
      candidates.push(...additional);
    }

    // TODO: 去重 / rerank – 留待后续的结果处理组件实现
    return candidates;
  }
}
