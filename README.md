# Claude账户爬虫

这是一个用Python编写的爬虫程序，用于访问Claude账户管理接口并获取账户信息。

## 功能特性

- 使用Bearer token进行身份认证
- 从配置文件读取认证信息
- 完整的错误处理和状态码检查
- 自动保存数据到JSON文件
- 支持超时和重试机制
- **类间直接调用架构**：ClaudeScraper和RateLimitChecker通过内存直接交互，无需文件依赖
- **飞书消息通知**：支持通过飞书机器人发送限流状态和错误通知
- **时区支持**：支持自定义时区设置，默认使用Asia/Shanghai

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

1. 编辑 `config.json` 文件：
```json
{
    "bearer_token": "your_actual_bearer_token_here",
    "timeout": 30,
    "retry_attempts": 3,
    "output_file": "claude_accounts.json",
    "feishu_webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook_id",
    "notification_enabled": true,
    "timezone": "Asia/Shanghai"
}
```

2. 配置说明：
   - `bearer_token`: 你的Claude API Bearer token
   - `feishu_webhook`: 飞书机器人webhook URL（可选）
   - `notification_enabled`: 是否启用飞书通知（true/false）
   - `timezone`: 时区设置（默认为Asia/Shanghai）

## 使用方法

### 1. 爬取Claude账户数据

#### 基本使用

```bash
python claude_scraper.py
```

#### 高级使用

你也可以在代码中自定义参数：

```python
from claude_scraper import ClaudeScraper

# 使用自定义配置文件
scraper = ClaudeScraper(config_file='my_config.json')

# 爬取数据
data = scraper.scrape_accounts()

# 保存到自定义文件
if data:
    scraper.save_to_file(data, 'custom_output.json')
```

### 2. 检查限流状态

运行限流状态检查脚本：

```bash
python rate_limit_checker.py
```

该脚本将：
- 显示当前限流状态（isRateLimited）
- 根据rateLimitedAt和minutesRemaining计算解除限流的时间
- 显示距离解除限流还有多长时间
- 提供今日使用情况摘要

### 3. 一键监控（推荐）

使用综合脚本同时执行数据爬取和限流检查：

```bash
python main.py
```

#### 参数选项

- `--config`, `-c`: 指定配置文件路径 (默认: config.json)
- `--data-file`, `-d`: 指定数据文件路径 (默认: claude_accounts.json)
- `--skip-scrape`: 跳过数据爬取，直接检查现有数据
- `--quiet`, `-q`: 静默模式，不显示详细信息

#### 使用示例

```bash
# 完整流程：爬取数据并检查限流状态
python main.py

# 只检查现有数据（不重新爬取）
python main.py --skip-scrape

# 使用自定义配置文件
python main.py --config my_config.json

# 静默模式运行
python main.py --quiet
```

## 输出格式

程序会将获取到的数据保存为JSON格式，文件名默认为 `claude_accounts.json`。

## 错误处理

程序包含完善的错误处理机制：

- **401**: 认证失败，请检查Bearer token
- **403**: 访问被拒绝，权限不足
- **网络错误**: 连接超时或网络问题
- **配置错误**: 配置文件不存在或格式错误

## 文件结构

```
.
├── claude_scraper.py     # Claude数据爬虫类
├── rate_limit_checker.py # 限流状态检查类
├── main.py              # 主协调程序
├── example_usage.py     # 使用示例脚本
├── config.json          # 配置文件
├── requirements.txt     # 依赖文件
├── README.md           # 说明文档
└── claude_accounts.json # 输出文件（可选）
```

## 注意事项

1. 请确保Bearer token的有效性和权限
2. 程序会自动处理常见的HTTP错误
3. 数据会以UTF-8编码保存到文件中
4. 程序包含30秒的请求超时设置

## 许可证

MIT License
