import axios from 'axios';
import { describe, it, expect } from '@jest/globals';

const nacosAddr = 'localhost:8848';
const userName = 'nacos';
const passwd = 'uhn5FD0Itp';

describe('Nacos HTTP Client Tests', () => {
  it('should successfully fetch MCP list from Nacos', async () => {
    const config = {
      method: 'get',
      url: `http://${nacosAddr}/nacos/v3/admin/ai/mcp/list?pageNo=1&pageSize=100`,
      headers: { 
        'Content-Type': 'application/json', 
        'charset': 'utf-8', 
        'userName': userName, 
        'password': passwd
      }
    };

    const response = await axios.request(config);
    expect(response.status).toBe(200);
    expect(response.data).toBeDefined();
    // 如果需要，可以添加更多具体的断言
    // expect(response.data).toHaveProperty('data');
  });
});
