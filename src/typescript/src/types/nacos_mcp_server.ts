import { NacosMcpServer as BaseNacosMcpServer } from "../router_types";

/**
 * Extended NacosMcpServer type that includes additional properties used in search and reranking
 */
export interface NacosMcpServer extends BaseNacosMcpServer {
  /** Optional provider name that returned this result */
  providerName?: string;

  /** Optional relevance score (0-1) from the search provider */
  similarity?: number;

  /** Optional computed score after reranking */
  score?: number;
}

/**
 * Type for partial NacosMcpServer properties that can be used to create a new instance
 */
type NacosMcpServerInit = Partial<BaseNacosMcpServer> & {
  name: string;
  description?: string;
  agentConfig?: Record<string, any>;
  mcpConfigDetail?: any;
  [key: string]: any; // Allow any additional properties
};

/**
 * Type guard to check if an object is a NacosMcpServer
 */
export function isNacosMcpServer(obj: any): obj is NacosMcpServer {
  return (
    obj &&
    typeof obj === 'object' &&
    'name' in obj &&
    'description' in obj &&
    'agentConfig' in obj &&
    typeof obj.getName === 'function' &&
    typeof obj.getDescription === 'function' &&
    typeof obj.getAgentConfig === 'function' &&
    typeof obj.toDict === 'function'
  );
}

/**
 * Creates a new NacosMcpServer with additional search/rerank properties
 * Ensures all required methods are properly bound to the returned object
 */
export function createMcpProviderResult(
  base: NacosMcpServerInit,
  options: {
    providerName?: string;
    similarity?: number;
    score?: number;
  } = {}
): NacosMcpServer {
  // Create a new instance of NacosMcpServer with required properties
  const server = new BaseNacosMcpServer(
    base.name,
    base.description || '',
    base.agentConfig || {}
  ) as NacosMcpServer;

  // Add mcpConfigDetail if provided
  if (base.mcpConfigDetail !== undefined) {
    (server as any).mcpConfigDetail = base.mcpConfigDetail;
  }

  // Add search/rerank specific properties
  if (options.providerName) {
    server.providerName = options.providerName;
  }
  // NacosMcpProvider is the default provider, so it should have the highest priority
  if (options.providerName === 'NacosMcpProvider') {
    server.similarity = 1;
    server.score = 1;
  } else {
    if (options.similarity !== undefined) {
      server.similarity = options.similarity;
    }
    if (options.score !== undefined) {
      server.score = options.score;
    }
  }

  // Copy any additional properties from base
  const extraProps = Object.entries(base).reduce<Record<string, any>>((acc, [key, value]) => {
    if (!['name', 'description', 'agentConfig', 'mcpConfigDetail'].includes(key)) {
      acc[key] = value;
    }
    return acc;
  }, {});

  Object.assign(server, extraProps);

  return server;
}
