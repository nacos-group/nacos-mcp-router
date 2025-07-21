# -*- coding: utf-8 -*-

import asyncio
import json
import os
import typing
from importlib.metadata import version as get_version

import anyio
from mcp import types
from mcp.client.stdio import get_default_environment
from mcp.server import Server

from .constants import TRANSPORT_TYPE_STDIO, MODE_ROUTER, MODE_PROXY
from .logger import NacosMcpRouteLogger
from .mcp_manager import McpUpdater
from .nacos_http_client import NacosHttpClient
from .router_exceptions import NacosMcpRouterException
from .router_types import ChromaDb, McpServer
from .router_types import CustomServer

version_number = f"nacos-mcp-router:v{get_version('nacos-mcp-router')}"
router_logger = NacosMcpRouteLogger.get_logger()
mcp_servers_dict: dict[str, CustomServer] = {}

mcp_updater: McpUpdater
nacos_http_client: NacosHttpClient
proxied_mcp_name: str = ""
mode: str = MODE_ROUTER
proxied_mcp_server_config: dict = {}
transport_type: str = TRANSPORT_TYPE_STDIO
auto_register_tools: bool = True
proxied_mcp_version: str = ''
mcp_app: Server
def router_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_mcp_server",
            description="执行任务前首先使用本工具。根据任务描述及关键字搜索mcp server, 制定完成任务的步骤。注意：任务描述及关键字需要同时包含中文和英文。",
            inputSchema={
                "type": "object",
                "required": ["task_description", "key_words"],
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "用户中文和英文任务描述，中英文描述各占单独一行。如果任务描述只包含中文，请同时输入英文描述，反之亦然。",
                    },
                    "key_words": {
                        "type": "string",
                        "description": "用户任务关键字，可以为多个，最多为4个，包含中英文关键字，英文逗号分隔"
                    }
                },
            },
        ),
        types.Tool(
            name="add_mcp_server",
            description="安装指定的mcp server",
            inputSchema={
                "type": "object",
                "required": ["mcp_server_name"],
                "properties": {
                    "mcp_server_name": {
                        "type": "string",
                        "description": "MCP Server名称"
                    }
                }
            }
        ),
        types.Tool(
            name="use_tool",
            description="使用某个MCP Server的工具",
            inputSchema={
                "type": "object",
                "required": ["mcp_server_name", "mcp_tool_name", "params"],
                "properties": {
                    "mcp_server_name": {
                        "type": "string",
                        "description": "需要使用的MCP Server名称"
                    },
                    "mcp_tool_name": {
                        "type": "string",
                        "description": "需要使用的MCP Server工具名称"
                    },
                    "params": {
                        "type": "string",
                        "description": "需要使用的MCP Server工具的参数"
                    }
                }
            }
        )
    ]


async def init_proxied_mcp() -> bool:
    global proxied_mcp_server_config
    if proxied_mcp_name in mcp_servers_dict:
        return True
    
    proxied_mcp_server_config_str = os.getenv("PROXIED_MCP_SERVER_CONFIG", "")

    if mode == MODE_PROXY and (proxied_mcp_server_config_str == "" or proxied_mcp_server_config_str is None):
        router_logger.info(f"proxied_mcp_server_config_str is empty, get mcp server from nacos, proxied_mcp_name: {proxied_mcp_name}")
        mcp_server = await nacos_http_client.get_mcp_server(id="", name=proxied_mcp_name)
        router_logger.info(f"proxied_mcp_server_config: {mcp_server.agent_config()}")
        proxied_mcp_server_config = mcp_server.agent_config()

    mcp_server = CustomServer(name=proxied_mcp_name, config=proxied_mcp_server_config)
    
    if mcp_server._protocol == 'stdio':
        await mcp_server.wait_for_initialization()

    if await mcp_server.healthy():
        mcp_servers_dict[proxied_mcp_name] = mcp_server
        init_result = await mcp_server.get_initialized_response(client_headers={})
        version = getattr(getattr(init_result, 'serverInfo', None), 'version', "1.0.0")
        mcp_app.version = version

        if auto_register_tools and nacos_http_client is not None:
            tools = await mcp_server.list_tools()
            await nacos_http_client.update_mcp_tools(proxied_mcp_name, tools, version, "")
        return True
    else:
        return False

