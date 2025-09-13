#!/usr/bin/env python3
"""
测试飞书回调功能
"""

import json
import requests
from datetime import datetime


def test_challenge_verification():
    """测试飞书URL验证（challenge）"""
    print("=== 测试飞书URL验证 ===")
    
    # 模拟飞书服务器发送的challenge验证
    challenge_data = {
        "challenge": "test_challenge_123",
        "timestamp": str(int(datetime.now().timestamp())),
        "nonce": "test_nonce"
    }
    
    try:
        response = requests.post(
            "http://localhost:8156/lark/callback",
            json=challenge_data,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("challenge") == challenge_data["challenge"]:
                print("✅ Challenge验证测试通过")
                return True
            else:
                print("❌ Challenge验证失败")
                return False
        else:
            print("❌ HTTP请求失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_callback_button_click():
    """测试飞书按钮点击回调"""
    print("\n=== 测试飞书按钮点击回调 ===")
    
    # 模拟飞书卡片按钮点击事件
    callback_data = {
        "schema": "2.0",
        "header": {
            "event_id": "test_event_123",
            "event_type": "card.action.trigger",
            "create_time": str(int(datetime.now().timestamp())),
            "token": "test_token",
            "app_id": "test_app_id"
        },
        "event": {
            "operator": {
                "operator_id": {
                    "union_id": "test_user_id",
                    "user_id": "test_user",
                    "open_id": "test_open_id"
                }
            },
            "action": {
                "value": {
                    "command": "monitor_accounts"
                },
                "tag": "button"
            }
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8156/lark/callback",
            json=callback_data,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("✅ 按钮点击回调测试通过")
                return True
            else:
                print("❌ 按钮点击回调失败")
                return False
        else:
            print("❌ HTTP请求失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_invalid_json():
    """测试无效JSON处理"""
    print("\n=== 测试无效JSON处理 ===")
    
    try:
        response = requests.post(
            "http://localhost:8156/lark/callback",
            data="invalid json data",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ 无效JSON处理测试通过")
            return True
        else:
            print("❌ 无效JSON处理失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("开始测试飞书回调功能...")
    print("请确保服务器运行在 http://localhost:8156")
    print()
    
    tests = [
        test_challenge_verification,
        test_callback_button_click,
        test_invalid_json
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️  {total - passed} 个测试失败")


if __name__ == "__main__":
    main()