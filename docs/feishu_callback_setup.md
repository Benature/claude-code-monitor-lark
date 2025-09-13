# 飞书机器人配置指南

本文档介绍如何配置飞书机器人的两种模式，以及如何使用回调功能。

## 模式概述

系统支持两种飞书机器人配置模式：

### 模式1：Webhook模式（简单）
- **配置要求**：只需配置 `webhook_url`
- **适用场景**：快速部署、简单使用场景、测试环境
- **按钮支持**：只支持URL跳转按钮
- **优点**：配置简单，无需复杂设置
- **缺点**：按钮点击会跳转浏览器

### 模式2：应用模式（高级）
- **配置要求**：配置 `app_id` 和 `app_secret`
- **适用场景**：生产环境、用户体验要求高的场景
- **按钮支持**：支持URL跳转和回调按钮
- **优点**：支持卡片内交互，用户体验更好
- **缺点**：需要在飞书开放平台创建应用

### 回调模式的优势（仅应用模式）
- 更好的用户体验（无需跳转）
- 支持权限控制
- 后台异步执行，响应更快
- 可以记录用户操作日志

## 配置步骤

### 1. 配置飞书机器人

在飞书开放平台（https://open.feishu.cn）：

1. **创建机器人应用**
2. **配置事件与回调**：
   - 事件订阅：启用 `卡片回调` 事件
   - 添加回调事件：`card.action.trigger` - 卡片按钮点击事件
   - 设置回调地址：`http://your-domain:8155/lark/callback`
   - 飞书会自动发送challenge验证（系统会自动处理）

3. **获取Webhook URL**：
   - 在机器人配置中获取webhook地址
   - 格式类似：`https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxx`

### 2. 修改配置文件

将配置文件中的按钮模式改为回调模式：

```yaml
# config.yaml
notification:
  enabled: true
  feishu:
    webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook_id"
    enabled: true
    
    buttons:
      # 关键：设置为回调模式
      action_type: "callback"
      
      # 回调按钮配置
      callback_actions:
        - text: "🔍 监控账户状态"
          value: "monitor_accounts"      # 对应API命令
          style: "default"
        - text: "📊 监控API使用情况"
          value: "monitor_api_usage"
          style: "default"
        - text: "🚀 完整监控"
          value: "full_monitor"
          style: "primary"
```

### 3. 启动服务器

确保FastAPI服务器运行并可以从外网访问：

```bash
# 开发环境
make server-dev

# 或者直接运行
python start_server.py --host 0.0.0.0 --port 8155
```

**重要**：如果部署在内网，需要通过内网穿透或反向代理让飞书服务器能访问到回调端点。

## 工作流程

### 回调验证流程
1. 飞书服务器向 `/lark/callback` 发送challenge验证
2. 系统自动解析并返回challenge值
3. 验证通过后，飞书开始发送实际回调事件

### 按钮点击流程
1. 用户点击卡片上的回调按钮
2. 飞书发送回调事件到 `/lark/callback`
3. 系统解析按钮的 `value.command` 字段
4. 立即返回成功响应给飞书（避免超时）
5. 后台异步执行对应的监控命令
6. 监控完成后发送新的通知卡片

### 数据流示例

**回调事件数据结构**：
```json
{
  "schema": "2.0",
  "header": {
    "event_type": "card.action.trigger",
    "event_id": "xxx",
    "create_time": "1234567890"
  },
  "event": {
    "action": {
      "value": {
        "command": "monitor_accounts"  // 配置的按钮命令
      },
      "tag": "button"
    }
  }
}
```

**系统响应**：
```json
{
  "code": 0,
  "msg": "ok", 
  "data": {}
}
```

## 测试验证

### 1. 运行自动化测试
```bash
# 确保服务器运行在 localhost:8155
make server-dev

# 运行回调测试
make test-callback

# 或者直接运行测试脚本
python tests/test_feishu_callback.py
```

### 2. 手动测试步骤

1. **验证回调端点**：
   ```bash
   curl -X POST http://localhost:8155/lark/callback \
     -H "Content-Type: application/json" \
     -d '{"challenge":"test123","timestamp":"1234567890","nonce":"abc"}'
   ```
   应该返回：`{"challenge":"test123"}`

2. **测试按钮回调**：
   ```bash
   curl -X POST http://localhost:8155/lark/callback \
     -H "Content-Type: application/json" \
     -d '{
       "schema": "2.0",
       "header": {"event_type": "card.action.trigger"},
       "event": {
         "action": {
           "value": {"command": "monitor_accounts"},
           "tag": "button"
         }
       }
     }'
   ```
   应该返回：`{"code":0,"msg":"ok","data":{}}`

3. **检查服务器日志**：
   观察是否有以下日志：
   - `收到飞书回调: ...`
   - `收到卡片交互事件`
   - `处理按钮命令: monitor_accounts`
   - `开始执行回调命令: monitor_accounts`

## 故障排除

### 常见问题

1. **飞书验证失败**
   - 检查回调URL是否可以从外网访问
   - 确认端口号和路径正确：`/lark/callback`
   - 查看服务器日志是否收到challenge请求

2. **按钮点击无响应**
   - 确认配置文件中 `action_type: "callback"`
   - 检查按钮的 `value` 字段是否正确
   - 查看服务器日志确认收到回调事件

3. **命令执行失败**
   - 检查配置文件路径和API连接
   - 确认Bearer token等认证信息正确
   - 查看后台异步任务的执行日志

### 日志分析

正常工作的日志应该包含：
```
收到飞书回调: {...}
飞书URL验证，返回challenge: xxx          # 首次验证
收到卡片交互事件                           # 按钮点击
处理按钮命令: monitor_accounts            # 命令解析
开始执行回调命令: monitor_accounts        # 异步执行
账户监控结果: 账户监控完成，通知发送: 成功  # 执行结果
```

## 与URL模式的对比

| 特性 | URL模式 | 回调模式 |
|------|---------|----------|
| 用户体验 | 跳转到浏览器 | 卡片内操作 |
| 权限控制 | URL参数验证 | 飞书用户身份 |
| 执行方式 | 同步响应 | 异步后台 |
| 配置复杂度 | 简单 | 需要配置飞书回调 |
| 网络要求 | 用户能访问服务器 | 飞书能访问服务器 |

建议：
- **开发/测试环境**：使用URL模式，配置简单
- **生产环境**：使用回调模式，用户体验更好