async def filter_tools(tools:list[types.Tool], mcp_server_from_registry:McpServer) -> list[types.Tool]:
    if mcp_server_from_registry is None:
        return tools

    disenabled_tools = {}
    tools_meta = {}
    if hasattr(mcp_server_from_registry, 'mcp_config_detail') and mcp_server_from_registry.mcp_config_detail is not None:
        if hasattr(mcp_server_from_registry.mcp_config_detail, 'tool_spec') and mcp_server_from_registry.mcp_config_detail.tool_spec is not None:
            if hasattr(mcp_server_from_registry.mcp_config_detail.tool_spec, 'tools_meta') and mcp_server_from_registry.mcp_config_detail.tool_spec.tools_meta is not None:
                tools_meta = mcp_server_from_registry.mcp_config_detail.tool_spec.tools_meta

    for tool_name in tools_meta:
        meta = tools_meta[tool_name]
        if not meta.enabled:
            disenabled_tools[tool_name] = True

    from mcp import types
    tool_list = list[types.Tool]()
    for tool in tools:
        if tool.name in disenabled_tools:
            continue
        dct = {}

        dct['name'] = tool.name
        if hasattr(mcp_server_from_registry, 'mcp_config_detail') and mcp_server_from_registry.mcp_config_detail is not None:
            if hasattr(mcp_server_from_registry.mcp_config_detail, 'tool_spec') and mcp_server_from_registry.mcp_config_detail.tool_spec is not None:
                if hasattr(mcp_server_from_registry.mcp_config_detail.tool_spec, 'tools_dict') and mcp_server_from_registry.mcp_config_detail.tool_spec.tools_dict is not None:
                    if tool.name in mcp_server_from_registry.mcp_config_detail.tool_spec.tools_dict:
                        tool.description = mcp_server_from_registry.mcp_config_detail.tool_spec.tools_dict[tool.name].description
                        tool.inputSchema = mcp_server_from_registry.mcp_config_detail.tool_spec.tools_dict[tool.name].input_schema

        tool_list.append(tool)
    return tool_list


async def proxied_mcp_tools(client_headers: dict[str, str] = {}) -> list[types.Tool]:
    if await init_proxied_mcp():
        try:
            tool_list = await mcp_servers_dict[proxied_mcp_name].list_tools_with_headers(client_headers=client_headers)
            mcp_server_from_registry = await mcp_updater.get_mcp_server_by_name(proxied_mcp_name)
            if mcp_server_from_registry is not None:
                result = await filter_tools(tool_list, mcp_server_from_registry)
                return result
            return tool_list
        except (KeyError, Exception) as e:
            router_logger.warning("failed to list tools for proxied mcp server: " + proxied_mcp_name, exc_info=e)
            return []
    else:
        raise NacosMcpRouterException(msg=f"failed to initialize proxied MCP server {proxied_mcp_name}")


async def search_mcp_server(task_description: str, key_words: str) -> str:
    """
      Name:
          search_mcp_server

      Description:
          执行任务前首先使用本工具。根据任务描述及关键字搜索mcp server，制定完成任务的步骤。

      Args:
          task_description (string): 用户任务描述，使用中文
          key_words (string): 字符串数组，用户任务关键字，可以为多个，英文逗号分隔，最多为2个
    """
    try:
        if mcp_updater is None:
            return "服务初始化中，请稍后再试"

        router_logger.info(f"Searching tools for {task_description}, key words: {key_words}")
        mcp_servers1 = []
        keywords = key_words.split(",")
        for key_word in keywords:
            mcps = await mcp_updater.search_mcp_by_keyword(key_word)
            mcp_servers1.extend(mcps or [])
        router_logger.info("mcp size searched by keywords is " + str(len(mcp_servers1)))
        if len(mcp_servers1) < 5:
            mcp_servers2 = await mcp_updater.getMcpServer(task_description, 5 - len(mcp_servers1))
            mcp_servers1.extend(mcp_servers2 or [])

        result = {}
        for mcpServer in mcp_servers1:
            mname = str(mcpServer.get_name())
            dct = dict(name=mname,
                       description=mcpServer.get_description())

            result[mname] = dct

        router_logger.info(f"Found {len(result)} server(s) totally")
        content = json.dumps(result, ensure_ascii=False)

        json_string = ("## 获取" + task_description + "的步骤如下：\n"
                  + "### 1. 当前可用的mcp server列表为：" + content
                  + "\n### 2. 从当前可用的mcp server列表中选择你需要的mcp server调add_mcp_server工具安装mcp server")

        return json_string
    except Exception as e:
        msg = f"failed to search mcp server for {task_description}"
        router_logger.warning(msg, exc_info=e)
        return f"Error: {msg}"


