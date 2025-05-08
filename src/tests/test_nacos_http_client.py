import unittest, os, asyncio

from nacos_mcp_router.nacos_http_client import NacosHttpClient, McpServer, Tool

class TestNacosHttpClient(unittest.TestCase):

    def setUp(self):

        self.client = NacosHttpClient(nacosAddr="localhost:8848", userName="nacos", passwd="pass")

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
