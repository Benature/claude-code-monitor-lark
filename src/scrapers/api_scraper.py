#!/usr/bin/env python3
"""
API密钥使用情况爬虫
爬取Claude API密钥的使用统计数据
"""

import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime
from ..utils.config_loader import create_config_manager


class ApiKeyScraper:

    def __init__(self, config_file: str = 'config.yaml'):
        """
        初始化API密钥爬虫

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config_manager = create_config_manager(config_file)

        # 获取API配置
        api_config = self.config_manager.get_api_config()
        usage_config = api_config.get('usage', {})
        base_url = api_config.get('base_url', 'http://localhost:8000')

        self.token = self.config_manager.get('api.claude.bearer_token', '')
        self.timeout = usage_config.get('timeout', 30)
        self.retry_attempts = usage_config.get('retry_attempts', 3)
        endpoint_path = usage_config.get('endpoint', '/admin/api-keys')
        self.endpoint = f"{base_url}{endpoint_path}"

    def _get_headers(self) -> Dict[str, str]:
        """
        获取请求头

        Returns:
            包含Authorization的请求头字典
        """
        if not self.token:
            return {}
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Claude-API-Scraper/1.0'
        }

    def scrape_api_keys(self,
                        time_range: str = 'today') -> Optional[Dict[str, Any]]:
        """
        爬取API密钥使用情况

        Args:
            time_range: 时间范围，如 'today', 'week', 'month'

        Returns:
            响应数据字典，如果请求失败返回None
        """
        if not self.token:
            print("错误：未找到有效的Bearer token")
            return None

        url = self.endpoint
        headers = self._get_headers()
        params = {'timeRange': time_range}

        try:
            print(f"正在访问: {url} (timeRange={time_range})")
            response = requests.get(url,
                                    headers=headers,
                                    params=params,
                                    timeout=self.timeout)

            print(f"响应状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print("成功获取API密钥数据")
                    return data
                except json.JSONDecodeError:
                    print("错误：响应不是有效的JSON格式")
                    print(f"响应内容: {response.text[:500]}...")
                    return None
            elif response.status_code == 401:
                print("错误：认证失败，请检查Bearer token是否正确")
                return None
            elif response.status_code == 403:
                print("错误：访问被拒绝，权限不足")
                return None
            else:
                print(f"错误：请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text[:500]}...")
                return None

        except requests.exceptions.Timeout:
            print("错误：请求超时")
            return None
        except requests.exceptions.ConnectionError:
            print("错误：连接失败，请检查网络连接")
            return None
        except requests.exceptions.RequestException as e:
            print(f"错误：请求异常: {e}")
            return None
        except Exception as e:
            print(f"错误：发生未知异常: {e}")
            return None

    def save_to_file(self,
                     data: Dict[str, Any],
                     filename: str = 'api_keys_usage.json') -> bool:
        """
        将数据保存到文件

        Args:
            data: 要保存的数据
            filename: 保存的文件名

        Returns:
            保存是否成功
        """
        try:
            # 添加时间戳
            data['scraped_at'] = datetime.now().isoformat()

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"API密钥数据已保存到文件: {filename}")
            return True
        except Exception as e:
            print(f"错误：保存文件时发生异常: {e}")
            return False


def main():
    """
    主函数
    """
    scraper = ApiKeyScraper()

    # 爬取数据
    data = scraper.scrape_api_keys('today')

    if data:
        # 保存数据到文件
        scraper.save_to_file(data)
        print("API密钥数据爬取完成！")
    else:
        print("API密钥数据爬取失败！")


if __name__ == "__main__":
    main()
