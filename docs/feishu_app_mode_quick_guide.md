# 飞书应用模式快速配置指南

## 应用模式配置

应用模式支持更高级的功能，包括回调按钮和群聊自动选择。

### 1. 基本配置

```yaml
notification:
  feishu:
    enabled: true
    app_id: "cli_your_app_id"           # 必需：飞书应用ID
    app_secret: "your_app_secret"       # 必需：飞书应用Secret
    chat_id: "oc_your_chat_id"          # 可选：指定群聊ID
```

### 2. chat_id 配置选项

#### 选项1：手动指定群聊ID（推荐）
```yaml
chat_id: "oc_1234567890abcdef"  # 明确指定要发送消息的群聊
```

#### 选项2：自动获取第一个群聊
```yaml
# chat_id: "..."  # 注释掉或不配置chat_id
```
系统会自动获取机器人所在的第一个群聊并发送消息。

### 3. 获取群聊ID的方法

#### 方法1：通过系统日志
1. 不配置 `chat_id`，启动系统
2. 查看日志输出，会显示所有群聊：
```
获取到 3 个群聊
  群聊: 监控告警群 (ID: oc_1234567890abcdef)
  群聊: 开发讨论群 (ID: oc_abcdef1234567890)
  群聊: 测试群 (ID: oc_567890abcdef1234)
```
3. 复制需要的群聊ID到配置文件

#### 方法2：通过飞书开放平台
1. 使用飞书开放API获取群聊列表
2. 调用 `/open-apis/im/v1/chats` 接口

### 4. 完整配置示例

```yaml
notification:
  feishu:
    enabled: true
    app_id: "cli_a832e4452ff8900d"
    app_secret: "MtgxKVniQ97fMj4UO86kIbHioxKJdzYk"
    chat_id: "oc_1234567890abcdef"      # 可选，推荐配置
    
    buttons:
      action_type: "callback"           # 应用模式支持回调
      callback_actions:
        - text: "🔍 监控账户状态"
          value: "monitor_accounts"
          style: "default"
        - text: "📊 监控API使用情况"
          value: "monitor_api_usage"
          style: "default"
        - text: "🚀 完整监控"
          value: "full_monitor"
          style: "primary"
```

## 测试配置

```bash
# 测试应用模式和chat_id功能
make test-chat-id

# 测试模式检测
make test-modes

# 测试回调功能
make test-callback
```

## 常见问题排查

### 问题1：系统提示"无法获取访问令牌"
**原因**：app_id 或 app_secret 配置错误
**解决**：检查飞书开放平台的应用凭证

### 问题2：系统提示"无法获取到任何群聊"
**原因**：
1. 机器人未添加到任何群聊
2. 应用缺少"获取群信息"权限

**解决**：
1. 将机器人添加到目标群聊
2. 在飞书开放平台为应用添加相关权限

### 问题3：消息发送失败
**原因**：chat_id 不存在或机器人不在该群聊中
**解决**：
1. 检查 chat_id 是否正确
2. 确认机器人在目标群聊中
3. 尝试使用自动获取模式（不配置chat_id）

### 问题4：回调按钮不工作
**原因**：未配置飞书应用的回调地址
**解决**：
1. 在飞书开放平台配置事件订阅
2. 设置回调地址：`http://your-domain:8155/lark/callback`
3. 确保服务器可从外网访问

## 权限配置

在飞书开放平台为应用配置以下权限：

### 必需权限
- `im:chat:readonly` - 获取群组信息
- `im:message:send_as_bot` - 以机器人身份发送消息

### 回调功能额外权限
- `im:message` - 接收消息事件
- `im:chat` - 接收群聊事件

### 事件订阅
- 启用"卡片回调"事件
- 添加回调事件：`card.action.trigger` - 卡片按钮点击事件
- 设置回调地址：`http://your-domain:8155/lark/callback`