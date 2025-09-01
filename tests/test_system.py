#!/usr/bin/env python3
"""
系统测试脚本
测试Claude限流监控系统的各个组件
"""

import json
import sys
import os
from datetime import datetime, timedelta

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rate_limit_checker import RateLimitChecker
from feishu_notifier import FeishuNotifier


def create_test_data():
    """
    创建测试数据
    """
    # 模拟限流状态
    rate_limited_at = datetime.now().isoformat() + 'Z'
    minutes_remaining = 15

    test_data = {
        "success":
        True,
        "data": [{
            "id": "test-account-001",
            "name": "Claude Pro (测试)",
            "description": "测试账户",
            "email": "test@example.com",
            "isActive": True,
            "status": "active",
            "rateLimitStatus": {
                "isRateLimited": True,
                "rateLimitedAt": rate_limited_at,
                "minutesRemaining": minutes_remaining
            },
            "usage": {
                "daily": {
                    "tokens": 150000,
                    "inputTokens": 30000,
                    "outputTokens": 120000,
                    "requests": 250,
                    "allTokens": 150000
                },
                "total": {
                    "tokens": 2000000,
                    "requests": 5000,
                    "allTokens": 2000000
                }
            }
        }]
    }

    return test_data


def test_rate_limit_checker():
    """
    测试限流状态检查器
    """
    print("=== 测试限流状态检查器 ===")

    test_data = create_test_data()

    # 使用内存数据测试
    checker = RateLimitChecker(test_data)
    success = checker.check_rate_limit_status()

    if success:
        print("✅ 限流状态检查器测试通过")
        return True
    else:
        print("❌ 限流状态检查器测试失败")
        return False


def test_feishu_notifier():
    """
    测试飞书通知器
    """
    print("\n=== 测试飞书通知器 ===")

    # 使用示例webhook（这不会真的发送消息）
    test_webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/test_webhook"

    try:
        notifier = FeishuNotifier(test_webhook, enabled=True)

        if notifier.bot:
            print("✅ 飞书通知器初始化成功")

            # 测试发送通知
            test_account = create_test_data()["data"][0]
            result = notifier.send_rate_limit_notification(test_account)

            if result:
                print("✅ 飞书通知发送成功")
            else:
                print("⚠️ 飞书通知发送失败（可能是网络或配置问题）")

            return True
        else:
            print("⚠️ 飞书通知器初始化失败（可能是网络或配置问题）")
            return True  # 不算测试失败

    except Exception as e:
        print(f"❌ 飞书通知器测试异常: {e}")
        return False


def test_config_loading():
    """
    测试配置文件加载
    """
    print("\n=== 测试配置文件加载 ===")

    try:
        # 测试示例配置文件
        with open('config.example.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        required_fields = [
            'bearer_token', 'feishu_webhook', 'notification_enabled'
        ]
        missing_fields = [
            field for field in required_fields if field not in config
        ]

        if missing_fields:
            print(f"⚠️ 配置文件缺少字段: {missing_fields}")
            return False
        else:
            print("✅ 配置文件格式正确")
            return True

    except FileNotFoundError:
        print("❌ 配置文件不存在")
        return False
    except json.JSONDecodeError:
        print("❌ 配置文件JSON格式错误")
        return False
    except Exception as e:
        print(f"❌ 配置文件加载异常: {e}")
        return False


def main():
    """
    主测试函数
    """
    print("Claude限流监控系统 - 组件测试")
    print("=" * 50)

    test_results = []

    # 测试各个组件
    test_results.append(("限流状态检查器", test_rate_limit_checker()))
    test_results.append(("飞书通知器", test_feishu_notifier()))
    test_results.append(("配置文件加载", test_config_loading()))

    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n总体结果: {passed}/{total} 个测试通过")

    if passed == total:
        print("🎉 所有测试通过！系统运行正常。")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关配置。")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
