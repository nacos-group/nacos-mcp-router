# Contributing to Nacos MCP Router TypeScript

Thank you for your interest in contributing to Nacos MCP Router TypeScript! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in the [Issues](https://github.com/nacos-group/nacos-mcp-router-typescript/issues) section
2. If not, create a new issue with a clear title and description
3. Include as much relevant information as possible:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Node.js version, etc.)
   - Screenshots if applicable

### Suggesting Features

1. Check if the feature has already been suggested in the [Issues](https://github.com/nacos-group/nacos-mcp-router-typescript/issues) section
2. If not, create a new issue with the "enhancement" label
3. Provide a clear description of the feature and its benefits
4. Include any relevant examples or use cases

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature/fix
3. Make your changes
4. Write or update tests as needed
5. Ensure all tests pass
6. Update documentation if necessary
7. Submit a pull request

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/nacos-group/nacos-mcp-router-typescript.git
   cd nacos-mcp-router-typescript
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the project:
   ```bash
   npm run build
   ```

4. Run tests:
   ```bash
   npm test
   ```

### Coding Standards

- Follow the TypeScript style guide
- Use meaningful variable and function names
- Write clear comments for complex logic
- Keep functions small and focused
- Follow the existing code structure and patterns

### Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Maintain or improve test coverage
- Include integration tests for complex features

### Documentation

- Update README.md if needed
- Add JSDoc comments for new functions/classes
- Update API documentation
- Include examples for new features

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Adding or updating tests
- chore: Maintenance tasks

### Review Process

1. All PRs require at least one review
2. Address review comments promptly
3. Keep PRs focused and manageable in size
4. Respond to CI/CD feedback

### Release Process

1. Version bump following [Semantic Versioning](https://semver.org/)
2. Update CHANGELOG.md
3. Create release tag
4. Publish to npm

## Getting Help

- Join our [Discussions](https://github.com/nacos-group/nacos-mcp-router-typescript/discussions)
- Check existing [Issues](https://github.com/nacos-group/nacos-mcp-router-typescript/issues)
- Review [Documentation](https://nacos.io/docs/)

## License

By contributing to Nacos MCP Router TypeScript, you agree that your contributions will be licensed under the project's [Apache License 2.0](LICENSE). 