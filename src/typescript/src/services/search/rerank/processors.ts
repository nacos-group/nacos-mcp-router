import { logger } from "../../../logger";
import { BaseRerankProcessor, IRerankProcessor, ProviderPriorities, RerankOptions } from "../../../types/rerank";
import { NacosMcpServer, createMcpProviderResult } from "../../../types/nacos_mcp_server";
import { NacosMcpServer as BaseNacosMcpServer } from "../../../router_types";

// Helper type guard for enhanced NacosMcpServer
function isEnhancedServer(server: any): server is NacosMcpServer {
  return server && typeof server === 'object' && 'name' in server && 'description' in server;
}

// Helper to ensure we have a properly typed server
function ensureEnhancedServer(server: any): NacosMcpServer {
  if (isEnhancedServer(server)) {
    return server;
  }
  return createMcpProviderResult(server as BaseNacosMcpServer);
}

/**
 * Calculates scores for results based on provider priority and similarity
 */
export class ScoreCalculationProcessor extends BaseRerankProcessor {
  constructor(private providerPriorities: ProviderPriorities) {
    super();
  }

  process(
    results: NacosMcpServer[],
    options: RerankOptions
  ): NacosMcpServer[] {
    const scored = results.map(server => {
      const result = ensureEnhancedServer(server);
      
      // If score already calculated, use it
      if ('score' in result && result.score !== undefined) return result;
      
      // Otherwise calculate based on provider priority and similarity
      const priority = this.providerPriorities[result.providerName || ''] || 0;
      const similarity = result.similarity ?? 0;
      
      // Simple weighted score - can be adjusted based on requirements
      const score = similarity * 0.7 + (priority / 10) * 0.3;
      
      return createMcpProviderResult(result, { score });
    });

    return this.next(scored, options);
  }
}

/**
 * Filters out results below the minimum similarity threshold
 */
export class ScoreFilterProcessor extends BaseRerankProcessor {
  process(results: NacosMcpServer[], options: RerankOptions): NacosMcpServer[] {
    if (options.minSimilarity === undefined) {
      return this.next(results, options);
    }

    const filtered = results.map(ensureEnhancedServer).filter(
      result => (result.similarity ?? 0) >= options.minSimilarity!
    );

    if (filtered.length < results.length) {
      logger.debug(
        `Filtered out ${results.length - filtered.length} results below min similarity ${options.minSimilarity}`
      );
    }

    return this.next(filtered, options);
  }
}

/**
 * Sorts results by score in descending order
 */
export class ScoreSortProcessor extends BaseRerankProcessor {
  process(results: NacosMcpServer[]): NacosMcpServer[] {
    const sorted = [...results].map(ensureEnhancedServer).sort((a, b) => {
      const scoreA = a.score ?? a.similarity ?? 0;
      const scoreB = b.score ?? b.similarity ?? 0;
      return scoreB - scoreA; // Descending
    });
    
    return this.next(sorted, {});
  }
}

/**
 * Limits the number of results returned
 */
export class LimitProcessor extends BaseRerankProcessor {
  process(results: NacosMcpServer[], options: RerankOptions): NacosMcpServer[] {
    if (options.limit === undefined || options.limit <= 0) {
      return this.next(results, options);
    }
    
    const limited = results.map(ensureEnhancedServer).slice(0, options.limit);
    
    if (limited.length < results.length) {
      logger.debug(`Limited results from ${results.length} to ${options.limit}`);
    }
    
    return limited; // No next processor after limit
  }
}

/**
 * Placeholder for domain-specific professional reranking
 * Can be extended with custom business logic
 */
export class ProfessionalRerankProcessor extends BaseRerankProcessor {
  constructor(private enabled: boolean = false) {
    super();
  }

  process(results: NacosMcpServer[], options: RerankOptions): NacosMcpServer[] {
    if (!this.enabled && !options.enableProfessionalRerank) {
      return this.next(results, options);
    }

    // Ensure all results are properly typed
    const enhancedResults = results.map(ensureEnhancedServer);
    
    // TODO: Implement domain-specific reranking logic here
    // For now, just pass through
    logger.debug("Professional rerank executed (no-op in current implementation)");
    
    return this.next(enhancedResults, options);
  }
}

/**
 * Factory for creating the rerank processor chain
 */
export class RerankProcessorFactory {
  static createChain(providerPriorities: ProviderPriorities): IRerankProcessor {
    const scoreCalculation = new ScoreCalculationProcessor(providerPriorities);
    const scoreFilter = new ScoreFilterProcessor();
    const scoreSort = new ScoreSortProcessor();
    const limit = new LimitProcessor();
    const professionalRerank = new ProfessionalRerankProcessor(false);

    // Build the chain: calculate -> filter -> professional -> sort -> limit
    scoreCalculation
      .setNext(scoreFilter)
      .setNext(professionalRerank)
      .setNext(scoreSort)
      .setNext(limit);

    return scoreCalculation;
  }
}
