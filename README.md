# Claude 限制监控系统

这是一个全面的 Claude 账户和 API 使用情况监控系统，支持实时状态检查、智能通知和远程控制。

> **数据源依赖**: 本项目需要配合 [claude-relay-service](https://github.com/Wei-Shaw/claude-relay-service) 使用，该服务提供Claude账户和API密钥的数据接口。

## 功能特性

### 🔍 双重监控
- **Claude账户监控**：检查账户限流状态、使用情况和恢复时间
- **API密钥监控**：跟踪API密钥的使用统计和消耗情况

### 🔧 智能架构
- **内存数据流**：组件间通过内存直接交互，无需文件依赖
- **变化检测**：仅在状态发生变化时发送通知，避免垃圾信息
- **模块化设计**：清晰的组件分离，易于维护和扩展

### 📱 飞书集成
- **多模式支持**：Webhook模式和应用模式
- **交互式卡片**：美观的消息卡片，包含详细统计信息
- **智能按钮**：支持URL跳转和回调两种按钮类型
- **Challenge验证**：完整支持飞书回调验证机制

### 🌐 HTTP API
- **FastAPI服务器**：提供RESTful API用于远程控制
- **多种认证**：支持API密钥认证和HMAC签名验证
- **简单触发**：支持URL参数验证的快速触发接口

### ⚙️ 灵活配置
- **YAML配置**：结构化配置文件，按功能模块组织
- **时区支持**：可配置时区显示（默认：Asia/Shanghai）
- **错误处理**：完善的异常处理和降级通知

## 快速开始

### 1. 安装依赖

```bash
# 使用Makefile（推荐）
make install

# 或手动安装
pip install -r requirements.txt
```

### 2. 配置系统

复制并编辑配置文件：

```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml 文件，配置API端点、认证信息和飞书通知
```

主要配置项：
- **API数据源**：配置Claude账户和API密钥数据端点
- **飞书通知**：设置Webhook URL或应用模式认证
- **服务器设置**：FastAPI服务器主机、端口和认证配置

### 3. 运行监控

```bash
# 使用Makefile运行（推荐）
make run              # Claude账户监控
make run-api          # API使用情况监控  
make run-server       # 启动HTTP API服务器

# 或直接运行Python脚本
python main.py        # Claude账户监控
python api_monitor.py # API使用情况监控
python start_server.py # HTTP API服务器
```

## 详细使用指南

### Makefile 命令（推荐）

```bash
# 查看所有可用命令
make help

# 主要监控功能
make run              # Claude账户监控（推荐）
make run-api          # API使用情况监控
make run-force        # 强制发送Claude账户通知
make run-api-force    # 强制发送API使用通知

# 服务器相关
make run-server       # 启动FastAPI服务器
make run-dev          # 开发模式（热重载）
make server-dev       # 开发服务器
make server-prod      # 生产服务器（多进程）

# 单独组件测试
make scrape-accounts  # 仅爬取Claude账户数据
make scrape-api       # 仅爬取API使用数据
make check-limits     # 仅检查限流状态
make notify           # 测试通知功能

# 远程触发（需要服务器运行）
make trigger-accounts # 触发账户监控
make trigger-api      # 触发API监控
make trigger-full     # 触发完整监控

# 开发相关
make test             # 运行测试
make lint             # 代码检查
make format           # 代码格式化
```

### 命令行参数

所有主要脚本都支持以下参数：

```bash
# 使用自定义配置文件
python main.py --config custom_config.yaml
python api_monitor.py --config custom_config.yaml

# 跳过数据爬取，使用现有数据
python main.py --skip-scrape

# 静默模式运行
python main.py --quiet
python api_monitor.py --quiet

# 强制发送通知（忽略状态变化检测）
python main.py --force-notify
python api_monitor.py --force-notify
```

### HTTP API 使用

启动服务器后，可通过HTTP API远程控制监控：

```bash
# 简单URL触发（浏览器访问或curl）
curl "http://localhost:8155/trigger/monitor_accounts?k=your_simple_key"
curl "http://localhost:8155/trigger/monitor_api_usage?k=your_simple_key"
curl "http://localhost:8155/trigger/full_monitor?k=your_simple_key"

# 强制发送通知
curl "http://localhost:8155/trigger/monitor_accounts?k=your_simple_key&f=true"

# 使用自定义配置
curl "http://localhost:8155/trigger/full_monitor/custom.yaml?k=your_simple_key"

# API文档
http://localhost:8155/docs
```

## 核心架构

### 组件结构

```
src/
├── scrapers/           # 数据爬取模块
│   ├── claude_scraper.py   # Claude账户数据爬取
│   └── api_scraper.py      # API使用数据爬取
├── monitors/           # 监控分析模块
│   ├── rate_limit_checker.py  # 限流状态检查
│   ├── main.py             # Claude账户监控编排
│   └── api_monitor.py      # API使用监控编排
├── notifiers/          # 通知发送模块
│   ├── feishu_notifier.py  # 飞书通知（Claude账户）
│   └── api_notifier.py     # 飞书通知（API使用）
├── server/             # HTTP API服务
│   ├── fastapi_server.py   # FastAPI服务器
│   └── start_server.py     # 服务器启动脚本
└── utils/              # 工具模块
    └── config_loader.py    # 配置文件加载器
```

### 数据流

- **Claude账户监控**: `ClaudeScraper` → `RateLimitChecker` → `FeishuNotifier`
- **API使用监控**: `ApiKeyScraper` → `ApiNotifier`
- **HTTP API**: `Client` → `FastAPI Server` → `Internal Components` → `Response`

### 配置结构

系统使用YAML格式的配置文件，按功能模块组织：

- **api**: API数据源配置（Claude账户、API使用端点）
- **storage**: 数据存储配置（文件路径、目录设置）
- **notification**: 通知系统配置（飞书Webhook/应用模式、按钮配置）
- **server**: FastAPI服务器配置（主机、端口、认证）
- **system**: 系统配置（时区等）

## 飞书集成详解

### 通知模式

#### 1. Webhook模式（简单）
- 配置：仅需 `webhook_url`
- 限制：只支持URL跳转按钮
- 适用：快速部署、简单场景

#### 2. 应用模式（高级）
- 配置：需要 `app_id` 和 `app_secret`
- 功能：支持回调按钮、Challenge验证
- 适用：生产环境、交互体验

### 按钮配置

支持两种按钮类型：
- **URL跳转**: 点击后跳转到指定URL执行操作
- **回调模式**: 点击后触发飞书回调事件（仅应用模式）

### Challenge验证

完整支持飞书Challenge验证机制：
- **明文模式**: 直接处理JSON请求
- **加密模式**: AES-256-CBC解密处理
- **Token验证**: 可选的来源验证

## 错误处理

系统包含多层错误处理：

### API层面
- **认证错误**: Bearer token无效或权限不足
- **网络错误**: 连接超时、DNS解析失败
- **数据格式**: API响应格式错误处理

### 通知层面
- **飞书API**: Webhook失败时的降级处理
- **配置错误**: 缺少必要配置时的友好提示

### 系统层面
- **文件操作**: 数据目录创建、权限检查
- **进程管理**: 优雅的异常退出和资源清理

## 部署建议

### 开发环境
```bash
make install    # 安装依赖
make run-dev    # 开发模式启动服务器
```

### 生产环境
```bash
make install
make server-prod  # 多进程生产服务器
```

### 定时任务
```bash
# crontab 示例
*/5 * * * * cd /path/to/project && make run >/dev/null 2>&1
```

## 许可证

MIT License