async def use_tool(mcp_server_name: str, mcp_tool_name: str, params: dict, client_headers: dict[str, str] = {}) -> str:
    try:
        if mcp_server_name not in mcp_servers_dict or mcp_servers_dict[mcp_server_name] is None :
            router_logger.warning(f"mcp server {mcp_server_name} not found, "
                                  f"use search_mcp_server to get mcp servers")
            return "mcp server not found, use search_mcp_server to get mcp servers"

        mcp_server = mcp_servers_dict[mcp_server_name]
        response = await mcp_server.execute_tool(mcp_tool_name, params, client_headers=client_headers)        
        return str(response.content)
    except Exception as e:
        router_logger.warning("failed to use tool: " + mcp_tool_name, exc_info=e)
        return "failed to use tool: " + mcp_tool_name + ", please use add_mcp_server to install mcp server"

async def add_mcp_server(mcp_server_name: str, client_headers: dict[str, str] = {}) -> str:
    """
    安装指定的mcp server
    :param mcp_server_name: mcp server名称
    :return: mcp server安装结果
    """
    try:
        if nacos_http_client is None or mcp_updater is None:
            return "服务初始化中，请稍后再试"

        mcp_server = await mcp_updater.get_mcp_server_by_name(mcp_server_name)

        if mcp_server is None:
            return mcp_server_name + " is not found" + ", use search_mcp_server to get mcp servers"

        disabled_tools = {}
        tools_meta = mcp_server.mcp_config_detail.tool_spec.tools_meta
        for tool_name in tools_meta:
            meta = tools_meta[tool_name]
            if not meta.enabled:
                disabled_tools[tool_name] = True

        if mcp_server_name not in mcp_servers_dict or mcp_servers_dict[mcp_server_name] is None or not await mcp_servers_dict[mcp_server_name].healthy():
            env = get_default_environment()
            if mcp_server.agentConfig is None:
                mcp_server.agentConfig = {}
            if 'mcpServers' not in mcp_server.agentConfig or mcp_server.agentConfig['mcpServers'] is None:
                mcp_server.agentConfig['mcpServers'] = {}

            mcp_servers = mcp_server.agentConfig["mcpServers"]
            for key, value in mcp_servers.items():
                server_config = value
                if 'env' in server_config:
                    for k in server_config['env']:
                        env[k] = server_config['env'][k]
                server_config['env'] = env
                if 'headers' not in server_config:
                    server_config['headers'] = {}
            router_logger.info(f"add mcp server: {mcp_server_name}, config:{mcp_server.agentConfig}")
            server = CustomServer(name=mcp_server_name, config=mcp_server.agentConfig)
            if server._protocol == 'stdio':
                await server.wait_for_initialization()
                if await server.healthy():
                    mcp_servers_dict[mcp_server_name] = server
            else:
                mcp_servers_dict[mcp_server_name] = server
        
        if mcp_server_name not in mcp_servers_dict:
            return "failed to install mcp server: " + mcp_server_name
    
        server = mcp_servers_dict[mcp_server_name]

        tools = await server.list_tools_with_headers(client_headers=client_headers)
        init_result = await server.get_initialized_response(client_headers=client_headers)
        mcp_version = init_result.serverInfo.version if init_result and hasattr(init_result, 'serverInfo') else "1.0.0"
        router_logger.info(f"add mcp server: {mcp_server_name}, version:{mcp_version}")

        tool_list = []
        for tool in tools:
            if tool.name in disabled_tools:
                continue
            dct = {}
            dct['name'] = tool.name
            tool_info = mcp_server.mcp_config_detail.tool_spec.tools_dict.get(tool.name)
            if tool_info:
                dct['description'] = tool_info.description
                dct['inputSchema'] = tool_info.input_schema
            else:
                dct['description'] = tool.description
                dct['inputSchema'] = tool.inputSchema

            tool_list.append(dct)

        if nacos_http_client is not None:
            await nacos_http_client.update_mcp_tools(mcp_server_name, tools, mcp_version,
                                                     mcp_server.id if mcp_server.id else "")

        result = "1. " + mcp_server_name + "安装完成, tool 列表为: " + json.dumps(tool_list, ensure_ascii=False) + "\n2." + mcp_server_name + "的工具需要通过nacos-mcp-router的use_tool工具代理使用"
        return result
    except Exception as e:
        router_logger.warning("failed to install mcp server: " + mcp_server_name, exc_info=e)
        return "failed to install mcp server: " + mcp_server_name

