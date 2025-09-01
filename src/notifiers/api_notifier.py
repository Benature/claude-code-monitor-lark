#!/usr/bin/env python3
"""
API使用情况飞书通知模块
发送API密钥使用统计的飞书通知
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from .feishu_notifier import FeishuNotifier
from ..utils.config_loader import create_config_manager

class ApiUsageNotifier(FeishuNotifier):
    
    def _calculate_usage_stats(self, api_keys: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算使用统计和比例"""
        stats = {
            "total_requests": 0,
            "total_tokens": 0, 
            "total_cost": 0.0,
            "active_keys": 0,
            "cost_breakdown": [],
            "request_breakdown": [],
            "token_breakdown": []
        }
        
        # 收集所有API的使用数据
        api_usage_data = []
        for key in api_keys:
            usage = key.get('usage', {})
            # 优先使用 today 数据，因为 daily 可能不包含 cost
            daily = usage.get('today', {}) or usage.get('daily', {})
            
            requests_count = daily.get('requests', 0)
            tokens_count = daily.get('allTokens', 0)
            cost = daily.get('cost', 0.0)
            
            if requests_count > 0 or tokens_count > 0 or cost > 0:
                api_usage_data.append({
                    "name": key.get('name', 'Unknown'),
                    "requests": requests_count,
                    "tokens": tokens_count,
                    "cost": cost,
                    "formatted_cost": daily.get('formattedCost', f'${cost:.2f}')
                })
                
                stats["total_requests"] += requests_count
                stats["total_tokens"] += tokens_count
                stats["total_cost"] += cost
                stats["active_keys"] += 1
        
        # 计算比例并排序
        if stats["total_cost"] > 0:
            for api in api_usage_data:
                cost_percentage = (api["cost"] / stats["total_cost"]) * 100
                request_percentage = (api["requests"] / max(stats["total_requests"], 1)) * 100
                token_percentage = (api["tokens"] / max(stats["total_tokens"], 1)) * 100
                
                stats["cost_breakdown"].append({
                    "name": api["name"],
                    "cost": api["cost"],
                    "formatted_cost": api["formatted_cost"],
                    "percentage": cost_percentage
                })
                
                stats["request_breakdown"].append({
                    "name": api["name"],
                    "requests": api["requests"],
                    "percentage": request_percentage
                })
                
                stats["token_breakdown"].append({
                    "name": api["name"],
                    "tokens": api["tokens"],
                    "percentage": token_percentage
                })
        
        # 按费用排序
        stats["cost_breakdown"].sort(key=lambda x: x["cost"], reverse=True)
        stats["request_breakdown"].sort(key=lambda x: x["requests"], reverse=True)
        stats["token_breakdown"].sort(key=lambda x: x["tokens"], reverse=True)
        
        return stats

    def send_api_usage_notification(self, api_data: Dict[str, Any]) -> bool:
        """
        发送API使用情况通知

        Args:
            api_data: API使用数据

        Returns:
            发送是否成功
        """
        if not self.enabled or not self.bot:
            return True

        try:
            # 解析API数据
            success = api_data.get('success', False)
            if not success:
                return self.send_error_notification("API数据获取失败")

            api_keys = api_data.get('data', [])
            if not api_keys:
                return self.send_error_notification("未找到API密钥数据")

            # 计算使用统计和比例
            stats = self._calculate_usage_stats(api_keys)

            # 构建美化的卡片消息
            card_message = {
                "msg_type": "interactive", 
                "card": {
                    "config": {
                        "wide_screen_mode": True
                    },
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": "📊 Claude API 使用统计"
                        },
                        "template": "blue"
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": f"📈 **今日概览**"
                            }
                        },
                        {
                            "tag": "div",
                            "fields": [
                                {
                                    "is_short": True,
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**总请求数**\n{stats['total_requests']:,}"
                                    }
                                },
                                {
                                    "is_short": True,
                                    "text": {
                                        "tag": "lark_md", 
                                        "content": f"**总Token数**\n{stats['total_tokens']:,}"
                                    }
                                },
                                {
                                    "is_short": True,
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**总费用**\n${stats['total_cost']:.2f}"
                                    }
                                },
                                {
                                    "is_short": True,
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**活跃密钥**\n{stats['active_keys']}/{len(api_keys)}"
                                    }
                                }
                            ]
                        },
                        {
                            "tag": "hr"
                        }
                    ]
                }
            }

            # 添加费用分析
            if stats['cost_breakdown']:
                cost_elements = [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"💰 **费用分析** (Top 5)"
                        }
                    }
                ]

                for i, item in enumerate(stats['cost_breakdown'][:5], 1):
                    cost_element = {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**{i}. {item['name']}**\n{item['formatted_cost']} ({item['percentage']:.1f}%)"
                        }
                    }
                    cost_elements.append(cost_element)

                card_message["card"]["elements"].extend(cost_elements)

            # 添加使用量分析
            if stats['request_breakdown']:
                usage_elements = [
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"🔑 **使用量分析** (Top 5)"
                        }
                    }
                ]

                for i, item in enumerate(stats['request_breakdown'][:5], 1):
                    usage_element = {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**{i}. {item['name']}**\n请求: {item['requests']:,} ({item['percentage']:.1f}%) | Token: {next(t['tokens'] for t in stats['token_breakdown'] if t['name'] == item['name']):,}"
                        }
                    }
                    usage_elements.append(usage_element)

                card_message["card"]["elements"].extend(usage_elements)

            # 添加时间戳
            timestamp_element = [
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**更新时间**: {self._get_current_time()}"
                    }
                }
            ]
            card_message["card"]["elements"].extend(timestamp_element)

            # 发送消息
            response = self.bot.send_with_payload(card_message)
            response_data = response.json()
            print(f"飞书API响应: {response_data}")

            if response_data.get('code') == 0:
                print("✅ API使用情况通知发送成功")
                return True
            else:
                print(f"❌ API使用情况通知发送失败: {response_data}")
                return False

        except Exception as e:
            print(f"❌ 发送API使用情况通知时发生异常: {e}")
            return False

def create_api_notifier_from_config(config_file: str = 'config.yaml') -> Optional[ApiUsageNotifier]:
    """
    从配置文件创建API使用情况通知器

    Args:
        config_file: 配置文件路径

    Returns:
        ApiUsageNotifier实例，如果创建失败返回None
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
            return ApiUsageNotifier(webhook_url, enabled, server_host, server_port, simple_key)
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
    print("API使用情况通知模块测试")

    notifier = create_api_notifier_from_config('config.yaml')
    
    if notifier:
        # 测试数据
        test_api_data = {
            "success": True,
            "data": [
                {
                    "id": "key1",
                    "name": "Production API",
                    "usage": {
                        "daily": {
                            "requests": 1500,
                            "allTokens": 75000
                        }
                    }
                },
                {
                    "id": "key2", 
                    "name": "Development API",
                    "usage": {
                        "daily": {
                            "requests": 300,
                            "allTokens": 15000
                        }
                    }
                }
            ]
        }

        success = notifier.send_api_usage_notification(test_api_data)
        print(f"API使用情况通知测试: {'成功' if success else '失败'}")
    else:
        print("API使用情况通知器创建失败")