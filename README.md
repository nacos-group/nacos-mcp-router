# nacos-mcp-router: 一个提供MCP Server推荐、分发、安装及代理功能的MCP Server.

## 概述

[Nacos](https://nacos.io) 一个更易于构建云原生应用的动态服务发现、配置管理和服务管理平台。Nacos提供了一组简单易用的特性集，帮助您快速实现动态服务发现、服务配置、服务元数据及流量管理

Nacos-MCP-Router是一个基于MCP官方标准SDK实现的的MCP Server。它提供了一组工具，提供MCP Server推荐、分发、安装及代理其他MCP Server的功能，帮助用户更方便的使用MCP Server服务。



## Python版接入
Nacos-MCP-Routery有两种工作模式：
1. router模式：默认模式，通过MCP Server推荐、分发、安装及代理其他MCP Server的功能，帮助用户更方便的使用MCP Server服务。
2. prroxy模式：使用环境变量MODE=proxy指定，通过简单配置可以把sse、stdio协议MCP Server转换为streamableHTTP协议MCP Server。
### router模式
#### Tools

1. `search_mcp_server`
    - 根据任务描述及关键字从MCP注册中心（Nacos）中搜索相关的MCP Server列表
    - 输入:
      - `task_description`(string): 任务描述，示例：今天杭州天气如何
      - `key_words`(string): 任务关键字，示例：天气、杭州
    - 输出: list of MCP servers and instructions to complete the task.
2. `add_mcp_server`
    - 添加并初始化一个MCP Server，根据Nacos中的配置与该MCP Server建立连接，等待调用。
    - 输入:
      - `mcp_server_name`(string): 需要添加的MCP Server名字
    - 输出: MCP Server工具列表及使用方法
3. `use_tool`
   - 代理其他MCP Server的工具
   - 输入:
     - `mcp_server_name`(string): 被调的目标MCP Server名称.
     - `mcp_tool_name`(string): 被调的目标MCP Server的工具名称
     - `params`(map): 被调的目标MCP Server的工具的参数
   - 输出: 被调的目标MCP Server的工具的输出结果

#### 使用
##### 使用 uv
如果使用 [`uv`](https://docs.astral.sh/uv/) 无须安装额外的依赖， 使用
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) 直接运行 *nacos-mcp-router*。
```
export NACOS_ADDR=127.0.0.1:8848
export NACOS_USERNAME=nacos
export NACOS_PASSWORD=$PASSWORD
uvx nacos-mcp-router@latest
```

##### 使用 PIP

此外，你也可以通过pip安装 `nacos-mcp-router` : 

```
pip install nacos-mcp-router
```

安装完成后，使用如下命令运行（以Nacos本地standalone模式部署为例）:

```
export NACOS_ADDR=127.0.0.1:8848
export NACOS_USERNAME=nacos
export NACOS_PASSWORD=$PASSWORD
python -m nacos-mcp-router
```

##### 使用docker
```
docker run -it --rm --network host -e NACOS_ADDR=$NACOS_ADDR -e NACOS_USERNAME=$NACOS_USERNAME -e NACOS_PASSWORD=$NACOS_PASSWORD -e TRANSPORT_TYPE=$TRANSPORT_TYPE nacos-mcp-router:latest
```

##### 使用Cline、Cursor、Claude等

添加MCP Server配置如下:

###### 使用 uvx

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
                "NACOS_ADDR": "<NACOS-ADDR>, 选填，默认为127.0.0.1:8848",
                "NACOS_USERNAME": "<NACOS-USERNAME>, 选填，默认为nacos",
                "NACOS_PASSWORD": "<NACOS-PASSWORD>, 必填"
            }
        }
    }
}
```

> 如果启动失败，你需要把`command`字段里的`uvx`替换为命令的全路径。`uvx`命令全路径查找方法为：MacOS或Linux系统下使用`which uvx`，Windows系统使用`where uvx`。

###### 使用 docker
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

### proxy模式
proxy模式支持把sse、stdio协议MCP Server转换为streamableHTTP协议MCP Server。
#### 使用
proxy模式的使用与router类似，参数略有不同，建议使用docker部署。
```
docker run -d --rm --network host -e NACOS_ADDR=$NACOS_ADDR -e NACOS_USERNAME=$NACOS_USERNAME -e NACOS_PASSWORD=$NACOS_PASSWORD -e TRANSPORT_TYPE=streamable_http -e PROXIED_MCP_NAME=$PROXIED_MCP_NAME -e   nacos-mcp-router:latest
```

### 开发

本地开发步骤如下:

1. 克隆仓库；
2. 修改代码；
3. 在Cline等工具中测试功能:

```json
{
  "mcpServers": {
    "nacos-mcp-router": {
      "command": "uv",
      "args": [
        "--directory","PATH-TO-PROJECT","run","nacos-mcp-router"
      ],
      "env": {
        "NACOS_ADDR": "<NACOS-ADDR>, 选填，默认为127.0.0.1:8848",
        "NACOS_USERNAME": "<NACOS-USERNAME>, 选填，默认为nacos",
        "NACOS_PASSWORD": "<NACOS-PASSWORD>, 必填"
      }
    }
  }
}
```

### 环境变量设置
|    |    |    |    |    |
|----|----|----|----|----|
|  参数 | 描述 | 默认值 | 是否必填 | 备注 |
| NACOS_ADDR | Nacos 服务器地址 | 127.0.0.1:8848 | 否 | 填写 Nacos 服务器的地址，如 192.168.1.1:8848，注意要写端口
| NACOS_USERNAME | Nacos 用户名 | nacos | 否 | 填写 Nacos 用户名，如 nacos
| NACOS_PASSWORD | Nacos 密码 | 密码 | 是 | 填写 Nacos 密码，如 nacos
| TRANSPORT_TYPE | 传输协议类型 | stdio | 否 | 填写传输协议类型，可选值：stdio、sse、streamable_http
| PROXIED_MCP_NAME | 代理的 MCP 服务器名称 | - | 否 | proxy模式下需要被转换的 MCP 服务器名称，需要先注册到Nacos
| MODE | 工作模式 | router  | 否 |可选的值：router、proxy |





## Typescript接入

### 配置

在 MCP 客户端（如 Cursor、Cline 等）中添加如下配置：

```json
{
  "mcpServers": {
    "nacos-mcp-router": {
      "command": "npx",
      "args": [
        "nacos-mcp-router@latest"
      ],
      "env": {
        "NACOS_ADDR": "<NACOS-ADDR>, 选填，默认为127.0.0.1:8848",
        "NACOS_USERNAME": "<NACOS-USERNAME>, 选填，默认为nacos",
        "NACOS_PASSWORD": "<NACOS-PASSWORD>, 必填"
      }
    }
  }
}
```

## 许可证
nacos-mcp-router 使用 Apache 2.0 许可证. 这意味着您可以自由地使用、修改和分发该软件，但需遵守 Apache 2.0 许可证的条款和条件。更多详细信息，请参阅项目仓库中的 LICENSE 文件
