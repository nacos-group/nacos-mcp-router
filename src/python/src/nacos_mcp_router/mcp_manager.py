#-*- coding: utf-8 -*-
import functools
import os
import time
import itertools
import asyncio
from typing import Optional, List

from chromadb.api.types import ID

from .md5_util import get_md5
from .nacos_http_client import NacosHttpClient
from .router_types import ChromaDb, McpServer
from .logger import NacosMcpRouteLogger
from .constants import MODE_ROUTER
import threading

logger = NacosMcpRouteLogger.get_logger()

class McpUpdater:
  def __init__(self,
               nacosHttpClient: NacosHttpClient,
               chromaDbService: ChromaDb | None = None,
               update_interval: float = 60,
               enable_vector_db: bool = True,
               mode: str = MODE_ROUTER,
               proxy_mcp_name: str = "",
               enable_auto_refresh: bool = True):
    self.nacosHttpClient = nacosHttpClient
    self.chromaDbService = chromaDbService
    self.interval = update_interval
    self._running = False
    self._update_task: Optional[asyncio.Task] = None
    self.mcp_server_config_version = {}
    self._cache = dict[str, McpServer]()
    self._chromaDbId = f"nacos_mcp_router_collection"
    self.enable_vector_db = enable_vector_db
    self.lock = threading.Lock()
    self.mode = mode
    self.proxy_mcp_name = proxy_mcp_name
    self.enable_auto_refresh = enable_auto_refresh
    self._thread = None

  @classmethod
  def create(cls,
             nacos_client: NacosHttpClient,
             chroma_db: ChromaDb | None = None,
             update_interval: float = 30,
             enable_vector_db: bool = False,
             mode: str = MODE_ROUTER,
             proxy_mcp_name: str = "",
             enable_auto_refresh: bool = True):
    """创建 McpUpdater 实例并启动后台任务"""
    updater = cls(nacos_client, chroma_db, update_interval, enable_vector_db, mode, proxy_mcp_name, enable_auto_refresh)
 
    updater._thread = threading.Thread(target=functools.partial(updater.asyncUpdater))
    updater._thread.daemon = True
    
    if enable_auto_refresh:
        updater._thread.start()
    
    return updater

  def asyncUpdater(self) -> None:
    debug_mode = os.getenv('DEBUG_MODE')
    if debug_mode is not None:
      logger.info("debug mode is enabled")
      return

    while True:
      try:
        if self.mode == MODE_ROUTER:
            asyncio.run(self.refresh())
        else:
            asyncio.run(self.refreshOne())
        time.sleep(self.interval)
      except Exception as e:
        logger.warning("exception while updating mcp servers: " , exc_info=e)

  def get_deleted_ids(self) -> List[str]:
    if self.chromaDbService is None:
      return []

    all_ids_in_chromadb = self.chromaDbService.get_all_ids()
    if all_ids_in_chromadb is None:
      return []

    deleted_id = []
    for id in all_ids_in_chromadb:
      if id not in self._cache:
        deleted_id.append(id)
    return deleted_id

  async def refresh(self) -> None:
    """刷新所有 MCP 服务器"""
    if not self.enable_auto_refresh:
      return
    
    try:
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
          if self.enable_vector_db:
            docs.append(des)
      with self.lock:
        self._cache = cache

      if not ids:
        return
      if self.enable_vector_db and self.chromaDbService is not None:
        self.chromaDbService.update_data(documents=docs, ids=ids)
        deleted_id = self.get_deleted_ids()
        if len(deleted_id) > 0 and len(mcpServers) > 0:
          self.chromaDbService.delete_data(ids=deleted_id)
    except Exception as e:
      logger.warning("exception while refreshing mcp servers: ", exc_info=e)

  async def refreshOne(self) -> None:
    """刷新单个 MCP 服务器"""
    try:
      mcpServer = await self.nacosHttpClient.get_mcp_server(id='', name=self.proxy_mcp_name)
      if mcpServer is None:
        return
      docs = []
      ids = []
      cache = {}
      des = mcpServer.description
      detail = mcpServer.mcp_config_detail
      if detail is not None:
        des = detail.get_tool_description()

      name = mcpServer.get_name()
      sname = str(name)

      cache[sname] = mcpServer

      md5_str = get_md5(des)

      with self.lock:
        self._cache = cache
    except Exception as e:
      logger.warning("exception while updating mcp server: ", exc_info=e)

  async def _get_from_cache(self, id: str) -> Optional[McpServer]:
    """从缓存中获取 MCP 服务器"""
    with self.lock:
      return self._cache.get(id)

  async def _cache_values(self) -> List[McpServer]:
    """获取缓存中的所有值"""
    with self.lock:
      return list(self._cache.values())

  async def getMcpServer(self, query: str, count: int) -> List[McpServer]:
    """通过查询获取 MCP 服务器"""
    if not self.enable_vector_db or self.chromaDbService is None:
      return []

    try:
      result = self.chromaDbService.query(query, count)
      if result is None:
        return []
      
      ids = result.get('ids')
      logger.info("find mcps in vector db, query: " + query + ",ids: " + str(ids))
      if ids is None:
        return []

      mcp_servers = []
      for id1 in itertools.chain.from_iterable(ids):
        server = await self._get_from_cache(id1)
        if server is not None:
          mcp_servers.append(server)
      
      return mcp_servers
      
    except Exception as e:
      logger.warning(f"exception while getting mcp server by query: {query}", exc_info=e)
      return []

  async def search_mcp_by_keyword(self, keyword: str) -> List[McpServer]:
    """通过关键词搜索 MCP 服务器"""
    try:
      servers = []
      cache_values = await self._cache_values()
      logger.info("cache size: " + str(len(cache_values)))

      for mcp_server in cache_values:
        if mcp_server.description is None:
          continue

        if keyword in mcp_server.description:
          servers.append(mcp_server)

      logger.info(f"result mcp servers search by keywords: {len(servers)}, key: {keyword}")
      return servers
      
    except Exception as e:
      logger.warning(f"exception while searching mcp by keyword: {keyword}", exc_info=e)
      return []

  async def get_mcp_server_by_name(self, mcp_name: str) -> Optional[McpServer]:
    """通过名称获取 MCP 服务器"""
    return await self._get_from_cache(mcp_name)

