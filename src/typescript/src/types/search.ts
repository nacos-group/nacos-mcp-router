import { NacosMcpServer } from "../router_types";

/**
 * Parameters used to search for MCP servers.
 */
export interface SearchParams {
    /** 描述用户当前任务，用于在向量库中检索相关的 MCP 服务器 */
    taskDescription: string;
    /** 搜索关键词，可选。将直接在缓存中做关键词匹配 */
    keywords?: string[];
    /** 所需的能力标签，可选。预留字段，方便后续在不同 Provider 中做能力过滤或参与向量搜索 */
    capabilities?: string[];
  }


  /**
   * A SearchProvider is responsible for returning a list of {@link NacosMcpServer}
   * that are most relevant to the provided {@link SearchParams}.
   *
   * In the future there could be many different implementations (e.g. remote HTTP
   * provider, local cache provider, LLM‐based provider, etc.).  All of them must
   * conform to this interface so that the router can chain providers,
   * re-rank results, and finally return a unified list to the caller.
   */
  export interface SearchProvider {
    /**
     * Search MCP servers based on the given parameters.
     *
     * @param params Parameters describing the user task and optional filters.
     * @returns A promise that resolves to an array of matching MCP servers.
     */
    search(params: SearchParams): Promise<NacosMcpServer[]>;
  }
  