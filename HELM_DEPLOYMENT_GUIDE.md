# nacos-mcp-router Helm Chart 部署指南

## 概述

本Helm Chart用于在Kubernetes集群中部署Nacos和nacos-mcp-router服务。该Chart满足以下要求：

1. ✅ **Router和Nacos部署在同一个Pod内** - 使用两个容器共享网络
2. ✅ **先部署Nacos，成功后部署Router** - 通过健康检查和启动脚本确保顺序
3. ✅ **自动配置Router环境变量** - 根据Nacos配置自动设置连接参数
4. ✅ **参考官方Nacos Docker部署** - 遵循官方standalone模式配置

## 文件结构

```
helm/nacos-mcp-router/
├── Chart.yaml                    # Chart基本信息
├── values.yaml                   # 默认配置值
├── README.md                     # 使用文档
├── templates/
│   ├── _helpers.tpl              # 模板助手函数
│   ├── configmap.yaml            # 配置文件和启动脚本
│   ├── deployment.yaml           # 主要部署配置
│   ├── service.yaml              # 服务配置
│   ├── serviceaccount.yaml       # 服务账户
│   ├── ingress.yaml              # Ingress配置（可选）
│   ├── pvc.yaml                  # 持久化存储（可选）
│   ├── hpa.yaml                  # 自动扩缩容（可选）
│   └── NOTES.txt                 # 部署后说明
└── examples/
    ├── basic-values.yaml         # 基本配置示例
    └── production-values.yaml    # 生产环境配置示例
```

## 核心特性

### 1. 同Pod部署架构

- **Nacos容器**: 运行Nacos服务器，提供服务注册和配置管理
- **Router容器**: 运行nacos-mcp-router，等待Nacos就绪后启动
- **共享网络**: 两个容器共享Pod网络，Router通过localhost访问Nacos

### 2. 启动顺序控制

通过ConfigMap中的启动脚本实现：
```bash
# 等待Nacos健康检查通过
while [ $attempt -lt $max_attempts ]; do
  if curl -f -s http://localhost:8848/nacos/actuator/health; then
    echo "Nacos is ready!"
    break
  fi
  sleep 5
done

# 启动Router
exec python -m nacos_mcp_router
```

### 3. 自动配置

Router的环境变量自动从Nacos配置中获取：
- `NACOS_ADDR`: 自动设置为localhost:8848
- `NACOS_PASSWORD`: 自动使用Nacos管理员密码
- 其他认证参数自动配置

## 快速开始

### 1. 基本部署

```bash
# 使用部署脚本（推荐）
./deploy.sh basic my-nacos-router default

# 或使用Helm命令
helm install my-nacos-router ./helm/nacos-mcp-router \
  -f helm/nacos-mcp-router/examples/basic-values.yaml
```

### 2. 生产环境部署

```bash
# 修改生产配置
cp helm/nacos-mcp-router/examples/production-values.yaml my-prod-values.yaml
# 编辑 my-prod-values.yaml，修改密码、域名等

# 部署
./deploy.sh custom my-nacos-prod production
```

### 3. 访问服务

```bash
# 端口转发
kubectl port-forward svc/my-nacos-router 8080:8080

# 访问Nacos控制台
# URL: http://localhost:8080/nacos
# 用户名: nacos
# 密码: 配置文件中的adminPassword
```

## 配置说明

### 核心配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `nacos.mode` | Nacos运行模式 | `standalone` |
| `nacos.adminPassword` | Nacos管理员密码 | `nacos123` |
| `nacos.auth.token` | JWT Token密钥 | 预设Base64值 |
| `router.mode` | Router工作模式 | `router` |
| `router.transportType` | 传输协议 | `stdio` |

### 安全配置

生产环境必须修改：
- `nacos.adminPassword`: 管理员密码
- `nacos.auth.token`: JWT Token（Base64编码，>32字符）
- `nacos.auth.identityKey/Value`: 服务间认证

### 网络配置

```yaml
service:
  type: ClusterIP  # 或 LoadBalancer/NodePort
  nacosConsolePort: 8080
  nacosServerPort: 8848
  nacosGrpcPort: 9848
  routerPort: 8000  # 仅HTTP模式使用
```

## 部署验证

### 1. 检查Pod状态

```bash
kubectl get pods -l app.kubernetes.io/name=nacos-mcp-router
```

预期输出：
```
NAME                                READY   STATUS    RESTARTS   AGE
nacos-mcp-router-xxx-xxx           2/2     Running   0          5m
```

### 2. 检查日志

```bash
# Nacos日志
kubectl logs -l app.kubernetes.io/name=nacos-mcp-router -c nacos

# Router日志
kubectl logs -l app.kubernetes.io/name=nacos-mcp-router -c router
```

### 3. 健康检查

```bash
# 检查Nacos健康状态
kubectl exec -it <pod-name> -c nacos -- curl http://localhost:8848/nacos/actuator/health

# 检查Router连接
kubectl exec -it <pod-name> -c router -- curl http://localhost:8848/nacos/v3/client/ns/instance/list?serviceName=test
```

## 故障排除

### 常见问题

1. **Pod启动失败**
   - 检查资源限制
   - 查看Pod事件：`kubectl describe pod <pod-name>`

2. **Nacos无法访问**
   - 确认Service配置正确
   - 检查端口转发：`kubectl port-forward svc/<service-name> 8080:8080`

3. **Router连接失败**
   - 检查Nacos是否完全启动
   - 验证认证配置
   - 查看Router日志

### 调试命令

```bash
# 进入Pod调试
kubectl exec -it <pod-name> -c nacos -- /bin/bash
kubectl exec -it <pod-name> -c router -- /bin/bash

# 查看配置
kubectl get configmap <configmap-name> -o yaml

# 查看服务
kubectl get svc -l app.kubernetes.io/name=nacos-mcp-router
```

## 高级配置

### 1. 持久化存储

```yaml
persistence:
  enabled: true
  storageClass: "fast-ssd"
  size: 10Gi
```

### 2. Ingress配置

```yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: nacos.example.com
      paths:
        - path: /
          pathType: Prefix
```

### 3. 资源限制

```yaml
resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 2Gi
```

## 升级和维护

### 升级Chart

```bash
# 升级到新版本
helm upgrade my-nacos-router ./helm/nacos-mcp-router

# 升级并修改配置
helm upgrade my-nacos-router ./helm/nacos-mcp-router -f new-values.yaml
```

### 备份和恢复

```bash
# 备份Nacos数据（如果启用持久化）
kubectl exec -it <pod-name> -c nacos -- tar -czf /tmp/nacos-backup.tar.gz /home/nacos/data

# 复制备份文件
kubectl cp <pod-name>:/tmp/nacos-backup.tar.gz ./nacos-backup.tar.gz -c nacos
```

## 生产部署建议

1. **安全性**
   - 修改所有默认密码
   - 使用强密码和随机Token
   - 启用HTTPS（通过Ingress）

2. **可靠性**
   - 启用持久化存储
   - 配置适当的资源限制
   - 设置健康检查

3. **监控**
   - 配置日志收集
   - 设置监控指标
   - 配置告警规则

4. **网络**
   - 使用LoadBalancer或Ingress
   - 配置网络策略
   - 启用TLS加密

## 参考资料

- [Nacos官方文档](https://nacos.io/docs/latest/quickstart/quick-start-docker/?spm=5238cd80.2ef5001f.0.0.3f613b7cl5pstT)
- [nacos-mcp-router项目](https://github.com/nacos-group/nacos-mcp-router)
- [Helm官方文档](https://helm.sh/docs/)
- [Kubernetes官方文档](https://kubernetes.io/docs/) 