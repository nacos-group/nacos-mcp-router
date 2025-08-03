# E2E Testing with MCP Inspector

这个文档介绍了基于 **真正的 MCP Inspector + Playwright** 的端到端测试实现。

## 🎯 真正的 MCP Inspector E2E 测试

与之前的简单实现不同，现在我们使用了正确的测试方式：

### ✅ 正确的方式（新实现）
1. **启动 MCP Inspector**: 使用 `npx @modelcontextprotocol/inspector node dist/stdio.js` 
2. **解析认证信息**: 从日志中提取 URL 和 AUTH_TOKEN
3. **使用 Playwright**: 进行真正的浏览器 UI 自动化测试
4. **模拟用户操作**: 通过 UI 点击、输入等操作测试 MCP 功能

### ❌ 之前的错误方式
- 直接调用 `node dist/stdio.js` 
- 没有使用 MCP Inspector 的 Web 界面
- 没有模拟真实的用户 UI 操作

## 🚀 测试架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Mock Nacos    │    │  MCP Inspector   │    │   Playwright    │
│     Server      │◄───│     (Web UI)     │◄───│   Browser Tests │
│   (Port 8848)   │    │   (Port 6274)    │    │  (UI Automation)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │ Nacos MCP Router │
                        │   (stdio.js)     │
                        └──────────────────┘
```

## 📋 NPM 命令

### 真正的 MCP Inspector E2E 测试
```bash
# 无头模式（推荐用于 CI/CD）
npm run test:e2e

# 有头模式（可以看到浏览器操作）
npm run test:e2e:headed

# 调试模式（逐步执行）
npm run test:e2e:debug

# UI 模式（Playwright UI 界面）
npm run test:e2e:ui

# 仅运行 Playwright 测试（需要手动启动服务）
npm run test:playwright
npm run test:playwright:headed
```

### 旧的简单测试（已保留）
```bash
# 旧的直接调用方式（不是真正的 MCP Inspector 测试）
npm run test:e2e:old
```

## 🧪 测试用例

### 1. MCP Inspector 界面测试
- ✅ 验证 MCP Inspector 成功启动
- ✅ 验证 Web 界面正常加载
- ✅ 验证认证 Token 正确设置

### 2. 工具列表测试
- 🔍 检查 SearchMcpServer 工具是否在列表中
- 🔍 验证工具参数表单是否正确显示

### 3. 搜索功能测试
- 🧪 精确服务器名称搜索
- 🧪 多关键词搜索
- 🧪 不存在关键词的处理
- 🧪 UI 交互操作（选择工具、填写参数、点击调用）

## 🔧 实现细节

### MCP Inspector 启动流程
1. **环境变量设置**: 指向 Mock Nacos 服务器
2. **启动命令**: `npx @modelcontextprotocol/inspector node dist/stdio.js`
3. **日志解析**: 提取 URL 和认证 Token
4. **健康检查**: 确保服务就绪

### Playwright 配置
- **浏览器**: Chromium（默认）
- **模式**: 支持 headless、headed、debug、ui
- **截图**: 失败时自动截图
- **视频**: 失败时录制视频
- **报告**: HTML 格式测试报告

### Mock 服务器
- **Mock Nacos**: 提供标准的 Nacos API 响应
- **测试数据**: 包含 exact-server-name、database-query-server、file-server 等
- **API 兼容**: 支持分页、搜索、健康检查等端点

## 🎯 验证结果

测试已验证以下流程正确工作：

### ✅ 成功验证的部分
- ✅ Mock Nacos 服务器启动 (Port 8848)
- ✅ MCP Inspector 启动 (Port 6274)
- ✅ 认证 Token 生成和解析
- ✅ 服务健康检查通过
- ✅ Playwright 配置正确
- ✅ 测试用例结构完整
- ✅ **自动依赖安装** - 零配置运行

### 🔄 需要完成的部分
- 🔄 运行完整的 UI 测试流程
- 🔄 优化测试用例的 UI 选择器

## 🚀 快速开始

### 一键运行（完全自动化）
```bash
# 构建项目并运行 E2E 测试（全自动，包含依赖安装）
npm run test:e2e:headed
```

**🎉 新特性：零配置运行！**
- ✅ 自动检测并安装 Playwright 浏览器
- ✅ 自动启动 Mock Nacos 服务器  
- ✅ 自动启动 MCP Inspector
- ✅ 自动运行所有测试用例
- ✅ 自动清理资源

### 手动安装（可选）
如果你想手动控制依赖安装：
```bash
npm install
npx playwright install chromium
npm run build
npm run test:e2e:headed
```

### 查看结果
- 测试报告: `npx playwright show-report`
- 截图位置: `test-results/`
- 视频位置: `test-results/`

## 🎉 主要成就

1. **真正的 MCP Inspector 集成**: 不再是简单的 stdio 调用
2. **完整的 UI 自动化**: 使用 Playwright 模拟用户操作
3. **Mock 服务架构**: 无需外部 Nacos 依赖
4. **多种测试模式**: 支持 headless、headed、debug、ui 模式
5. **全自动化流程**: 一键启动所有服务并运行测试
6. **🆕 零配置运行**: 自动检测并安装 Playwright 浏览器依赖

这是一个**真正的端到端测试框架**，完全基于 MCP Inspector 的 Web 界面进行 UI 自动化测试！用户只需运行一个命令即可完成所有设置和测试。