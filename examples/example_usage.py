#!/usr/bin/env python3
"""
Claude限流监控使用示例
展示如何在代码中使用ClaudeScraper和RateLimitChecker类
"""

from src.scrapers.claude_scraper import ClaudeScraper
from src.monitors.rate_limit_checker import RateLimitChecker


def example_direct_usage():
    """
    示例1: 类间直接调用
    """
    print("=== 示例1: 类间直接调用 ===")

    # 创建爬虫实例
    scraper = ClaudeScraper('config.yaml')

    # 获取数据
    data = scraper.scrape_accounts()

    if data:
        print("✅ 数据获取成功")

        # 直接将数据传递给限流检查器（内存中传递）
        checker = RateLimitChecker(data)
        checker.check_rate_limit_status()
    else:
        print("❌ 数据获取失败")


def example_file_usage():
    """
    示例2: 使用文件数据源
    """
    print("\n=== 示例2: 使用文件数据源 ===")

    # 使用文件路径作为数据源
    checker = RateLimitChecker('claude_accounts.json')
    checker.check_rate_limit_status()


def example_custom_processing():
    """
    示例3: 自定义数据处理
    """
    print("\n=== 示例3: 自定义数据处理 ===")

    scraper = ClaudeScraper('config.yaml')
    data = scraper.scrape_accounts()

    if data and 'data' in data:
        accounts = data['data']

        # 自定义处理逻辑
        for account in accounts:
            rate_limit = account.get('rateLimitStatus', {})
            if rate_limit.get('isRateLimited'):
                print(f"账户 {account['name']} 正在限流")
                print(f"剩余时间: {rate_limit.get('minutesRemaining', 0)} 分钟")
            else:
                print(f"账户 {account['name']} 正常")


def example_advanced_usage():
    """
    示例4: 高级用法 - 条件检查
    """
    print("\n=== 示例4: 高级用法 - 条件检查 ===")

    scraper = ClaudeScraper('config.yaml')
    data = scraper.scrape_accounts()

    if data:
        checker = RateLimitChecker(data)

        # 可以在这里添加自定义逻辑
        # 例如：只有在限流时才发送通知
        # 或者：根据使用情况调整请求频率

        print("数据已准备好进行进一步处理...")
        print("- 可以集成到监控系统中")
        print("- 可以触发自动化告警")
        print("- 可以用于API使用量分析")


if __name__ == "__main__":
    print("Claude限流监控 - 使用示例")
    print("=" * 50)

    # 运行所有示例
    example_direct_usage()
    example_file_usage()
    example_custom_processing()
    example_advanced_usage()

    print("\n" + "=" * 50)
    print("示例运行完成！")
