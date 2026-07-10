import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

import { CustomServer } from '../../src/router_types';

describe('CustomServer streamable HTTP protocol', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('selects the streamable HTTP transport factory', () => {
    const server = new CustomServer(
      'test-server',
      { mcpServers: { test: { url: 'http://localhost:3000/mcp' } } },
      'mcp-streamable'
    );

    const factory = (server as any)._transportContextFactory;
    const transport = factory({ url: 'http://localhost:3000/mcp' });

    expect(transport).toBeInstanceOf(StreamableHTTPClientTransport);
  });

  it('passes the current session id to the transport factory', async () => {
    const server = new CustomServer(
      'test-server',
      { mcpServers: { test: { url: 'http://localhost:3000/mcp' } } },
      'mcp-streamable'
    );
    const transport = {} as any;
    const factory = jest.fn(() => transport);
    (server as any)._transportContextFactory = factory;
    (server as any).sessionId = 'existing-session';
    jest.spyOn(Client.prototype, 'connect').mockResolvedValue(undefined);

    await server.start('test');

    expect(factory).toHaveBeenCalledWith({
      url: 'http://localhost:3000/mcp',
      sessionId: 'existing-session'
    });
  });
});
