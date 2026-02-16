# 架构设计文档

本文档详细说明Infinity AI框架的架构设计和实现原理。

## 核心理念

基于Anthropic的论文["Effective Harnesses for Long-Running Agents"](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)，框架解决的核心问题是：

> 如何让AI Agent跨多个上下文窗口（会话）保持一致的进度？

答案：**持久化状态工具包**（Persistent State Harness）

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户接口层                               │
│  CLI (infinity-ai init/run/status/report)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     调度层                                   │
│  AgentScheduler                                             │
│  - 管理会话生命周期                                          │
│  - 决定运行哪个Agent                                         │
│  - 处理错误和重试                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────┬──────────────────────────────────────┐
│   初始化Agent         │         编码Agent                     │
│  (第一次会话)         │      (后续会话循环)                   │
│                      │                                       │
│  1. 分析需求          │  1. 读取当前状态                      │
│  2. 创建功能列表      │  2. 选择未完成功能                    │
│  3. 生成init.sh      │  3. 实现代码                          │
│  4. 初始化Git        │  4. 测试验证                          │
│                      │  5. 提交更新                          │
└──────────────────────┴──────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   状态管理层                                 │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │FeatureManager │  │ProgressTracker│  │  GitManager    │  │
│  │               │  │               │  │                │  │
│  │功能列表JSON   │  │进度日志TXT    │  │版本控制        │  │
│  └───────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   工具层                                     │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │FileManager    │  │BrowserTester │  │  LLM Client    │  │
│  └───────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件详解

### 1. AgentScheduler（调度器）

**职责：**
- 检测项目状态，决定是否需要初始化
- 管理Agent的生命周期
- 处理运行模式（continuous/single/interactive）
- 错误恢复和重试逻辑

**关键决策：**

```python
if 项目未初始化:
    运行 InitializerAgent
else:
    循环运行 CodingAgent 直到:
        - 所有功能完成
        - 达到最大迭代次数
        - 用户中断
```

### 2. InitializerAgent（初始化器）

**运行时机：** 仅第一次会话

**核心任务：**

1. **需求分析**
   - 使用Claude分析项目需求文档
   - 生成结构化的功能列表
   - 为每个功能定义测试步骤

2. **环境准备**
   - 创建 `init.sh` 启动脚本
   - 初始化Git仓库
   - 创建 `.gitignore`

3. **状态文件创建**
   - `feature_list.json` - 功能列表（JSON格式防意外修改）
   - `claude-progress.txt` - 进度日志

**示例输出：**

```json
{
  "features": [
    {
      "id": "feature_001",
      "description": "用户可以添加新任务",
      "steps": [
        "Navigate to homepage",
        "Click add task button",
        "Enter task title",
        "Verify task appears in list"
      ],
      "priority": 1,
      "passes": false
    }
  ]
}
```

### 3. CodingAgent（编码器）

**运行时机：** 后续所有会话（循环）

**会话流程：**

```
1. 读取当前状态
   ├─ Git最近提交
   ├─ 进度文件最后100行
   └─ 功能列表摘要

2. 启动开发服务器（可选）
   └─ 提示用户使用init.sh

3. 运行基本测试
   └─ 检测现有Bug

4. 选择下一个功能
   └─ 最高优先级未完成功能

5. 实现功能
   ├─ Claude生成代码
   ├─ 解析响应
   └─ 写入文件

6. 测试验证
   ├─ 使用Playwright运行测试步骤
   └─ 验证功能正常工作

7. 更新状态
   ├─ 标记功能完成
   ├─ 更新进度日志
   └─ Git提交
```

### 4. FeatureManager（功能管理器）

**数据结构：**

```python
class Feature:
    id: str                    # 功能唯一标识
    description: str           # 功能描述
    steps: List[str]           # 测试步骤
    priority: int              # 优先级 1-5
    passes: bool               # 是否通过
    created_at: datetime       # 创建时间
    completed_at: datetime     # 完成时间
```

**关键方法：**

- `get_next_incomplete_feature()` - 获取下一个待处理功能（按优先级）
- `mark_feature_complete()` - 标记完成
- `get_progress_summary()` - 计算进度统计

### 5. ProgressTracker（进度追踪器）

**记录内容：**

```
================================================================================
SESSION START: coding_abc123
Agent Type: coding_agent
Timestamp: 2026-02-16 10:30:00
================================================================================

[2026-02-16 10:30:05] STARTED FEATURE: feature_001
  Description: 用户可以添加新任务

[2026-02-16 10:35:12] CREATED FILE: index.html
  Details: Homepage with task input form

[2026-02-16 10:40:30] TEST PASSED: feature_001
  Details: All test steps completed successfully

[2026-02-16 10:41:00] GIT COMMIT: a1b2c3d4
  Details: [Feature] 用户可以添加新任务

================================================================================
SESSION END: coding_abc123
Timestamp: 2026-02-16 10:42:00
Features Completed: 1
Summary: Successfully implemented feature_001
================================================================================
```

### 6. BrowserTester（浏览器测试器）

**工作原理：**

1. **测试脚本生成**
   - 解析测试步骤描述
   - 生成Playwright JavaScript代码

