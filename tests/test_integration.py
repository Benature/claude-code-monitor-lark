#!/usr/bin/env python3
"""
集成测试：模拟完整的监控流程
"""

import json
import os
import sys

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_scraper import ClaudeScraper
from feishu_notifier import FeishuNotifier



def test_integration_flow():
    """测试完整的集成流程"""
    print("=== 集成测试：完整的监控流程 ===\n")

    # 测试数据文件
    test_data_file = 'test_current_data.json'
    history_file = 'claude_accounts.json'

    # 步骤1: 创建初始历史数据（模拟第一次运行后的数据）
    initial_data = {
        "data": [{
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
                "isRateLimited": False,
                "minutesRemaining": 0
            },
            "usage": {
                "daily": {
                    "requests": 30,
                    "allTokens": 15000
                }
            }
        }]
    }

    print("步骤1: 创建初始历史数据")
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, indent=2, ensure_ascii=False)
    print(f"✅ 初始历史数据已保存到 {history_file}")

    # 显示初始状态
    print("\n初始状态:")
    for account in initial_data['data']:
        status = "限流中" if account['rateLimitStatus']['isRateLimited'] else "正常"
        print(f"  - {account['name']}: {status}")

    # 步骤2: 模拟第二次运行 - 账户1变为限流状态
    print("\n步骤2: 模拟第二次运行（账户1变为限流状态）")
    second_run_data = {
        "data": [
            {
                "name": "Claude Pro 账户1",
                "id": "account-1",
                "rateLimitStatus": {
                    "isRateLimited": True,  # 状态变化！
                    "minutesRemaining": 15
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
                    "isRateLimited": False,  # 状态不变
                    "minutesRemaining": 0
                },
                "usage": {
                    "daily": {
                        "requests": 35,
                        "allTokens": 18000
                    }
                }
            }
        ]
    }

    # 保存当前数据到临时文件
    with open(test_data_file, 'w', encoding='utf-8') as f:
        json.dump(second_run_data, f, indent=2, ensure_ascii=False)

    print("当前状态:")
    for account in second_run_data['data']:
        status = "限流中" if account['rateLimitStatus']['isRateLimited'] else "正常"
        print(f"  - {account['name']}: {status}")

    # 步骤3: 创建通知器并测试状态变化检测
    print("\n步骤3: 检测状态变化并发送通知")
    notifier = FeishuNotifier("https://test-webhook.example.com",
                              enabled=False)

    # 读取历史数据进行比较
    previous_data = notifier._load_previous_data(history_file)
    if previous_data:
        print("✅ 成功读取历史数据")

        # 检测状态变化
        accounts = second_run_data['data']
        notifications_sent = []

        for account in accounts:
            if notifier._has_rate_limit_status_changed(account,
                                                       previous_data['data']):
                notifications_sent.append(account)
                print(f"📤 需要发送通知: {account['name']}")
            else:
                print(f"⏭️  跳过通知: {account['name']} (状态未变化)")

        # 步骤4: 模拟保存新数据（通知发送完成后）
        print("\n步骤4: 保存当前数据作为新的历史数据")
        # 这里模拟main.py中的逻辑：在通知发送完成后保存数据
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(second_run_data, f, indent=2, ensure_ascii=False)
        print(f"数据已保存到: {history_file}")

        print("✅ 新数据已保存，完成一次完整的监控周期")

        # 验证结果
        print("\n=== 测试结果总结 ===")
        print(f"📊 检测到的状态变化: {len(notifications_sent)} 个账户")
        print(f"📁 历史文件更新: ✅")
        print(f"🔄 监控周期完成: ✅")

        if len(notifications_sent) == 1:
            print("🎉 测试成功！只有状态发生变化的账户才会收到通知")
        else:
            print(f"⚠️  测试结果异常：期望1个通知，实际{len(notifications_sent)}个")

    # 清理测试文件
    for file in [test_data_file, history_file]:
        if os.path.exists(file):
            os.remove(file)
            print(f"清理文件: {file}")


if __name__ == "__main__":
    try:
        test_integration_flow()
        print("\n🎉 集成测试完成！")
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
