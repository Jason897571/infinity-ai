# 贡献指南

感谢你考虑为Infinity AI贡献！本文档将帮助你了解如何参与项目开发。

## 行为准则

- 尊重所有贡献者
- 保持建设性的讨论
- 欢迎不同观点和经验水平

## 如何贡献

### 报告Bug

如果你发现了bug，请创建Issue并包含：

1. **Bug描述** - 清晰简洁地描述问题
2. **复现步骤** - 详细的步骤让我们能重现问题
3. **预期行为** - 你期望发生什么
4. **实际行为** - 实际发生了什么
5. **环境信息**:
   - Python版本
   - 操作系统
   - Infinity AI版本
6. **日志输出** - 相关的错误日志或截图

**Issue模板：**

```markdown
## Bug描述
[简要描述bug]

## 复现步骤
1. 运行 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

## 预期行为
[描述你期望发生什么]

## 实际行为
[描述实际发生了什么]

## 环境
- Python: 3.11.0
- OS: macOS 13.0
- Infinity AI: 0.1.0

## 日志
```
[粘贴相关日志]
```
```

### 建议新功能

欢迎提出新功能建议！请在Issue中说明：

1. **功能描述** - 你希望添加什么功能
2. **使用场景** - 这个功能解决什么问题
3. **实现建议** - 如果你有想法，简单描述如何实现
4. **替代方案** - 你考虑过的其他解决方案

### 提交代码

#### 开发环境设置

```bash
# 1. Fork并克隆仓库
git clone https://github.com/your-username/infinity-ai.git
cd infinity-ai

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 创建功能分支
git checkout -b feature/your-feature-name
```

#### 代码风格

我们使用以下工具保持代码质量：

- **Black** - 代码格式化
- **Ruff** - 代码检查
- **Mypy** - 类型检查
- **Pytest** - 测试

运行检查：

```bash
# 格式化代码
make format

# 代码检查
make lint

# 运行测试
make test
```

#### 提交规范

使用清晰的提交消息：

```
类型: 简短描述

详细说明（可选）

# 类型:
# - feat: 新功能
# - fix: Bug修复
# - docs: 文档更新
# - test: 测试相关
# - refactor: 重构
# - chore: 构建/工具
```

示例：

```
feat: 添加Docker支持

- 创建Dockerfile
- 添加docker-compose.yml
- 更新文档说明Docker使用方法
```

#### Pull Request流程

1. **确保测试通过**
   ```bash
   pytest tests/
   ```

2. **更新文档**
   - 新功能需要更新README.md
   - API变更需要更新文档

3. **创建Pull Request**

   PR描述应包含：
   - 变更说明
   - 相关Issue（如果有）
   - 测试方法
   - 截图（如果适用）

**PR模板：**

```markdown
## 变更说明
[描述你的变更]

## 相关Issue
Closes #123

## 测试
- [ ] 单元测试已添加/更新
- [ ] 所有测试通过
- [ ] 手动测试完成

## 检查清单
- [ ] 代码遵循项目风格
- [ ] 文档已更新
- [ ] 无新的警告
- [ ] 测试覆盖新功能
```

4. **代码审查**
   - 响应审查意见
   - 进行必要的修改
   - 保持讨论焦点

## 开发指南

### 项目结构

```
infinity-ai/
├── infinity_ai/          # 主代码
│   ├── core/             # 核心模块
│   ├── config/           # 配置
│   ├── utils/            # 工具函数
│   └── cli.py            # CLI接口
├── tests/                # 测试
├── docs/                 # 文档
├── examples/             # 示例
└── Makefile             # 开发脚本
```

### 添加新功能

1. **在core/中实现核心逻辑**
2. **在tests/中添加测试**
3. **在cli.py中添加CLI命令**
4. **更新文档**

### 添加新的Agent类型

1. 继承基础Agent类：

```python
from infinity_ai.core.base import BaseAgent

class MyCustomAgent(BaseAgent):
    def run_session(self):
        # 实现你的逻辑
        pass
```

2. 在scheduler中集成
3. 添加测试
4. 更新文档

### 添加新的测试器

1. 继承BrowserTester：

```python
from infinity_ai.utils.browser_tester import BrowserTester

class CustomTester(BrowserTester):
    def test_feature(self, feature):
        # 自定义测试逻辑
        pass
```

## 发布流程

维护者遵循以下步骤发布新版本：

1. 更新版本号（pyproject.toml）
2. 更新CHANGELOG.md
3. 创建Git标签
4. 构建并发布到PyPI

## 获取帮助

- **GitHub Issues** - Bug报告和功能建议
- **讨论区** - 问答和讨论
- **文档** - 查看README和docs/

## 许可证

贡献的代码将以MIT许可证发布。提交PR即表示你同意此许可。

---

再次感谢你的贡献！🎉