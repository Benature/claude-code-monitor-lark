#!/usr/bin/env python3
"""
飞书通知模块
使用larkpy发送飞书消息通知
"""

import json
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any
from larkpy import LarkBot
from ..utils.config_loader import create_config_manager



class FeishuNotifier:

    def __init__(self, webhook_url: str, enabled: bool = True, 
                 server_host: str = "localhost", server_port: int = 8155, simple_key: str = "key"):
        """
        初始化飞书通知器

        Args:
            webhook_url: 飞书webhook URL
            enabled: 是否启用通知
            server_host: 服务器主机地址
            server_port: 服务器端口
            simple_key: API访问密钥
        """
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.server_host = server_host
        self.server_port = server_port
        self.simple_key = simple_key
        self.bot = None

        if self.enabled and self.webhook_url:
            try:
                # 尝试不同的初始化方式
                if LarkBot:
                    self.bot = LarkBot(self.webhook_url)
                else:
                    # 如果LarkBot不可用，使用requests
                    import requests
                    self.bot = None
                    self.requests_fallback = True
            except Exception as e:
                print(f"警告：初始化飞书机器人失败: {e}")
                self.bot = None

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
        current_minutes_remaining = current_rate_status.get('minutesRemaining', 0)

        # 查找上一次相同账户的数据
        for prev_account in previous_accounts:
            if prev_account.get('id') == current_id:
                prev_rate_status = prev_account.get('rateLimitStatus', {})
                prev_rate_limited = prev_rate_status.get('isRateLimited', False)
                prev_minutes_remaining = prev_rate_status.get('minutesRemaining', 0)

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
            data_file: str = 'claude_accounts.json') -> bool:
        """
        批量发送限流状态通知，只在状态发生变化时发送

        Args:
            accounts_data: 账户数据列表
            data_file: 上一次数据文件路径

        Returns:
            是否有通知发送成功
        """
        if not self.enabled or not self.bot:
            return True

        # 读取上一次的数据
        previous_data = self._load_previous_data(data_file)
        previous_accounts = previous_data.get('data',
                                              []) if previous_data else []

        sent_any = False

        for account in accounts_data:
            # 检查状态是否发生变化
            if self._has_rate_limit_status_changed(account, previous_accounts):
                # 发送通知
                success = self.send_rate_limit_notification(account)
                if success:
                    sent_any = True
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
        if not self.enabled or not self.bot:
            return True  # 如果未启用或初始化失败，视为成功（不影响主流程）

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
                }]
            }]

            card_message["card"]["elements"].extend(usage_elements)

            # 添加操作按钮（先添加分隔线）
            card_message["card"]["elements"].append({"tag": "hr"})
            
            actions_element = {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "监控账户状态"
                        },
                        "type": "default",
                        "url": f"http://{self.server_host}:{self.server_port}/trigger/monitor_accounts?k={self.simple_key}"
                    },
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "监控API使用情况"
                        },
                        "type": "primary",
                        "url": f"http://{self.server_host}:{self.server_port}/trigger/monitor_api_usage?k={self.simple_key}"
                    }
                ]
            }
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
                        "tag": "lark_md",
                        "content": f"**恢复时间**: {(datetime.now() +relativedelta(minutes=minutes_remaining)).strftime('%Y/%m/%d %H:%M')}"
                    }
                }]
                card_message["card"]["elements"].extend(rate_limit_elements)

            # 发送消息
            response = self.bot.send_with_payload(card_message)
            response_data = response.json()
            print(f"飞书API响应: {response_data}")

            if response_data.get('code') == 0:
                print("✅ 飞书通知发送成功")
                return True
            else:
                print(f"❌ 飞书通知发送失败: {response_data}")
                return False

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
        if not self.enabled or not self.bot:
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

            response = self.bot.send_with_payload(error_card)
            response_data = response.json()
            print(f"飞书API响应: {response_data}")

            if response_data.get('code') == 0:
                print("✅ 错误通知发送成功")
                return True
            else:
                print(f"❌ 错误通知发送失败: {response_data}")
                return False

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
        
        webhook_url = feishu_config.get('webhook_url', '')
        enabled = notification_config.get('enabled', False) and feishu_config.get('enabled', True)
        server_host = server_config.get('host', 'localhost')
        server_port = server_config.get('port', 8155)
        simple_key = auth_config.get('simple_key', 'key')

        if webhook_url and enabled:
            return FeishuNotifier(webhook_url, enabled, server_host, server_port, simple_key)
        else:
            print("飞书通知未启用或webhook未配置")
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
