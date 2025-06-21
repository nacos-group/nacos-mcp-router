import { NacosMcpServer } from '../../src/router_types';

export interface SearchTestCase {
  name: string;
  input: {
    taskDescription: string;
    keyWords: string[];
  };
  expected: {
    minResults: number;
    expectedKeywords?: string[];
    descriptionShouldContain?: string[];
  };
}

export const searchTestCases: SearchTestCase[] = [
  {
    name: 'should find MCP servers by exact name',
    input: {
      taskDescription: 'Find MCP server by exact name',
      keyWords: ['exact-server-name']
    },
    expected: {
      minResults: 1,
      expectedKeywords: ['exact-server-name']
    }
  },
  {
    name: 'should find MCP servers by description keywords',
    input: {
      taskDescription: 'Find MCP servers related to database operations',
      keyWords: ['database', 'query']
    },
    expected: {
      minResults: 1,
      descriptionShouldContain: ['database', 'queries']
    }
  },
  {
    name: 'should handle empty results gracefully',
    input: {
      taskDescription: 'Non-existent server search',
      keyWords: ['nonexistent12345']
    },
    expected: {
      minResults: 0
    }
  },
  {
    name: 'should handle special characters in search',
    input: {
      taskDescription: 'Search with special characters',
      keyWords: ['api-v1', 'test@example.com']
    },
    expected: {
      minResults: 0
    }
  }
];

export const mockMcpServers: NacosMcpServer[] = [
  {
    name: 'exact-server-name',
    description: 'A test server for exact name matching exact-server-name',
    mcpConfigDetail: null,
    agentConfig: {},
    getName: () => 'exact-server-name',
    getDescription: () => 'A test server for exact name matching: exact-server-name',
    getAgentConfig: () => ({}),
    toDict: () => ({
      name: 'exact-server-name',
      description: 'A test server for exact name matching exact-server-name',
      mcpConfigDetail: null,
      agentConfig: {}
    })
  },
  {
    name: 'database-query-server',
    description: 'Handles database queries and operations',
    mcpConfigDetail: null,
    agentConfig: {},
    getName: () => 'database-query-server',
    getDescription: () => 'Handles database queries and operations',
    getAgentConfig: () => ({}),
    toDict: () => ({
      name: 'database-query-server',
      description: 'Handles database queries and operations',
      mcpConfigDetail: null,
      agentConfig: {}
    })
  }
];
