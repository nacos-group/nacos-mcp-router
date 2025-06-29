# nacos-mcp-router Helm Chart

这个Helm chart用于在Kubernetes集群中部署Nacos和nacos-mcp-router服务。

## 前置条件

- Kubernetes 1.16+
- Helm 3.2.0+
- 可用的存储类（如果启用持久化）

## 安装Chart

### 基本安装

```bash
helm install my-nacos-mcp-router ./helm/nacos-mcp-router
```

### 自定义配置安装

```bash
helm install my-nacos-mcp-router ./helm/nacos-mcp-router \
  --set nacos.adminPassword=your-secure-password \
  --set router.nacos.password=your-secure-password
```

### 使用自定义values文件

```bash
helm install my-nacos-mcp-router ./helm/nacos-mcp-router -f my-values.yaml
```

## 卸载Chart

```bash
helm uninstall my-nacos-mcp-router
```

## 配置

### 主要配置参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `replicaCount` | Pod副本数 | `1` |
| `image.nacos.repository` | Nacos镜像仓库 | `nacos/nacos-server` |
| `image.nacos.tag` | Nacos镜像标签 | `latest` |
| `image.router.repository` | Router镜像仓库 | `nacos/nacos-mcp-router` |
| `image.router.tag` | Router镜像标签 | `latest` |

### Nacos配置

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `nacos.mode` | Nacos运行模式 | `standalone` |
| `nacos.auth.token` | 认证token (Base64编码) | `VGhpc0lzTXlTZWNyZXRLZXlGb3JOYWNvc01DUFJvdXRlcjEyMzQ1Njc4OTA=` |
| `nacos.auth.identityKey` | 服务间认证key | `nacos-server-identity` |
| `nacos.auth.identityValue` | 服务间认证value | `nacos-server-value` |
| `nacos.adminPassword` | 管理员密码 | `nacos123` |

### Router配置

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `router.mode` | Router工作模式 | `router` |
| `router.transportType` | 传输协议类型 | `stdio` |
| `router.nacos.addr` | Nacos地址 | `127.0.0.1:8848` |
| `router.nacos.username` | Nacos用户名 | `nacos` |
| `router.nacos.password` | Nacos密码 | `""` (使用nacos.adminPassword) |
| `router.search.compassApiBase` | Compass API端点 | `https://registry.mcphub.io` |
| `router.search.minSimilarity` | 最小相似度 | `0.5` |
| `router.search.resultLimit` | 结果限制 | `10` |

### 服务配置

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `service.type` | Service类型 | `ClusterIP` |
| `service.nacosConsolePort` | Nacos控制台端口 | `8080` |
| `service.nacosServerPort` | Nacos服务端口 | `8848` |
| `service.nacosGrpcPort` | Nacos gRPC端口 | `9848` |
| `service.routerPort` | Router端口 | `8000` |

### 持久化配置

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `persistence.enabled` | 启用持久化 | `false` |
| `persistence.storageClass` | 存储类 | `""` |
| `persistence.accessMode` | 访问模式 | `ReadWriteOnce` |
| `persistence.size` | 存储大小 | `1Gi` |

### Ingress配置

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `ingress.enabled` | 启用Ingress | `false` |
| `ingress.className` | Ingress类名 | `""` |
| `ingress.hosts[0].host` | 主机名 | `nacos-mcp-router.local` |
| `ingress.hosts[0].paths[0].path` | 路径 | `/` |
| `ingress.hosts[0].paths[0].pathType` | 路径类型 | `Prefix` |

## 使用示例

### 1. 启用持久化存储

```yaml
# values-persistent.yaml
persistence:
  enabled: true
  storageClass: "fast-ssd"
  size: 5Gi

nacos:
  adminPassword: "your-secure-password"

router:
  nacos:
    password: "your-secure-password"
```

```bash
helm install my-nacos-mcp-router ./helm/nacos-mcp-router -f values-persistent.yaml
```

### 2. 配置Ingress访问

```yaml
# values-ingress.yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: nacos.example.com
      paths:
        - path: /
          pathType: Prefix
          port: 8080
  tls:
    - secretName: nacos-tls
      hosts:
        - nacos.example.com

nacos:
  adminPassword: "your-secure-password"
```

```bash
helm install my-nacos-mcp-router ./helm/nacos-mcp-router -f values-ingress.yaml
```

### 3. 配置为Proxy模式

```yaml
# values-proxy.yaml
router:
  mode: "proxy"
  transportType: "streamable_http"
  proxy:
    mcpName: "your-mcp-server-name"

nacos:
  adminPassword: "your-secure-password"
```

```bash
helm install my-nacos-mcp-router ./helm/nacos-mcp-router -f values-proxy.yaml
```

## 访问服务

### 访问Nacos控制台

```bash
# 使用port-forward访问
kubectl port-forward svc/my-nacos-mcp-router 8080:8080

# 然后在浏览器中访问 http://localhost:8080/nacos
# 用户名: nacos
# 密码: 配置的adminPassword
```

### 查看日志

```bash
# 查看Nacos日志
kubectl logs -l app.kubernetes.io/name=nacos-mcp-router -c nacos

# 查看Router日志
kubectl logs -l app.kubernetes.io/name=nacos-mcp-router -c router
```

## 故障排除

### 常见问题

1. **Pod启动失败**
   ```bash
   kubectl describe pod -l app.kubernetes.io/name=nacos-mcp-router
   kubectl logs -l app.kubernetes.io/name=nacos-mcp-router -c nacos
   kubectl logs -l app.kubernetes.io/name=nacos-mcp-router -c router
   ```

2. **Nacos无法访问**
   - 检查Service是否正确创建
   - 确认端口转发是否正常
   - 验证认证配置是否正确

3. **Router连接Nacos失败**
   - 确认Nacos已完全启动
   - 检查网络连接
   - 验证认证信息

### 健康检查

```bash
# 检查Pod状态
kubectl get pods -l app.kubernetes.io/name=nacos-mcp-router

# 检查Service状态
kubectl get svc -l app.kubernetes.io/name=nacos-mcp-router

# 测试Nacos健康状态
kubectl exec -it <pod-name> -c nacos -- curl http://localhost:8848/nacos/actuator/health
```

## 升级

```bash
# 升级到新版本
helm upgrade my-nacos-mcp-router ./helm/nacos-mcp-router

# 升级并修改配置
helm upgrade my-nacos-mcp-router ./helm/nacos-mcp-router -f new-values.yaml
```

## 参考文档

- [Nacos官方文档](https://nacos.io/docs/latest/quickstart/quick-start-docker/?spm=5238cd80.2ef5001f.0.0.3f613b7cl5pstT)
- [nacos-mcp-router项目](https://github.com/nacos-group/nacos-mcp-router)
- [MCP协议文档](https://modelcontextprotocol.org) 