import { Router } from "../../src/router";
import { SearchService } from "../../src/services/search/SearchService";
import { NacosMcpProvider } from "../../src/services/search/NacosMcpProvider";
import { mockMcpServers as originalMockMcpServers, searchTestCases } from "../fixtures/searchTestData";
import { NacosMcpServer } from "../../src/types/nacos_mcp_server";
import { SearchParams } from "../../src/types/search";

// Minimal McpManager interface with only the methods we need for testing
interface MinimalMcpManager {
  searchMcpByKeyword(keyword: string): Promise<NacosMcpServer[]>;
  getMcpServer(taskDescription: string, count: number): Promise<NacosMcpServer[]>;
  getMcpServers(): Promise<NacosMcpServer[]>;
}

// Type guard to check if params is a string
function isStringParam(params: SearchParams | string): params is string {
  return typeof params === 'string';
}

// Helper function to extract query from SearchParams
function getQueryFromParams(params: SearchParams | string): string {
  return isStringParam(params) ? params : (params as any).query || '';
}

// Helper function to create a proper NacosMcpServer object
function createNacosMcpServer(base: Partial<NacosMcpServer>): NacosMcpServer {
  // Create a new object with all required properties
  const server = {
    name: base.name || '',
    description: base.description || '',
    mcpConfigDetail: base.mcpConfigDetail || null,
    agentConfig: base.agentConfig || {},
    providerName: base.providerName || 'nacos',
    similarity: base.similarity || 1.0,
    score: base.score || 1.0,
    // Ensure all required methods are properly bound to the object
    getName: function() { return this.name; },
    getDescription: function() { return this.description; },
    getAgentConfig: function() { return this.agentConfig; },
    toDict: function() {
      return {
        name: this.name,
        description: this.description,
        mcpConfigDetail: this.mcpConfigDetail,
        agentConfig: this.agentConfig
      };
    }
  };

  // Copy any additional properties from base
  Object.assign(server, base);
  
  return server;
}

// Create enhanced mock servers with all required NacosMcpServer methods
const mockMcpServers = originalMockMcpServers.map(serverData => {
  // Create a new server with all required methods and data
  return createNacosMcpServer({
    ...serverData,
    providerName: 'nacos',
    // Ensure these are set in case they're not in serverData
    name: serverData.name || '',
    description: serverData.description || '',
    mcpConfigDetail: serverData.mcpConfigDetail || null,
    agentConfig: serverData.agentConfig || {}
  });
});

/**
 * Simplified McpManager implementation for testing
 */
class DummyMcpManager implements MinimalMcpManager {
  async searchMcpByKeyword(keyword: string): Promise<NacosMcpServer[]> {
    const kw = keyword.toLowerCase();
    return mockMcpServers.filter(server => 
      server.getName().toLowerCase().includes(kw) || 
      (server.getDescription() || '').toLowerCase().includes(kw)
    );
  }

  async getMcpServer(_taskDescription: string, count: number): Promise<NacosMcpServer[]> {
    return mockMcpServers.slice(0, count);
  }

  async getMcpServers(): Promise<NacosMcpServer[]> {
    return [...mockMcpServers];
  }
}

// Minimal Router configuration – values are irrelevant for the tested method
const dummyConfig = {
  nacos: {
    serverAddr: "dummy-addr",
    username: "dummy-user",
    password: "dummy-pass"
  },
  mcp: {
    host: "",
    port: 0
  }
} as any;

// Mock CompassSearchProvider for testing
class MockCompassSearchProvider {
  async search(_params: SearchParams | string): Promise<NacosMcpServer[]> {
    // Return a subset of mock data that would match a typical search
    return mockMcpServers.slice(0, 2).map(serverData => {
      // Create a new server instance with compass provider info
      const server = createNacosMcpServer({
        ...serverData,
        providerName: 'compass',
        similarity: 0.9,
        score: 0.9
      });
      
      // Ensure all data is properly set on the instance
      return Object.assign(server, serverData);
    });
  }
}

