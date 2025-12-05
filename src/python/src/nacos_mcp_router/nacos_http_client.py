#-*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import json
import random
import time
import urllib.parse
import httpx
import asyncio
import os
from mcp import Tool
from packaging import version

from .router_types import McpServer
from .nacos_mcp_server_config import NacosMcpServerConfig
from .logger import NacosMcpRouteLogger

# logger, setup logger if not exists
logger = NacosMcpRouteLogger.get_logger()

# Content types, used in request Nacos Server http headers, default is JSON.
CONTENT_TYPE_JSON = "application/json; charset=utf8"
CONTENT_TYPE_URLENCODED = "application/x-www-form-urlencoded; charset=utf8"

# HTTP schema, default is HTTP
_SCHEMA_HTTP = "http"
_SCHEMA = os.getenv("NACOS_SERVER_SCHEMA", _SCHEMA_HTTP)

class NacosHttpClient:
    def __init__(self, params: dict[str,str]) -> None:
        nacosAddr = params["nacosAddr"]
        userName = params["userName"]
        passwd = params["password"]
    
        self.nacosAddr = nacosAddr
        self.userName = userName
        self.passwd = passwd
        self.schema = _SCHEMA
        self.namespaceId = params["namespaceId"] if params["namespaceId"] else ""
        self.ak = params["ak"] if params["ak"] else ""
        self.sk = params["sk"] if params["sk"] else ""

        if self.ak and not self.sk:
            raise ValueError("ak and sk are required when using nacos http client")
        if self.sk and not self.ak:
            raise ValueError("ak and sk are required when using nacos http client")

        from .auth import StaticCredentialsProvider
        self.credentials_provider = StaticCredentialsProvider(self.ak, self.sk)

    def __do_sign(self, sign_str, sk):
        return base64.encodebytes(
            hmac.new(sk.encode(), sign_str.encode(), digestmod=hashlib.sha1).digest()).decode().strip()

    def _inject_auth_info(self, headers: dict[str, str]) -> None:
        credentials = self.credentials_provider.get_credentials()

        if not str.strip(credentials.get_access_key_id()) or not str.strip(credentials.get_access_key_secret()):
            return

        ts = str(int(round(time.time() * 1000)))
        sign_str = self.namespaceId if self.namespaceId else "public" + "+" + "DEFAULT_GROUP" + "+"+ ts

        headers.update({
            "Spas-AccessKey": credentials.get_access_key_id(),
            "timeStamp": ts,
        })
        headers["Spas-Signature"] = self.__do_sign(sign_str, credentials.get_access_key_secret())

    async def get_mcp_server(self, id: str, name:str) -> McpServer:
        """
        Retrieve an MCP server by its name from the NACOS server.

        This asynchronous method sends a GET request to the NACOS server to fetch the configuration
        of a specific MCP server identified by its name. If the request is successful, it constructs
        an `McpServer` object using the retrieved data. If the request fails, it logs a warning and
        returns an `McpServer` object with default values.

        Args:
            name (str): The name of the MCP server to retrieve.
            id (str): The ID of the MCP server to retrieve.

        Returns:
            McpServer: An [McpServer] object representing the retrieved MCP server. If the request
                       fails, the object will have default values.
        """
        params = {}
        if self.namespaceId != "" and self.namespaceId is not None:
            params['namespaceId'] = self.namespaceId
        if id is not None and id != "":
            params['mcpId'] = id
        else:
            params['mcpName'] = name

        uri = f'/nacos/v3/admin/ai/mcp?' + urllib.parse.urlencode(params)

        success, data = await self.request_nacos(uri)
        if not success:
            logger.warning(f"failed to get mcp server, name {name}, id {id}")
            return  McpServer(name=name, description="", agentConfig={}, id=id, version="0.0.0")

        data['id'] = id
        config = NacosMcpServerConfig.from_dict(data)
        config.local_server_config['protocol'] = config.protocol
        mcp_server = McpServer(name=config.name,
                               description=config.description or "",
                               agentConfig=config.local_server_config,
                               id=id,
                               version=config.version)
            
        mcp_server.mcp_config_detail = config
        protocol = config.protocol
        if protocol == "stdio" or len(config.backend_endpoints) == 0:
            return mcp_server

        _parse_mcp_detail(mcp_server, config, name)
        return mcp_server

    async def get_mcp_servers_by_page(self, page_no: int, page_size: int):
        mcp_servers = list[McpServer]()

        params = {}
        if self.namespaceId != "":
            params['namespaceId'] = self.namespaceId
        params['pageNo'] = page_no
        params['pageSize'] = page_size
        params['search'] = "blur"

        uri = f'/nacos/v3/admin/ai/mcp/list?'+urllib.parse.urlencode(params)


        success, data = await self.request_nacos(uri)

        if not success:
            logger.warning("failed to get mcp server list response")
            return 0, mcp_servers

        total_count = data['totalCount']

        async def _to_mcp_server(m: dict) -> McpServer | None:
            """
            Fetch the mcp server unless the server is disabled(enabled=false)
            or it's description field is None.
            """
            if not m["enabled"]:
                return None
            name = m["name"]
            if (m["frontProtocol"] == "mcp-sse" or m["frontProtocol"] == "stdio") or m["frontProtocol"] == "mcp-streamable" :
                id = ""
                if "id" in m and m["id"] is not None:
                    id = m["id"]
                
                s = await self.get_mcp_server(id, name)
                return s if s.description else None
            else:
                return None

        tasks = [ _to_mcp_server(m) for m in data['pageItems']]
        tasks = [t for t in tasks if t is not None]
        if tasks:
            # use asyncio.gather to run the tasks concurrently
            # and wait for all of them to complete
            # this is more efficient than using await for each task
            # because it allows multiple tasks to run at the same time
            # instead of waiting for each one to finish before starting the next
            mcp_servers = await asyncio.gather(*tasks)
            mcp_servers = [s for s in mcp_servers if s is not None]

        return total_count, list(mcp_servers)

    async def get_mcp_servers(self) -> list[McpServer]:
        """Loading the remote MCP servers from Nacos Server.

        This asynchronous method retrieves a list of MCP servers from the Nacos Server.
        It uses pagination to continuously fetch server information until all server information is obtained.
        The method first initializes the list of MCP servers and pagination parameters, then enters a loop to call
        the get_mcp_servers_by_page method to get the total number of servers and server list for the current page.
        If the total number of servers is 0 or the server list is empty, it means there are no servers available, and the loop ends.
        Otherwise, the server list for the current page is added to the result list. If the number of servers collected reaches the total number,
        it means all server information has been collected, and the loop ends. Otherwise, the page number is incremented and the loop continues until all servers are collected.

        Returns:
            list[McpServer]: A list of MCP servers.
        """
        mcp_servers, page_no, page_size = [], 1, 100

        while True:
            total_count, servers = await self.get_mcp_servers_by_page(page_no, page_size)
            if total_count == 0 or not servers:
                break

            mcp_servers.extend(servers)
            if len(mcp_servers) >= total_count:
                break

            # continue to looping
            page_no += 1

        logger.info(f"get mcp server list, total count {len(mcp_servers)}")
        return mcp_servers

    async def update_mcp_tools(self, mcp_name:str, tools: list[Tool], mcp_version: str, id: str) -> bool:
        """
        Update the tools list for a specified MCP.

        This asynchronous method updates the tools associated with a specific MCP by sending
        an HTTP PUT request to the Nacos server. It first retrieves the current configuration
        of the MCP using a GET request. If the retrieval is unsuccessful, it logs a warning
        and returns False. If successful, it parses the tool parameters and sends a PUT request
        to update the tools list.

        Args:
           mcp_name (str): The name of the MCP for which the tools list needs to be updated.
           tools (list[Tool]): A list of Tool objects representing the new tools configuration.
           id (str): The id of the MCP server.

        Returns:
           bool: True if the update was successful, otherwise False.
        """
        params = {}
        if self.namespaceId != "":
            params['namespaceId'] = self.namespaceId
        if id != "":
            params['mcpId'] = id
        else:
            params['mcpName'] = mcp_name

        uri = f'/nacos/v3/admin/ai/mcp?'+urllib.parse.urlencode(params)

        # get original server config
        success, data = await self.request_nacos(uri)
        if 'version' in data and data['version'] is not None \
                and isinstance(data['version'], str) and version.parse(data['version']) > version.parse(mcp_version) \
                and 'toolSpec' in data and data['toolSpec'] is not None \
                and 'tools' in data['toolSpec'] and data['toolSpec']['tools'] is not None \
                and len(data['toolSpec']['tools']) > 0:
            return True

        if not success:
            logger.warning(f"failed to update mcp tools list, uri {uri}")
            return False
        data["versionDetail"] = {"version": mcp_version}
        
        if self.namespaceId != "":
            data["namespaceId"] = self.namespaceId

        params = _parse_tool_params(data, mcp_name, tools)

        logger.info(f"Trying to update mcp tools with params {json.dumps(params, ensure_ascii=False)}")

        success, _ = await self.request_nacos(f"/nacos/v3/admin/ai/mcp?",
                                              method='PUT',
                                              data=params,
                                              content_type=CONTENT_TYPE_URLENCODED)

        logger.info(f"Update mcp tools, name: {mcp_name}, result: {success}")

        return success

    async def request_nacos(self, uri,
                            method='GET',
                            data=None,
                            content_type=CONTENT_TYPE_JSON) -> tuple[bool, dict]:
        """
        Asynchronously send a request to the NACOS server.

        This method sends an HTTP request to the NACOS server using the specified URI, HTTP method, and data.
        It handles exceptions and logs warnings for any errors encountered during the request or response parsing with
        json.

        Args:
            uri (str): The URI path for the request.
            method (str): The HTTP method to use. Supported methods are 'GET', 'POST', 'PUT', and 'DELETE'. Defaults to 'GET'.
            data (dict, optional): The data to send with the request. Required for 'POST', 'PUT', and 'DELETE' methods. Defaults to None.
            content_type (str, optional): The transmitting http body using encoding methd.

        Returns:
            tuple[bool, dict]: A tuple containing:
                - A boolean indicating whether the request was successful.
                - The parsed JSON response data if the request was successful, otherwise None.

        Raises:
            ValueError: If an invalid HTTP method is provided.
        """

        try:
            url = f"{self.schema}://{self.nacosAddr}{uri}"
            headers = {"Content-Type": content_type,
                       "charset": "utf-8",
                       "userName": self.userName,
                       "password": self.passwd}
            self._inject_auth_info(headers)

            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, data=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, data=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError("Invalid method")
        except Exception as e:
            logger.warning(f"failed to request with NACOS server, uri: {uri}, error: {e}", exc_info=e)
            return False, {}

        code = response.status_code
        if code != 200:
            logger.warning(f"failed to request with NACOS server, uri: {uri}, code: {code}, response: {response.content}")
            return False, {}

        try:
            return True, json.loads(response.content.decode("utf-8")).get("data")
        except Exception as e:
            logger.warning(f"failed to parse response with NACOS server, uri: {uri}, error: {e}")
            return False, {}


