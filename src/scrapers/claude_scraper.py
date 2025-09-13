import requests
import json
import sys
from typing import Optional, Dict, Any
from ..utils.config_loader import create_config_manager


class ClaudeScraper:

    def __init__(self, config_file: str = 'config.yaml'):
        """
        初始化爬虫类

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config_manager = create_config_manager(config_file)

        # 获取API配置
        api_config = self.config_manager.get_api_config()
        claude_config = api_config.get('claude', {})
        base_url = api_config.get('base_url', 'http://localhost:8000')

        self.token = claude_config.get('bearer_token', '')
        self.timeout = claude_config.get('timeout', 30)
        self.retry_attempts = claude_config.get('retry_attempts', 3)
        endpoint_path = claude_config.get('endpoint', '/admin/claude-accounts')
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
            'User-Agent': 'Claude-Scraper/1.0'
        }

    def scrape_accounts(self) -> Optional[Dict[str, Any]]:
        """
        爬取Claude账户信息

        Returns:
            响应数据字典，如果请求失败返回None
        """
        if not self.token:
            print("错误：未找到有效的Bearer token")
            return None

        url = self.endpoint
        headers = self._get_headers()

        try:
            print(f"正在访问: {url}")
            response = requests.get(url, headers=headers, timeout=self.timeout)

            print(f"响应状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print("成功获取数据")
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
                     filename: str = 'claude_accounts.json') -> bool:
        """
        将数据保存到文件

        Args:
            data: 要保存的数据
            filename: 保存的文件名

        Returns:
            保存是否成功
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"数据已保存到文件: {filename}")
            return True
        except Exception as e:
            print(f"错误：保存文件时发生异常: {e}")
            return False


def main():
    """
    主函数
    """
    scraper = ClaudeScraper()

    # 爬取数据
    data = scraper.scrape_accounts()

    if data:
        # 保存数据到文件
        scraper.save_to_file(data)
        print("爬取完成！")
    else:
        print("爬取失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