def start_server() -> int:
    
    match transport_type:
        case 'stdio':
            from mcp.server.stdio import stdio_server

            async def arun():
                async with stdio_server() as streams:
                    await mcp_app.run(
                        streams[0], streams[1], mcp_app.create_initialization_options()
                    )

            anyio.run(arun)

            return 0
        case 'sse':
            from mcp.server.sse import SseServerTransport
            from starlette.applications import Starlette
            from starlette.routing import Mount, Route
            import contextlib
            from collections.abc import AsyncIterator
            from starlette.responses import Response
            sse_transport = SseServerTransport("/messages/")
            sse_port = int(os.getenv("PORT", "8000"))

            async def handle_sse(request):
                async with sse_transport.connect_sse(
                    request.scope, request.receive, request._send
                ) as streams:
                    await mcp_app.run(
                    streams[0], streams[1], mcp_app.create_initialization_options()
                    )
            @contextlib.asynccontextmanager
            async def sse_lifespan(app: Starlette) -> AsyncIterator[None]:
                """Context manager for session manager."""
                try:
                    if mode == MODE_PROXY:
                        if not await init_proxied_mcp():
                            raise NacosMcpRouterException("failed to init mcp server")
                    yield
                    for mcp in mcp_servers_dict.values():
                        await mcp.cleanup()
                finally:
                    router_logger.info("Application shutting down...")


            starlette_app = Starlette(
                debug=True,
                routes=[
                    Route("/sse", endpoint=handle_sse, methods=["GET"]),
                    Mount("/messages/", app=sse_transport.handle_post_message),
                ],
                lifespan= sse_lifespan,
            )

            import uvicorn

            uvicorn.run(starlette_app, host="0.0.0.0", port=sse_port)
            return 0
        case 'streamable_http':
            from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
            from starlette.types import Scope
            from starlette.types import Receive
            from starlette.types import Send

            streamable_port = int(os.getenv("PORT", "8000"))
            session_manager = StreamableHTTPSessionManager(
                app=mcp_app,
                event_store=None,
                json_response=False,
                stateless=True,
            )

            from mcp.server.sse import SseServerTransport
            from starlette.applications import Starlette
            from starlette.responses import Response
            from starlette.routing import Mount, Route
            import contextlib
            from collections.abc import AsyncIterator

            sse_transport = SseServerTransport("/messages/")

            async def handle_streamable_http(
                    scope: Scope, receive: Receive, send: Send
            ) -> None:
                await session_manager.handle_request(scope, receive, send)
            @contextlib.asynccontextmanager
            async def lifespan(app: Starlette) -> AsyncIterator[None]:
                """Context manager for session manager."""
                async with session_manager.run():
                    try:
                        if mode == MODE_PROXY:
                            if not await init_proxied_mcp():
                                raise NacosMcpRouterException("failed to init mcp server")
                        yield

                        for mcp in mcp_servers_dict.values():
                            await mcp.cleanup()
                    finally:
                        router_logger.info("Application shutting down...")

            starlette_app = Starlette(
                debug=True,
                routes=[
                    Mount("/mcp", app=handle_streamable_http),
                    Mount("/messages/", app=sse_transport.handle_post_message),
                ],
                lifespan=lifespan,
            )
            import uvicorn
            uvicorn.run(starlette_app, host="0.0.0.0", port=streamable_port)
            return 0
        case _:
            router_logger.error("unknown transport type: " + transport_type)
            return 1


