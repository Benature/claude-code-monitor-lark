#!/usr/bin/env python3
"""
FastAPI客户端使用示例
演示如何调用监控API接口
"""

import requests
import json
import yaml
import hashlib
import hmac
from datetime import datetime
from typing import Optional

class MonitorClient:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "", api_secret: str = ""):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
    
    def _get_headers(self, request_body: str = "") -> dict:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 如果有secret，生成签名
        if self.api_secret and request_body:
            timestamp = datetime.now().isoformat() + "Z"
            message = f"{timestamp}{request_body}"
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers["signature"] = signature
            headers["timestamp"] = timestamp
        
        return headers
    
    def execute_command(self, command: str, config_file: str = "config.yaml", time_range: str = "today") -> dict:
        """执行监控命令"""
        url = f"{self.base_url}/command"
        
        payload = {
            "command": command,
            "config_file": config_file,
            "time_range": time_range
        }
        
        request_body = json.dumps(payload)
        headers = self._get_headers(request_body)
        
        try:
            response = requests.post(url, headers=headers, data=request_body)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"请求失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def health_check(self) -> dict:
        """健康检查"""
        url = f"{self.base_url}/health"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}

def main():
    """示例用法"""
    # 从配置文件读取API密钥
    try:
        with open('../config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            server_config = config.get('server', {})
            auth_config = server_config.get('auth', {})
            api_key = auth_config.get('api_key', '')
            api_secret = auth_config.get('api_secret', '')
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        api_key = input("请输入API密钥: ").strip()
        api_secret = input("请输入API密钥(可选): ").strip()
    
    client = MonitorClient(api_key=api_key, api_secret=api_secret)
    
    print("=== Claude监控API客户端示例 ===\n")
    
    # 健康检查
    print("1. 健康检查:")
    health = client.health_check()
    print(f"   状态: {health.get('status', 'unknown')}")
    print()
    
    # 执行各种监控命令
    commands = [
        ("check_accounts", "检查账户状态"),
        ("check_api_usage", "检查API使用情况"),
        ("notify_accounts", "发送账户状态通知"),
        ("notify_api_usage", "发送API使用通知"),
        ("full_monitor", "完整监控流程")
    ]
    
    for command, description in commands:
        print(f"2. {description}:")
        result = client.execute_command(command)
        print(f"   成功: {result.get('success', False)}")
        print(f"   消息: {result.get('message', 'N/A')}")
        
        if result.get('data'):
            data = result['data']
            if isinstance(data, dict):
                # 显示一些关键信息
                if 'data' in data and isinstance(data['data'], list):
                    print(f"   账户数: {len(data['data'])}")
                if 'notifications' in data:
                    notifs = data['notifications']
                    print(f"   通知发送: 账户={notifs.get('accounts_sent', False)}, API={notifs.get('api_usage_sent', False)}")
        print()
    
    print("示例执行完成！")

if __name__ == "__main__":
    main()