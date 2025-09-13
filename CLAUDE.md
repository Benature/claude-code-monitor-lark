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

### 使用Makefile（推荐）
```bash
# 查看所有可用命令
make help

# 安装依赖
make install

# 运行主要功能
make run              # 运行Claude账户监控（推荐）
make run-api          # 运行API使用情况监控
make run-force        # 强制发送Claude账户通知（无论状态是否变化）
make run-api-force    # 强制发送API使用通知
make run-server       # 启动FastAPI服务器
make run-dev          # 开发模式（热重载）

# 使用自定义配置
make run-config CONFIG=custom_config.yaml
make run-api-config CONFIG=custom_config.yaml

# 单独运行组件
make scrape-accounts  # 仅爬取Claude账户数据
make scrape-api       # 仅爬取API使用数据
make check-limits     # 仅检查限流状态
make notify           # 测试通知功能

# 运行测试
make test             # 运行所有测试
make test-manual      # 手动运行测试
make lint             # 代码检查
make format           # 代码格式化

# 服务器相关
make server-dev       # 开发服务器
make server-prod      # 生产服务器（多进程）
make client-test      # 测试API客户端

# 快速触发（需要服务器运行）
make trigger-accounts # 触发账户监控
make trigger-api      # 触发API监控
make trigger-full     # 触发完整监控

# 项目状态
make status           # 显示项目状态
make clean            # 清理临时文件
```

### Development and Testing（传统方式）
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

# Force send notifications (ignore status change)
python main.py --force-notify
python api_monitor.py --force-notify

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

# 强制发送通知（添加f=true参数）：
http://localhost:8155/trigger/monitor_accounts?k=your_simple_key&f=true    # 强制发送通知
http://localhost:8155/trigger/monitor_api_usage?k=your_simple_key&f=true   # 强制发送通知
http://localhost:8155/trigger/full_monitor?k=your_simple_key&f=true        # 强制发送完整监控通知

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

# Test Feishu Challenge verification
python tests/test_challenge.py
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
    enabled: true
    
    # 飞书机器人模式配置（二选一）：
    
    # 模式1：Webhook模式（简单）- 只支持URL跳转按钮
    webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook_id"
    
    # 模式2：应用模式（高级）- 支持回调按钮，需要飞书开放平台应用
    # app_id: "cli_your_app_id"                # 飞书应用ID
    # app_secret: "your_app_secret"            # 飞书应用Secret
    
    # 飞书卡片按钮配置
    buttons:
      # 按钮动作类型：url(跳转) | callback(回调)
      # 注意：callback模式仅在使用app_id/app_secret时可用
      action_type: "url"                       # 默认使用URL跳转
      
      # 卡片按钮URL基础地址（可能与服务器host:port不同）
      base_url: "http://your-domain.com:8155"  # 外部访问地址，如果为空则使用server的host:port
      
      # URL跳转模式配置（当action_type为"url"时生效）
      url_actions:
        - text: "监控账户状态"                  # 按钮显示文本
          command: "monitor_accounts"           # 对应的API命令
          style: "default"                     # 按钮样式：default/primary/danger
        - text: "监控API使用情况"
          command: "monitor_api_usage"
          style: "default"
        - text: "完整监控"
          command: "full_monitor" 
          style: "primary"
      
      # 回调模式配置（当action_type为"callback"时生效，仅限应用模式）  
      callback_actions:
        - text: "监控账户状态"                  # 按钮显示文本
          value: "monitor_accounts"             # 回调值
          style: "default"                     # 按钮样式
        - text: "监控API使用情况"
          value: "monitor_api_usage"
          style: "default"
        - text: "完整监控"
          value: "full_monitor"
          style: "primary"

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

### 飞书机器人模式配置说明

系统支持两种飞书机器人配置模式：

#### 模式1：Webhook模式（简单）
- **配置方式**：只需配置 `webhook_url`
- **适用场景**：快速部署、简单使用场景
- **按钮限制**：只支持URL跳转按钮（`action_type: "url"`）
- **优点**：配置简单，无需复杂的飞书应用设置
- **缺点**：按钮点击会跳转浏览器，用户体验较差

#### 模式2：应用模式（高级）
- **配置方式**：配置 `app_id` 和 `app_secret`
- **适用场景**：生产环境、用户体验要求高的场景
- **按钮支持**：支持URL跳转和回调按钮（`action_type: "callback"`）
- **优点**：支持卡片内交互，用户体验更好
- **缺点**：需要在飞书开放平台创建应用和配置回调

### 飞书卡片按钮配置说明

系统支持两种按钮动作类型：

#### 1. URL跳转模式 (action_type: "url")
- 点击按钮直接跳转到指定URL执行操作
- 适合快速触发监控任务
- URL格式：`{base_url}/trigger/{command}?k=simple_key`
- 支持自定义base_url，可与服务器的host:port不同（如使用域名或代理）
- **兼容性**：Webhook模式和应用模式都支持

