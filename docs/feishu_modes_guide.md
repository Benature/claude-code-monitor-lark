# 飞书机器人模式使用指南

## 快速选择

### 我应该选择哪种模式？

| 场景 | 推荐模式 | 原因 |
|------|----------|------|
| 快速测试 | Webhook | 配置简单，只需webhook URL |
| 开发环境 | Webhook | 无需复杂设置，专注功能开发 |
| 生产环境 | 应用模式 | 用户体验更好，支持高级功能 |
| 用户体验要求高 | 应用模式 | 支持卡片内交互，无需跳转 |
| 需要用户权限控制 | 应用模式 | 可获取用户身份信息 |

## 配置对比

参考 `config.example.yaml` 文件末尾的配置示例：

### Webhook模式（简单）
- 只需配置 `webhook_url`
- 使用 `action_type: "url"`
- 按钮使用 `url_actions` 配置

### 应用模式（高级）
- 配置 `app_id` 和 `app_secret`（取消注释）
- 可选配置 `chat_id` 指定目标群聊（不填则自动获取第一个群聊）
- 可使用 `action_type: "callback"`
- 按钮使用 `callback_actions` 配置

## 功能对比

| 功能 | Webhook模式 | 应用模式 |
|------|-------------|----------|
| 配置难度 | ⭐ 简单 | ⭐⭐⭐ 复杂 |
| URL跳转按钮 | ✅ 支持 | ✅ 支持 |
| 回调按钮 | ❌ 不支持 | ✅ 支持 |
| 群聊选择 | ❌ 无需配置 | ✅ 自动获取或手动指定 |
| 用户体验 | ⭐⭐ 需跳转 | ⭐⭐⭐⭐ 卡片内交互 |
| 权限控制 | ⭐ 简单 | ⭐⭐⭐ 丰富 |
| 维护成本 | ⭐ 低 | ⭐⭐ 中等 |

## 设置步骤

### Webhook模式设置
1. **创建机器人**：在飞书群里创建机器人
2. **获取Webhook**：获取机器人的webhook URL
3. **配置系统**：参考 `config.example.yaml` 中的【示例1】，填入webhook_url
4. **测试功能**：运行 `make test-modes` 测试

### 应用模式设置
1. **创建应用**：在飞书开放平台创建企业自建应用
2. **开通机器人**：为应用开通机器人能力
3. **配置回调**：设置事件订阅，添加 `card.action.trigger` 事件，回调地址：`http://your-domain:8155/lark/callback`
4. **获取凭证**：获取app_id和app_secret
5. **配置系统**：参考 `config.example.yaml` 中的【示例2】，取消注释并填入app_id和app_secret
6. **测试功能**：运行 `make test-modes` 和 `make test-callback` 测试

## 常见问题

### Q: 可以同时配置两种模式吗？
A: 可以同时配置，系统会优先使用应用模式（app_id + app_secret）。

### Q: Webhook模式配置callback按钮会怎样？
A: 系统会自动切换为url模式并发出警告，不会报错。

### Q: 如何测试配置是否正确？
A: 运行以下测试命令：
```bash
make test-modes      # 测试模式检测
make test-callback   # 测试回调功能（仅应用模式）
make test-chat-id    # 测试chat_id功能
```

### Q: 回调功能不工作怎么办？
A: 检查以下项目：
1. 确保使用应用模式（配置了app_id和app_secret）
2. 飞书应用已配置回调地址
3. 服务器可以从外网访问
4. 查看服务器日志确认收到回调请求

### Q: 如何获取群聊ID (chat_id)？
A: 有两种方式：
1. **自动获取**：应用模式下不配置chat_id，系统会自动选择第一个群聊
2. **手动指定**：在群聊中发送消息，通过开发工具或API获取chat_id后配置

### Q: 应用模式找不到群聊怎么办？
A: 检查以下项目：
1. 确认飞书应用已添加到目标群聊
2. 应用具有"获取群信息"权限
3. app_id和app_secret配置正确
4. 查看日志确认API调用结果

### Q: 按钮样式有哪些？
A: 支持三种样式：
- `default`：默认样式（灰色）
- `primary`：主要按钮（蓝色）
- `danger`：危险操作（红色）

## 迁移指南

### 从Webhook模式迁移到应用模式
1. 在飞书开放平台创建应用
2. 获取app_id和app_secret
3. 更新配置文件：
   - 参考 `config.example.yaml` 中的【示例2】
   - 取消 `app_id` 和 `app_secret` 的注释并填入真实值
   - 可选：注释掉 `webhook_url` 行
   - 可选：将 `action_type` 改为 `"callback"` 并使用 `callback_actions`
4. 重启服务器
5. 测试功能：`make test-modes`

## 最佳实践

1. **开发阶段**：使用Webhook模式快速开发和测试
2. **测试阶段**：使用应用模式测试回调功能
3. **生产环境**：使用应用模式提供最佳用户体验
4. **定期测试**：使用 `make test-modes` 确保配置正确
5. **监控日志**：关注服务器日志中的模式切换警告