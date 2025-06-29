#!/bin/bash

# nacos-mcp-router Docker构建和测试脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查Docker是否运行
check_docker() {
    print_step "检查Docker环境..."
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker未运行，请启动Docker"
        exit 1
    fi
    print_info "Docker环境正常"
}

# 构建镜像
build_image() {
    local dockerfile=$1
    local tag=$2
    
    print_step "构建Docker镜像: $tag"
    print_info "使用Dockerfile: $dockerfile"
    
    docker build -f $dockerfile -t $tag .
    
    if [ $? -eq 0 ]; then
        print_info "镜像构建成功: $tag"
    else
        print_error "镜像构建失败"
        exit 1
    fi
}

# 测试镜像
test_image() {
    local tag=$1
    local port_offset=${2:-0}
    
    print_step "测试Docker镜像: $tag"
    
    local console_port=$((8080 + port_offset))
    local server_port=$((8848 + port_offset))
    local grpc_port=$((9848 + port_offset))
    
    print_info "启动容器，端口映射: $console_port:8080, $server_port:8848, $grpc_port:9848"
    
    # 停止并删除已存在的测试容器
    docker stop nacos-mcp-test 2>/dev/null || true
    docker rm nacos-mcp-test 2>/dev/null || true
    
    # 启动测试容器
    docker run -d \
        --name nacos-mcp-test \
        -p $console_port:8080 \
        -p $server_port:8848 \
        -p $grpc_port:9848 \
        -e NACOS_PASSWORD=test123 \
        -e TRANSPORT_TYPE=stdio \
        $tag
    
    print_info "等待服务启动..."
    
    # 等待服务启动
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s http://localhost:$server_port/nacos/actuator/health >/dev/null 2>&1; then
            print_info "✅ 服务启动成功！"
            break
        fi
        echo -n "."
        sleep 5
        attempt=$((attempt+1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "服务启动超时"
        print_info "查看容器日志:"
        docker logs nacos-mcp-test
        docker stop nacos-mcp-test
        docker rm nacos-mcp-test
        return 1
    fi
    
    # 测试Nacos API
    print_step "测试Nacos API..."
    
    # 健康检查
    if curl -f -s http://localhost:$server_port/nacos/actuator/health | grep -q "UP"; then
        print_info "✅ Nacos健康检查通过"
    else
        print_error "❌ Nacos健康检查失败"
        docker logs nacos-mcp-test
        docker stop nacos-mcp-test
        docker rm nacos-mcp-test
        return 1
    fi
    
    # 测试服务注册
    print_step "测试服务注册..."
    if curl -X POST "http://localhost:$server_port/nacos/v3/client/ns/instance?serviceName=test-service&ip=127.0.0.1&port=8080" >/dev/null 2>&1; then
        print_info "✅ 服务注册成功"
    else
        print_warn "⚠️  服务注册测试失败（可能需要认证）"
    fi
    
    # 显示访问信息
    print_info "========================================"
    print_info "🌐 Nacos控制台: http://localhost:$console_port/nacos"
    print_info "👤 用户名: nacos"
    print_info "🔑 密码: test123"
    print_info "📡 API端点: http://localhost:$server_port"
    print_info "========================================"
    
    # 询问是否保持容器运行
    read -p "是否保持容器运行以便测试？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "容器将继续运行，使用以下命令停止:"
        echo "  docker stop nacos-mcp-test"
        echo "  docker rm nacos-mcp-test"
        return 0
    else
        print_info "停止并删除测试容器..."
        docker stop nacos-mcp-test
        docker rm nacos-mcp-test
    fi
}

# 显示帮助信息
show_help() {
    echo "nacos-mcp-router Docker构建和测试脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  build     - 构建Docker镜像"
    echo "  test      - 测试Docker镜像"
    echo "  latest    - 构建并测试最新版本镜像"
    echo "  all       - 构建并测试所有镜像"
    echo "  clean     - 清理Docker镜像和容器"
    echo "  -h, --help - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 build    # 只构建镜像"
    echo "  $0 test     # 只测试镜像"
    echo "  $0 all      # 构建并测试所有镜像"
    echo ""
}

# 清理函数
clean_up() {
    print_step "清理Docker资源..."
    
    # 停止并删除测试容器
    docker stop nacos-mcp-test 2>/dev/null || true
    docker rm nacos-mcp-test 2>/dev/null || true
    
    # 删除构建的镜像
    docker rmi nacos-mcp-router:latest 2>/dev/null || true
    docker rmi nacos-mcp-router:auto-latest 2>/dev/null || true
    
    # 清理未使用的镜像
    docker image prune -f
    
    print_info "清理完成"
}

# 主函数
main() {
    case ${1:-all} in
        build)
            check_docker
            build_image "src/python/Dockerfile" "nacos-mcp-router:latest"
            ;;
        test)
            check_docker
            test_image "nacos-mcp-router:latest" 0
            ;;
        latest)
            check_docker
            build_image "src/python/Dockerfile.latest" "nacos-mcp-router:auto-latest"
            test_image "nacos-mcp-router:auto-latest" 10
            ;;
        all)
            check_docker
            print_info "========================================"
            print_info "🚀 开始构建和测试所有镜像"
            print_info "========================================"
            
            # 构建固定版本镜像
            build_image "src/python/Dockerfile" "nacos-mcp-router:latest"
            
            # 构建自动最新版本镜像
            build_image "src/python/Dockerfile.latest" "nacos-mcp-router:auto-latest"
            
            # 测试固定版本镜像
            print_info "测试固定版本镜像..."
            test_image "nacos-mcp-router:latest" 0
            
            # 测试自动最新版本镜像
            print_info "测试自动最新版本镜像..."
            test_image "nacos-mcp-router:auto-latest" 10
            
            print_info "========================================"
            print_info "✅ 所有测试完成！"
            print_info "========================================"
            ;;
        clean)
            clean_up
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@" 