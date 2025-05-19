import unittest, os, asyncio
import time
from mcp import Tool
from unittest.mock import AsyncMock


class TestAsyncGeneratorsPerformance(unittest.TestCase):
    def setUp(self):
        from nacos_mcp_router.nacos_http_client import NacosHttpClient
        self.client = NacosHttpClient(nacosAddr="localhost:8848", userName="nacos", passwd="pass")
    async def asynchronize(self, item):
        await asyncio.sleep(0.1)  # Simulate async operation
        return item * 2

    async def method_await_for(self, items):
        return [await self.asynchronize(m) for m in items]

    async def method_gather(self, items):
        tasks = [self.asynchronize(m) for m in items]
        return await asyncio.gather(*tasks)

    def test_performance_comparison(self):
        items = list(range(10))  # Example input list

        # Measure performance of method_await_for
        start_time = time.perf_counter()
        result_await_for = asyncio.run(self.method_await_for(items))
        duration_await_for = time.perf_counter() - start_time

        # Measure performance of method_gather
        start_time = time.perf_counter()
        result_gather = asyncio.run(self.method_gather(items))
        duration_gather = time.perf_counter() - start_time

        # Assert results are the same
        self.assertEqual(result_await_for, result_gather)

        # Print performance results
        print(f"method_await_for duration: {duration_await_for:.4f} seconds")
        print(f"method_gather duration: {duration_gather:.4f} seconds")

    #@patch('httpx.AsyncClient.get', new_callable=AsyncMock)
    def test_get_mcp_server_by_name_success(self):
        mcp_server = asyncio.run(self.client.get_mcp_server_by_name("Puppeteer"))
        self.assertEqual(mcp_server.name, "Puppeteer")
        self.assertTrue('Puppeteer' in mcp_server.description, "Check puppeteer is in the returned value.")

    def test_get_mcp_server_by_name_failure(self):
        mcp_server = asyncio.run(self.client.get_mcp_server_by_name("non_existent_mcp"))
        self.assertEqual(mcp_server.name, "non_existent_mcp")
        self.assertEqual(mcp_server.description, "")
        self.assertEqual(mcp_server.agentConfig, {})

    def test_update_mcp_tools_success(self):
        tool = Tool(name="Puppeteer", description="Test Tool-UPDATED", inputSchema={})
        success = asyncio.run(self.client.update_mcp_tools("Puppeteer", [tool]))
        self.assertTrue(success)

    def test_update_mcp_tools_failure(self):

        tool = Tool(name="test_tool", description="Test Tool", inputSchema={})
        success = asyncio.run(self.client.update_mcp_tools("non_existent_mcp", [tool]))
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
