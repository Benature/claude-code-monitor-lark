#!/usr/bin/env python3
"""
飞书通知模块
使用larkpy发送飞书消息通知
"""

import json
import sys
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any
from larkpy import LarkWebhook, LarkMessage
from ..utils.config_loader import create_config_manager


class FeishuNotifier:

    def __init__(self,
                 webhook_url: Optional[str] = None,
                 app_id: Optional[str] = None,
                 app_secret: Optional[str] = None,
                 chat_id: Optional[str] = None,
                 enabled: bool = True,
                 server_host: str = "localhost",
                 server_port: int = 8155,
                 simple_key: str = "key",
                 button_config: Optional[Dict[str, Any]] = None,
                 encrypt_key: Optional[str] = None,
                 verification_token: Optional[str] = None):
        """
        初始化飞书通知器

        Args:
            webhook_url: 飞书webhook URL (Webhook模式)
            app_id: 飞书应用ID (应用模式)
            app_secret: 飞书应用Secret (应用模式)
            chat_id: 目标群聊ID (应用模式，可选)
            enabled: 是否启用通知
            server_host: 服务器主机地址
            server_port: 服务器端口
            simple_key: API访问密钥
            button_config: 按钮配置字典
            encrypt_key: 飞书加密密钥 (用于Challenge验证)
            verification_token: 飞书验证Token
        """
        self.webhook_url = webhook_url
        self.app_id = app_id
        self.app_secret = app_secret
        self.chat_id = chat_id
        self.enabled = enabled
        self.server_host = server_host
        self.server_port = server_port
        self.simple_key = simple_key
        self.button_config = button_config or {}
        self.encrypt_key = encrypt_key
        self.verification_token = verification_token
        self.bot = None
        self.lark_message = None
        self.mode = self._determine_mode()
        self.resolved_chat_id = None  # 最终使用的群聊ID

        # 打印当前使用的飞书模式
        if self.mode == "app":
            print(f"🔧 飞书通知模式: 应用模式 (App ID: {self.app_id})")
        elif self.mode == "webhook":
            print(f"🔧 飞书通知模式: Webhook模式")
        else:
            print(f"⚠️ 飞书通知模式: 无效配置")

        if self.enabled and self._has_valid_config():
            try:
                # 根据模式初始化
                if self.mode == "webhook" and self.webhook_url:
                    self.bot = LarkWebhook(self.webhook_url)
                elif self.mode == "app" and self.app_id and self.app_secret:
                    # 使用 LarkMessage 替代原生 requests
                    self.lark_message = LarkMessage(app_id=self.app_id,
                                                    app_secret=self.app_secret,
                                                    log_level='ERROR')
                    print("✅ LarkMessage 初始化成功")
            except Exception as e:
                print(f"警告：初始化飞书机器人失败: {e}")
                self.bot = None
                self.lark_message = None

    def _determine_mode(self) -> str:
        """
        根据配置确定飞书机器人模式
        
        Returns:
            "webhook" 或 "app" 或 "none"
        """
        if self.app_id and self.app_secret:
            return "app"
        elif self.webhook_url:
            return "webhook"
        else:
            return "none"

    def _has_valid_config(self) -> bool:
        """
        检查是否有有效的配置
        
        Returns:
            布尔值表示配置是否有效
        """
        if self.mode == "webhook":
            return bool(self.webhook_url)
        elif self.mode == "app":
            return bool(self.app_id and self.app_secret)
        else:
            return False

    def _supports_callback(self) -> bool:
        """
        检查当前模式是否支持回调
        
        Returns:
            布尔值表示是否支持回调模式
        """
        return self.mode == "app"

    def decrypt_challenge(self, encrypted_data: str) -> Optional[str]:
        """
        解密飞书 Challenge 数据 (AES-256-CBC)
        
        Args:
            encrypted_data: Base64编码的加密数据
            
        Returns:
            解密后的JSON字符串，失败返回None
        """
        if not self.encrypt_key:
            print("警告：未配置加密密钥，无法解密Challenge")
            return None

        try:
            # 1. 对 Encrypt Key 进行 SHA256 哈希，得到密钥
            key = hashlib.sha256(self.encrypt_key.encode('utf-8')).digest()

            # 2. Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data)

            # 3. 提取前16字节作为IV
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]

            # 4. 使用 AES-256-CBC 解密
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_bytes = cipher.decrypt(ciphertext)

            # 5. 移除PKCS7填充
            decrypted_data = unpad(decrypted_bytes, AES.block_size)

            # 6. 转换为字符串
            return decrypted_data.decode('utf-8')

        except Exception as e:
            print(f"解密Challenge时发生错误: {e}")
            return None

    def verify_challenge_request(self, request_data: Dict[str, Any]) -> bool:
        """
        验证飞书Challenge请求的合法性
        
        Args:
            request_data: 请求数据字典
            
        Returns:
            布尔值表示验证是否成功
        """
        try:
            # 如果配置了verification_token，验证token
            if self.verification_token:
                request_token = request_data.get('token')
                if not request_token or request_token != self.verification_token:
                    print("Challenge验证失败：Token不匹配")
                    return False

            # 验证请求类型
            request_type = request_data.get('type')
            if request_type != 'url_verification':
                print(f"Challenge验证失败：请求类型错误 ({request_type})")
                return False

            # 验证challenge字段存在
            challenge = request_data.get('challenge')
            if not challenge:
                print("Challenge验证失败：缺少challenge字段")
                return False

            return True

        except Exception as e:
            print(f"验证Challenge请求时发生错误: {e}")
            return False

    def process_challenge_request(
            self, request_body: str) -> Optional[Dict[str, str]]:
        """
        处理飞书Challenge请求
        
        支持明文和加密两种模式：
        - 明文模式：直接解析JSON并返回challenge
        - 加密模式：先解密再解析JSON并返回challenge
        
        Args:
            request_body: 请求体字符串
            
        Returns:
            包含challenge的响应字典，失败返回None
        """
        try:
            # 先尝试作为JSON解析（明文模式）
            try:
                request_data = json.loads(request_body)

                # 检查是否为加密模式（包含encrypt字段）
                if 'encrypt' in request_data:
                    print("检测到加密模式Challenge请求")

                    # 解密数据
                    encrypted_data = request_data['encrypt']
                    decrypted_json = self.decrypt_challenge(encrypted_data)

                    if not decrypted_json:
                        print("Challenge解密失败")
                        return None

                    # 解析解密后的JSON
                    decrypted_data = json.loads(decrypted_json)
                    request_data = decrypted_data
                    print("Challenge解密成功")
                else:
                    print("检测到明文模式Challenge请求")

            except json.JSONDecodeError:
                print("Challenge请求JSON解析失败")
                return None

            # 验证请求合法性
            if not self.verify_challenge_request(request_data):
                return None

            # 提取并返回challenge
            challenge = request_data.get('challenge')
            print(f"处理Challenge请求成功，返回challenge: {challenge}")

            return {"challenge": challenge}

        except Exception as e:
            print(f"处理Challenge请求时发生错误: {e}")
            return None

    def _get_chat_list(self) -> list:
        """
        获取机器人所在的群聊列表
        
        Returns:
            群聊列表，格式：[{"chat_id": "xxx", "name": "群名称", "chat_type": "group"}]
        """
        if self.mode != "app" or not self.lark_message:
            return []

        try:
            # 使用 LarkMessage 的内置方法获取群聊列表
            chats = self.lark_message.get_group_chat_list()

            if isinstance(chats, dict) and chats.get("code") == 0:
                chat_items = chats.get("data", {}).get("items", [])
                print(f"获取到 {len(chat_items)} 个群聊")
                for chat in chat_items:
                    print(
                        f"  群聊: {chat.get('name', 'N/A')} (ID: {chat.get('chat_id', 'N/A')})"
                    )
                return chat_items
            else:
                print(f"获取群聊列表失败: {chats}")
                return []

        except Exception as e:
            print(f"获取群聊列表时发生异常: {e}")
            return []

    def _resolve_chat_id(self) -> Optional[str]:
        """
        解析最终使用的群聊ID（仅应用模式）
        
        Returns:
            群聊ID，如果无法获取或非应用模式返回None
        """
        # Webhook模式不需要chat_id
        if self.mode != "app":
            return None

        if self.resolved_chat_id:
            return self.resolved_chat_id

        # 如果指定了chat_id，直接使用
        if self.chat_id:
            self.resolved_chat_id = self.chat_id
            print(f"使用指定的群聊ID: {self.chat_id}")
            return self.resolved_chat_id

        # 应用模式且未指定chat_id，自动获取第一个群聊
        print("未指定群聊ID，自动获取机器人所在的第一个群聊...")
        chats = self._get_chat_list()
        if chats:
            first_chat = chats[0]
            self.resolved_chat_id = first_chat.get("chat_id")
            print(
                f"自动选择第一个群聊: {first_chat.get('name', 'N/A')} (ID: {self.resolved_chat_id})"
            )
            return self.resolved_chat_id
        else:
            print("警告：无法获取到任何群聊")
            return None

    def _send_message(self, message_payload: dict) -> bool:
        """
        统一的消息发送方法，根据模式选择发送方式
        
        Args:
            message_payload: 消息载荷
            
        Returns:
            发送是否成功
        """
        if self.mode == "app" and self.lark_message:
            # 应用模式：使用 LarkMessage 发送
            chat_id = self._resolve_chat_id()
            if not chat_id:
                print("❌ 无法获取群聊ID，消息发送失败")
                return False

            print(f"🎯 发送飞书消息到群聊: {chat_id}")

            try:
                # 检查消息类型并使用相应的方法发送
                if message_payload.get("msg_type") == "interactive":
                    # 对于卡片消息，使用 messages 方法，并指定 msg_type 和 receive_id_type
                    result = self.lark_message.messages(
                        content=message_payload.get("card"),  # 卡片内容
                        receive_id=chat_id,
                        msg_type="interactive",
                        receive_id_type="chat_id")
                else:
                    # 对于其他类型消息，使用通用的 send 方法
                    result = self.lark_message.send(content=message_payload,
                                                    receive_id=chat_id)

                if isinstance(result, dict) and result.get("code") == 0:
                    print("✅ 应用模式消息发送成功")
                    return True
                else:
                    print(f"❌ 应用模式消息发送失败: {result}")
                    return False

            except Exception as e:
                print(f"❌ 发送应用模式消息时发生异常: {e}")
                return False

        elif self.mode == "webhook" and self.bot:
            # Webhook模式：使用 LarkWebhook 发送
            try:
                response = self.bot.send_with_payload(message_payload)
                response_data = response.json()
                print(f"飞书API响应: {response_data}")

                if response_data.get('code') == 0:
                    print("✅ Webhook消息发送成功")
                    return True
                else:
                    print(f"❌ Webhook消息发送失败: {response_data}")
                    return False
            except Exception as e:
                print(f"❌ 发送Webhook消息时发生异常: {e}")
                return False
        else:
            print("❌ 未配置有效的发送方式")
            return False

    def _get_button_base_url(self) -> str:
        """
        获取按钮URL的基础地址
        
        Returns:
            基础URL字符串
        """
        if self.button_config and self.button_config.get('base_url'):
            return self.button_config['base_url']
        else:
            # 回退到server配置
            return f"http://{self.server_host}:{self.server_port}"

    def _get_button_actions(self) -> list:
        """
        根据配置生成按钮动作列表
        
        Returns:
            按钮动作元素列表
        """
        base_url = self._get_button_base_url()

        if not self.button_config:
            # 默认按钮配置（保持向后兼容）
            return [{
                "tag":
                "button",
                "text": {
                    "tag": "plain_text",
                    "content": "监控账户状态"
                },
                "type":
                "default",
                "url":
                f"{base_url}/trigger/monitor_accounts?k={self.simple_key}"
            }, {
                "tag":
                "button",
                "text": {
                    "tag": "plain_text",
                    "content": "监控API使用情况"
                },
                "type":
                "default",
                "url":
                f"{base_url}/trigger/monitor_api_usage?k={self.simple_key}"
            }]

        action_type = self.button_config.get('action_type', 'url')
        actions = []

        # 检查模式兼容性
        if action_type == 'callback' and not self._supports_callback():
            print(f"警告：当前模式 '{self.mode}' 不支持回调按钮，自动切换为URL模式")
            action_type = 'url'

        if action_type == 'url':
            # URL跳转模式
            url_actions = self.button_config.get('url_actions', [])
            for action in url_actions:
                button = {
                    "tag":
                    "button",
                    "text": {
                        "tag": "plain_text",
                        "content": action.get('text', '未知按钮')
                    },
                    "type":
                    action.get('style', 'default'),
                    "url":
                    f"{base_url}/trigger/{action.get('command', 'monitor_accounts')}?k={self.simple_key}"
                }
                actions.append(button)

        elif action_type == 'callback':
            # 回调模式（仅应用模式支持）
            callback_actions = self.button_config.get('callback_actions', [])
            for action in callback_actions:
                button = {
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": action.get('text', '未知按钮')
                    },
                    "type": action.get('style', 'default'),
                    "value": {
                        "command": action.get('value', 'monitor_accounts')
                    }
                }
                actions.append(button)

        return actions

    def _get_current_time(self) -> str:
        """
        获取当前时间的格式化字符串

        Returns:
            格式化的时间字符串
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _load_previous_data(
            self,
            data_file: str = 'claude_accounts.json'
    ) -> Optional[Dict[str, Any]]:
        """
        读取上一次的爬虫结果

        Args:
            data_file: 数据文件路径

        Returns:
            上一次的数据字典，如果读取失败返回None
        """
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"上一次数据文件 '{data_file}' 不存在，将发送首次通知")
            return None
        except json.JSONDecodeError:
            print(f"上一次数据文件 '{data_file}' 格式错误")
            return None
        except Exception as e:
            print(f"读取上一次数据时发生异常: {e}")
            return None

    def _has_rate_limit_status_changed(self, current_account: Dict[str, Any],
                                       previous_accounts: list) -> bool:
        """
        检查限流状态或剩余时间是否发生变化

        Args:
            current_account: 当前账户数据
            previous_accounts: 上一次的账户数据列表

        Returns:
            如果状态或剩余时间发生变化返回True，否则返回False
        """
        current_id = current_account.get('id')
        current_rate_status = current_account.get('rateLimitStatus', {})
        current_rate_limited = current_rate_status.get('isRateLimited', False)
        current_minutes_remaining = current_rate_status.get(
            'minutesRemaining', 0)

        # 查找上一次相同账户的数据
        for prev_account in previous_accounts:
            if prev_account.get('id') == current_id:
                prev_rate_status = prev_account.get('rateLimitStatus', {})
                prev_rate_limited = prev_rate_status.get(
                    'isRateLimited', False)
                prev_minutes_remaining = prev_rate_status.get(
                    'minutesRemaining', 0)

                # 检查限流状态变化
                if prev_rate_limited != current_rate_limited:
                    print(
                        f"账户 {current_id} 限流状态变化: {prev_rate_limited} -> {current_rate_limited}"
                    )
                    return True

                # 检查剩余时间变化（如果都处于限流状态时）
                if current_rate_limited and prev_rate_limited:
                    if prev_minutes_remaining != current_minutes_remaining:
                        print(
                            f"账户 {current_id} 限流剩余时间变化: {prev_minutes_remaining} -> {current_minutes_remaining} 分钟"
                        )
                        return True

                # 状态和时间都未变化
                return False

        # 如果是新账户，发送通知
        print(f"发现新账户: {current_id}")
        return True

    def send_rate_limit_notifications_batch(
            self,
            accounts_data: list,
            data_file: str = 'claude_accounts.json',
            force_notify: bool = False) -> bool:
        """
        批量发送限流状态通知，只在状态发生变化时发送

        Args:
            accounts_data: 账户数据列表
            data_file: 上一次数据文件路径
            force_notify: 强制发送通知，忽略状态变化检查

        Returns:
            是否有通知发送成功
        """
        if not self.enabled:
            return True

        # 检查是否有有效的发送客户端
        if self.mode == "webhook" and not self.bot:
            return True
        elif self.mode == "app" and not self.lark_message:
            return True

        # 读取上一次的数据
        previous_data = self._load_previous_data(data_file)
        previous_accounts = previous_data.get('data',
                                              []) if previous_data else []

        sent_any = False

        for account in accounts_data:
            # 检查是否强制发送或状态发生变化
            should_send = force_notify or self._has_rate_limit_status_changed(
                account, previous_accounts)

            if should_send:
                # 发送通知
                success = self.send_rate_limit_notification(account)
                if success:
                    sent_any = True
                    if force_notify:
                        account_id = account.get('id')
                        print(f"强制发送账户 {account_id} 通知成功")
                else:
                    print(f"发送账户 {account.get('id')} 通知失败")
            else:
                account_id = account.get('id')
                is_rate_limited = account.get('rateLimitStatus',
                                              {}).get('isRateLimited', False)
                status_text = "限流中" if is_rate_limited else "正常"
                print(f"账户 {account_id} 状态未变化 ({status_text})，跳过通知")

        return sent_any

    def send_rate_limit_notification(self, account_data: Dict[str,
                                                              Any]) -> bool:
        """
        发送限流状态通知

        Args:
            account_data: 账户数据

        Returns:
            发送是否成功
        """
        if not self.enabled:
            return True  # 如果未启用，视为成功（不影响主流程）

        # 检查是否有有效的发送客户端
        if self.mode == "webhook" and not self.bot:
            return True  # Webhook模式下如果bot未初始化，视为成功
        elif self.mode == "app" and not self.lark_message:
            return True  # 应用模式下如果lark_message未初始化，视为成功

        try:
            # 构建消息内容
            account_name = account_data.get('name', 'Unknown')
            account_id = account_data.get('id', 'Unknown')

            rate_limit_status = account_data.get('rateLimitStatus', {})
            is_rate_limited = rate_limit_status.get('isRateLimited', False)
            minutes_remaining = rate_limit_status.get('minutesRemaining', 0)

            # 获取使用情况
            usage = account_data.get('usage', {})
            daily = usage.get('daily', {})
            requests_count = daily.get('requests', 0)
            tokens_count = daily.get('allTokens', 0)
            daily_cost = daily.get('cost', 0)

            # 获取会话窗口成本
            session_window = usage.get('sessionWindow', {})
            session_cost = session_window.get('totalCost', 0)

            # 构建美化的卡片消息
            status_emoji = "🔴" if is_rate_limited else "🟢"
            status_text = "限流中" if is_rate_limited else "正常"
            status_color = "red" if is_rate_limited else "green"

            # 创建卡片消息
            card_message = {
                "msg_type": "interactive",
                "card": {
                    "config": {
                        "wide_screen_mode": True
                    },
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": f"{status_emoji} Claude 状态{status_text}"
                        },
                        "template": status_color
                    },
                    "elements": [
                        {
                            "tag":
                            "div",
                            "fields": [
                                {
                                    "is_short": True,
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**账户名称**\n{account_name}"
                                    }
                                },
                                #            {
                                #     "is_short": True,
                                #     "text": {
                                #         "tag": "lark_md",
                                #         "content": f"**账户ID**\n{account_id}"
                                #     }
                                # },
                                {
                                    "is_short": True,
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**当前状态**\n{status_text}"
                                    }
                                },
                                # {
                                #     "is_short": True,
                                #     "text": {
                                #         "tag":
                                #         "lark_md",
                                #         "content":
                                #         f"**更新时间**\n{self._get_current_time()}"
                                #     }
                                # }
                            ]
                        },
                        {
                            "tag": "hr"
                        }
                    ]
                }
            }

            # 添加使用情况统计
            usage_elements = [{
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📊 使用统计"
                }
            }, {
                "tag":
                "div",
                "fields": [{
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": f"**今日请求**\n{requests_count:,}"
                    }
                }, {
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": f"**今日Token**\n{tokens_count:,}"
                    }
                }, {
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": f"**今日成本**\n${daily_cost:.4f}"
                    }
                }, {
                    "is_short": True,
                    "text": {
                        "tag":
                        "lark_md",
                        "content":
                        f"**会话成本**\n${session_cost:.4f}"
                        if session_cost > 0 else "**会话成本**\n$0.0000"
                    }
                }]
            }]

            card_message["card"]["elements"].extend(usage_elements)

            # 添加操作按钮（先添加分隔线）
            card_message["card"]["elements"].append({"tag": "hr"})

            # 使用配置化的按钮
            button_actions = self._get_button_actions()
            print(button_actions)
            if button_actions:
                actions_element = {"tag": "action", "actions": button_actions}
                card_message["card"]["elements"].append(actions_element)

            # 如果正在限流，添加限流信息
            if is_rate_limited:
                rate_limit_elements = [{
                    "tag": "hr"
                }, {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"⚠️ 限流警告"
                    }
                }, {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**剩余恢复时长**: {minutes_remaining} 分钟"
                    }
                }, {
                    "tag": "div",
                    "text": {
                        "tag":
                        "lark_md",
                        "content":
                        f"**恢复时间**: {(datetime.now() +relativedelta(minutes=minutes_remaining)).strftime('%Y/%m/%d %H:%M')}"
                    }
                }]
                card_message["card"]["elements"].extend(rate_limit_elements)

            # 发送消息
            return self._send_message(card_message)

        except Exception as e:
            print(f"❌ 发送飞书通知时发生异常: {e}")
            return False

    def send_error_notification(self, error_message: str) -> bool:
        """
        发送错误通知

        Args:
            error_message: 错误消息

        Returns:
            发送是否成功
        """
        if not self.enabled:
            return True

        # 检查是否有有效的发送客户端
        if self.mode == "webhook" and not self.bot:
            return True
        elif self.mode == "app" and not self.lark_message:
            return True

        try:
            # 构建美化的错误通知卡片
            error_card = {
                "msg_type": "interactive",
                "card": {
                    "config": {
                        "wide_screen_mode": True
                    },
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": "❌ Claude 监控系统错误"
                        },
                        "template": "red"
                    },
                    "elements": [{
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"### 🚨 错误详情"
                        }
                    }, {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**错误信息**\n```\n{error_message}\n```"
                        }
                    }, {
                        "tag": "hr"
                    }, {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**发生时间**\n{self._get_current_time()}"
                        }
                    }, {
                        "tag": "div",
                        "text": {
                            "tag":
                            "lark_md",
                            "content":
                            "**建议操作**\n- 检查网络连接\n- 验证API密钥\n- 查看系统日志\n- 联系技术支持"
                        }
                    }]
                }
            }

            return self._send_message(error_card)

        except Exception as e:
            print(f"❌ 发送错误通知时发生异常: {e}")
            return False


def create_notifier_from_config(
        config_file: str = 'config.yaml') -> Optional[FeishuNotifier]:
    """
    从配置文件创建飞书通知器

    Args:
        config_file: 配置文件路径

    Returns:
        FeishuNotifier实例，如果创建失败返回None
    """
    try:
        config_manager = create_config_manager(config_file)

        # 获取通知配置
        notification_config = config_manager.get_notification_config()
        feishu_config = notification_config.get('feishu', {})

        # 获取服务器配置
        server_config = config_manager.get_server_config()
        auth_config = server_config.get('auth', {})

        webhook_url = feishu_config.get('webhook_url')
        app_id = feishu_config.get('app_id')
        app_secret = feishu_config.get('app_secret')
        chat_id = feishu_config.get('chat_id')
        enabled = notification_config.get(
            'enabled', False) and feishu_config.get('enabled', True)
        server_host = server_config.get('host', 'localhost')
        server_port = server_config.get('port', 8155)
        simple_key = auth_config.get('simple_key', 'key')
        button_config = feishu_config.get('buttons', {})
        encrypt_key = feishu_config.get('encrypt_key')
        verification_token = feishu_config.get('verification_token')

        if enabled and (webhook_url or (app_id and app_secret)):
            return FeishuNotifier(webhook_url=webhook_url,
                                  app_id=app_id,
                                  app_secret=app_secret,
                                  chat_id=chat_id,
                                  enabled=enabled,
                                  server_host=server_host,
                                  server_port=server_port,
                                  simple_key=simple_key,
                                  button_config=button_config,
                                  encrypt_key=encrypt_key,
                                  verification_token=verification_token)
        else:
            print("飞书通知未启用或未配置有效的webhook_url/app_id/app_secret")
            return None

    except FileNotFoundError:
        print(f"配置文件 '{config_file}' 未找到")
        return None
    except Exception as e:
        print(f"读取配置文件时发生异常: {e}")
        return None


if __name__ == "__main__":
    # 测试用例
    print("飞书通知模块测试")

    # 使用示例配置
    notifier = create_notifier_from_config('config.yaml')

    if notifier:
        # 测试发送通知
        test_data = {
            "name": "Claude Pro",
            "id": "test-id",
            "rateLimitStatus": {
                "isRateLimited": True,
                "minutesRemaining": 15
            },
            "usage": {
                "daily": {
                    "requests": 100,
                    "allTokens": 50000
                }
            }
        }

        # 测试限流状态通知
        success1 = notifier.send_rate_limit_notification(test_data)
        print(f"限流通知测试: {'成功' if success1 else '失败'}")

        # 测试错误通知
        test_error = "测试错误：网络连接超时"
        success2 = notifier.send_error_notification(test_error)
        print(f"错误通知测试: {'成功' if success2 else '失败'}")

        print(f"\n测试完成: {success1 and success2 and '全部成功' or '部分失败'}")
    else:
        print("飞书通知器创建失败")
