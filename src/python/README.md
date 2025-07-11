# nacos-mcp-router: A MCP server that provides  functionalities such as search, installation, proxy, and more.

[切换到中文版](README_cn.md)


## Overview

[Nacos](https://nacos.io) is an easy-to-use platform designed for dynamic service discovery and configuration and service management. It helps you to build cloud native applications and microservices platform easily.

This MCP(Model Context Protocol) Server provides tools to search, install, proxy other MCP servers.

Nacos-MCP-Router has two working modes:

Router mode: The default mode, which recommends, distributes, installs, and proxies the functions of other MCP Servers through the MCP Server, helping users more conveniently utilize MCP Server services.

Proxy mode: Specified by the environment variable MODE=proxy, it can convert SSE and stdio protocol MCP Servers into streamable HTTP protocol MCP Servers through simple configuration.

## Quick Start
### router mode
#### Tools

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

####  Usage
##### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *nacos-mcp-router*.
```
export NACOS_ADDR=127.0.0.1:8848
export NACOS_USERNAME=nacos
export NACOS_PASSWORD=$PASSWORD
uvx nacos-mcp-router@latest
```

##### Using PIP

Alternatively you can install `nacos-mcp-router` via pip:

```
pip install nacos-mcp-router
```

After installation, you can run it as a script using（As an example，Nacos is deployed in standalone mode on the local machine）:

```
export NACOS_ADDR=127.0.0.1:8848
export NACOS_USERNAME=nacos
export NACOS_PASSWORD=$PASSWORD
python -m nacos-mcp-router
```

##### Using Docker
```
docker run -i --rm --network host -e NACOS_ADDR=$NACOS_ADDR -e NACOS_USERNAME=$NACOS_USERNAME -e NACOS_PASSWORD=$NACOS_PASSWORD -e TRANSPORT_TYPE=$TRANSPORT_TYPE nacos-mcp-router:latest
```

##### Usage with Cline、Cursor、Claude and other applications

Add this to MCP settings of your application:

####### Using uvx

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

###### Using docker
```json
{
  "mcpServers": {
    "nacos-mcp-router": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--network", "host",  "-e", "NACOS_ADDR=<NACOS-ADDR>", "-e",  "NACOS_USERNAME=<NACOS-USERNAME>", "-e", "NACOS_PASSWORD=<NACOS-PASSWORD>" ,"-e", "TRANSPORT_TYPE=stdio", "nacos-mcp-router:latest"
      ]
    }
  }
}
```

### Proxy Mode
The proxy mode supports converting SSE and stdio protocol MCP Servers into streamable HTTP protocol MCP Servers.

#### Usage
The usage of proxy mode is similar to that of router mode, with slightly different parameters. Docker deployment is recommended.
```
docker run -i --rm --network host -e NACOS_ADDR=$NACOS_ADDR -e NACOS_USERNAME=$NACOS_USERNAME -e NACOS_PASSWORD=$NACOS_PASSWORD -e TRANSPORT_TYPE=streamable_http -e MODE=proxy -e PROXIED_MCP_NAME=$PROXIED_MCP_NAME  nacos-mcp-router:latest
```


## Development

If you are doing local development, simply follow the steps:

1. Clone this repo into your local environment.
2. Modify codes in `src/mcp_server_nacos` to implement your wanted features.
3. Test using the Claude desktop app. Add the following to your claude_desktop_config.json:

```json
{
  "mcpServers": {
    "nacos-mcp-router": {
      "command": "uv",
      "args": [
        "--directory","PATH-TO-PROJECT","run","nacos-mcp-router"
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

## Environment Variable Settings  

| Parameter | Description             | Default Value | Required | Remarks                                                                                        |  
|-----------|-------------------------|---------------|----------|------------------------------------------------------------------------------------------------|  
| NACOS_ADDR | Nacos server address    | 127.0.0.1:8848 | No       | the Nacos server address, e.g., 192.168.1.1:8848. Note: Include the port.                      |  
| NACOS_USERNAME | Nacos username          | nacos | No       | the Nacos username, e.g., nacos.                                                               |  
| NACOS_PASSWORD | Nacos password          | - | Yes      | the Nacos password, e.g., nacos.                                                               |
|NACOS_NAMESPACE| Nacos Namespace         | public         | No       | Nacos namespace, e.g. public                                                                   |
| TRANSPORT_TYPE | Transport protocol type | stdio | No       | transport protocol type. Options: stdio, sse, streamable_http.                                 |  
| PROXIED_MCP_NAME | Proxied MCP server name | - | No       | In proxy mode, specify the MCP server name to be converted. Must be registered in Nacos first. |  
| MODE | Working mode            | router | No       | Available options: router, proxy.                                                              |
|ACCESS_KEY_ID | Aliyun ram access key id| - | No | |
|ACCESS_KEY_SECRET | Aliyun ram access key secret | - | No | |

## License

nacos-mcp-router is licensed under the Apache 2.0 License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the Apache 2.0 License. For more details, please see the `LICENSE` file in the project repository.
