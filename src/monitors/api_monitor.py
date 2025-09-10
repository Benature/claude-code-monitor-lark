#!/usr/bin/env python3
"""
API使用情况监控脚本
爬取API使用数据后直接发送飞书通知，数据通过内存传递
"""

import sys
import argparse
from pathlib import Path
from ..scrapers.api_scraper import ApiKeyScraper
from ..notifiers.api_notifier import create_api_notifier_from_config

def main():
    """
    主函数：爬取API使用情况并发送飞书通知
    """
    parser = argparse.ArgumentParser(description='API使用情况监控工具')
    parser.add_argument('--config', 
                        '-c', 
                        default='config.yaml',
                        help='配置文件路径 (默认: config.yaml)')
    parser.add_argument('--time-range',
                        '-t',
                        default='today',
                        help='时间范围 (默认: today)')
    parser.add_argument('--save-file',
                        '-s',
                        help='可选：保存数据到文件')
    parser.add_argument('--quiet',
                        '-q',
                        action='store_true',
                        help='静默模式，不显示详细信息')
    parser.add_argument('--no-notify',
                        '-n',
                        action='store_true',
                        help='禁用飞书通知，仅爬取数据')

    args = parser.parse_args()

    try:
        if not args.quiet:
            print("=== 开始API使用情况监控 ===")

        # 1. 爬取API使用数据
        if not args.quiet:
            print("正在爬取API使用数据...")
        
        scraper = ApiKeyScraper(args.config)
        api_data = scraper.scrape_api_keys(args.time_range)

        if not api_data:
            error_msg = "API使用数据爬取失败"
            print(f"❌ {error_msg}")
            sys.exit(1)

        if not args.quiet:
            print("✅ API使用数据爬取完成")

        # 2. 初始化飞书通知器并发送通知（如果未禁用）
        notifier = None
        if not args.no_notify:
            if not args.quiet:
                print("初始化飞书通知器...")
                
            notifier = create_api_notifier_from_config(args.config)
            if not notifier:
                error_msg = "飞书通知器初始化失败"
                print(f"❌ {error_msg}")
                sys.exit(1)

            # 3. 直接发送通知（内存传递数据）
            if not args.quiet:
                print("发送API使用情况通知...")

            notification_success = notifier.send_api_usage_notification(api_data)

            if notification_success:
                if not args.quiet:
                    print("✅ 飞书通知发送成功")
            else:
                print("❌ 飞书通知发送失败")
        else:
            if not args.quiet:
                print("⚠️  飞书通知已禁用，跳过通知发送")

        # 4. 可选：保存数据到文件
        if args.save_file:
            scraper.save_to_file(api_data, args.save_file)
            if not args.quiet:
                print(f"✅ 数据已保存到: {args.save_file}")

        if not args.quiet:
            print("=== API监控完成 ===")
            
        # 输出统计信息
        if api_data.get('success') and api_data.get('data'):
            api_keys = api_data['data']
            
            # 使用通知器的统计计算方法
            if 'notifier' in locals() and notifier:
                stats = notifier._calculate_usage_stats(api_keys)
                print(f"\n📊 统计摘要:")
                print(f"   API密钥总数: {len(api_keys)}")
                print(f"   活跃密钥数: {stats['active_keys']}")
                print(f"   今日总请求: {stats['total_requests']:,}")
                print(f"   今日总Token: {stats['total_tokens']:,}")
                print(f"   今日总费用: ${stats['total_cost']:.2f}")
                
                # 显示费用明细
                if stats['cost_breakdown']:
                    print(f"\n💰 费用明细:")
                    for item in stats['cost_breakdown']:
                        print(f"   {item['name']}: ${item['cost']:.2f} ({item['percentage']:.1f}%)")
            else:
                # 备用统计方法
                total_requests = sum(key.get('usage', {}).get('today', {}).get('requests', 0) or key.get('usage', {}).get('daily', {}).get('requests', 0) for key in api_keys)
                total_tokens = sum(key.get('usage', {}).get('today', {}).get('allTokens', 0) or key.get('usage', {}).get('daily', {}).get('allTokens', 0) for key in api_keys)
                total_cost = sum(key.get('usage', {}).get('today', {}).get('cost', 0.0) for key in api_keys)
                active_keys = sum(1 for key in api_keys if (key.get('usage', {}).get('today', {}).get('requests', 0) or key.get('usage', {}).get('daily', {}).get('requests', 0)) > 0)
                
                print(f"\n📊 统计摘要:")
                print(f"   API密钥总数: {len(api_keys)}")
                print(f"   活跃密钥数: {active_keys}")
                print(f"   今日总请求: {total_requests:,}")
                print(f"   今日总Token: {total_tokens:,}")
                print(f"   今日总费用: ${total_cost:.2f}")

    except KeyboardInterrupt:
        print("\n⚠️  操作被用户中断")
        sys.exit(1)
    except Exception as e:
        error_msg = f"发生错误: {e}"
        print(f"❌ {error_msg}")
        
        # 尝试发送错误通知（如果通知器已初始化且未禁用通知）
        try:
            if 'notifier' in locals() and notifier and not args.no_notify:
                notifier.send_error_notification(error_msg)
        except:
            pass
            
        sys.exit(1)

if __name__ == "__main__":
    main()