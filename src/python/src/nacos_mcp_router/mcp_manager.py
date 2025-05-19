#-*- coding: utf-8 -*-
import functools
import os
import threading
import time
import itertools
import asyncio

from .md5_util import get_md5
from .nacos_http_client import NacosHttpClient
from .router_types import ChromaDb, McpServer
from .logger import NacosMcpRouteLogger

logger = NacosMcpRouteLogger.get_logger()

class McpUpdater:
  def __init__(self,
               nacosHttpClient: NacosHttpClient,
               chromaDbService: ChromaDb,
               update_interval: float) -> None:
    self.nacosHttpClient = nacosHttpClient
    self.chromaDbService = chromaDbService
    self.interval = update_interval
    self._loop = None
    self._thread = None
    self._running = False
    self.mcp_server_config_version={}
    self._cache = dict[str, McpServer]()
    self._chromaDbId = f"nacos_mcp_router_collection_{os.getpid()}"

  @classmethod
  async def create(cls,
             nacos_client: NacosHttpClient,
             chroma_db: ChromaDb,
             update_interval: float):

    updater = cls(nacos_client, chroma_db, update_interval)
    await updater.refresh()
    updater._thread = threading.Thread(target=functools.partial(updater.asyncUpdater))
    updater._thread.daemon = False
    updater._thread.start()

    return updater

  async def refresh(self)-> None:
    mcpServers = await self.nacosHttpClient.get_mcp_servers()
    logger.info(f"get mcp server list from nacos, size: {len(mcpServers)}")
    if not mcpServers:
      return

    docs = []
    ids = []
    cache = {}

    for mcpServer in mcpServers:
      des = mcpServer.description
      detail = mcpServer.mcp_config_detail
      if detail is not None:
        des = detail.get_tool_description()

      name = mcpServer.get_name()
      sname = str(name)

      cache[sname] = mcpServer
      md5_str = get_md5(des)
      version = self.mcp_server_config_version.get(sname, '')

      if version != md5_str:
        self.mcp_server_config_version[sname] = md5_str
        ids.append(sname)
        docs.append(des)

    self._cache = cache

    if not ids:
      return
      
    self.chromaDbService.update_data(documents=docs, ids=ids)
      
  def asyncUpdater(self) -> None:
    debug_mode = os.getenv('DEBUG_MODE')
    if debug_mode is not None:
      logger.info("debug mode is enabled")
      return

    while True:
      try:
        time.sleep(self.interval)
        asyncio.run(self.refresh())
      except Exception as e:
        logger.warning("exception while updating mcp servers: " , exc_info=e)

  def getMcpServer(self, query: str, count: int) -> list[McpServer | None]:
    result = self.chromaDbService.query(query, count)
    if result is None:
      return []
    
    ids = result.get('ids')
    if ids is None:
      return []
    
    mcp_servers = [self._cache.get(id1) 
                   for id1  
                   in itertools.chain.from_iterable(ids)]
    
    mcp_servers = [s for s in mcp_servers if s is not None]

    return list(mcp_servers)

  def search_mcp_by_keyword(self, keyword: str) -> list[McpServer]:
    servers = list[McpServer]()
    logger.info("cache size: " + str(len(self._cache.values())))

    for mcp_server in self._cache.values():
      if mcp_server.description is None:
        continue

      if keyword in mcp_server.description:
        servers.append(mcp_server)

    logger.info(f"result mcp servers search by keywords: {len(servers)}")
    return servers

  def get_mcp_server_by_name(self, mcp_name: str) -> McpServer | None:
    return self._cache.get(mcp_name)
    