def _parse_tool_params(data, mcp_name, tools) -> dict[str, str]:
    tool_list = map(
        lambda tool: {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema
        },
        tools
    )

    endpoint_specification = None
    if data['protocol'] != "stdio":
        endpoint_specification = {
            'data': data.get('remoteServerConfig', {}).get('serviceRef'),
            'type': 'REF'
        }

    tool_spec = data.get('toolSpec') or {}
    tool_spec['tools'] = list(tool_list)

    del data['backendEndpoints']

    return {
        'mcpName': mcp_name,
        'serverSpecification': json.dumps(data, ensure_ascii=False),
        'endpointSpecification': json.dumps(endpoint_specification or {}, ensure_ascii=False),
        'toolSpecification': json.dumps(tool_spec, ensure_ascii=False),
        'latest':'True'
    }

def _parse_mcp_detail(mcp_server, config, searching_name):
    endpoint = random.choice(config.backend_endpoints)
    http_schema = "https" if endpoint.port == 443 else "http"
    path = config.remote_server_config.export_path
    if not path.startswith("/"):
        path = f"/{path}"
    url = f"{http_schema}://{endpoint.address}:{endpoint.port}{path}"

    mcp_servers = mcp_server.agentConfig.setdefault("mcpServers", {})
    dct = {
        "name": searching_name,
        "description": '',
        "url": url,
        "protocol": mcp_server.agentConfig["protocol"],
    }

    mcp_servers[searching_name] = dct