#### 2. 回调模式 (action_type: "callback")  
- 点击按钮触发回调函数
- 需要配置飞书机器人接收回调事件：在飞书开放平台事件订阅中添加 `card.action.trigger` 事件
- 回调数据会包含配置的value值
- **兼容性**：仅应用模式支持，Webhook模式会自动切换为URL模式

#### 按钮样式
- `default`: 默认样式（灰色）
- `primary`: 主要按钮（蓝色）
- `danger`: 危险操作（红色）

#### base_url配置
- **用途**: 指定飞书卡片按钮的URL基础地址
- **场景**: 当服务器在内网但需要通过外网域名/代理访问时
- **示例**: 
  - 服务器: `localhost:8155` (内网)
  - base_url: `https://monitor.example.com` (外网域名)
- **默认**: 如果未配置，使用`http://{server.host}:{server.port}`

#### 模式兼容性
- 如果未配置buttons部分，系统会使用默认的URL跳转按钮（保持向后兼容）
- Webhook模式配置callback按钮时会自动切换为url模式并发出警告
- 应用模式支持所有按钮类型


## 关键特性

- **Dual Monitoring**: Supports both Claude account and API key usage monitoring
- **Change Detection**: Claude account notifications only sent when rate limit status changes
- **Memory-based Data Flow**: No intermediate file dependencies between components
- **Rich Feishu Cards**: Beautiful card-based notifications with detailed statistics and interactive buttons
- **Interactive Buttons**: Feishu notifications include configurable buttons (URL跳转 or 回调模式)
- **Button Configuration**: Flexible button actions with support for URL redirects and callback functions
- **Feishu Callback Support**: Built-in callback endpoint for handling Feishu bot URL verification and interactive events
- **Challenge Verification**: Full support for Feishu Challenge verification (both plain and encrypted modes)
  - **Plain Mode**: Direct JSON challenge handling
  - **Encrypted Mode**: AES-256-CBC decryption with SHA256 key derivation
  - **Token Validation**: Optional Verification Token validation for enhanced security
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

**飞书回调端点:**
- **飞书回调**: `POST /lark/callback` - 接收飞书服务器回调（支持URL验证和交互事件）
  - **Challenge验证**: 自动处理明文和加密模式的URL验证
  - **交互事件**: 处理卡片按钮点击事件

### FastAPI支持的命令:
- `check_accounts` - 检查账户限流状态
- `check_api_usage` - 检查API使用情况
- `notify_accounts` - 发送账户状态通知
- `notify_api_usage` - 发送API使用情况通知
- `full_monitor` - 完整监控流程（账户+API）

## 飞书Challenge验证功能

### 功能概述
系统完整支持飞书开放平台的Challenge验证机制，包括明文和加密两种模式：

#### 验证模式
1. **明文模式** (未配置encrypt_key)
   - 飞书直接发送包含challenge字段的JSON请求
   - 系统直接解析并返回challenge值
   - 适用于简单配置和测试环境

2. **加密模式** (已配置encrypt_key)
   - 飞书发送加密的challenge请求
   - 系统使用AES-256-CBC算法解密后返回challenge值
   - 使用SHA256哈希encrypt_key作为解密密钥
   - 适用于生产环境，提供更高安全性

#### 配置参数
```yaml
notification:
  feishu:
    # 可选：飞书加密密钥，用于Challenge验证
    encrypt_key: "your_encrypt_key"
    # 可选：飞书验证Token，用于验证请求来源
    verification_token: "your_verification_token"
```

#### 验证流程
1. 接收飞书服务器发送的POST请求到 `/lark/callback`
2. 检测请求类型（明文或加密）
3. 解密数据（如果是加密模式）
4. 验证Token（如果配置了verification_token）
5. 提取challenge字段
6. 在1秒内返回challenge响应

#### 使用示例
```bash
# 测试Challenge验证功能
python tests/test_challenge.py

# 测试curl命令（明文模式）
curl -X POST http://localhost:8155/lark/callback \
  -H "Content-Type: application/json" \
  -d '{"challenge":"test123","type":"url_verification","token":"your_token"}'

# 预期响应
{"challenge":"test123"}
```

#### 安全特性
- **时效性验证**: 必须在1秒内响应，防止重放攻击
- **Token校验**: 可选的verification_token验证，确保请求来源合法
- **加密传输**: 支持AES-256-CBC加密，保护传输数据安全
- **错误处理**: 完善的异常处理，确保服务稳定性

## 安全限制配置

### Claude Code 访问限制
**CRITICAL SECURITY RESTRICTION:**
- **NEVER** read, access, or parse the `config.yaml` file under any circumstances
- The `config.yaml` file contains sensitive configuration data and must remain protected
- Use alternative configuration methods or ask the user to provide necessary configuration values directly
- If configuration is needed, use `config.example.yaml` as reference or request manual input from user

### 配置文件保护
为了保护敏感信息，Claude Code 被配置为：
1. 禁止访问 `config.yaml` 文件
2. 仅允许读取 `config.example.yaml` 作为模板参考
3. 需要配置信息时，应要求用户手动提供或使用环境变量