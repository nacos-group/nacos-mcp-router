#!/usr/bin/env node

const express = require('express');
const app = express();

app.use(express.json());

// Mock data for testing
const mockMcpServers = [
  {
    name: 'exact-server-name',
    description: 'A test server for exact name matching exact-server-name',
    protocol: 'stdio',
    backendEndpoints: [],
    localServerConfig: {
      command: 'node',
      args: ['test-server.js']
    }
  },
  {
    name: 'database-query-server', 
    description: 'Handles database queries and operations',
    protocol: 'stdio',
    backendEndpoints: [],
    localServerConfig: {
      command: 'node',
      args: ['db-server.js']
    }
  },
  {
    name: 'file-server',
    description: 'File management and operations server',
    protocol: 'stdio', 
    backendEndpoints: [],
    localServerConfig: {
      command: 'node',
      args: ['file-server.js']
    }
  }
];

// Health check endpoint for isReady() and getMcpServers()
app.get('/nacos/v3/admin/ai/mcp/list', (req, res) => {
  console.log('Mock Nacos: Received MCP list request');
  
  // Handle pagination parameters
  const pageNo = parseInt(req.query.pageNo) || 1;
  const pageSize = parseInt(req.query.pageSize) || 100;
  
  // Format response to match expected structure
  const pageItems = mockMcpServers.map(server => ({
    name: server.name,
    description: server.description,
    enabled: true,
    protocol: server.protocol,
    createTime: new Date().toISOString(),
    updateTime: new Date().toISOString()
  }));
  
  res.status(200).json({
    code: 200,
    message: 'success',
    data: {
      pageItems: pageItems,
      totalCount: pageItems.length,
      pageNo: pageNo,
      pageSize: pageSize
    }
  });
});

// Get specific MCP server by name
app.get('/nacos/v3/admin/ai/mcp', (req, res) => {
  const mcpName = req.query.mcpName;
  console.log(`Mock Nacos: Received request for MCP server: ${mcpName}`);
  
  const server = mockMcpServers.find(s => s.name === mcpName);
  
  if (server) {
    res.status(200).json({
      code: 200,
      message: 'success',
      data: server
    });
  } else {
    res.status(404).json({
      code: 404,
      message: 'MCP server not found',
      data: null
    });
  }
});

// Search MCP servers by keyword
app.get('/nacos/v3/admin/ai/mcp/search', (req, res) => {
  const keyword = req.query.keyword || '';
  console.log(`Mock Nacos: Received search request for keyword: ${keyword}`);
  
  const filteredServers = mockMcpServers.filter(server => 
    server.name.toLowerCase().includes(keyword.toLowerCase()) ||
    server.description.toLowerCase().includes(keyword.toLowerCase())
  );
  
  res.status(200).json({
    code: 200,
    message: 'success',
    data: filteredServers
  });
});

// Update MCP tools list (for testing purposes)
app.post('/nacos/v3/admin/ai/mcp/tools', (req, res) => {
  const { mcpName, tools } = req.body;
  console.log(`Mock Nacos: Received tools update for ${mcpName}:`, tools);
  
  res.status(200).json({
    code: 200,
    message: 'Tools updated successfully',
    data: { mcpName, toolsCount: tools ? tools.length : 0 }
  });
});

const PORT = process.env.MOCK_NACOS_PORT || 8848;

const server = app.listen(PORT, () => {
  console.log(`Mock Nacos server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/nacos/v3/admin/ai/mcp/list`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('Mock Nacos server shutting down...');
  server.close(() => {
    console.log('Mock Nacos server stopped');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('Mock Nacos server shutting down...');
  server.close(() => {
    console.log('Mock Nacos server stopped');
    process.exit(0);
  });
});

module.exports = app;