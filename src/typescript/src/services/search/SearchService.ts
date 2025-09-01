import { SearchParams, SearchProvider } from "../../types/search";
import { logger } from "../../logger";
import { RerankMcpServer, type ProviderPriorities, type RerankOptions } from "./rerank/RerankMcpServer";
import { type ProviderResult } from "../../types/rerank";
import { NacosMcpServer, createMcpProviderResult as createServer } from "../../types/nacos_mcp_server";
import { CompassSearchProvider } from "./CompassSearchProvider";

/**
 * Base URL for the COMPASS API.
 * Can be overridden by setting the COMPASS_API_BASE environment variable.
 */
export const COMPASS_API_BASE = process.env.COMPASS_API_BASE || 'https://registry.mcphub.io';

// Helper to ensure we have a properly typed server with all required methods
function ensureEnhancedServer(server: any): NacosMcpServer {
  // If it's already a proper NacosMcpServer with all methods, return as is
  if (server && 
      typeof server.getName === 'function' && 
      typeof server.getDescription === 'function' &&
      typeof server.getAgentConfig === 'function' &&
      typeof server.toDict === 'function') {
    return server as NacosMcpServer;
  }
  
  // Otherwise create a new NacosMcpServer instance with all required methods
  return createServer({
    ...server,
    name: server.name || '',
    description: server.description || '',
    agentConfig: server.agentConfig || {},
    mcpConfigDetail: server.mcpConfigDetail || null
  }, {
    providerName: server.providerName || 'unknown',
    similarity: server.similarity || 0,
    score: server.score || 0
  });
}

/**
 * A lightweight search service that orchestrates multiple SearchProviders
 * and provides a single `search` facade. The implementation is simplified
 * compared to the mcpadvisor version but keeps extensibility hooks (add / remove
 * provider, result dedup / basic priority ordering).
 */
export class SearchService {
  private providers: SearchProvider[] = [];
  private rerankService: RerankMcpServer;
  private defaultRerankOptions: RerankOptions = {
    limit: 7,
    minSimilarity: 0.4,
    enableProfessionalRerank: false,
  };

  constructor(
    providers: SearchProvider[] = [],
    providerPriorities: ProviderPriorities = {},
    rerankOptions?: Partial<RerankOptions>,
    enableCompass: boolean = true
  ) {
    this.providers = [...providers];
    if (enableCompass) {
      const compassProvider = new CompassSearchProvider(COMPASS_API_BASE);
      this.providers.push(compassProvider);
    }
    
    this.defaultRerankOptions = { ...this.defaultRerankOptions, ...rerankOptions };
    this.rerankService = new RerankMcpServer(providerPriorities, this.defaultRerankOptions);
    
    logger.info(`SearchService initialized with ${this.providers.length} providers.`);
    logger.debug(`COMPASS_API_BASE: ${COMPASS_API_BASE}`);
  }

  /** Add a provider at runtime */
  addProvider(provider: SearchProvider): void {
    this.providers.push(provider);
  }

  /** Remove provider by index */
  removeProvider(index: number): void {
    if (index >= 0 && index < this.providers.length) {
      this.providers.splice(index, 1);
    }
  }

  /** Return copy of current providers list */
  getProviders(): SearchProvider[] {
    return [...this.providers];
  }

  /**
   * Update provider priorities for reranking
   */
  updateProviderPriorities(priorities: ProviderPriorities): void {
    this.rerankService.updateProviderPriorities(priorities);
  }

  /**
   * Update default rerank options
   */
  updateRerankOptions(options: Partial<RerankOptions>): void {
    this.defaultRerankOptions = { ...this.defaultRerankOptions, ...options };
    this.rerankService.updateDefaultOptions(options);
  }

  /**
   * Invoke all providers in parallel, merge, deduplicate and rerank results.
   */
  async search(
    params: SearchParams,
    rerankOptions: Partial<RerankOptions> = {}
  ): Promise<NacosMcpServer[]> {
    if (this.providers.length === 0) {
      logger.warn("No search providers registered, returning empty result.");
      return [];
    }

    logger.info(`Searching with params: ${JSON.stringify(params)}`);
    const providerResults: ProviderResult[] = [];
    const searchPromises = this.providers.map(async (provider) => {
      const providerName = provider.constructor.name;
      try {
        const results = await provider.search(params);
        logger.info(`${providerName} returned ${results.length} results: ${JSON.stringify(results)}`);
        const typedResults = results.map(result => 
          ensureEnhancedServer({
            ...result,
            providerName
          })
        );
        
        providerResults.push({
          providerName,
          results: typedResults,
        });
      } catch (err) {
        logger.error(`Provider ${providerName} failed:`, err);
        // Push empty results on error
        providerResults.push({
          providerName,
          results: [],
        });
      }
    });

    await Promise.all(searchPromises);

    try {
      // Merge and rerank results
      const mergedOptions = { ...this.defaultRerankOptions, ...rerankOptions };
      logger.info(`Reranking with options: ${JSON.stringify(mergedOptions)}`);
      
      const rerankedResults = await this.rerankService.rerank(providerResults, mergedOptions);
      
      logger.info(`Successfully reranked to ${rerankedResults.length} results`);
      return rerankedResults;
    } catch (error) {
      logger.error('Error during reranking:', error);
      // Fallback to simple merge if reranking fails
      const allResults = providerResults.flatMap(pr => pr.results);
      return [...new Map(allResults.map(r => [r.getName(), r])).values()];
    }
  }
}
