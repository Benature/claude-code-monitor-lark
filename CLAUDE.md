# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

This is a Claude account monitoring and rate limit checking system that:
- Scrapes Claude account data from an API endpoint
- Monitors rate limiting status
- Sends Feishu (Lark) notifications when status changes
- Uses direct memory-based class interaction for data exchange

## 核心架构

The system follows a **direct class interaction** pattern where components pass data through memory rather than files:

### Core Components:
1. **ClaudeScraper** (`src/scrapers/claude_scraper.py`) - Fetches Claude account data from API
2. **RateLimitChecker** (`src/monitors/rate_limit_checker.py`) - Analyzes rate limit status from data
3. **FeishuNotifier** (`src/notifiers/feishu_notifier.py`) - Sends Claude account notifications via Lark webhook
4. **ApiKeyScraper** (`src/scrapers/api_scraper.py`) - Fetches API key usage data from endpoint
5. **ApiNotifier** (`src/notifiers/api_notifier.py`) - Sends API usage notifications via Lark webhook
6. **Main** (`src/monitors/main.py`) - Orchestrates Claude account monitoring with data flow
7. **ApiMonitor** (`src/monitors/api_monitor.py`) - Orchestrates API usage monitoring with data flow
8. **FastAPI Server** (`src/server/fastapi_server.py`) - HTTP API for remote monitoring control

### Data Flows:
- **Account Monitoring**: ClaudeScraper → RateLimitChecker → FeishuNotifier (with change detection)
- **API Usage Monitoring**: ApiKeyScraper → ApiNotifier (direct notification)
- **HTTP API**: Client → FastAPI Server → Internal Components → Response

## 常用命令

### Development and Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run main Claude account monitoring (recommended)
python main.py

# Run API usage monitoring
python api_monitor.py

# Start FastAPI server
python start_server.py
# or directly
python fastapi_server.py

# Run with custom config (仅支持YAML格式)
python main.py --config custom_config.yaml
python api_monitor.py --config custom_config.yaml

# Skip scraping, only check existing data
python main.py --skip-scrape

# Run in quiet mode
python main.py --quiet
python api_monitor.py --quiet

# Individual components
python -m src.scrapers.claude_scraper       # Only scrape Claude account data
python -m src.scrapers.api_scraper          # Only scrape API usage data
python -m src.monitors.rate_limit_checker   # Only check rate limits
python -m src.notifiers.feishu_notifier     # Test Claude account notifications
python -m src.notifiers.api_notifier        # Test API usage notifications
```

### FastAPI Server
```bash
# Start server with default settings (port 8155)
python start_server.py

# Start with custom host and port
python start_server.py --host 127.0.0.1 --port 8080

# Start with hot reload for development
python start_server.py --reload

# Start with multiple workers
python start_server.py --workers 4

# Use client example to test API
python examples/client_example.py

# Simple URL triggers (with parameter authentication)
curl "http://localhost:8155/trigger/monitor_accounts?k=your_simple_key"
curl "http://localhost:8155/trigger/monitor_api_usage?k=your_simple_key"  
curl "http://localhost:8155/trigger/full_monitor?k=your_simple_key"
```

### 简单URL触发 (参数验证)
```bash
# 直接在浏览器或curl中访问（需要k参数）：
http://localhost:8155/trigger/monitor_accounts?k=your_simple_key    # 监控账户状态并发送通知
http://localhost:8155/trigger/monitor_api_usage?k=your_simple_key   # 监控API使用情况并发送通知
http://localhost:8155/trigger/full_monitor?k=your_simple_key        # 完整监控流程

# 使用自定义配置文件：
http://localhost:8155/trigger/full_monitor/custom_config.yaml?k=your_simple_key
```

### Testing
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run individual test files
python3 tests/test_integration.py
python3 tests/test_status_change.py  
python3 tests/test_system.py

# Run all tests manually
for test in tests/test_*.py; do python3 "$test"; done
```

## 配置文件

### YAML配置格式

使用YAML格式配置文件（`config.yaml`），结构清晰，按功能分类：

```yaml
# API数据源配置
api:
  base_url: "http://localhost:8000"     # API服务器基础URL
  claude:
    bearer_token: "your_bearer_token_here"
    endpoint: "/admin/claude-accounts"          # 端点路径
    timeout: 30
    retry_attempts: 3
  usage:
    endpoint: "/admin/api-keys"                 # 端点路径
    timeout: 30
    retry_attempts: 3

# 数据存储配置
storage:
  claude_accounts_file: "claude_accounts.json"
  api_usage_file: "api_keys_usage.json"
  data_directory: "data"

# 通知系统配置
notification:
  enabled: true
  feishu:
    webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook_id"
    enabled: true

# FastAPI服务器配置
server:
  host: "localhost"
  port: 8155
  auth:
    api_key: "your_fastapi_access_key_here"
    api_secret: "your_fastapi_secret_key_here"
    require_signature: false
    simple_key: "your_simple_key_here"

# 系统配置
system:
  timezone: "Asia/Shanghai"
```


## 关键特性

- **Dual Monitoring**: Supports both Claude account and API key usage monitoring
- **Change Detection**: Claude account notifications only sent when rate limit status changes
- **Memory-based Data Flow**: No intermediate file dependencies between components
- **Rich Feishu Cards**: Beautiful card-based notifications with detailed statistics and interactive buttons
- **Interactive Buttons**: Feishu notifications include clickable buttons to trigger monitoring actions
- **HTTP API**: FastAPI server for remote monitoring control with authentication
- **Flexible Configuration**: Supports both JSON and YAML configuration formats with automatic detection
- **Error Handling**: Comprehensive error handling with fallback notifications
- **Timezone Support**: Configurable timezone display (default: Asia/Shanghai)
- **Batch Processing**: Handles multiple accounts/API keys efficiently
- **Security**: Optional API key authentication and HMAC signature verification

## 数据结构

The system expects API responses with this structure:
```json
{
    "success": true,
    "data": [
        {
            "id": "account_id",
            "name": "Account Name",
            "isActive": true,
            "rateLimitStatus": {
                "isRateLimited": false,
                "rateLimitedAt": "2025-08-30T11:49:55.522Z", 
                "minutesRemaining": 22
            },
            "usage": {
                "daily": {
                    "requests": 100,
                    "allTokens": 50000
                }
            }
        }
    ]
}
```

## API端点

### 数据源端点 (需要Bearer token认证):
- **账户数据**: `http://localhost:8000/admin/claude-accounts`
- **API密钥**: `http://localhost:8000/admin/api-keys?timeRange=today`

### FastAPI监控端点:

**需要API key认证的端点:**
- **根路径**: `GET /` - API信息
- **健康检查**: `GET /health` - 服务状态
- **执行命令**: `POST /command` - 远程执行监控命令（需认证）
- **API文档**: `GET /docs` - Swagger UI文档

**简单触发端点（参数验证）:**
- **简单触发**: `GET /trigger/{command}?k=your_key` - 通过URL参数验证后触发监控
- **指定配置**: `GET /trigger/{command}/{config_file}?k=your_key` - 使用指定配置文件触发

### FastAPI支持的命令:
- `check_accounts` - 检查账户限流状态
- `check_api_usage` - 检查API使用情况
- `notify_accounts` - 发送账户状态通知
- `notify_api_usage` - 发送API使用情况通知
- `full_monitor` - 完整监控流程（账户+API）