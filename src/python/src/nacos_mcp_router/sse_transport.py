from mcp import ClientSession
from mcp.types import CallToolRequest
from mcp.client.sse import sse_client
from typing import Any
import asyncio
from .mcp_transport import McpTransport
from mcp.types import Tool
from mcp.types import InitializeResult
from .logger import NacosMcpRouteLogger
from mcp.types import ListToolsResult
class McpSseTransport(McpTransport):
    def __init__(self, url: str, headers: dict[str, str]):
        self.url = url
        self.headers = headers
        if 'Content-Length' in self.headers:
            del self.headers['Content-Length']

    async def handle_tool_call(self, args: dict[str, Any], client_headers: dict[str, str], name: str):
        """处理tool调用，转发客户端headers到目标服务器"""
        # 使用特定headers连接目标服务器
        async with sse_client(
            url=self.url,
            headers=self.clean_headers(client_headers)
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(name=name, arguments=args)
    async def handle_list_tools(self, client_headers: dict[str, str]) -> ListToolsResult:
        NacosMcpRouteLogger.get_logger().info(f"handle_list_tools, url: {self.url}, headers: {client_headers}")

        async with sse_client(
            url=self.url,
            headers=self.clean_headers(client_headers)
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.list_tools()
    async def handle_initialize(self, client_headers: dict[str, str]) -> InitializeResult:
        async with sse_client(
            url=self.url,
            headers=self.clean_headers(client_headers)
        ) as (read, write):
            async with ClientSession(read, write) as session:
                return await session.initialize()