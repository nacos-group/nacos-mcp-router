from typing import Any
from mcp.types import Tool
from mcp.types import CallToolResult
from mcp.types import InitializeResult
from mcp.types import ListToolsResult

class McpTransport:
    def __init__(self, url: str, headers: dict[str, str]):
        self.url = url
        self.headers = headers
    
    async def handle_tool_call(self, args: dict[str, Any], client_headers: dict[str, str], name: str) -> Any:
        pass

    async def handle_list_tools(self, client_headers: dict[str, str]) -> Any:
        pass

    async def handle_initialize(self, client_headers: dict[str, str]) -> Any:
        pass

    def clean_headers(self, client_headers: dict[str, str]) -> dict[str, str]:
        return {k: v for k, v in client_headers.items() if k != 'Content-Length' and k != 'content-length' and k != 'host' and k != 'Host'}

    def merged_headers(self, client_headers: dict[str, str]) -> dict[str, str]:
        """Merge registered headers (self.headers) with client request headers.

        - Registered headers (e.g. auth headers from the Nacos registration config)
          take precedence so downstream servers always receive them.
        - Other headers from the client are passed through.
        - Deduplication is case-insensitive: client header names may be lowercase,
          and keeping both would send two same-named headers that confuse downstream
          parsers."""
        merged = self.clean_headers(client_headers)
        for k, v in self.headers.items():
            lk = k.lower()
            for mk in [mk for mk in merged if mk.lower() == lk]:
                del merged[mk]
            merged[k] = v
        return merged