# nacos-mcp-router Docker 部署指南

## 概述

本项目提供了两个Dockerfile版本，用于构建包含Nacos Server和nacos-mcp-router的Docker镜像：

1. **`Dockerfile`** - 使用固定版本的Nacos Server (v2.3.2)
2. **`Dockerfile.latest`** - 自动下载GitHub上最新版本的Nacos Server

## 🚀 主要特性

### ✅ 满足的需求
- **自动下载Nacos Server** - 从GitHub Release自动下载最新或指定版本
- **启动顺序控制** - 先启动Nacos Server，等待就绪后启动Router
- **健康检查** - 内置健康检查机制，确保服务正常运行
- **环境变量配置** - 支持通过环境变量灵活配置
- **日志输出** - 友好的日志输出，便于调试

### 🔧 核心功能
- 单容器运行Nacos + Router
- 自动等待Nacos启动完成
- 支持standalone模式
- 内置健康检查
- 持久化数据支持

## 📁 文件说明

```
src/python/
├── Dockerfile          # 固定版本Dockerfile (Nacos v2.3.2)
├── Dockerfile.latest   # 自动最新版本Dockerfile
docker-compose.yml      # Docker Compose配置
build-and-test.sh      # 构建测试脚本
```

## 🛠️ 快速开始

### 方法1: 使用构建脚本（推荐）

```bash
# 构建并测试所有镜像
./build-and-test.sh all

# 只构建固定版本镜像
./build-and-test.sh build

# 只构建最新版本镜像
./build-and-test.sh latest

# 清理所有镜像和容器
./build-and-test.sh clean
```

### 方法2: 使用Docker Compose

```bash
# 启动固定版本服务
docker-compose up -d

# 启动最新版本服务
docker-compose --profile latest up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方法3: 直接使用Docker

```bash
# 构建镜像
docker build -f src/python/Dockerfile -t nacos-mcp-router:latest .

# 运行容器
docker run -d \
  --name nacos-mcp-router \
  -p 8080:8080 \
  -p 8848:8848 \
  -p 9848:9848 \
  -e NACOS_PASSWORD=your-password \
  nacos-mcp-router:latest
```

## 🔧 环境变量配置

### Nacos 配置

| 环境变量 | 描述 | 默认值 |
|---------|------|--------|
| `MODE` | Nacos运行模式 | `standalone` |
| `NACOS_AUTH_TOKEN` | JWT认证Token | 预设值 |
| `NACOS_AUTH_IDENTITY_KEY` | 服务间认证Key | `nacos-server-identity` |
| `NACOS_AUTH_IDENTITY_VALUE` | 服务间认证Value | `nacos-server-value` |
| `NACOS_AUTH_ENABLE` | 启用认证 | `true` |
| `SPRING_SECURITY_ENABLED` | 启用Spring Security | `true` |
| `NACOS_PASSWORD` | 管理员密码 | `nacos` |

### Router 配置

| 环境变量 | 描述 | 默认值 |
|---------|------|--------|
| `NACOS_ADDR` | Nacos地址 | `127.0.0.1:8848` |
| `NACOS_USERNAME` | Nacos用户名 | `nacos` |
| `TRANSPORT_TYPE` | 传输协议 | `stdio` |
| `ROUTER_MODE` | Router模式 | `router` |
| `COMPASS_API_BASE` | Compass API端点 | `https://registry.mcphub.io` |
| `SEARCH_MIN_SIMILARITY` | 搜索最小相似度 | `0.5` |
| `SEARCH_RESULT_LIMIT` | 搜索结果限制 | `10` |

## 📊 启动流程

容器启动时的详细流程：

```
1. 🚀 启动容器
2. 📦 显示Nacos版本信息
3. 🔄 启动Nacos Server
4. ⏳ 等待Nacos健康检查通过
5. ✅ Nacos就绪
6. 🔄 启动nacos-mcp-router
7. 🌐 服务可用
```

## 🔍 访问服务

### Nacos 控制台
- **URL**: http://localhost:8080/nacos
- **用户名**: nacos
- **密码**: 环境变量 `NACOS_PASSWORD` 的值

### API 端点
- **Nacos Server**: http://localhost:8848
- **健康检查**: http://localhost:8848/nacos/actuator/health
- **Router**: 根据 `TRANSPORT_TYPE` 配置

## 🐛 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 查看容器日志
   docker logs nacos-mcp-router
   
   # 检查容器状态
   docker ps -a
   ```

2. **Nacos启动超时**
   ```bash
   # 增加内存限制
   docker run --memory=2g nacos-mcp-router:latest
   
   # 检查Java进程
   docker exec -it nacos-mcp-router ps aux | grep java
   ```

3. **健康检查失败**
   ```bash
   # 手动检查健康状态
   docker exec -it nacos-mcp-router curl http://localhost:8848/nacos/actuator/health
   
   # 检查端口占用
   docker exec -it nacos-mcp-router netstat -tlnp
   ```

### 调试命令

```bash
# 进入容器
docker exec -it nacos-mcp-router /bin/bash

# 查看Nacos日志
docker exec -it nacos-mcp-router tail -f /opt/nacos/logs/nacos-startup.log

# 查看进程
docker exec -it nacos-mcp-router ps aux

# 测试网络连接
docker exec -it nacos-mcp-router curl http://localhost:8848/nacos/actuator/health
```

## 📈 性能优化

### 资源配置

```bash
# 推荐的资源配置
docker run -d \
  --name nacos-mcp-router \
  --memory=2g \
  --cpus=1.0 \
  -p 8080:8080 \
  -p 8848:8848 \
  -p 9848:9848 \
  nacos-mcp-router:latest
```

### 持久化数据

```bash
# 使用数据卷持久化
docker run -d \
  --name nacos-mcp-router \
  -v nacos-data:/opt/nacos/data \
  -v nacos-logs:/opt/nacos/logs \
  -p 8080:8080 \
  -p 8848:8848 \
  nacos-mcp-router:latest
```

## 🔄 版本比较

| 特性 | Dockerfile | Dockerfile.latest |
|------|------------|-------------------|
| Nacos版本 | 固定 v2.3.2 | 自动获取最新版 |
| 构建速度 | 快 | 较慢（需要API调用） |
| 稳定性 | 高 | 中等 |
| 适用场景 | 生产环境 | 开发测试 |

## 🚢 生产部署建议

1. **使用固定版本** - 生产环境推荐使用 `Dockerfile`
2. **设置资源限制** - 配置适当的内存和CPU限制
3. **启用持久化** - 使用数据卷保存Nacos数据
4. **配置健康检查** - 使用Docker健康检查机制
5. **安全配置** - 修改默认密码和认证配置

## 📚 相关文档

- [Nacos官方文档](https://nacos.io/docs/latest/quickstart/quick-start-docker/)
- [Docker官方文档](https://docs.docker.com/)
- [nacos-mcp-router项目](https://github.com/nacos-group/nacos-mcp-router)

## 🤝 贡献

如果你发现问题或有改进建议，欢迎提交Issue或Pull Request。 