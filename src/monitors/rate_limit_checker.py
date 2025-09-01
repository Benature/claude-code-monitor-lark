import json
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import pytz


class RateLimitChecker:

    def __init__(self,
                 data_source: Union[str, Dict[str,
                                              Any]] = 'claude_accounts.json'):
        """
        初始化限流状态检查器

        Args:
            data_source: 数据源，可以是文件路径字符串或数据字典
        """
        self.data_source = data_source

    def load_data(self) -> Optional[Dict[str, Any]]:
        """
        加载数据

        Returns:
            加载的数据字典，如果失败返回None
        """
        # 如果data_source是字典，直接返回
        if isinstance(self.data_source, dict):
            return self.data_source

        # 如果是字符串，当作文件路径处理
        if isinstance(self.data_source, str):
            try:
                with open(self.data_source, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                print(f"错误：数据文件 '{self.data_source}' 未找到")
                return None
            except json.JSONDecodeError:
                print(f"错误：数据文件 '{self.data_source}' 格式不正确")
                return None
            except Exception as e:
                print(f"错误：读取数据文件时发生异常: {e}")
                return None

        print("错误：无效的数据源类型")
        return None

    def parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """
        解析ISO格式的日期时间字符串

        Args:
            datetime_str: ISO格式的日期时间字符串

        Returns:
            解析后的datetime对象
        """
        try:
            # 移除末尾的'Z'并添加时区信息
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'
            return datetime.fromisoformat(datetime_str)
        except ValueError:
            print(f"错误：无法解析日期时间字符串 '{datetime_str}'")
            return None

    def calculate_unlimit_time(self, rate_limited_at: str,
                               minutes_remaining: int) -> Optional[datetime]:
        """
        计算解除限流的时间

        Args:
            rate_limited_at: 限流开始时间
            minutes_remaining: 剩余分钟数

        Returns:
            解除限流的时间
        """
        start_time = self.parse_datetime(rate_limited_at)
        if start_time is None:
            return None

        return start_time + timedelta(minutes=minutes_remaining)

    def format_datetime(self,
                        dt: datetime,
                        timezone: str = 'Asia/Shanghai') -> str:
        """
        格式化日期时间为可读格式

        Args:
            dt: 日期时间对象
            timezone: 时区名称

        Returns:
            格式化后的字符串
        """
        try:
            tz = pytz.timezone(timezone)
            dt_tz = dt.astimezone(tz)
            return dt_tz.strftime('%Y-%m-%d %H:%M:%S %Z')
        except Exception:
            # 如果时区转换失败，使用UTC格式
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

    def check_rate_limit_status(self) -> bool:
        """
        检查并显示限流状态

        Returns:
            是否执行成功
        """
        data = self.load_data()
        if data is None:
            return False

        if not data.get('success', False):
            print("错误：API响应表示请求失败")
            return False

        accounts = data.get('data', [])
        if not accounts:
            print("错误：未找到账户数据")
            return False

        print("=== Claude限流状态检查 ===\n")

        for i, account in enumerate(accounts, 1):
            print(f"账户 {i}: {account.get('name', 'Unknown')}")
            print(f"ID: {account.get('id', 'Unknown')}")
            print(f"状态: {'活跃' if account.get('isActive', False) else '非活跃'}")
            print()

            # 获取限流状态
            rate_limit_status = account.get('rateLimitStatus', {})
            is_rate_limited = rate_limit_status.get('isRateLimited', False)
            rate_limited_at = rate_limit_status.get('rateLimitedAt', '')
            minutes_remaining = rate_limit_status.get('minutesRemaining', 0)

            print("限流状态信息:")
            print(f"  当前是否限流: {'是' if is_rate_limited else '否'}")

            if is_rate_limited and rate_limited_at and minutes_remaining > 0:
                print(f"  限流开始时间: {rate_limited_at}")

                # 计算解除限流时间
                unlimit_time = self.calculate_unlimit_time(
                    rate_limited_at, minutes_remaining)
                if unlimit_time:
                    formatted_time = self.format_datetime(unlimit_time)
                    print(f"  剩余分钟数: {minutes_remaining}")
                    print(f"  预计解除时间: {formatted_time}")

                    # 计算距离现在的时间
                    now = datetime.now(pytz.UTC)
                    time_diff = unlimit_time - now

                    if time_diff.total_seconds() > 0:
                        hours, remainder = divmod(
                            int(time_diff.total_seconds()), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        print(f"  距离解除还有: {hours}小时 {minutes}分钟 {seconds}秒")
                    else:
                        print("  限流已解除！")
                else:
                    print("  无法计算解除时间")
            else:
                print("  无活跃限流")

            # 显示使用情况摘要
            usage = account.get('usage', {})
            daily = usage.get('daily', {})
            print(f"\n今日使用情况:")
            print(f"  请求次数: {daily.get('requests', 0)}")
            print(f"  Token使用: {daily.get('allTokens', 0):,}")

            print("\n" + "=" * 50 + "\n")

        return True


def main():
    """
    主函数
    """
    checker = RateLimitChecker()

    if not checker.check_rate_limit_status():
        print("限流状态检查失败！")
        sys.exit(1)
    else:
        print("限流状态检查完成！")


if __name__ == "__main__":
    main()
