from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession


async def main():
    # Connect to a streamable HTTP server
    async with streamablehttp_client(url="http://127.0.0.1:8000/mcp") as (
        read_stream,
        write_stream,
        _,
    ):
        # Create a session using the client streams
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            tool_list = await session.list_tools()
            print(tool_list)
            # Call a tool
            tool_result = await session.call_tool("search_mcp_server", {"task_description": "天气","key_words": "天气"})
            print(tool_result)
            tool_result = await session.call_tool("add_mcp_server", {"mcp_server_name": "amap-mcp-server"})
            print(tool_result)
            tool_result = await session.call_tool("use_tool", {"mcp_server_name": "amap-mcp-server","mcp_tool_name": "maps_weather","params": "{\"city\": \"杭州\"}"})
            print(tool_result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())