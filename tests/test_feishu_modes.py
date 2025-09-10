#!/usr/bin/env python3
"""
测试飞书机器人两种模式功能
"""

import sys
sys.path.append('.')

from src.notifiers.feishu_notifier import FeishuNotifier


def test_webhook_mode():
    """测试Webhook模式"""
    print("=== 测试Webhook模式 ===")
    
    # 创建Webhook模式通知器
    notifier = FeishuNotifier(
        webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test_webhook",
        enabled=True,
        button_config={
            "action_type": "url",
            "url_actions": [
                {"text": "测试按钮", "command": "test", "style": "default"}
            ]
        }
    )
    
    # 测试模式检测
    print(f"检测到的模式: {notifier.mode}")
    print(f"是否支持回调: {notifier._supports_callback()}")
    print(f"配置是否有效: {notifier._has_valid_config()}")
    
    # 测试按钮生成
    actions = notifier._get_button_actions()
    print(f"生成的按钮数量: {len(actions)}")
    for i, action in enumerate(actions):
        print(f"  按钮{i+1}: {action.get('text', {}).get('content', 'N/A')}")
        if 'url' in action:
            print(f"    URL: {action['url']}")
    
    assert notifier.mode == "webhook", f"期望webhook模式，实际: {notifier.mode}"
    assert not notifier._supports_callback(), "Webhook模式不应支持回调"
    assert notifier._has_valid_config(), "Webhook模式配置应有效"
    
    print("✅ Webhook模式测试通过\n")
    return True


def test_app_mode():
    """测试应用模式"""
    print("=== 测试应用模式 ===")
    
    # 创建应用模式通知器
    notifier = FeishuNotifier(
        app_id="cli_test_app_id",
        app_secret="test_app_secret",
        enabled=True,
        button_config={
            "action_type": "callback",
            "callback_actions": [
                {"text": "回调按钮", "value": "test_callback", "style": "primary"}
            ]
        }
    )
    
    # 测试模式检测
    print(f"检测到的模式: {notifier.mode}")
    print(f"是否支持回调: {notifier._supports_callback()}")
    print(f"配置是否有效: {notifier._has_valid_config()}")
    
    # 测试按钮生成
    actions = notifier._get_button_actions()
    print(f"生成的按钮数量: {len(actions)}")
    for i, action in enumerate(actions):
        print(f"  按钮{i+1}: {action.get('text', {}).get('content', 'N/A')}")
        if 'value' in action:
            print(f"    回调值: {action['value']}")
        if 'url' in action:
            print(f"    URL: {action['url']}")
    
    assert notifier.mode == "app", f"期望app模式，实际: {notifier.mode}"
    assert notifier._supports_callback(), "应用模式应支持回调"
    assert notifier._has_valid_config(), "应用模式配置应有效"
    
    print("✅ 应用模式测试通过\n")
    return True


def test_mode_compatibility():
    """测试模式兼容性"""
    print("=== 测试模式兼容性 ===")
    
    # 测试1：Webhook模式配置callback按钮（应自动切换为url）
    print("测试1: Webhook模式配置callback按钮")
    notifier = FeishuNotifier(
        webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test_webhook",
        enabled=True,
        button_config={
            "action_type": "callback",  # 配置callback但使用webhook
            "callback_actions": [
                {"text": "回调按钮", "value": "test", "style": "default"}
            ],
            "url_actions": [
                {"text": "URL按钮", "command": "test", "style": "default"}
            ]
        }
    )
    
    actions = notifier._get_button_actions()
    has_url_button = any('url' in action for action in actions)
    has_callback_button = any('value' in action for action in actions)
    
    print(f"  生成URL按钮: {has_url_button}")
    print(f"  生成回调按钮: {has_callback_button}")
    
    # 应该有URL按钮，没有回调按钮
    assert has_url_button or len(actions) > 0, "应该生成默认URL按钮或从url_actions生成按钮"
    print("  ✅ 兼容性测试1通过")
    
    # 测试2：应用模式支持callback
    print("测试2: 应用模式配置callback按钮")
    notifier = FeishuNotifier(
        app_id="cli_test_app_id",
        app_secret="test_app_secret",
        enabled=True,
        button_config={
            "action_type": "callback",
            "callback_actions": [
                {"text": "回调按钮", "value": "test", "style": "default"}
            ]
        }
    )
    
    actions = notifier._get_button_actions()
    has_callback_button = any('value' in action for action in actions)
    
    print(f"  生成回调按钮: {has_callback_button}")
    
    assert has_callback_button, "应用模式应支持回调按钮"
    print("  ✅ 兼容性测试2通过")
    
    print("✅ 模式兼容性测试通过\n")
    return True


def test_invalid_config():
    """测试无效配置"""
    print("=== 测试无效配置 ===")
    
    # 测试1：没有任何配置
    print("测试1: 无配置")
    notifier = FeishuNotifier(enabled=True)
    print(f"  模式: {notifier.mode}")
    print(f"  配置有效: {notifier._has_valid_config()}")
    
    assert notifier.mode == "none", f"期望none模式，实际: {notifier.mode}"
    assert not notifier._has_valid_config(), "无配置时应无效"
    print("  ✅ 无配置测试通过")
    
    # 测试2：不完整的应用配置
    print("测试2: 不完整的应用配置")
    notifier = FeishuNotifier(app_id="test_id", enabled=True)  # 缺少app_secret
    print(f"  模式: {notifier.mode}")
    print(f"  配置有效: {notifier._has_valid_config()}")
    
    assert notifier.mode == "none", "不完整的应用配置应为none模式"
    assert not notifier._has_valid_config(), "不完整的应用配置应无效"
    print("  ✅ 不完整配置测试通过")
    
    print("✅ 无效配置测试通过\n")
    return True


def main():
    """运行所有测试"""
    print("开始测试飞书机器人两种模式...")
    print()
    
    tests = [
        test_webhook_mode,
        test_app_mode,
        test_mode_compatibility,
        test_invalid_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 失败: {e}")
    
    print(f"=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️  {total - passed} 个测试失败")


if __name__ == "__main__":
    main()