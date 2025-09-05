
# nacos-mcp-router: A MCP server that provides  functionalities such as search, installation, proxy, and more.
[![Model Context Protocol](https://img.shields.io/badge/Model%20Context%20Protocol-purple)](https://modelcontextprotocol.org)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/nacos-group/nacos-mcp-router)

<p>
<a href="./README.md">English</a> | <a href="./README_cn.md">简体中文</a> 
</p>

## Overview

[Nacos](https://nacos.io) is an easy-to-use platform designed for dynamic service discovery and configuration and service management. It helps you to build cloud native applications and microservices platform easily.

This MCP(Model Context Protocol) Server provides tools to search, install, proxy other MCP servers, with advanced search capabilities including vector similarity search and multi-provider result aggregation.

Nacos-MCP-Router has two working modes:
 
Router mode: The default mode, which recommends, distributes, installs, and proxies the functions of other MCP Servers through the MCP Server, helping users more conveniently utilize MCP Server services.

Proxy mode: Specified by the environment variable MODE=proxy, it can convert SSE and stdio protocol MCP Servers into streamable HTTP protocol MCP Servers through simple configuration.

## Search Features

Nacos-MCP-Router provides powerful search capabilities through multiple providers:

### Search Providers

1. **Nacos Provider**
   - Searches MCP servers using Nacos service discovery
   - Supports keyword matching and vector similarity search
   - Integrated with the local Nacos instance

2. **Compass Provider**
   - Connects to a COMPASS API endpoint for enhanced search
   - Supports semantic search and relevance scoring
   - Configurable API endpoint (default: https://registry.mcphub.io)

### Search Configuration

Configure search behavior using environment variables:

```bash
# YOUR COMPASS API endpoint (for Outer Provider called Compass Provider)
COMPASS_API_BASE=https://registry.mcphub.io

# Minimum similarity score for results (0.0 to 1.0)
SEARCH_MIN_SIMILARITY=0.5

# Maximum number of results to return
SEARCH_RESULT_LIMIT=10
```

### Search API

The search functionality is available through the MCP interface:

```typescript
// Search for MCP servers
const results = await searchMcpServer(
  "Find MCP servers for natural language processing",
  ["nlp", "language"]
);
```

Results include:
- Server name and description
- Provider information
- Relevance score
- Additional metadata

## Quick Start
### Python
#### router mode
##### Tools

1. `search_mcp_server`
    - Search MCP servers by task and keywords.
    - Input:
      - `task_description`(string): Task description
      - `key_words`(string): Keywords of task
    - Returns: list of MCP servers and instructions to complete the task.
2. `add_mcp_server`
    - Add a MCP server. If the MCP server is a stdio server, this tool will install it and  establish connection to it. If the MCP server is a sse server, this tool will establish connection to it
    - Input:
      - `mcp_server_name`(string): The name of MCP server.
    - Returns: tool list of the MCP server and how to use these tools.
3. `use_tool`
   - This tool helps LLM to use the tool of some MCP server. It will proxy requests to the target MCP server.
   - Input:
     - `mcp_server_name`(string): The target MCP server name that LLM wants to call.
     - `mcp_tool_name`(string): The tool name of target MCP server that LLM wants to call.
     - `params`(map): The parameters of the MCP tool.
   - Returns: Result returned from the target MCP server.

#####  Usage
###### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *nacos-mcp-router*.
```
export NACOS_ADDR=127.0.0.1:8848
export NACOS_USERNAME=nacos
export NACOS_PASSWORD=$PASSWORD
uvx nacos-mcp-router@latest
```

###### Using PIP

Alternatively you can install `nacos-mcp-router` via pip:

```
pip install nacos-mcp-router
```

After installation, you can run it as a script using（As an example，Nacos is deployed in standalone mode on the local machine）:

```
export NACOS_ADDR=127.0.0.1:8848
export NACOS_USERNAME=nacos
export NACOS_PASSWORD=$PASSWORD
python -m nacos_mcp_router
```

###### Using Docker
```
docker run -i --rm --network host -e NACOS_ADDR=$NACOS_ADDR -e NACOS_USERNAME=$NACOS_USERNAME -e NACOS_PASSWORD=$NACOS_PASSWORD -e TRANSPORT_TYPE=$TRANSPORT_TYPE nacos/nacos-mcp-router:latest
```

###### Usage with Cline、Cursor、Claude and other applications

Add this to MCP settings of your application:

* Using uvx

```json
{
    "mcpServers":
    {
        "nacos-mcp-router":
        {
            "command": "uvx",
            "args":
            [
                "nacos-mcp-router@latest"
            ],
            "env":
            {
                "NACOS_ADDR": "<NACOS-ADDR>, optional, default is 127.0.0.1:8848",
                "NACOS_USERNAME": "<NACOS-USERNAME>, optional, default is nacos",
                "NACOS_PASSWORD": "<NACOS-PASSWORD>, required"
            }
        }
    }
}
```

> You may need to put the full path to the `uvx` executable in the `command` field. You can get this by running `which uvx` on MacOS/Linux or `where uvx` on Windows.

* Using docker
```json
{
  "mcpServers": {
    "nacos-mcp-router": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--network", "host",  "-e", "NACOS_ADDR=<NACOS-ADDR>", "-e",  "NACOS_USERNAME=<NACOS-USERNAME>", "-e", "NACOS_PASSWORD=<NACOS-PASSWORD>" ,"-e", "TRANSPORT_TYPE=stdio", "nacos/nacos-mcp-router:latest"
      ]
    }
  }
}
```

#### Proxy Mode
The proxy mode supports converting SSE and stdio protocol MCP Servers into streamable HTTP protocol MCP Servers.

##### Usage
The usage of proxy mode is similar to that of router mode, with slightly different parameters. Docker deployment is recommended.
```
docker run -i --rm --network host -e NACOS_ADDR=$NACOS_ADDR -e NACOS_USERNAME=$NACOS_USERNAME -e NACOS_PASSWORD=$NACOS_PASSWORD -e TRANSPORT_TYPE=streamable_http -e MODE=proxy -e PROXIED_MCP_NAME=$PROXIED_MCP_NAME  nacos/nacos-mcp-router:latest
```

#### Environment Variable Settings  

| Parameter | Description                                                | Default Value | Required | Remarks                                                                                       |  
|-----------|------------------------------------------------------------|---------------|----------|-----------------------------------------------------------------------------------------------|  
| NACOS_ADDR | Nacos server address                                       | 127.0.0.1:8848 | No       | the Nacos server address, e.g., 192.168.1.1:8848. Note: Include the port.                     |  
| NACOS_USERNAME | Nacos username                                             | nacos | No       | the Nacos username, e.g., nacos.                                                              |  
| NACOS_PASSWORD | Nacos password                                             | - | Yes      | the Nacos password, e.g., nacos.                                                              |
| COMPASS_API_BASE | COMPASS API endpoint for enhanced search | https://registry.mcphub.io | No | Override the default COMPASS API endpoint |
| SEARCH_MIN_SIMILARITY | Minimum similarity score (0.0-1.0) | 0.5 | No | Filter search results by minimum similarity score |
| SEARCH_RESULT_LIMIT | Maximum number of results to return | 10 | No | Limit the number of search results |
|NACOS_NAMESPACE| Nacos Namespace                                            | public         | No       | Nacos namespace, e.g. public                                                                  |
| TRANSPORT_TYPE | Transport protocol type                                    | stdio | No       | transport protocol type. Options: stdio, sse, streamable_http.                                |  
| PROXIED_MCP_NAME | Proxied MCP server name                                    | - | No       | In proxy mode, specify the MCP server name to be converted. Must be registered in Nacos first. |  
| MODE | Working mode                                               | router | No       | Available options: router, proxy.                                                             |
| PORT| Service port when TRANSPORT_TYPE is sse or streamable_http | 8000| No       |                                       |
|ACCESS_KEY_ID | Aliyun ram access key id| - | No | |
|ACCESS_KEY_SECRET | Aliyun ram access key secret | - | No | |

### typescript
#### Usage with Cline、Cursor、Claude and other applications

```json
{
  "mcpServers": {
    "nacos-mcp-router": {
      "command": "npx",
      "args": [
        "nacos-mcp-router@latest"
      ],
      "env": {
        "NACOS_ADDR": "<NACOS-ADDR>, optional, default is 127.0.0.1:8848",
        "NACOS_USERNAME": "<NACOS-USERNAME>, optional, default is nacos",
        "NACOS_PASSWORD": "<NACOS-PASSWORD>, required"
      }
    }
  }
}
```

## License

nacos-mcp-router is licensed under the Apache 2.0 License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the Apache 2.0 License. For more details, please see the `LICENSE` file in the project repository.
