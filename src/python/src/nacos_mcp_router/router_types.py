#-*- coding: utf-8 -*-

import asyncio
import logging
import os
from contextlib import AsyncExitStack
from typing import Optional, Any

import chromadb
import mcp.types
from chromadb import Metadata
from chromadb.config import Settings
from chromadb.api.types import OneOrMany, ID, Document, GetResult, QueryResult
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from .logger import NacosMcpRouteLogger
from .nacos_mcp_server_config import NacosMcpServerConfig
from mcp.client.streamable_http import streamablehttp_client


def _stdio_transport_context(config: dict[str, Any]):
  server_params = StdioServerParameters(command=config['command'], args=config['args'] if 'args' in config else [], env=config['env'] if 'env' in config else {})
  return stdio_client(server_params)

def _sse_transport_context(config: dict[str, Any]):
  return sse_client(url=config['url'], headers=config['headers'] if 'headers' in config else {}, timeout=10)

def _streamable_http_transport_context(config: dict[str, Any]):
  return streamablehttp_client(url=config["url"], headers=config['headers'] if 'headers' in config else {})

class CustomServer:
  def __init__(self, name: str, config: dict[str, Any]) -> None:
    self.name: str = name
    self.config: dict[str, Any] = config
    self.stdio_context: Any | None = None
    self.session: ClientSession | None = None
    self._cleanup_lock: asyncio.Lock = asyncio.Lock()
    self.exit_stack: AsyncExitStack = AsyncExitStack()
    self._initialized_event = asyncio.Event()
    self._shutdown_event = asyncio.Event()
    self._initialized: bool = False  # 初始化状态标记
    if 'protocol' in config['mcpServers'][name] and  "mcp-sse" == config['mcpServers'][name]['protocol']:
      self._transport_context_factory = _sse_transport_context
      self._protocol = 'mcp-sse'
    elif 'protocol' in config['mcpServers'][name] and "mcp-streamable" == config['mcpServers'][name]['protocol']:
      self._transport_context_factory = _streamable_http_transport_context
      self._protocol = 'mcp-streamable'
    else:
      self._transport_context_factory = _stdio_transport_context
      self._protocol = 'stdio'

    self._server_task = asyncio.create_task(self._server_lifespan_cycle())



  async def _server_lifespan_cycle(self):
    try:
      server_config = self.config
      if "mcpServers" in self.config:
        mcp_servers = self.config["mcpServers"]
        for key, value in mcp_servers.items():
          server_config = value
      if self._protocol == 'mcp-streamable':
        async with _streamable_http_transport_context(server_config) as (read, write, _):
          async with ClientSession(read, write) as session:
            self.session_initialized_response = await session.initialize()
            self.session = session
            self._initialized = True
            self._initialized_event.set()
            await self.wait_for_shutdown_request()
      elif self._protocol == 'mcp-sse':
        async with _sse_transport_context(server_config) as (read, write):
          async with ClientSession(read, write) as session:
            self.session_initialized_response = await session.initialize()
            self.session = session
            self._initialized = True
            self._initialized_event.set()
            await self.wait_for_shutdown_request()
      else:
        async with _stdio_transport_context(server_config) as (read, write):
          async with ClientSession(read, write) as session:
            self.session_initialized_response = await session.initialize()
            self.session = session
            self._initialized = True
            self._initialized_event.set()
            await self.wait_for_shutdown_request()
    except Exception as e:
      NacosMcpRouteLogger.get_logger().warning("failed to init mcp server " + self.name + ", config: " + str(self.config), exc_info=e)
      self._initialized = False
      self._initialized_event.set()
      self._shutdown_event.set()
  def get_initialized_response(self) -> mcp.types.InitializeResult:
    return self.session_initialized_response

  async def healthy(self) -> bool:
    """更新healthy方法，增加更详细的检查"""
    return (self.session is not None and 
            self._initialized and 
            not self._shutdown_event.is_set()
            and not await self.is_session_disconnected())

  async def wait_for_initialization(self):
    await self._initialized_event.wait()

  async def request_for_shutdown(self):
    self._shutdown_event.set()

  async def wait_for_shutdown_request(self):
    await self._shutdown_event.wait()

  async def list_tools(self) -> list[mcp.types.Tool]:
    if not self.session:
      raise RuntimeError(f"Server {self.name} is not initialized")

    tools_response = await self.session.list_tools()

    return tools_response.tools

  async def execute_tool(
          self,
          tool_name: str,
          arguments: dict[str, Any],
          retries: int = 2,
          delay: float = 1.0,
  ) -> Any:
    if not self.session:
      raise RuntimeError(f"Server {self.name} not initialized")

    attempt = 0
    while attempt < retries:
      try:
        result = await self.session.call_tool(tool_name, arguments)

        return result

      except Exception as e:
        attempt += 1
        if attempt < retries:
          await asyncio.sleep(delay)
          await self.session.initialize()
          try:
            result = await self.session.call_tool(tool_name, arguments)
            return result
          except Exception as e:
            raise e
        else:
          raise



  async def cleanup(self) -> None:
    """Clean up server resources."""
    async with self._cleanup_lock:
      try:
        await self.exit_stack.aclose()
        self.session = None
        self.stdio_context = None
      except Exception as e:
        logging.error(f"Error during cleanup of server {self.name}: {e}")

  async def is_session_disconnected(self, timeout: float = 5.0) -> bool:
    """
    检查session是否断开连接
    
    Args:
        timeout: 检测超时时间（秒）
        
    Returns:
        bool: True表示连接断开，False表示连接正常
    """
    # 基础检查：session对象是否存在
    if not self.session:
      NacosMcpRouteLogger.get_logger().info(f"Server {self.name}: session object is None")
      return True
    
    # 检查是否已初始化
    if not self._initialized:
      NacosMcpRouteLogger.get_logger().info(f"Server {self.name}: not initialized")
      return True
    
    # 检查是否请求关闭
    if self._shutdown_event.is_set():
      NacosMcpRouteLogger.get_logger().info(f"Server {self.name}: shutdown requested")
      return True
    
    try:
      # 尝试执行一个轻量级操作来测试连接
      NacosMcpRouteLogger.get_logger().info(f"Server {self.name}: testing connection health")
      return await self._test_connection_health(timeout)
    except Exception as e:
      NacosMcpRouteLogger.get_logger().warning(f"Server {self.name}: connection test failed: {e}")
      return True

  async def _test_connection_health(self, timeout: float) -> bool:
    import anyio
    """
    测试连接健康状态
    
    Args:
        timeout: 超时时间
        
    Returns:
        bool: True表示连接断开，False表示连接正常
    """
    try:
      # 使用asyncio.wait_for设置超时
      async with asyncio.timeout(timeout):
        if self.session is None:
          return True
        # 尝试调用一个简单的MCP操作
        await self.session.list_tools()
        # 更新最后活动时间
        import time
        self._last_activity_time = time.time()
        return False  # 连接正常
        
    except (asyncio.TimeoutError, mcp.McpError, anyio.ClosedResourceError):
      NacosMcpRouteLogger.get_logger().warning(f"Server {self.name}: connection test timeout after {timeout}s")
      return True
    except (ConnectionError, BrokenPipeError, OSError) as e:
      NacosMcpRouteLogger.get_logger().warning(f"Server {self.name}: connection error: {e}")
      return True
    except Exception as e:
      # 对于其他异常，可能是协议错误或服务器内部错误
      # 这里可以根据具体的异常类型来判断是否是连接问题
      error_msg = str(e).lower()
      if any(keyword in error_msg for keyword in ['connection', 'broken', 'closed', 'reset', 'timeout']):
        NacosMcpRouteLogger.get_logger().warning(f"Server {self.name}: connection-related error: {e}")
        return True
      else:
        # 其他错误可能不是连接问题，连接可能仍然正常
        NacosMcpRouteLogger.get_logger().error(f"Server {self.name}: non-connection error during health check", exc_info=e)
        return False
