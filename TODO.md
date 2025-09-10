- [ ] 用larkpy使用app模式发送飞书

## 已完成功能
- [x] 添加飞书模式显示（Webhook/应用模式）
- [x] 添加Chat ID获取和显示流程  
- [x] 添加详细错误信息打印
- [x] 为api_monitor.py添加--no-notify参数控制飞书通知

## 当前问题
### 🔴 飞书应用模式消息发送失败
**问题描述：**
- 错误代码：99992402
- 错误信息：field validation failed - receive_id_type is required
- 状态：参数`receive_id_type`确实存在且值为`chat_id`，但API仍然报告该字段缺失

**已尝试的修复方法：**
1. ✅ 使用tenant_access_token替代app_access_token
2. ✅ 调整参数顺序和格式
3. ✅ 简化为基础文本消息测试
4. ✅ 修改Content-Type和请求头格式

**当前状态：**
- 能够成功获取tenant_access_token
- 能够获取群聊列表和Chat ID
- Chat ID解析和显示功能正常
- 消息发送时仍然出现字段验证错误

**可能原因分析：**
1. 可能需要特定的飞书应用权限配置
2. 可能需要使用不同的API端点或版本
3. 可能是请求体格式与飞书API期望不匹配

**下一步调试方向：**
- 检查飞书应用权限配置
- 尝试使用飞书官方SDK
- 对比飞书官方文档的完整示例