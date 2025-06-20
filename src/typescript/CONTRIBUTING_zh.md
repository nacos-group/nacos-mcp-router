# 为 Nacos MCP Router TypeScript 做贡献

感谢您对 Nacos MCP Router TypeScript 项目感兴趣！本文档提供了参与项目贡献的指南和说明。

## 行为准则

参与本项目即表示您同意遵守我们的[行为准则](CODE_OF_CONDUCT.md)。

## 如何贡献

### 报告 Bug

1. 检查 [Issues](https://github.com/nacos-group/nacos-mcp-router-typescript/issues) 部分是否已经报告了该 bug
2. 如果没有，创建一个新的 issue，包含清晰的标题和描述
3. 尽可能包含以下相关信息：
   - 复现步骤
   - 预期行为
   - 实际行为
   - 环境详情（操作系统、Node.js 版本等）
   - 如适用，提供截图

### 建议新功能

1. 检查 [Issues](https://github.com/nacos-group/nacos-mcp-router-typescript/issues) 部分是否已经提出了该功能建议
2. 如果没有，创建一个带有 "enhancement" 标签的新 issue
3. 提供清晰的功能描述和其优势
4. 包含任何相关的示例或使用场景

### 提交 Pull Request

1. Fork 仓库
2. 为您的功能/修复创建新分支
3. 进行更改
4. 根据需要编写或更新测试
5. 确保所有测试通过
6. 必要时更新文档
7. 提交 pull request

### 开发环境设置

1. 克隆仓库：
   ```bash
   git clone https://github.com/nacos-group/nacos-mcp-router-typescript.git
   cd nacos-mcp-router-typescript
   ```

2. 安装依赖：
   ```bash
   npm install
   ```

3. 构建项目：
   ```bash
   npm run build
   ```

4. 运行测试：
   ```bash
   npm test
   ```

### 编码规范

- 遵循 TypeScript 风格指南
- 使用有意义的变量和函数名
- 为复杂逻辑编写清晰的注释
- 保持函数小巧且专注
- 遵循现有的代码结构和模式

### 测试

- 为新功能编写单元测试
- 提交 PR 前确保所有测试通过
- 保持或提高测试覆盖率
- 为复杂功能包含集成测试

### 文档

- 必要时更新 README.md
- 为新函数/类添加 JSDoc 注释
- 更新 API 文档
- 为新功能包含示例

### 提交信息

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[可选的正文]

[可选的页脚]
```

类型：
- feat: 新功能
- fix: Bug 修复
- docs: 文档更改
- style: 代码风格更改
- refactor: 代码重构
- test: 添加或更新测试
- chore: 维护任务

### 审查流程

1. 所有 PR 至少需要一个审查
2. 及时处理审查意见
3. 保持 PR 重点突出且规模可控
4. 响应 CI/CD 反馈

### 发布流程

1. 按照[语义化版本](https://semver.org/)进行版本更新
2. 更新 CHANGELOG.md
3. 创建发布标签
4. 发布到 npm

## 获取帮助

- 加入我们的[讨论](https://github.com/nacos-group/nacos-mcp-router-typescript/discussions)
- 查看现有[问题](https://github.com/nacos-group/nacos-mcp-router-typescript/issues)
- 查阅[文档](https://nacos.io/docs/)

## 许可证

通过为 Nacos MCP Router TypeScript 做贡献，您同意您的贡献将按照项目的 [Apache License 2.0](LICENSE) 进行许可。 