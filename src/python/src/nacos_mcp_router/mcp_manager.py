#-*- coding: utf-8 -*-
import functools
import os
import threading
import time
import itertools
import asyncio

from chromadb.api.types import ID

from .md5_util import get_md5
from .nacos_http_client import NacosHttpClient
from .router_types import ChromaDb, McpServer
from .logger import NacosMcpRouteLogger

logger = NacosMcpRouteLogger.get_logger()

class McpUpdater:
  def __init__(self,
               nacosHttpClient: NacosHttpClient,
               chromaDbService: ChromaDb | None = None,
               update_interval: float = 60,
               enable_vector_db: bool = True) -> None:
    self.nacosHttpClient = nacosHttpClient
    self.chromaDbService = chromaDbService
    self.interval = update_interval
    self._loop = None
    self._thread = None
    self._running = False
    self.mcp_server_config_version={}
    self._cache = dict[str, McpServer]()
    self._chromaDbId = f"nacos_mcp_router_collection"
    self.enable_vector_db = enable_vector_db
    self.lock = threading.RLock()

  @classmethod
  async def create(cls,
             nacos_client: NacosHttpClient,
             chroma_db: ChromaDb | None = None,
             update_interval: float = 30,
             enable_vector_db: bool = False):

    updater = cls(nacos_client, chroma_db, update_interval, enable_vector_db)
    await updater.refresh()
    updater._thread = threading.Thread(target=functools.partial(updater.asyncUpdater))
    updater._thread.daemon = False
    updater._thread.start()
    return updater
  def get_deleted_ids(self) -> list[str]:
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

  def _get_from_cache(self, id:str) :
    with self.lock:
      if id in self._cache:
        return self._cache[id]
      return None


  def _cache_values(self):
    with self.lock:
      return self._cache.values()

  def getMcpServer(self, query: str, count: int) -> list[McpServer]:
    if not self.enable_vector_db or self.chromaDbService is None:
      return []

    result = self.chromaDbService.query(query, count)
    if result is None:
      return []
    
    ids = result.get('ids')
    logger.info("find mcps in vector db, query: " + query + ",ids: " + str(ids))
    if ids is None:
      return []

    mcp_servers = [self._get_from_cache(id1)
                   for id1  
                   in itertools.chain.from_iterable(ids)]
    
    mcp_servers = [s for s in mcp_servers if s is not None]

    return mcp_servers

  def search_mcp_by_keyword(self, keyword: str) -> list[McpServer]:
    servers = list[McpServer]()
    cache_values = self._cache_values()
    logger.info("cache size: " + str(len(cache_values)))

    for mcp_server in cache_values:
      if mcp_server.description is None:
        continue

      if keyword in mcp_server.description:
        servers.append(mcp_server)

    logger.info(f"result mcp servers search by keywords: {len(servers)}, key: {keyword}")
    return servers

  def get_mcp_server_by_name(self, mcp_name: str) -> McpServer | None:
    return self._get_from_cache(mcp_name)
    

