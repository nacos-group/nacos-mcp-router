#!/bin/bash

# Nacos MCP Router 端到端测试启动脚本
# 基于 MCP Inspector + Playwright 的真正 E2E 测试

set -e

echo "🚀 开始 Nacos MCP Router 端到端测试流程"
echo "======================================="

# 清理函数
cleanup() {
    echo ""
    echo "🧹 清理进程..."
    if [[ -n $MCP_INSPECTOR_PID ]]; then
        kill $MCP_INSPECTOR_PID 2>/dev/null || true
        echo "✅ MCP Inspector 进程已终止"
    fi
    
    if [[ -n $MOCK_NACOS_PID ]]; then
        kill $MOCK_NACOS_PID 2>/dev/null || true
        echo "✅ Mock Nacos 进程已终止"
    fi
    
    # 额外清理可能占用端口的进程
    cleanup_ports
    
    # 清理临时文件
    rm -f mcp-inspector.log mock-nacos.log
    
    exit 0
}

# 清理端口占用
cleanup_ports() {
    local ports=(6274 6277 8848)
    for port in "${ports[@]}"; do
        local pids=$(lsof -ti :$port 2>/dev/null || true)
        if [[ -n "$pids" ]]; then
            echo "🧹 清理端口 $port 上的进程: $pids"
            kill -9 $pids 2>/dev/null || true
        fi
    done
    # 额外清理 inspector 相关进程 - 更精确的匹配
    pkill -f "mcp-inspector" 2>/dev/null || true
    pkill -f "scripts/e2e/mock-nacos-server.js" 2>/dev/null || true
    sleep 2
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 第一步：构建项目
echo "📦 构建 Nacos MCP Router..."
cd "$PROJECT_ROOT"
npm run build

if [ $? -ne 0 ]; then
    echo "❌ 构建失败"
    exit 1
fi

echo "✅ 构建完成"

# 第二步：检查并安装 Playwright 浏览器
echo ""
echo "🎭 检查 Playwright 浏览器..."

# 检查 Playwright 浏览器是否可用（更通用的检测方式）
if ! npx playwright test --list > /dev/null 2>&1; then
    echo "🔄 Playwright 浏览器未安装，正在自动安装..."
    
    # 安装 Playwright 浏览器
    npx playwright install chromium --with-deps
    
    if [ $? -ne 0 ]; then
        echo "❌ Playwright 浏览器安装失败"
        echo "💡 提示：你也可以手动运行：npx playwright install chromium"
        exit 1
    fi
    
    echo "✅ Playwright 浏览器安装完成"
else
    echo "✅ Playwright 浏览器已就绪"
fi

# 第三步：启动 Mock Nacos 服务器
echo ""
echo "🔄 启动 Mock Nacos 服务器..."

# 先清理可能占用的端口
echo "🧹 清理现有端口占用..."
cleanup_ports

node "$SCRIPT_DIR/e2e/mock-nacos-server.js" > mock-nacos.log 2>&1 &
MOCK_NACOS_PID=$!

echo "⏳ 等待 Mock Nacos 服务器启动..."
sleep 3

# 检查 Mock Nacos 是否启动成功
if ! curl -s "http://localhost:8848/nacos/v3/admin/ai/mcp/list" > /dev/null 2>&1; then
    echo "❌ Mock Nacos 服务器启动失败"
    echo "日志内容："
    cat mock-nacos.log 2>/dev/null || echo "无法读取日志文件"
    cleanup
fi

echo "✅ Mock Nacos 服务器已启动"

# 第四步：启动 MCP Inspector
echo ""
echo "🔄 启动 MCP Inspector..."

# 设置环境变量指向 Mock Nacos
export NACOS_SERVER_ADDR="localhost:8848"
export NACOS_USERNAME="nacos"
export NACOS_PASSWORD="nacos_password"
export COMPASS_API_BASE="https://registry.mcphub.io"

ENABLE_FILE_LOGGING=true npx @modelcontextprotocol/inspector node "$PROJECT_ROOT/dist/stdio.js" > mcp-inspector.log 2>&1 &
MCP_INSPECTOR_PID=$!

echo "⏳ 等待 MCP Inspector 启动..."

# 等待并解析 MCP Inspector 输出
timeout=30
count=0
INSPECTOR_URL=""
AUTH_TOKEN=""

while [ $count -lt $timeout ]; do
    if [[ -f mcp-inspector.log ]]; then
        # 首先检查是否有带 token 的完整 URL
        if grep -q "inspector with token pre-filled" mcp-inspector.log; then
            INSPECTOR_URL=$(grep -o "http://localhost:[0-9]*/?MCP_PROXY_AUTH_TOKEN=[a-f0-9-]*" mcp-inspector.log | head -1)
            if [[ -n $INSPECTOR_URL ]]; then
                # 提取 token 和 base URL
                AUTH_TOKEN=$(echo $INSPECTOR_URL | grep -o "MCP_PROXY_AUTH_TOKEN=[a-f0-9-]*" | cut -d'=' -f2)
                BASE_URL=$(echo $INSPECTOR_URL | cut -d'?' -f1)
                echo "✅ 找到完整的 Inspector URL: $INSPECTOR_URL"
                break
            fi
        fi
        
        # 检查服务器是否启动（寻找端口信息）
        if grep -q "localhost:6274" mcp-inspector.log; then
            BASE_URL="http://localhost:6274"
            # 尝试多种方式提取 token
            AUTH_TOKEN=$(grep -oE "token[\"':]*[[:space:]]*[\"']?[a-f0-9-]+" mcp-inspector.log | head -1 | grep -oE "[a-f0-9-]+$" || echo "")
            
            # 如果没有找到 token，尝试其他模式
            if [[ -z $AUTH_TOKEN ]]; then
                AUTH_TOKEN=$(grep -oE "MCP_PROXY_AUTH_TOKEN[=:][\"']?[a-f0-9-]+" mcp-inspector.log | head -1 | grep -oE "[a-f0-9-]+$" || echo "")
            fi
            
            if [[ -n $AUTH_TOKEN ]]; then
                INSPECTOR_URL="$BASE_URL?MCP_PROXY_AUTH_TOKEN=$AUTH_TOKEN"
                echo "✅ 从日志提取到 Inspector URL: $INSPECTOR_URL"
                break
            else
                echo "⚠️  找到服务器但未找到 token，使用基础 URL: $BASE_URL"
                INSPECTOR_URL="$BASE_URL"
                break
            fi
        fi
    fi
    sleep 1
    count=$((count + 1))
done

if [[ -z $BASE_URL ]]; then
    echo "❌ MCP Inspector 启动失败或超时"
    echo "日志内容："
    cat mcp-inspector.log 2>/dev/null || echo "无法读取日志文件"
    cleanup
fi

echo "✅ MCP Inspector 已启动"
echo "📍 URL: $BASE_URL"
echo "🔑 Token: $AUTH_TOKEN"

# 第五步：等待服务就绪
echo ""
echo "⏳ 等待服务就绪..."
for i in {1..10}; do
    if curl -s "$BASE_URL" > /dev/null 2>&1; then
        echo "✅ 服务就绪"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ 服务未就绪，超时"
        cleanup
    fi
    sleep 2
done

# 第六步：运行 Playwright 测试
echo ""
echo "🧪 运行 Playwright 测试..."
echo "使用 URL: $INSPECTOR_URL"

# 导出环境变量供 Playwright 使用
export MCP_AUTH_TOKEN="$AUTH_TOKEN"
export MCP_INSPECTOR_URL="$BASE_URL"
export MCP_INSPECTOR_FULL_URL="$INSPECTOR_URL"

# 运行测试（根据参数选择模式）
TEST_MODE=${1:-"headed"}

case $TEST_MODE in
    "headless")
        echo "🔧 运行无头模式测试..."
        NODE_OPTIONS='--no-deprecation' npx playwright test
        ;;
    "debug")
        echo "🐛 运行调试模式测试..."
        NODE_OPTIONS='--no-deprecation' npx playwright test --debug
        ;;
    "ui")
        echo "🎨 运行 UI 模式测试..."
        NODE_OPTIONS='--no-deprecation' npx playwright test --ui
        ;;
    *)
        echo "👀 运行有头模式测试..."
        NODE_OPTIONS='--no-deprecation' npx playwright test --headed
        ;;
esac

TEST_EXIT_CODE=$?

# 第七步：显示结果
echo ""
echo "======================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ 测试完成！所有测试通过"
else
    echo "❌ 测试完成，但有测试失败"
    echo "📊 查看详细报告: npx playwright show-report"
fi

echo ""
echo "📊 测试报告和截图位置: test-results/"
echo "🔗 Inspector 仍在运行: $INSPECTOR_URL"
echo ""
echo "按 Ctrl+C 停止所有服务并退出..."

# 保持脚本运行直到用户中断
while true; do
    sleep 1
done