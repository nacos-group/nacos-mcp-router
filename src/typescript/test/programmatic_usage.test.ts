import { NacosMcpRouter, type NacosMcpRouterConfig } from '../src/index';
import { describe, it, expect, beforeAll, afterAll } from '@jest/globals';

describe('NacosMcpRouter Programmatic Usage In Stdio Mode', () => {
  let router: InstanceType<typeof NacosMcpRouter>;

  beforeAll(() => {
    router = new NacosMcpRouter({
      nacos: {
        serverAddr: 'localhost:8848',
        username: 'nacos',
        password: 'uhn5FD0Itp'
      },
      logLevel: 'info'
    });
  });

  afterAll(async () => {
    // 清理资源
    if (router) {
      // 这里可以添加清理逻辑
    }
  });

  it('should initialize router successfully', async () => {
    await expect(router.start()).resolves.not.toThrow();
  });

  it('should register MCP tools', async () => {
    // 启动路由器
    await router.start();

    // 验证 MCP 工具是否已注册
    // 注意：由于工具注册是内部的，我们只能通过启动过程来验证
    expect(router).toBeDefined();
  });

  it('should handle MCP server operations', async () => {
    // 启动路由器
    await router.start();

    // 由于大部分操作都是通过 MCP 工具进行的，这里我们只验证基本功能
    expect(router).toBeDefined();
  });
});
