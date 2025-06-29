#!/bin/bash

# nacos-mcp-router Helm Chart 部署脚本
# 使用方法: ./deploy.sh [basic|production|custom] [release-name] [namespace]

set -e

# 默认值
DEPLOYMENT_TYPE=${1:-basic}
RELEASE_NAME=${2:-nacos-mcp-router}
NAMESPACE=${3:-default}
CHART_PATH="./helm/nacos-mcp-router"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查前置条件
check_prerequisites() {
    print_info "检查前置条件..."
    
    if ! command -v helm &> /dev/null; then
        print_error "Helm 未安装，请先安装 Helm"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl 未安装，请先安装 kubectl"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        print_error "无法连接到 Kubernetes 集群"
        exit 1
    fi
    
    print_info "前置条件检查通过"
}

# 创建命名空间
create_namespace() {
    if [ "$NAMESPACE" != "default" ]; then
        print_info "创建命名空间: $NAMESPACE"
        kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    fi
}

# 部署函数
deploy() {
    local values_file=""
    
    case $DEPLOYMENT_TYPE in
        basic)
            print_info "使用基本配置部署..."
            values_file="$CHART_PATH/examples/basic-values.yaml"
            ;;
        production)
            print_info "使用生产环境配置部署..."
            values_file="$CHART_PATH/examples/production-values.yaml"
            print_warn "生产环境配置需要手动修改密码和域名等信息"
            ;;
        custom)
            print_info "使用自定义配置部署..."
            read -p "请输入自定义values文件路径: " custom_values
            if [ ! -f "$custom_values" ]; then
                print_error "文件不存在: $custom_values"
                exit 1
            fi
            values_file="$custom_values"
            ;;
        *)
            print_error "不支持的部署类型: $DEPLOYMENT_TYPE"
            print_info "支持的类型: basic, production, custom"
            exit 1
            ;;
    esac
    
    if [ ! -d "$CHART_PATH" ]; then
        print_error "Helm Chart 目录不存在: $CHART_PATH"
        exit 1
    fi
    
    print_info "验证 Helm Chart..."
    helm lint $CHART_PATH
    
    print_info "开始部署 $RELEASE_NAME 到命名空间 $NAMESPACE..."
    
    if [ -n "$values_file" ] && [ -f "$values_file" ]; then
        helm upgrade --install $RELEASE_NAME $CHART_PATH \
            --namespace $NAMESPACE \
            --values $values_file \
            --wait \
            --timeout 10m
    else
        helm upgrade --install $RELEASE_NAME $CHART_PATH \
            --namespace $NAMESPACE \
            --wait \
            --timeout 10m
    fi
    
    print_info "部署完成！"
}

# 显示部署后信息
show_post_deployment_info() {
    print_info "获取部署状态..."
    
    kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=nacos-mcp-router
    kubectl get svc -n $NAMESPACE -l app.kubernetes.io/name=nacos-mcp-router
    
    print_info "访问Nacos控制台:"
    print_info "1. 使用端口转发:"
    echo "   kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME 8080:8080"
    echo "   然后访问: http://localhost:8080/nacos"
    
    print_info "2. 查看日志:"
    echo "   kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=nacos-mcp-router -c nacos"
    echo "   kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=nacos-mcp-router -c router"
}

# 主函数
main() {
    echo "========================================"
    echo "  nacos-mcp-router Helm Chart 部署工具"
    echo "========================================"
    
    print_info "部署参数:"
    echo "  - 部署类型: $DEPLOYMENT_TYPE"
    echo "  - Release名称: $RELEASE_NAME"
    echo "  - 命名空间: $NAMESPACE"
    echo ""
    
    check_prerequisites
    create_namespace
    deploy
    show_post_deployment_info
    
    print_info "部署完成！"
}

# 处理命令行参数
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "nacos-mcp-router Helm Chart 部署脚本"
    echo "使用方法: $0 [部署类型] [Release名称] [命名空间]"
    echo "部署类型: basic, production, custom"
    exit 0
fi

# 运行主函数
main 