2. **示例转换：**

   输入：
   ```
   Navigate to http://localhost:3000
   Click #add-task
   Verify .task-item exists
   ```

   输出：
   ```javascript
   await page.goto("http://localhost:3000");
   await page.click("#add-task");
   await page.waitForSelector(".task-item");
   ```

3. **执行验证**
   - 运行生成的脚本
   - 捕获输出和错误
   - 返回测试结果

## 关键设计决策

### 1. 为什么使用JSON而非Markdown存储功能列表？

**原因：** JSON有严格的结构定义，Claude模型不太可能意外修改其结构。Markdown更自由，容易被模型添加额外内容或改变格式。

### 2. 为什么需要init.sh？

**解决的问题：** 每个新会话都面临"如何启动项目"的问题。通过标准化的启动脚本，Agent可以立即开始工作，无需探索项目结构。

### 3. 为什么需要进度日志文件？

**与Git历史互补：**

| Git历史 | 进度文件 |
|---------|----------|
| 记录代码变更 | 记录Agent思考和决策 |
| 结构化（diff） | 叙述性文本 |
| 难以快速理解意图 | 清晰解释"为什么" |

两者结合提供完整的上下文。

### 4. 测试步骤为什么是字符串列表？

**设计权衡：**

- 结构化对象（更严格）vs 字符串列表（更灵活）
- 选择字符串列表因为：
  1. 便于Initializer Agent生成
  2. 易于转换为Playwright代码
  3. 人类可读性强

## 运行模式对比

### Continuous（连续模式）

```
Session 1 → Session 2 → Session 3 → ... → 完成
```

**特点：**
- 全自动运行
- 失败后自动重试（最多3次连续失败后暂停）
- 适合夜间运行、长期项目

### Single（单次模式）

```
Session 1 → 停止
```

**特点：**
- 执行一个功能后停止
- 适合调试、测试
- 可以逐步观察

### Interactive（交互模式）

```
Session 1 → 等待确认 → Session 2 → 等待确认 → ...
```

**特点：**
- 每次会话后暂停
- 人工监督每个决策
- 适合高价值项目、学习理解

## 数据流

```
用户需求
    ↓
Initializer Agent
    ↓
feature_list.json ←───┐
    ↓                  │
    ├→ claude-progress.txt
    ↓                  │
Coding Agent (循环) ───┘
    ↓
代码文件
    ↓
Git提交
```

## 扩展点

### 1. 自定义测试验证器

可以实现自定义的测试验证逻辑：

```python
class CustomTester(BrowserTester):
    def test_feature(self, feature):
        # 自定义测试逻辑
        pass
```

### 2. 多Agent协作

未来可扩展为专门的Agent：

- TestingAgent - 专注测试
- QA_Agent - 质量保证
- DocumentationAgent - 文档生成

### 3. 其他LLM后端

当前使用Claude API，架构设计支持替换：

```python
# 潜在扩展
class CodingAgent:
    def __init__(self, llm_backend):
        self.llm = llm_backend  # 可以是Claude/OpenAI/Local
```

## 性能考虑

### 1. Token消耗

每个会话消耗：
- 初始化：~2000 tokens（需求分析）
- 编码：~3000 tokens（实现+测试）
- 100个功能项目总消耗：~300K tokens

### 2. 时间成本

- 单个功能：2-5分钟
- 100功能项目：3-8小时连续运行

### 3. 优化策略

- 并行测试（未来特性）
- 缓存常用提示
- 批量处理简单功能

## 安全性

### API密钥管理

- 不硬编码在代码中
- 通过环境变量传递
- 配置验证确保格式正确

### 代码审查

建议：
- 每个功能完成后人工审查
- 设置自动代码扫描
- 使用Git分支隔离

### 测试隔离

- 测试脚本在独立进程运行
- 超时保护（默认30秒）
- 错误不影响主流程

## 故障恢复

### 自动恢复机制

1. **连续失败检测**
   ```python
   if consecutive_failures >= 3:
       暂停30秒
       重置失败计数
   ```

2. **状态持久化**
   - 功能列表自动保存
   - 进度实时追加
   - Git提供完整历史

3. **断点续传**
   - 重新运行自动从上次停止处继续
   - 不重复已完成功能

## 最佳实践

1. **需求文档质量**
   - 清晰、具体的功能描述
   - 明确的验收标准
   - 合理的功能粒度

2. **测试环境**
   - 稳定的开发服务器
   - 干净的浏览器环境
   - 可重复的测试条件

3. **监控和审查**
   - 定期检查进度文件
   - 审查Git提交历史
   - 手动验证关键功能

## 未来路线图

### 短期（1-2个月）
- [ ] 支持更多测试框架（Selenium、Cypress）
- [ ] Web UI监控界面
- [ ] Docker容器化部署

### 中期（3-6个月）
- [ ] 多Agent协作模式
- [ ] 支持更多LLM后端
- [ ] 云端运行支持

### 长期（6-12个月）
- [ ] 可视化项目构建器
- [ ] AI辅助需求分析
- [ ] 企业级功能（权限、审计）

## 参考资料

- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Playwright Documentation](https://playwright.dev/)