class McpServer:
  name: str
  description: str
  client: ClientSession
  session: ClientSession
  mcp_config_detail: NacosMcpServerConfig
  agentConfig: dict[str, Any]
  version: str
  def __init__(self, name: str, description: str, agentConfig: dict, id: str, version: str):
    self.name = name
    self.description = description
    self.agentConfig = agentConfig
    self.id = id
    self.version = version
  def get_name(self) -> str:
    return self.name
  def get_description(self) -> str:
    return self.description
  def agent_config(self) -> dict:
    return self.agentConfig
  def to_dict(self):
    return {
      "name": self.name,
      "description": self.description,
      "agentConfig": self.agent_config(),
    }

class ChromaDb:
  def __init__(self) -> None:
    self.dbClient = chromadb.PersistentClient(path=os.path.expanduser("~") + "/.nacos_mcp_router/chroma_db",
                settings=Settings(
                    anonymized_telemetry=False,
                ))
    self._collectionId = "nacos_mcp_router-collection"
    self._collection = self.dbClient.get_or_create_collection(name=self._collectionId)
    self.preIds = []

  def update_data(self, ids: OneOrMany[ID],
        metadatas: Optional[OneOrMany[Metadata]] = None,
        documents: Optional[OneOrMany[Document]] = None,) -> None:
    self._collection.upsert(documents=documents, metadatas=metadatas, ids=ids)

  def get_all_ids(self) -> list[ID]:
    return self._collection.get().get('ids')
  def delete_data(self, ids: list[ID]) -> None:
    self._collection.delete(ids=ids)

  def query(self, query: str, count: int) -> QueryResult:
    NacosMcpRouteLogger.get_logger().info(f"Querying chroma {query}")
    return self._collection.query(
      query_texts=[query],
      n_results=count
    )

  def get(self, id: list[str]) -> GetResult:
    return self._collection.get(ids=id)
