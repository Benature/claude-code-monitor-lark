#!/usr/bin/env python3
"""
测试飞书Challenge验证功能
"""

import sys
import os
import json
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# 将父目录添加到路径中以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.notifiers.feishu_notifier import FeishuNotifier

def create_encrypted_challenge(challenge_data: dict, encrypt_key: str) -> str:
    """
    创建加密的Challenge数据（模拟飞书服务器加密过程）
    
    Args:
        challenge_data: Challenge数据字典
        encrypt_key: 加密密钥
        
    Returns:
        Base64编码的加密数据
    """
    try:
        # 1. 将数据转换为JSON字符串
        json_data = json.dumps(challenge_data, ensure_ascii=False)
        data_bytes = json_data.encode('utf-8')
        
        # 2. 对 Encrypt Key 进行 SHA256 哈希
        key = hashlib.sha256(encrypt_key.encode('utf-8')).digest()
        
        # 3. 生成16字节随机IV
        import os
        iv = os.urandom(16)
        
        # 4. 使用PKCS7填充
        padded_data = pad(data_bytes, AES.block_size)
        
        # 5. 使用AES-256-CBC加密
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(padded_data)
        
        # 6. 将IV和密文拼接后Base64编码
        full_encrypted = iv + encrypted_data
        return base64.b64encode(full_encrypted).decode('utf-8')
        
    except Exception as e:
        print(f"创建加密Challenge时发生错误: {e}")
        return ""

def test_plain_challenge():
    """测试明文Challenge处理"""
    print("=" * 50)
    print("测试明文模式Challenge验证")
    print("=" * 50)
    
    # 创建飞书通知器实例（不提供加密密钥）
    notifier = FeishuNotifier(
        webhook_url="https://example.com/webhook",
        enabled=True,
        verification_token="test_token_123"
    )
    
    # 模拟明文Challenge请求
    challenge_request = {
        "challenge": "ajls384kdjxxxx",
        "token": "test_token_123",
        "type": "url_verification"
    }
    
    request_body = json.dumps(challenge_request, ensure_ascii=False)
    print(f"请求体: {request_body}")
    
    # 处理Challenge请求
    result = notifier.process_challenge_request(request_body)
    print(f"处理结果: {result}")
    
    if result and result.get("challenge") == "ajls384kdjxxxx":
        print("✅ 明文Challenge测试成功")
        return True
    else:
        print("❌ 明文Challenge测试失败")
        return False

def test_encrypted_challenge():
    """测试加密Challenge处理"""
    print("\n" + "=" * 50)
    print("测试加密模式Challenge验证")
    print("=" * 50)
    
    # 测试加密密钥
    encrypt_key = "test_encrypt_key_12345"
    
    # 创建飞书通知器实例（提供加密密钥）
    notifier = FeishuNotifier(
        webhook_url="https://example.com/webhook",
        enabled=True,
        encrypt_key=encrypt_key,
        verification_token="test_token_456"
    )
    
    # 创建Challenge数据
    challenge_data = {
        "challenge": "encrypted_challenge_xyz789",
        "token": "test_token_456",
        "type": "url_verification"
    }
    
    print(f"原始Challenge数据: {challenge_data}")
    
    # 加密Challenge数据
    encrypted_data = create_encrypted_challenge(challenge_data, encrypt_key)
    if not encrypted_data:
        print("❌ 加密Challenge数据失败")
        return False
    
    print(f"加密后数据: {encrypted_data}")
    
    # 模拟加密Challenge请求
    encrypted_request = {
        "encrypt": encrypted_data
    }
    
    request_body = json.dumps(encrypted_request, ensure_ascii=False)
    print(f"请求体: {request_body}")
    
    # 处理Challenge请求
    result = notifier.process_challenge_request(request_body)
    print(f"处理结果: {result}")
    
    if result and result.get("challenge") == "encrypted_challenge_xyz789":
        print("✅ 加密Challenge测试成功")
        return True
    else:
        print("❌ 加密Challenge测试失败")
        return False

def test_invalid_token():
    """测试Token验证失败的情况"""
    print("\n" + "=" * 50)
    print("测试Token验证失败")
    print("=" * 50)
    
    # 创建飞书通知器实例
    notifier = FeishuNotifier(
        webhook_url="https://example.com/webhook",
        enabled=True,
        verification_token="correct_token"
    )
    
    # 模拟错误Token的Challenge请求
    challenge_request = {
        "challenge": "test_challenge",
        "token": "wrong_token",  # 错误的token
        "type": "url_verification"
    }
    
    request_body = json.dumps(challenge_request, ensure_ascii=False)
    print(f"请求体: {request_body}")
    
    # 处理Challenge请求
    result = notifier.process_challenge_request(request_body)
    print(f"处理结果: {result}")
    
    if result is None:
        print("✅ Token验证失败测试成功（正确拒绝了错误Token）")
        return True
    else:
        print("❌ Token验证失败测试失败（应该拒绝错误Token）")
        return False

def main():
    """主测试函数"""
    print("飞书Challenge验证功能测试")
    print("=" * 50)
    
    results = []
    
    # 测试明文模式
    results.append(test_plain_challenge())
    
    # 测试加密模式
    results.append(test_encrypted_challenge())
    
    # 测试Token验证
    results.append(test_invalid_token())
    
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"总测试数: {total}")
    print(f"通过数: {passed}")
    print(f"失败数: {total - passed}")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)