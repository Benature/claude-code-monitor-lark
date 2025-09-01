# Claude Limit Monitor Makefile
# 包含常用的开发和运行命令

.PHONY: help install clean test lint run run-api run-server run-dev run-quiet
.PHONY: scrape-accounts scrape-api check-limits notify test-notify
.PHONY: server-dev server-prod client-test

# 默认目标
.DEFAULT_GOAL := help

# 帮助信息
help:
	@echo "Claude Limit Monitor - 可用命令:"
	@echo ""
	@echo "安装和环境:"
	@echo "  install     - 安装依赖包"
	@echo "  clean       - 清理临时文件"
	@echo ""
	@echo "主要运行命令:"
	@echo "  run         - 运行Claude账户监控（推荐）"
	@echo "  run-api     - 运行API使用情况监控"
	@echo "  run-server  - 启动FastAPI服务器"
	@echo "  run-dev     - 开发模式运行服务器（热重载）"
	@echo "  run-quiet   - 静默模式运行监控"
	@echo ""
	@echo "单独组件:"
	@echo "  scrape-accounts  - 仅爬取Claude账户数据"
	@echo "  scrape-api       - 仅爬取API使用数据"
	@echo "  check-limits     - 仅检查限流状态"
	@echo "  notify           - 测试Claude账户通知"
	@echo "  test-notify      - 测试API使用通知"
	@echo ""
	@echo "服务器相关:"
	@echo "  server-dev       - 开发服务器（端口8155，热重载）"
	@echo "  server-prod      - 生产服务器（多进程）"
	@echo "  client-test      - 测试API客户端"
	@echo ""
	@echo "测试和检查:"
	@echo "  test        - 运行所有测试"
	@echo "  test-manual - 手动运行所有测试文件"
	@echo "  lint        - 代码格式检查（如果可用）"

# 安装依赖
install:
	@echo "正在安装依赖..."
	pip install -r requirements.txt

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete

# 主要运行命令
run:
	@echo "运行Claude账户监控..."
	python main.py

run-api:
	@echo "运行API使用情况监控..."
	python api_monitor.py

run-server:
	@echo "启动FastAPI服务器..."
	python start_server.py

run-dev:
	@echo "开发模式运行服务器（热重载）..."
	python start_server.py --reload

run-quiet:
	@echo "静默模式运行监控..."
	python main.py --quiet

# 使用自定义配置运行
run-config:
	@echo "使用自定义配置运行（请指定CONFIG=config_file.yaml）..."
	python main.py --config $(or $(CONFIG),config.yaml)

run-api-config:
	@echo "使用自定义配置运行API监控..."
	python api_monitor.py --config $(or $(CONFIG),config.yaml)

# 单独组件
scrape-accounts:
	@echo "仅爬取Claude账户数据..."
	python -m src.scrapers.claude_scraper

scrape-api:
	@echo "仅爬取API使用数据..."
	python -m src.scrapers.api_scraper

check-limits:
	@echo "仅检查限流状态..."
	python -m src.monitors.rate_limit_checker

notify:
	@echo "测试Claude账户通知..."
	python -m src.notifiers.feishu_notifier

test-notify:
	@echo "测试API使用通知..."
	python -m src.notifiers.api_notifier

# 服务器相关
server-dev:
	@echo "启动开发服务器（端口8155，热重载）..."
	python start_server.py --host 127.0.0.1 --port 8155 --reload

server-prod:
	@echo "启动生产服务器（多进程）..."
	python start_server.py --workers 4

server-custom:
	@echo "启动自定义服务器配置..."
	python start_server.py --host $(or $(HOST),127.0.0.1) --port $(or $(PORT),8155)

client-test:
	@echo "测试API客户端..."
	python examples/client_example.py

# 测试相关
test:
	@echo "运行所有测试..."
	python3 -m pytest tests/ -v

test-manual:
	@echo "手动运行所有测试文件..."
	@for test in tests/test_*.py; do \
		echo "运行 $$test..."; \
		python3 "$$test"; \
	done

test-integration:
	@echo "运行集成测试..."
	python3 tests/test_integration.py

test-status:
	@echo "运行状态变化测试..."
	python3 tests/test_status_change.py

test-system:
	@echo "运行系统测试..."
	python3 tests/test_system.py

# 代码检查（如果有工具的话）
lint:
	@echo "检查代码格式..."
	@if command -v ruff > /dev/null; then \
		echo "使用 ruff 检查..."; \
		ruff check .; \
	elif command -v flake8 > /dev/null; then \
		echo "使用 flake8 检查..."; \
		flake8 src/ tests/ examples/; \
	elif command -v pylint > /dev/null; then \
		echo "使用 pylint 检查..."; \
		pylint src/ tests/ examples/; \
	else \
		echo "未找到代码检查工具 (ruff/flake8/pylint)"; \
	fi

# 格式化代码
format:
	@echo "格式化代码..."
	@if command -v ruff > /dev/null; then \
		echo "使用 ruff 格式化..."; \
		ruff format .; \
	elif command -v black > /dev/null; then \
		echo "使用 black 格式化..."; \
		black src/ tests/ examples/; \
	else \
		echo "未找到代码格式化工具 (ruff/black)"; \
	fi

# 快速触发监控（用于测试）
trigger-accounts:
	@echo "触发账户监控..."
	curl "http://localhost:8155/trigger/monitor_accounts?k=your_simple_key"

trigger-api:
	@echo "触发API使用监控..."
	curl "http://localhost:8155/trigger/monitor_api_usage?k=your_simple_key"

trigger-full:
	@echo "触发完整监控..."
	curl "http://localhost:8155/trigger/full_monitor?k=your_simple_key"

# 显示项目状态
status:
	@echo "项目状态:"
	@echo "- Python版本: $$(python --version)"
	@echo "- 配置文件: $$(ls -la config.* 2>/dev/null || echo '未找到配置文件')"
	@echo "- 数据文件: $$(ls -la *.json 2>/dev/null || echo '无数据文件')"
	@echo "- 测试文件: $$(ls tests/test_*.py 2>/dev/null | wc -l) 个测试文件"