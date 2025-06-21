import { NacosMcpServer } from "../router_types";

/**
 * Provider priorities for result reranking.
 * Higher values indicate higher priority when results have equal scores.
 */
export type ProviderPriorities = Record<string, number>;

/**
 * Options for the reranking process
 */
export interface RerankOptions {
  /** Maximum number of results to return */
  limit?: number;
  /** Minimum similarity score (0-1) for results to be included */
  minSimilarity?: number;
  /** Whether to enable professional reranking (e.g., domain-specific sorting) */
  enableProfessionalRerank?: boolean;
}

/**
 * Result from a single provider before merging/reranking
 */
export interface ProviderResult {
  /** Name of the provider */
  providerName: string;
  /** Results returned by this provider */
  results: NacosMcpServer[];
}

/**
 * Interface for rerank processor in the chain of responsibility
 */
export interface IRerankProcessor {
  /**
   * Process the results
   * @param results Results to process
   * @param options Reranking options
   * @returns Processed results
   */
  process(
    results: NacosMcpServer[],
    options: RerankOptions
  ): NacosMcpServer[];

  /**
   * Set the next processor in the chain
   * @param next Next processor
   */
  setNext(next: IRerankProcessor): IRerankProcessor;
}

/**
 * Base class for rerank processors implementing the chain of responsibility pattern
 */
export abstract class BaseRerankProcessor implements IRerankProcessor {
  protected nextProcessor: IRerankProcessor | null = null;

  setNext(next: IRerankProcessor): IRerankProcessor {
    this.nextProcessor = next;
    return next;
  }

  process(
    results: NacosMcpServer[],
    options: RerankOptions
  ): NacosMcpServer[] {
    if (this.nextProcessor) {
      return this.nextProcessor.process(results, options);
    }
    return results;
  }

  /**
   * Helper to safely call the next processor in the chain
   */
  protected next(
    results: NacosMcpServer[],
    options: RerankOptions
  ): NacosMcpServer[] {
    if (this.nextProcessor) {
      return this.nextProcessor.process(results, options);
    }
    return results;
  }
}