def create_mcp_app() -> Server:
    @mcp_app.call_tool()
    async def call_tool(
            name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        router_logger.info(f"calling tool: {name}, arguments: {arguments}")
        headers = {}
        if mcp_app.request_context is not None and mcp_app.request_context.request is not None and mcp_app.request_context.request.headers is not None:
            headers = mcp_app.request_context.request.headers
        if mode == 'proxy':
            if proxied_mcp_name not in mcp_servers_dict:
                if await init_proxied_mcp():
                    raise NameError(f"failed to init proxied mcp: {proxied_mcp_name}")
            result = await mcp_servers_dict[proxied_mcp_name].execute_tool(tool_name=name, arguments=arguments, client_headers=headers)
            return result.content
        else:
            match name:
                case "search_mcp_server":
                    content = await search_mcp_server(arguments["task_description"], arguments["key_words"])
                    return [types.TextContent(type="text", text=content)]
                case "add_mcp_server":
                    content = await add_mcp_server(arguments["mcp_server_name"], headers)
                    return [types.TextContent(type="text", text=content)]
                case "use_tool":
                    params = json.loads(arguments["params"])
                    content = await use_tool(arguments["mcp_server_name"], arguments["mcp_tool_name"], params, headers)
                    return [types.TextContent(type="text", text=content)]
                case _:
                    return [types.TextContent(type="text", text="not implemented tool")]

    @mcp_app.list_tools()
    async def list_tools() -> list[types.Tool]:
        headers = {}
        if mcp_app.request_context is not None and mcp_app.request_context.request is not None and mcp_app.request_context.request.headers is not None:
            headers = mcp_app.request_context.request.headers
        if mode == MODE_PROXY:
            return await proxied_mcp_tools(headers)
        else:
            return router_tools()

    return mcp_app


def main() -> int:
    if init() != 0:
        return 1
    create_mcp_app()
    return start_server()


def init() -> int:
    global mcp_app, mcp_updater, nacos_http_client, mode, proxied_mcp_name, proxied_mcp_server_config, transport_type, auto_register_tools, proxied_mcp_version
    
    try:
        mcp_app = Server("nacos-mcp-router")
        nacos_addr = os.getenv("NACOS_ADDR", "127.0.0.1:8848")
        nacos_user_name = os.getenv("NACOS_USERNAME", "nacos")
        nacos_password = os.getenv("NACOS_PASSWORD", "")
        nacos_namespace = os.getenv("NACOS_NAMESPACE", "")
        ak = os.getenv("ACCESS_KEY_ID", "")
        sk = os.getenv("ACCESS_KEY_SECRET","")
        params = {"nacosAddr":nacos_addr,"userName": nacos_user_name, "password": nacos_password, "namespaceId": nacos_namespace, "ak": ak, "sk": sk}
        
        auto_register_tools = os.getenv("AUTO_REGISTER_TOOLS", "true").lower() == "true"
        mode = os.getenv("MODE", MODE_ROUTER)
        proxied_mcp_name = os.getenv("PROXIED_MCP_NAME", "")
        proxied_mcp_server_config_str = os.getenv("PROXIED_MCP_SERVER_CONFIG", "")
        update_interval = int(os.getenv("UPDATE_INTERVAL", 60))

        if update_interval < 10:
            update_interval = 10

        if proxied_mcp_server_config_str != "" :
            proxied_mcp_server_config = json.loads(proxied_mcp_server_config_str)

        transport_type = os.getenv("TRANSPORT_TYPE", TRANSPORT_TYPE_STDIO)

        if mode == MODE_ROUTER or (mode == MODE_PROXY and auto_register_tools):
            if not isinstance(nacos_addr, str) or not nacos_addr.strip():
                raise ValueError("nacosAddr must be a non-empty string")

            if not isinstance(nacos_user_name, str) or not nacos_user_name.strip():
                raise ValueError("userName must be a non-empty string")
    
            if not isinstance(nacos_password, str) or not nacos_password.strip():
                raise ValueError("passwd must be a non-empty string")
        
        nacos_http_client = NacosHttpClient(params)
        
        init_str = (
            f"init server, nacos_addr: {nacos_addr}, "
            f"nacos_user_name: {nacos_user_name}, "
            f"nacos_password: {nacos_password}, "
            f"mode: {mode}, "
            f"transport_type: {transport_type}, "
            f"proxied_mcp_name: {proxied_mcp_name}, "
            f"proxied_mcp_server_config: {proxied_mcp_server_config}, "
            f"auto_register_tools: {auto_register_tools}, "
            f"version: {version_number}"
        )

        router_logger.info(init_str)

        if mode == MODE_PROXY and proxied_mcp_name == "":
            raise NacosMcpRouterException("proxied_mcp_name must be set in proxy mode")

        if  mode == MODE_ROUTER:
            chroma_db_service = ChromaDb()
            mcp_updater =  McpUpdater.create(nacos_client=nacos_http_client, chroma_db=chroma_db_service, update_interval=update_interval, enable_vector_db=True, mode=mode, proxy_mcp_name=proxied_mcp_name, enable_auto_refresh=True)
        else:
            if auto_register_tools:
                mcp_updater = McpUpdater.create(nacos_client=nacos_http_client, chroma_db=None, update_interval=update_interval, enable_vector_db=False, mode=mode, proxy_mcp_name=proxied_mcp_name, enable_auto_refresh=True)
            else:
                mcp_updater = McpUpdater.create(nacos_client=nacos_http_client, chroma_db=None, update_interval=update_interval, enable_vector_db=False, mode=mode, proxy_mcp_name=proxied_mcp_name, enable_auto_refresh=False)

        return 0
    except Exception as e:
        router_logger.error("failed to start", exc_info= e)
        raise e

