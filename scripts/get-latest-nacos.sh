#!/bin/bash

# 获取Nacos最新版本的脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 方法1: 使用GitHub API获取最新版本
get_latest_version_api() {
    print_step "使用GitHub API获取最新版本..."
    
    local api_url="https://api.github.com/repos/alibaba/nacos/releases/latest"
    local latest_version
    
    # 检查是否安装了jq
    if command -v jq >/dev/null 2>&1; then
        latest_version=$(curl -s "$api_url" | jq -r '.tag_name')
    else
        # 如果没有jq，使用grep和sed解析
        latest_version=$(curl -s "$api_url" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
    fi
    
    if [ -n "$latest_version" ] && [ "$latest_version" != "null" ]; then
        print_info "最新版本: $latest_version"
        echo "$latest_version"
    else
        print_error "无法获取最新版本"
        return 1
    fi
}

# 方法2: 使用GitHub Releases页面解析
get_latest_version_html() {
    print_step "使用HTML页面解析获取最新版本..."
    
    local releases_url="https://github.com/alibaba/nacos/releases/latest"
    local latest_version
    
    # 从重定向URL中提取版本号
    latest_version=$(curl -s -I "$releases_url" | grep -i location | sed -E 's/.*\/tag\/([^\/\r\n]+).*/\1/')
    
    if [ -n "$latest_version" ]; then
        print_info "最新版本: $latest_version"
        echo "$latest_version"
    else
        print_error "无法从HTML页面获取版本"
        return 1
    fi
}

# 方法3: 使用RSS Feed
get_latest_version_rss() {
    print_step "使用RSS Feed获取最新版本..."
    
    local rss_url="https://github.com/alibaba/nacos/releases.atom"
    local latest_version
    
    # 从RSS中提取第一个版本号
    latest_version=$(curl -s "$rss_url" | grep -o 'releases/tag/[^"]*' | head -1 | sed 's/releases\/tag\///')
    
    if [ -n "$latest_version" ]; then
        print_info "最新版本: $latest_version"
        echo "$latest_version"
    else
        print_error "无法从RSS获取版本"
        return 1
    fi
}

# 验证版本格式
validate_version() {
    local version=$1
    
    # 检查版本格式 (例如: v2.3.2, 2.3.2)
    if [[ $version =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        return 0
    else
        print_error "版本格式无效: $version"
        return 1
    fi
}

# 下载指定版本的Nacos
download_nacos() {
    local version=$1
    local download_dir=${2:-./downloads}
    
    # 确保版本号有v前缀
    if [[ ! $version =~ ^v ]]; then
        version="v$version"
    fi
    
    local download_url="https://github.com/alibaba/nacos/releases/download/${version}/nacos-server-${version}.tar.gz"
    local filename="nacos-server-${version}.tar.gz"
    
    print_step "下载Nacos $version..."
    print_info "下载URL: $download_url"
    
    mkdir -p "$download_dir"
    
    if curl -L -o "${download_dir}/${filename}" "$download_url"; then
        print_info "下载成功: ${download_dir}/${filename}"
        
        # 验证下载的文件
        if [ -f "${download_dir}/${filename}" ] && [ -s "${download_dir}/${filename}" ]; then
            print_info "文件大小: $(du -h "${download_dir}/${filename}" | cut -f1)"
            return 0
        else
            print_error "下载的文件无效"
            return 1
        fi
    else
        print_error "下载失败"
        return 1
    fi
}

# 获取所有可用版本
get_all_versions() {
    print_step "获取所有可用版本..."
    
    local api_url="https://api.github.com/repos/alibaba/nacos/releases"
    
    if command -v jq >/dev/null 2>&1; then
        curl -s "$api_url" | jq -r '.[].tag_name' | head -10
    else
        curl -s "$api_url" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/' | head -10
    fi
}

# 比较版本号
compare_versions() {
    local version1=$1
    local version2=$2
    
    # 移除v前缀
    version1=${version1#v}
    version2=${version2#v}
    
    if [ "$version1" = "$version2" ]; then
        echo "0"
    elif [ "$(printf '%s\n' "$version1" "$version2" | sort -V | head -n1)" = "$version1" ]; then
        echo "-1"
    else
        echo "1"
    fi
}

# 主函数
main() {
    local command=${1:-latest}
    
    case $command in
        latest|api)
            get_latest_version_api
            ;;
        html)
            get_latest_version_html
            ;;
        rss)
            get_latest_version_rss
            ;;
        all)
            print_info "尝试所有方法获取最新版本..."
            
            # 尝试API方法
            if latest_version=$(get_latest_version_api 2>/dev/null); then
                echo "$latest_version"
                exit 0
            fi
            
            # 尝试HTML方法
            if latest_version=$(get_latest_version_html 2>/dev/null); then
                echo "$latest_version"
                exit 0
            fi
            
            # 尝试RSS方法
            if latest_version=$(get_latest_version_rss 2>/dev/null); then
                echo "$latest_version"
                exit 0
            fi
            
            print_error "所有方法都失败了"
            exit 1
            ;;
        download)
            local version=${2:-$(get_latest_version_api)}
            local download_dir=${3:-./downloads}
            
            if validate_version "$version"; then
                download_nacos "$version" "$download_dir"
            fi
            ;;
        list)
            get_all_versions
            ;;
        compare)
            if [ $# -lt 3 ]; then
                print_error "用法: $0 compare <version1> <version2>"
                exit 1
            fi
            compare_versions "$2" "$3"
            ;;
        help|--help|-h)
            echo "Nacos版本管理工具"
            echo ""
            echo "用法:"
            echo "  $0 [命令] [参数...]"
            echo ""
            echo "命令:"
            echo "  latest, api    - 使用GitHub API获取最新版本（默认）"
            echo "  html          - 使用HTML页面解析获取最新版本"
            echo "  rss           - 使用RSS Feed获取最新版本"
            echo "  all           - 尝试所有方法获取最新版本"
            echo "  download [版本] [目录] - 下载指定版本到指定目录"
            echo "  list          - 列出最近10个版本"
            echo "  compare <v1> <v2> - 比较两个版本号"
            echo "  help          - 显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                    # 获取最新版本"
            echo "  $0 download           # 下载最新版本"
            echo "  $0 download v2.3.2    # 下载指定版本"
            echo "  $0 list               # 列出可用版本"
            echo "  $0 compare v2.3.1 v2.3.2  # 比较版本"
            ;;
        *)
            print_error "未知命令: $command"
            echo "使用 '$0 help' 查看帮助信息"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@" 