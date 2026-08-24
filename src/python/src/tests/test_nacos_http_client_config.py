import asyncio
import unittest
from unittest.mock import AsyncMock

from ..nacos_mcp_router.nacos_http_client import NacosHttpClient


class NacosHttpClientConfigTests(unittest.TestCase):

    def test_get_mcp_server_wraps_flat_stdio_config(self):
        client = NacosHttpClient({
            "nacosAddr": "localhost:8848",
            "userName": "nacos",
            "password": "nacos",
            "namespaceId": "",
            "ak": "",
            "sk": "",
        })
        client.request_nacos = AsyncMock(return_value=(True, {
            "name": "filesystem",
            "protocol": "stdio",
            "description": "Filesystem server",
            "version": "1.0.0",
            "remoteServerConfig": {},
            "localServerConfig": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "env": {"ROOT": "/tmp"},
            },
        }))

        server = asyncio.run(client.get_mcp_server("mcp-1", "filesystem"))

        self.assertEqual({
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                    "env": {"ROOT": "/tmp"},
                    "protocol": "stdio",
                }
            }
        }, server.agentConfig)

    def test_get_mcp_server_preserves_wrapped_stdio_config(self):
        local_server_config = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                }
            }
        }
        client = NacosHttpClient({
            "nacosAddr": "localhost:8848",
            "userName": "nacos",
            "password": "nacos",
            "namespaceId": "",
            "ak": "",
            "sk": "",
        })
        client.request_nacos = AsyncMock(return_value=(True, {
            "name": "filesystem",
            "protocol": "stdio",
            "description": "Filesystem server",
            "version": "1.0.0",
            "remoteServerConfig": {},
            "localServerConfig": local_server_config,
        }))

        server = asyncio.run(client.get_mcp_server("mcp-1", "filesystem"))

        self.assertIs(
            local_server_config["mcpServers"], server.agentConfig["mcpServers"]
        )
        self.assertEqual("stdio", server.agentConfig["protocol"])


if __name__ == "__main__":
    unittest.main()
