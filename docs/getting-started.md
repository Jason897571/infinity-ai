# 快速入门指南

本指南将帮助你在5分钟内开始使用Infinity AI框架。

## 第一步：安装

### 前置要求
- Python 3.10或更高版本
- Git
- Claude API密钥

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/jasongu/infinity-ai.git
cd infinity-ai

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装框架
pip install -e .
```

## 第二步：配置API密钥

### 方式一：环境变量

```bash
# 设置环境变量
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### 方式二：.env 文件（推荐）

在项目根目录或 `examples` 下创建 `.env` 文件：

```bash
# Anthropic 官方 API
ANTHROPIC_API_KEY=sk-ant-your-key-here

# 使用自定义代理时（如 OpenAI 兼容代理、GLM 等）
ANTHROPIC_API_KEY=your-api-key
BASE_URL=http://your-proxy-url
API_AUTH_TYPE=bearer   # 使用 Authorization: Bearer 头（代理通常需要此格式）
```

> **认证方式说明：** 若代理返回 `invalid x-api-key` 错误，说明代理期望 `Authorization: Bearer` 格式，请在 `.env` 中添加 `API_AUTH_TYPE=bearer`。

**获取API密钥：**
1. 访问 https://console.anthropic.com/
2. 创建账户并登录
3. 在API Keys页面生成新密钥

## 第三步：创建你的第一个项目

### 1. 创建项目目录

```bash
mkdir my-first-project
cd my-first-project
```

### 2. 编写需求文档

创建 `requirements.txt`：

```
创建一个简单的计数器Web应用：
- 显示当前计数（初始为0）
- 有"增加"按钮，每次点击计数+1
- 有"减少"按钮，每次点击计数-1
- 有"重置"按钮，将计数归零
- 使用localStorage保存计数，刷新页面后保持
```

### 3. 初始化项目

```bash
infinity-ai init --requirements requirements.txt
```

这将创建：
```
my-first-project/
├── feature_list.json     # 功能列表
├── claude-progress.txt   # 进度日志
├── init.sh              # 启动脚本
└── .gitignore           # Git忽略文件
```

### 4. 查看生成的功能列表

```bash
infinity-ai status
```

输出：
```
📊 Features:
  Total:      5
  Completed:  0
  Pending:    5
  Progress:   0.0%
```

## 第四步：运行Agent

### 启动开发服务器

首先，你需要启动一个开发服务器（或者让Agent知道如何启动）。

对于简单的HTML项目：
```bash
# 创建一个简单的HTTP服务器
python -m http.server 3000
```

### 运行Agent

在另一个终端：

```bash
# 连续运行模式（推荐）
                                                                                                    infinity-ai run --mode continuous
```

Agent会：
1. 读取功能列表
2. 选择第一个未完成的功能
3. 生成代码
4. 测试功能
5. 提交代码
6. 继续下一个功能

### 监控进度

实时查看进度：

```bash
# 在另一个终端
tail -f claude-progress.txt
```

或查看状态：

```bash
infinity-ai status
```

## 第五步：检查结果

### 查看生成的代码

```bash
ls -la
```

你应该看到生成的HTML、CSS和JavaScript文件。

### 查看Git提交

```bash
git log --oneline
```

### 查看测试结果

Agent会创建浏览器测试脚本：

```bash
ls tests/browser/
```

## 常见运行模式

### 1. 连续模式（默认）

自动运行直到所有功能完成：

```bash
infinity-ai run --mode continuous
```

适合：长时间无人值守运行

### 2. 单次模式

只运行一个会话：

```bash
infinity-ai run --mode single
```

适合：测试或调试

### 3. 交互模式

每次会话后暂停，等待确认：

```bash
infinity-ai run --mode interactive
```

适合：需要人工监督的场景

## 手动管理功能

### 添加新功能

```bash
infinity-ai add-feature "添加深色模式支持" \
  --steps "点击深色模式切换按钮" \
  --steps "验证页面颜色改变" \
  --category ui \
  --priority 2
```

### 标记功能为完成

```bash
infinity-ai complete-feature feature_006
```

### 生成报告

```bash
infinity-ai report --output project_report.md
```

## 故障排除

### API密钥无效

```
Error: Invalid LLM configuration
```

解决方案：确保正确设置了 `ANTHROPIC_API_KEY` 环境变量

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
echo $ANTHROPIC_API_KEY  # 验证设置成功
```

### 功能测试失败

Agent可能会遇到测试失败。查看日志：

```bash
cat claude-progress.txt | grep FAILED
```

你可以：
1. 手动修复问题
2. 让Agent重试（它会自动重试）

### 超过API限制

如果遇到API速率限制，框架会自动暂停并等待。

### Git提交失败

确保你有Git配置：

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

## 下一步

- 查看完整文档：[README.md](../README.md)
- 运行测试：`pytest tests/`
- 查看示例：`examples/` 目录

## 获取帮助

```bash
# 查看所有命令
infinity-ai --help

# 查看特定命令帮助
infinity-ai run --help
```