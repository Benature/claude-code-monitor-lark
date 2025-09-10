#!/usr/bin/env python3
"""
测试飞书应用模式chat_id功能
"""

import sys
sys.path.append('.')

from src.notifiers.feishu_notifier import FeishuNotifier


def test_app_mode_with_chat_id():
    """测试应用模式指定chat_id"""
    print("=== 测试应用模式指定chat_id ===")
    
    # 创建应用模式通知器，指定chat_id
    notifier = FeishuNotifier(
        app_id="cli_test_app_id",
        app_secret="test_app_secret",
        chat_id="oc_test_chat_id",
        enabled=True
    )
    
    # 测试基本属性
    print(f"模式: {notifier.mode}")
    print(f"配置的chat_id: {notifier.chat_id}")
    print(f"是否支持回调: {notifier._supports_callback()}")
    print(f"配置是否有效: {notifier._has_valid_config()}")
    
    # 测试chat_id解析
    resolved_chat_id = notifier._resolve_chat_id()
    print(f"解析的chat_id: {resolved_chat_id}")
    
    assert notifier.mode == "app", f"期望app模式，实际: {notifier.mode}"
    assert notifier.chat_id == "oc_test_chat_id", f"chat_id应为oc_test_chat_id，实际: {notifier.chat_id}"
    assert resolved_chat_id == "oc_test_chat_id", f"解析的chat_id应为oc_test_chat_id，实际: {resolved_chat_id}"
    
    print("✅ 应用模式指定chat_id测试通过\n")
    return True


def test_app_mode_auto_chat_id():
    """测试应用模式自动获取chat_id（模拟）"""
    print("=== 测试应用模式自动获取chat_id ===")
    
    # 创建应用模式通知器，不指定chat_id
    notifier = FeishuNotifier(
        app_id="cli_test_app_id",
        app_secret="test_app_secret",
        enabled=True
    )
    
    # 测试基本属性
    print(f"模式: {notifier.mode}")
    print(f"配置的chat_id: {notifier.chat_id}")
    print(f"是否支持回调: {notifier._supports_callback()}")
    
    # 注意：由于没有真实的app_id和app_secret，获取访问令牌会失败
    # 这是预期的行为，我们主要测试逻辑流程
    access_token = notifier._get_app_access_token()
    print(f"访问令牌获取结果: {'成功' if access_token else '失败（预期）'}")
    
    chat_list = notifier._get_chat_list()
    print(f"群聊列表获取结果: {len(chat_list)} 个群聊")
    
    # 由于无法获取真实的群聊列表，resolve_chat_id会返回None
    resolved_chat_id = notifier._resolve_chat_id()
    print(f"解析的chat_id: {resolved_chat_id}")
    
    assert notifier.mode == "app", f"期望app模式，实际: {notifier.mode}"
    assert notifier.chat_id is None, f"chat_id应为None，实际: {notifier.chat_id}"
    # 由于是模拟测试，resolved_chat_id预期为None
    
    print("✅ 应用模式自动获取chat_id测试通过（逻辑验证）\n")
    return True


def test_webhook_mode_compatibility():
    """测试Webhook模式兼容性"""
    print("=== 测试Webhook模式兼容性 ===")
    
    # 创建Webhook模式通知器，指定chat_id（应被忽略）
    notifier = FeishuNotifier(
        webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test_webhook",
        chat_id="oc_should_be_ignored",  # 这个应该被忽略
        enabled=True
    )
    
    print(f"模式: {notifier.mode}")
    print(f"配置的chat_id: {notifier.chat_id}")
    print(f"是否支持回调: {notifier._supports_callback()}")
    
    # Webhook模式下resolve_chat_id应该返回None
    resolved_chat_id = notifier._resolve_chat_id()
    print(f"解析的chat_id: {resolved_chat_id}")
    
    assert notifier.mode == "webhook", f"期望webhook模式，实际: {notifier.mode}"
    # 虽然设置了chat_id，但在webhook模式下不会使用
    assert resolved_chat_id is None, f"Webhook模式下resolved_chat_id应为None，实际: {resolved_chat_id}"
    
    print("✅ Webhook模式兼容性测试通过\n")
    return True


def test_config_priority():
    """测试配置优先级"""
    print("=== 测试配置优先级 ===")
    
    # 同时配置webhook和app参数，应优先使用app模式
    notifier = FeishuNotifier(
        webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test_webhook",
        app_id="cli_test_app_id",
        app_secret="test_app_secret",
        chat_id="oc_test_chat_id",
        enabled=True
    )
    
    print(f"模式: {notifier.mode}")
    print(f"webhook_url: {notifier.webhook_url}")
    print(f"app_id: {notifier.app_id}")
    print(f"chat_id: {notifier.chat_id}")
    
    # 应该优先使用应用模式
    assert notifier.mode == "app", f"期望app模式（优先级更高），实际: {notifier.mode}"
    assert notifier._supports_callback(), "应用模式应支持回调"
    
    resolved_chat_id = notifier._resolve_chat_id()
    print(f"解析的chat_id: {resolved_chat_id}")
    
    assert resolved_chat_id == "oc_test_chat_id", f"应使用指定的chat_id，实际: {resolved_chat_id}"
    
    print("✅ 配置优先级测试通过\n")
    return True


def main():
    """运行所有测试"""
    print("开始测试飞书应用模式chat_id功能...")
    print()
    
    tests = [
        test_app_mode_with_chat_id,
        test_app_mode_auto_chat_id,
        test_webhook_mode_compatibility,
        test_config_priority
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