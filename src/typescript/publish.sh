#!/usr/bin/env bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 脚本开始
echo -e "${GREEN}===== 开始自动化发布流程 ====${NC}"

# 检查是否有未提交的更改
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}错误: 有未提交的更改，请先提交或 stash。${NC}"
    exit 1
fi

# 获取当前分支
current_branch=$(git symbolic-ref --short HEAD)
if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
    echo -e "${YELLOW}警告: 当前分支不是 main/master，确定要发布吗?${NC}"
    read -p "按 Enter 继续，或按 Ctrl+C 取消..."
fi

# 检查npm登录状态
npm whoami || { echo -e "${RED}请先登录npm: npm login${NC}"; exit 1; }

# 检查是否为私有包
is_private=$(jq -r '.private' package.json)
if [[ "$is_private" == "true" ]]; then
    echo -e "${RED}错误: package.json 中 private 为 true，无法发布。${NC}"
    exit 1
fi

# 构建项目
echo -e "${GREEN}正在构建项目...${NC}"
npm run build || { echo -e "${RED}构建失败，请检查构建脚本。${NC}"; exit 1; }

# 运行测试
# echo -e "${GREEN}正在运行测试...${NC}"
# npm test || { echo -e "${RED}测试失败，请修复测试用例。${NC}"; exit 1; }

# 选择版本更新类型
echo -e "${GREEN}请选择版本更新类型:${NC}"
select update_type in "patch" "minor" "major" "custom"; do
    case $update_type in
        patch|minor|major)
            echo -e "${GREEN}将更新版本: ${update_type}${NC}"
            break
            ;;
        custom)
            read -p "请输入自定义版本号: " custom_version
            update_type="custom $custom_version"
            break
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            ;;
    esac
done

# 更新版本号
echo -e "${GREEN}正在更新版本号...${NC}"
if [[ "$update_type" == "custom"* ]]; then
    custom_version=$(echo $update_type | cut -d' ' -f2)
    npm version $custom_version -m "chore(release): 发布 v%s"
else
    npm version $update_type -m "chore(release): 发布 v%s"
fi

# 获取新版本号
new_version=$(jq -r '.version' package.json)
echo -e "${GREEN}新版本号: v$new_version${NC}"

# 生成变更日志 (需要安装 standard-version)
if command -v standard-version &> /dev/null; then
    echo -e "${GREEN}正在生成变更日志...${NC}"
    standard-version --skip.bump --skip.tag || { echo -e "${YELLOW}生成变更日志失败，继续发布...${NC}"; }
else
    echo -e "${YELLOW}未安装 standard-version，跳过变更日志生成。${NC}"
    echo -e "${YELLOW}安装方法: npm install -g standard-version${NC}"
fi

# 提交变更
git add package.json package-lock.json
if [ -f "CHANGELOG.md" ]; then
    git add CHANGELOG.md
fi
git commit -m "chore(release): 准备发布 v$new_version"

# 推送到GitHub的pr分支
echo -e "${GREEN}正在推送到GitHub的pr分支...${NC}"
git push github $current_branch
# 创建并推送tag
echo -e "${GREEN}正在创建版本标签...${NC}"
git tag -a "v$new_version" -m "Release v$new_version"
git push github "v$new_version"

# 发布到npm
echo -e "${GREEN}正在发布到npm...${NC}"
if [[ "$is_private" == "false" ]]; then
    npm publish --access public
else
    npm publish
fi

echo -e "${GREEN}===== 发布成功! ====${NC}"
echo -e "${GREEN}包版本: v$new_version${NC}"
echo -e "${GREEN}npm地址: https://www.npmjs.com/package/$(jq -r '.name' package.json)${NC}"
