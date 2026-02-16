# 变更日志

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中
- Web UI监控界面
- 支持更多LLM后端（OpenAI、本地模型）
- Docker容器化部署
- 多Agent协作模式

## [0.1.0] - 2026-02-16

### 新增
- ✨ 核心框架实现
  - InitializerAgent - 项目初始化Agent
  - CodingAgent - 代码实现Agent
  - AgentScheduler - 调度管理系统

- 📦 核心功能
  - FeatureManager - 功能列表管理（JSON格式）
  - ProgressTracker - 进度追踪和日志记录
  - GitManager - Git集成和自动提交
  - BrowserTester - 基于Playwright的浏览器测试

- 🎨 CLI接口
  - `infinity-ai init` - 初始化项目
  - `infinity-ai run` - 运行Agent（支持continuous/single/interactive模式）
  - `infinity-ai status` - 查看项目状态
  - `infinity-ai report` - 生成进度报告
  - `infinity-ai add-feature` - 手动添加功能
  - `infinity-ai complete-feature` - 标记功能完成
  - `infinity-ai config` - 显示配置

- 📚 文档
  - README.md - 完整的项目说明
  - docs/getting-started.md - 快速入门指南
  - docs/architecture.md - 架构设计文档
  - examples/todo-app/ - 待办事项应用示例
  - examples/demo.sh - 演示脚本

- 🧪 测试
  - FeatureManager单元测试
  - ProgressTracker单元测试
  - Settings和LLMConfig测试
  - pytest配置和conftest

- 🛠️ 开发工具
  - Makefile - 常用开发命令
  - requirements.txt - 依赖列表
  - pyproject.toml - 项目配置
  - .gitignore - Git忽略规则

### 核心设计原则
- 基于Anthropic论文实现持久化状态工具包
- 使用JSON格式存储功能列表（防止意外修改）
- 结构化测试步骤验证功能实现
- 三种运行模式适应不同场景

### 技术栈
- Python 3.10+
- Anthropic Claude API
- Pydantic 数据验证
- Click CLI框架
- Playwright 浏览器测试

## [0.0.1] - 2026-02-15

### 新增
- 🎉 项目初始化
- MIT许可证
- 基础项目结构

---

## 版本说明

### 版本号格式：MAJOR.MINOR.PATCH

- **MAJOR** - 不兼容的API变更
- **MINOR** - 向后兼容的功能新增
- **PATCH** - 向后兼容的问题修复

### 变更类型

- `新增` - 新功能
- `变更` - 现有功能的变更
- `修复` - Bug修复
- `移除` - 移除的功能
- `废弃` - 即将移除的功能
- `安全` - 安全相关

---

[未发布]: https://github.com/jasongu/infinity-ai/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jasongu/infinity-ai/releases/tag/v0.1.0
[0.0.1]: https://github.com/jasongu/infinity-ai/releases/tag/v0.0.1