describe("Router.searchNacosMcpServer", () => {
  let router: Router;
  let searchService: SearchService;

  beforeEach(() => {
    // Create a fresh instance of the mock manager for each test
    const mcpManager = new DummyMcpManager();
    
    // Create a mock NacosMcpProvider that works with our simplified McpManager
    const nacosProvider = {
      search: async (params: SearchParams | string) => {
        try {
          const query = getQueryFromParams(params);
          const results = await mcpManager.searchMcpByKeyword(query);
          
          // Ensure we return properly constructed NacosMcpServer instances
          return results.map(serverData => {
            const server = createNacosMcpServer({
              ...serverData,
              providerName: 'nacos'
            });
            
            // Verify the server has all required methods
            if (typeof server.getName !== 'function') {
              throw new Error('Server is missing getName method');
            }
            
            return server;
          });
        } catch (error) {
          console.error('Error in mock nacosProvider.search:', error);
          throw error;
        }
      }
    };
    
    // Create a mock CompassSearchProvider
    const compassProvider = new MockCompassSearchProvider();
    
    // Create the search service with our mock providers
    searchService = new SearchService([nacosProvider, compassProvider]);
    
    // Create router with minimal config
    router = new Router({
      nacos: {
        serverAddr: 'localhost:8848',
        username: 'nacos',
        password: 'nacos'
      },
      mcp: {
        host: '0.0.0.0',
        port: 0
      }
    });
    
    // Inject our mocks into the router
    // @ts-ignore - accessing private property for testing
    router.mcpManager = mcpManager as any;
    // @ts-ignore - accessing private property for testing
    router.searchService = searchService;
    
    // Verify the searchService is properly set
    if (!router['searchService']) {
      throw new Error('searchService not properly set on router');
    }
  });

  // Helper function to verify server has all required methods
  function verifyServerMethods(server: NacosMcpServer) {
    try {
      expect(server).toBeDefined();
      expect(server).toBeInstanceOf(Object);
      
      // Check for required methods
      const requiredMethods = ['getName', 'getDescription', 'getAgentConfig', 'toDict'];
      requiredMethods.forEach(method => {
        expect(server).toHaveProperty(method);
        expect(typeof (server as any)[method]).toBe('function');
      });
      
      // Verify method calls don't throw and return expected types
      expect(() => {
        const name = server.getName();
        expect(typeof name).toBe('string');
      }).not.toThrow();
      
      expect(() => {
        const desc = server.getDescription();
        expect(desc === undefined || typeof desc === 'string').toBe(true);
      }).not.toThrow();
      
      expect(() => {
        const agentConfig = server.getAgentConfig();
        expect(agentConfig).toBeDefined();
        expect(typeof agentConfig).toBe('object');
      }).not.toThrow();
      
      expect(() => {
        const dict = server.toDict();
        expect(dict).toBeDefined();
        expect(typeof dict).toBe('object');
        expect(dict).toHaveProperty('name');
        expect(dict).toHaveProperty('description');
        expect(dict).toHaveProperty('agentConfig');
      }).not.toThrow();
      
    } catch (error) {
      console.error('Server verification failed:', {
        server,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  it.each(searchTestCases)("%s", async testCase => {
    const { taskDescription, keyWords } = testCase.input;
    const { minResults, expectedKeywords, descriptionShouldContain } = testCase.expected;

    // Router method requires at least one keyword – cast to the required tuple type
    const results = await router.searchMcpServer(
      taskDescription,
      keyWords as [string, ...string[]]
    );

    // Minimum result count
    expect(results.length).toBeGreaterThanOrEqual(minResults);

    // Expected keywords contained in server names
    if (expectedKeywords) {
      expectedKeywords.forEach(k => {
        const has = results.some(r => r.name.includes(k));
        expect(has).toBe(true);
      });
    }

    // Expected substrings in description
    if (descriptionShouldContain) {
      descriptionShouldContain.forEach(substr => {
        const has = results.some(r => r.description.includes(substr));
        expect(has).toBe(true);
      });
    }
  });
});
