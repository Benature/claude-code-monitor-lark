#!/usr/bin/env python3
"""
测试状态变化检测功能
"""

import json
import os
import sys

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_notifier import FeishuNotifier


def create_test_data():
    """创建测试数据"""
    return [{
        "name": "Claude Pro 账户1",
        "id": "account-1",
        "rateLimitStatus": {
            "isRateLimited": False,
            "minutesRemaining": 0
        },
        "usage": {
            "daily": {
                "requests": 50,
                "allTokens": 25000
            }
        }
    }, {
        "name": "Claude Pro 账户2",
        "id": "account-2",
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
    }]


def create_previous_data():
    """创建上一次的数据（模拟状态变化）"""
    return {
        "data": [
            {
                "name": "Claude Pro 账户1",
                "id": "account-1",
                "rateLimitStatus": {
                    "isRateLimited": True,  # 上次是限流状态
                    "minutesRemaining": 10
                },
                "usage": {
                    "daily": {
                        "requests": 80,
                        "allTokens": 40000
                    }
                }
            },
            {
                "name": "Claude Pro 账户2",
                "id": "account-2",
                "rateLimitStatus": {
                    "isRateLimited": False,  # 上次是正常状态
                    "minutesRemaining": 0
                },
                "usage": {
                    "daily": {
                        "requests": 30,
                        "allTokens": 15000
                    }
                }
            }
        ]
    }


def test_status_change_detection():
    """测试状态变化检测功能"""
    print("=== 测试状态变化检测功能 ===\n")

    # 创建测试数据
    current_data = create_test_data()
    previous_data = create_previous_data()

    # 保存上一次的数据到文件（模拟历史数据）
    test_file = 'test_previous_data.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(previous_data, f, indent=2, ensure_ascii=False)

    print("历史数据已保存到 test_previous_data.json")
    print("当前数据:")
    for account in current_data:
        status = "限流中" if account['rateLimitStatus']['isRateLimited'] else "正常"
        print(f"  - {account['name']}: {status}")

    print("\n历史数据:")
    for account in previous_data['data']:
        status = "限流中" if account['rateLimitStatus']['isRateLimited'] else "正常"
        print(f"  - {account['name']}: {status}")

    # 创建通知器（使用测试webhook）
    notifier = FeishuNotifier("https://test-webhook.example.com",
                              enabled=False)

    print("\n=== 状态变化检测结果 ===")

    # 测试批量通知功能（此时应该检测到状态变化）
    result = notifier.send_rate_limit_notifications_batch(
        current_data, test_file)

    print(f"\n批量通知结果: {'成功' if result else '失败'}")

    # 验证文件是否仍然存在（模拟真实的程序运行）
    if os.path.exists(test_file):
        print("✅ 历史数据文件保持不变（正确的行为）")

    # 清理测试文件
    if os.path.exists(test_file):
        os.remove(test_file)
        print("清理测试文件完成")


def test_first_run():
    """测试首次运行（没有历史数据）"""
    print("\n=== 测试首次运行场景 ===\n")

    current_data = create_test_data()

    # 创建通知器
    notifier = FeishuNotifier("https://test-webhook.example.com",
                              enabled=False)

    print("模拟首次运行（无历史数据）:")
    result = notifier.send_rate_limit_notifications_batch(
        current_data, 'nonexistent_file.json')

    print(f"\n首次运行通知结果: {'成功' if result else '失败'}")


def test_no_changes():
    """测试无状态变化场景"""
    print("\n=== 测试无状态变化场景 ===\n")

    # 创建相同的数据
    current_data = create_test_data()
    previous_data = {
        "data": current_data.copy()  # 使用相同的数据
    }

    # 保存到文件
    test_file = 'test_no_change.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(previous_data, f, indent=2, ensure_ascii=False)

    # 创建通知器
    notifier = FeishuNotifier("https://test-webhook.example.com",
                              enabled=False)

    print("模拟无状态变化:")
    result = notifier.send_rate_limit_notifications_batch(
        current_data, test_file)

    print(f"\n无变化通知结果: {'成功' if result else '失败'}")

    # 清理
    if os.path.exists(test_file):
        os.remove(test_file)


if __name__ == "__main__":
    try:
        test_status_change_detection()
        test_first_run()
        test_no_changes()
        print("\n🎉 所有测试完成！")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
