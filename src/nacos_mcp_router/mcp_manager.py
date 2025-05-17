import functools
import os
import threading
import time
import traceback

from md5_util import get_md5
from nacos_http_client import NacosHttpClient
from router_types import ChromaDb, McpServer
from logger import NacosMcpRouteLogger


class McpUpdater:
  def __init__(self, nacosHttpClient: NacosHttpClient, chromaDbService: ChromaDb, update_interval: float) -> None:
    self.nacosHttpClient = nacosHttpClient
    self.chromaDbService = chromaDbService
    self.interval = update_interval
    self._loop = None
    self._thread = None
    self._running = False
    self.mcp_server_config_version={}
    self._cache = dict[str, McpServer]()
    self.updateNow()
    self._thread = threading.Thread(target=functools.partial(self.asyncUpdater))
    self._thread.daemon = False
    self._thread.start()
    self._chromaDbId = "nacos_mcp_router_collection_" + str(os.getpid())


  def updateNow(self)-> None:
    mcpServers = self.nacosHttpClient.get_mcp_servers()
    NacosMcpRouteLogger.get_logger().info("get mcp server list from nacos, size: " + str(len(mcpServers)))
    if len(mcpServers) == 0:
      return

    docs = []
    ids = []
    cache = {}
    for mcpServer in mcpServers:
      des = mcpServer.description
      if mcpServer.mcp_config_detail is not None:
        des = mcpServer.mcp_config_detail.get_tool_description()

      cache[str(mcpServer.get_name())] = mcpServer
      md5_str = get_md5(des)
      if mcpServer.name not in self.mcp_server_config_version or self.mcp_server_config_version[mcpServer.name] != md5_str:
        self.mcp_server_config_version[mcpServer.name] = md5_str
        ids.append(str(mcpServer.get_name()))
        docs.append(des)



    self._cache = cache

    if len(ids) > 0:
      self.chromaDbService.update_data(
        documents=docs,
        ids=ids)
  def asyncUpdater(self) -> None:
    while True:
      try:
        time.sleep(self.interval)
        self.updateNow()
      except Exception as e:
        NacosMcpRouteLogger.get_logger().warning("exception while updating mcp servers: " , exc_info=e)

  def getMcpServer(self, query: str, count: int) -> list[McpServer]:
    result = self.chromaDbService.query(query,count)
    ids = result['ids']
    mcp_servers = list[McpServer]()
    for id in ids:
      for id1 in id:
        mcp_server = self._cache.get(id1)
        if mcp_server is not None:
          mcp_servers.append(mcp_server)
    return mcp_servers

  def search_mcp_by_keyword(self, keyword: str) -> list[McpServer]:
    servers = list[McpServer]()
    NacosMcpRouteLogger.get_logger().info("cache size: " + str(len(self._cache.values())))

    for mcp_server in self._cache.values():

      if mcp_server.description is None:
        continue
      if keyword in mcp_server.description:
        servers.append(mcp_server)
    NacosMcpRouteLogger.get_logger().info("result mcp servers search by keywords: " + str(len(servers)))
    return servers

  def get_mcp_server_by_name(self, mcp_name: str) -> McpServer:
    result = self._cache[mcp_name]
    return result

