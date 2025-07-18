from mcp import ClientSession
from mcp.types import CallToolRequest
from mcp.client.streamable_http import streamablehttp_client
from typing import Any
import asyncio
from .mcp_transport import McpTransport
from mcp.types import Tool
from mcp.types import InitializeResult
from mcp.types import ListToolsResult
from mcp.types import CallToolResult

class McpStreamableHttpTransport(McpTransport):
    def __init__(self, url: str, headers: dict[str, str]):
        self.url = url
        self.headers = headers
        if 'Content-Length' in self.headers:
            del self.headers['Content-Length']
    async def handle_tool_call(self, args: dict[str, Any], client_headers: dict[str, str], name: str) -> CallToolResult:
        """处理tool调用，转发客户端headers到目标服务器"""
        # 使用特定headers连接目标服务器
        
        async with streamablehttp_client(
            url=self.url,
            headers=self.clean_headers(client_headers)
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                return await session.call_tool(name=name, arguments=args)
    async def handle_list_tools(self, client_headers: dict[str, str]) -> ListToolsResult:
        async with streamablehttp_client(
            url=self.url,
            headers=self.clean_headers(client_headers)
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                return await session.list_tools()
            
    async def handle_initialize(self, client_headers: dict[str, str]) -> InitializeResult:
        async with streamablehttp_client(
            url=self.url,
            headers=self.clean_headers(client_headers)
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                return await session.initialize()
async def main():
    transport = McpStreamableHttpTransport(
        url="http://localhost:9001/mcp",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer 1234567890"
        }
    )
    result = await transport.handle_tool_call(args={"a": 4,"b":4}, client_headers={}, name="add")
    print(result)
    

if __name__ == "__main__":
    asyncio.run(main())