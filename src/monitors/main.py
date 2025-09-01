#!/usr/bin/env python3
"""
Claude限流监控主程序
结合爬虫和限流状态检查功能，实现类间直接调用
"""

import sys
import argparse
from pathlib import Path
from ..scrapers.claude_scraper import ClaudeScraper
from .rate_limit_checker import RateLimitChecker
from ..notifiers.feishu_notifier import create_notifier_from_config

FILE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = FILE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='Claude限流监控工具')
    parser.add_argument('--config',
                        '-c',
                        default=str(FILE_DIR / 'config.yaml'),
                        help='配置文件路径 (默认: config.yaml)')
    parser.add_argument('--save-file',
                        '-s',
                        default=str(DATA_DIR / 'claude_accounts.json'),
                        help='保存数据文件路径 (默认: claude_accounts.json)')
    parser.add_argument('--skip-scrape',
                        action='store_true',
                        help='跳过数据爬取，直接检查现有数据')
    parser.add_argument('--quiet',
                        '-q',
                        action='store_true',
                        help='静默模式，不显示详细信息')

    args = parser.parse_args()

    try:
        # 初始化飞书通知器
        notifier = create_notifier_from_config(args.config)

        data = None

        if not args.skip_scrape:
            if not args.quiet:
                print("=== 开始爬取Claude账户数据 ===")

            # 创建爬虫实例并获取数据
            scraper = ClaudeScraper(args.config)
            data = scraper.scrape_accounts()

            if data:
                if not args.quiet:
                    print("✅ 数据爬取完成\n")
            else:
                error_msg = "数据爬取失败"
                print(f"❌ {error_msg}")

                # 发送错误通知
                if notifier:
                    notifier.send_error_notification(error_msg)

                sys.exit(1)
        else:
            if not args.quiet:
                print("=== 跳过数据爬取，使用现有数据 ===")

        if not args.quiet:
            print("=== 开始检查限流状态 ===")

        # 创建限流检查器并传入数据
        if data:
            # 使用内存中的数据
            checker = RateLimitChecker(data)
        else:
            # 如果没有数据，使用默认文件路径
            checker = RateLimitChecker(args.save_file)

        if checker.check_rate_limit_status():
            if not args.quiet:
                print("✅ 限流状态检查完成")

            # 发送限流状态通知（只在状态发生变化时发送）
            if data and notifier:
                accounts = data.get('data', [])
                if accounts:
                    print(f"\n=== 发送飞书通知 ===")
                    notification_sent = notifier.send_rate_limit_notifications_batch(
                        accounts, args.save_file)

                    # 通知发送完成后，保存当前数据到文件
                    if notification_sent or not args.quiet:
                        scraper.save_to_file(data, args.save_file)
                        if not args.quiet:
                            print("✅ 数据已保存到文件\n")
                else:
                    print("未找到账户数据，跳过通知")

        else:
            error_msg = "限流状态检查失败"
            print(f"❌ {error_msg}")

            # 发送错误通知
            if notifier:
                notifier.send_error_notification(error_msg)

            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  操作被用户中断")
        sys.exit(1)
    except Exception as e:
        error_msg = f"发生错误: {e}"
        print(f"❌ {error_msg}")

        # 发送错误通知
        if 'notifier' in locals() and notifier:
            notifier.send_error_notification(error_msg)

        sys.exit(1)


if __name__ == "__main__":
    main()
