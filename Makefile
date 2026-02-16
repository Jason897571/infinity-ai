.PHONY: install test lint format clean run-example

# 安装
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# 测试
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=infinity_ai --cov-report=html

# 代码质量
lint:
	ruff check infinity_ai/
	mypy infinity_ai/

format:
	black infinity_ai/
	ruff format infinity_ai/

# 清理
clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

# 示例
run-example:
	cd examples/todo-app && infinity-ai init --requirements requirements.txt
	cd examples/todo-app && infinity-ai status

# 文档
docs:
	@echo "查看文档："
	@echo "  docs/getting-started.md"
	@echo "  docs/architecture.md"

# 帮助
help:
	@echo "可用命令："
	@echo "  make install       - 安装框架"
	@echo "  make install-dev   - 安装开发依赖"
	@echo "  make test          - 运行测试"
	@echo "  make test-cov      - 运行测试并生成覆盖率报告"
	@echo "  make lint          - 代码检查"
	@echo "  make format        - 格式化代码"
	@echo "  make clean         - 清理临时文件"
	@echo "  make run-example   - 运行示例项目"