#!/usr/bin/env python3
"""
Claude监控FastAPI服务
提供HTTP接口来控制爬虫和通知功能
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Annotated
import asyncio
import json
import hashlib
import hmac
from datetime import datetime
from fastapi import Request

from ..scrapers.claude_scraper import ClaudeScraper
from ..monitors.rate_limit_checker import RateLimitChecker
from ..notifiers.feishu_notifier import create_notifier_from_config
from ..scrapers.api_scraper import ApiKeyScraper
from ..notifiers.api_notifier import create_api_notifier_from_config
from ..utils.config_loader import create_config_manager

app = FastAPI(title="Claude Monitor API",
              description="Claude账户监控和通知API服务",
              version="1.0.0")

# 安全配置
security = HTTPBearer()


def load_api_config() -> Dict[str, Any]:
    """加载API安全配置"""
    try:
        config_manager = create_config_manager('config.yaml')
        server_config = config_manager.get_server_config()
        auth_config = server_config.get('auth', {})

        return {
            "api_key": auth_config.get("api_key", ""),
            "api_secret": auth_config.get("api_secret", ""),
            "require_signature": auth_config.get("require_signature", False),
            "simple_key": auth_config.get("simple_key", "")
        }
    except Exception:
        return {
            "api_key": "",
            "api_secret": "",
            "require_signature": False,
            "simple_key": ""
        }


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(
    security)) -> str:
    """验证API密钥"""
    config = load_api_config()
    expected_key = config.get("api_key", "")

    if not expected_key:
        raise HTTPException(status_code=500, detail="服务器未配置API密钥")

    if credentials.credentials != expected_key:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    return credentials.credentials


def verify_signature(
        request_body: str,
        signature: Annotated[str | None, Header()] = None,
        timestamp: Annotated[str | None, Header()] = None) -> bool:
    """验证请求签名"""
    config = load_api_config()

    if not config.get("require_signature", False):
        return True

    api_secret = config.get("api_secret", "")
    if not api_secret:
        raise HTTPException(status_code=500, detail="服务器未配置API密钥")

    if not signature or not timestamp:
        raise HTTPException(status_code=400, detail="缺少签名或时间戳头")

    # 验证时间戳（防重放攻击）
    try:
        request_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now().replace(tzinfo=request_time.tzinfo)
        if abs((now - request_time).total_seconds()) > 300:  # 5分钟有效期
            raise HTTPException(status_code=401, detail="请求已过期")
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的时间戳格式")

    # 计算签名
    message = f"{timestamp}{request_body}"
    expected_signature = hmac.new(api_secret.encode('utf-8'),
                                  message.encode('utf-8'),
                                  hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="签名验证失败")

    return True


class CommandRequest(BaseModel):
    command: str
    config_file: Optional[str] = 'config.yaml'
    time_range: Optional[str] = 'today'
    force_notify: Optional[bool] = False
    params: Optional[Dict[str, Any]] = None


class CommandResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str


class FeishuChallenge(BaseModel):
    challenge: str
    timestamp: str
    nonce: str


class FeishuCallbackEvent(BaseModel):
    schema: str
    header: Dict[str, Any]
    event: Dict[str, Any]


@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message":
        "Claude Monitor API",
        "version":
        "1.0.0",
        "endpoints": [
            "/command - 执行监控命令 (需要认证)", "/trigger/{command} - 简单触发命令 (无需认证)",
            "/trigger/{command}/{config_file} - 指定配置文件触发 (无需认证)",
            "/callback/feishu - 飞书回调端点", "/health - 健康检查", "/docs - API文档"
        ],
        "simple_triggers": [
            "/trigger/monitor_accounts?k=your_key - 监控账户状态并发送通知",
            "/trigger/monitor_api_usage?k=your_key - 监控API使用情况并发送通知",
            "/trigger/full_monitor?k=your_key - 完整监控流程"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest,
                          api_key: str = Depends(verify_api_key)):
    """
    执行监控命令
    
    支持的命令：
    - monitor_accounts: 监控账户状态并发送通知
    - monitor_api_usage: 监控API使用情况并发送通知
    - full_monitor: 完整监控流程（账户+API）
    """

    try:
        command = request.command.lower()
        config_file = request.config_file
        time_range = request.time_range

        print(f"执行命令: {command}")

        if command == "monitor_accounts":
            return await _monitor_accounts(config_file, request.force_notify)

        elif command == "monitor_api_usage":
            return await _monitor_api_usage(config_file, time_range,
                                            request.force_notify)

        elif command == "full_monitor":
            return await _full_monitor(config_file, time_range,
                                       request.force_notify)

        else:
            raise HTTPException(
                status_code=400,
                detail=
                f"不支持的命令: {command}. 支持的命令: monitor_accounts, monitor_api_usage, full_monitor"
            )

    except Exception as e:
        print(f"执行命令时发生错误: {e}")
        return CommandResponse(success=False,
                               message=f"执行命令失败: {str(e)}",
                               timestamp=datetime.now().isoformat())


async def _monitor_accounts(config_file: str,
                            force_notify: bool = False) -> CommandResponse:
    """监控账户状态并发送通知"""
    try:
        # 爬取账户数据
        scraper = ClaudeScraper(config_file)
        data = scraper.scrape_accounts()

        if not data:
            return CommandResponse(success=False,
                                   message="账户数据爬取失败",
                                   timestamp=datetime.now().isoformat())

        # 检查限流状态
        checker = RateLimitChecker(data)
        if not checker.check_rate_limit_status():
            return CommandResponse(success=False,
                                   message="限流状态检查失败",
                                   timestamp=datetime.now().isoformat())

        # 发送通知
        try:
            notifier = create_notifier_from_config(config_file)
            if not notifier:
                return CommandResponse(success=False,
                                       message="飞书通知器初始化失败",
                                       timestamp=datetime.now().isoformat())

            # 使用批量通知方法，传入账户数据
            notification_result = notifier.send_rate_limit_notifications_batch(
                data.get('data', []), force_notify=force_notify)

            return CommandResponse(
                success=True,
                message=f"账户监控完成，通知发送: {'成功' if notification_result else '失败'}",
                data=data,
                timestamp=datetime.now().isoformat())
        except Exception as e:
            return CommandResponse(success=False,
                                   message=f"发送通知失败: {str(e)}",
                                   timestamp=datetime.now().isoformat())

    except Exception as e:
        return CommandResponse(success=False,
                               message=f"监控账户状态失败: {str(e)}",
                               timestamp=datetime.now().isoformat())


async def _monitor_api_usage(config_file: str,
                             time_range: str,
                             force_notify: bool = False) -> CommandResponse:
    """监控API使用情况并发送通知"""
    try:
        # 爬取API使用数据
        scraper = ApiKeyScraper(config_file)
        data = scraper.scrape_api_keys(time_range)

        if not data:
            return CommandResponse(success=False,
                                   message="API使用数据爬取失败",
                                   timestamp=datetime.now().isoformat())

        # 发送通知
        try:
            notifier = create_api_notifier_from_config(config_file)
            if not notifier:
                return CommandResponse(success=False,
                                       message="飞书通知器初始化失败",
                                       timestamp=datetime.now().isoformat())

            # 发送API使用情况通知
            success = notifier.send_api_usage_notification(data)

            return CommandResponse(
                success=success,
                message="API使用监控完成" if success else "API使用监控失败",
                data=data,
                timestamp=datetime.now().isoformat())
        except Exception as e:
            return CommandResponse(success=False,
                                   message=f"发送通知失败: {str(e)}",
                                   timestamp=datetime.now().isoformat())

    except Exception as e:
        return CommandResponse(success=False,
                               message=f"监控API使用情况失败: {str(e)}",
                               timestamp=datetime.now().isoformat())


async def _full_monitor(config_file: str,
                        time_range: str,
                        force_notify: bool = False) -> CommandResponse:
    """完整监控流程"""
    try:
        results = {
            "accounts": None,
            "api_usage": None,
            "notifications": {
                "accounts_sent": False,
                "api_usage_sent": False
            }
        }

        # 1. 监控账户状态并发送通知
        accounts_result = await _monitor_accounts(config_file, force_notify)
        results["accounts"] = accounts_result.dict()
        if accounts_result.success:
            results["notifications"]["accounts_sent"] = True

        # 2. 监控API使用情况并发送通知
        api_result = await _monitor_api_usage(config_file, time_range,
                                              force_notify)
        results["api_usage"] = api_result.dict()
        if api_result.success:
            results["notifications"]["api_usage_sent"] = True

        # 判断整体成功状态
        overall_success = accounts_result.success and api_result.success

        message_parts = []
        if accounts_result.success:
            message_parts.append("账户监控完成")
        else:
            message_parts.append("账户监控失败")

        if api_result.success:
            message_parts.append("API监控完成")
        else:
            message_parts.append("API监控失败")

        return CommandResponse(success=overall_success,
                               message=" | ".join(message_parts),
                               data=results,
                               timestamp=datetime.now().isoformat())

    except Exception as e:
        return CommandResponse(success=False,
                               message=f"完整监控流程失败: {str(e)}",
                               timestamp=datetime.now().isoformat())


# 简单的GET端点，通过参数验证，直接通过URL触发
@app.get("/trigger/{command}")
async def trigger_command_simple(command: str,
                                 k: Optional[str] = None,
                                 f: Optional[bool] = False):
    """
    简单触发命令的GET端点（参数验证）
    
    支持的命令：
    - monitor_accounts: 监控账户状态并发送通知
    - monitor_api_usage: 监控API使用情况并发送通知
    - full_monitor: 完整监控流程（账户+API）
    
    使用方法：
    - GET /trigger/monitor_accounts?k=your_key
    - GET /trigger/monitor_api_usage?k=your_key
    - GET /trigger/full_monitor?k=your_key
    - 添加&f=true参数强制发送通知
    """

    try:
        # 简单的参数验证
        config = load_api_config()
        expected_key = config.get("simple_key", "")
        print(expected_key)

        # 如果配置了simple_key，则需要验证
        if expected_key:
            if not k:
                print("缺少验证参数 k")
                return CommandResponse(success=False,
                                       message="缺少验证参数 k",
                                       timestamp=datetime.now().isoformat())
            if k != expected_key:
                print("验证失败：k参数不正确")
                return CommandResponse(success=False,
                                       message="验证失败：k参数不正确",
                                       timestamp=datetime.now().isoformat())

        # 如果没有配置simple_key，则允许无验证访问
        command = command.lower()

        print(f"简单触发命令: {command}")

        if command == "monitor_accounts":
            return await _monitor_accounts('config.yaml', f)

        elif command == "monitor_api_usage":
            return await _monitor_api_usage('config.yaml', 'today', f)

        elif command == "full_monitor":
            return await _full_monitor('config.yaml', 'today', f)

        else:
            return CommandResponse(
                success=False,
                message=
                f"不支持的命令: {command}. 支持的命令: monitor_accounts, monitor_api_usage, full_monitor",
                timestamp=datetime.now().isoformat())

    except Exception as e:
        print(f"执行简单触发命令时发生错误: {e}")
        return CommandResponse(success=False,
                               message=f"执行命令失败: {str(e)}",
                               timestamp=datetime.now().isoformat())


@app.get("/trigger/{command}/{config_file}")
async def trigger_command_with_config(command: str,
                                      config_file: str,
                                      k: Optional[str] = None,
                                      f: Optional[bool] = False):
    """
    简单触发命令的GET端点（参数验证，可指定配置文件）
    
    使用方法：
    - GET /trigger/monitor_accounts/custom_config.yaml?k=your_key
    - GET /trigger/monitor_api_usage/custom_config.yaml?k=your_key
    - GET /trigger/full_monitor/prod_config.yaml?k=your_key
    """

    try:
        # 简单的参数验证
        config = load_api_config()
        expected_key = config.get("simple_key", "")

        # 如果配置了simple_key，则需要验证
        if expected_key:
            if not k:
                return CommandResponse(success=False,
                                       message="缺少验证参数 k",
                                       timestamp=datetime.now().isoformat())
            if k != expected_key:
                return CommandResponse(success=False,
                                       message="验证失败：k参数不正确",
                                       timestamp=datetime.now().isoformat())
        command = command.lower()

        print(f"简单触发命令: {command}, 配置文件: {config_file}")

        if command == "monitor_accounts":
            return await _monitor_accounts(config_file, f)

        elif command == "monitor_api_usage":
            return await _monitor_api_usage(config_file, 'today', f)

        elif command == "full_monitor":
            return await _full_monitor(config_file, 'today', f)

        else:
            return CommandResponse(
                success=False,
                message=
                f"不支持的命令: {command}. 支持的命令: monitor_accounts, monitor_api_usage, full_monitor",
                timestamp=datetime.now().isoformat())

    except Exception as e:
        print(f"执行简单触发命令时发生错误: {e}")
        return CommandResponse(success=False,
                               message=f"执行命令失败: {str(e)}",
                               timestamp=datetime.now().isoformat())


def _check_feishu_app_mode() -> bool:
    """
    检查是否配置了飞书应用模式（app_id + app_secret）
    
    Returns:
        布尔值表示是否为应用模式
    """
    try:
        config_manager = create_config_manager('config.yaml')
        notification_config = config_manager.get_notification_config()
        feishu_config = notification_config.get('feishu', {})

        app_id = feishu_config.get('app_id')
        app_secret = feishu_config.get('app_secret')

        return bool(app_id and app_secret)
    except Exception:
        return False


@app.post("/")
async def feishu_callback(request: Request):
    """
    飞书回调端点
    
    处理飞书服务器发送的回调事件，包括：
    1. URL验证（challenge）- 支持明文和加密模式
    2. 交互事件处理（按钮点击）
    
    注意：回调功能仅在配置app_id和app_secret时可用
    """
    try:
        # 获取原始请求体
        request_body = await request.body()
        request_body_str = request_body.decode('utf-8')

        print(f"收到飞书回调请求")

        # 创建飞书通知器实例以处理Challenge验证
        notifier = create_notifier_from_config('config.yaml')
        if not notifier:
            print("无法创建飞书通知器实例")
            raise HTTPException(status_code=500, detail="飞书通知器配置错误")

        # 首先尝试处理Challenge请求（支持明文和加密模式）
        challenge_response = notifier.process_challenge_request(
            request_body_str)
        if challenge_response:
            print(f"返回Challenge响应: {challenge_response}")
            return challenge_response

        # 如果不是Challenge请求，继续处理其他事件
        # 检查是否为应用模式（仅限交互事件）
        if not _check_feishu_app_mode():
            print("警告：收到飞书回调请求，但当前配置为Webhook模式，交互功能不可用")
            raise HTTPException(status_code=400,
                                detail="交互功能仅在飞书应用模式（app_id + app_secret）下可用")

        # 解析JSON数据
        try:
            data = json.loads(request_body_str)
            print(f"解析飞书回调数据: {data}")
        except json.JSONDecodeError:
            print("飞书回调数据JSON解析失败")
            raise HTTPException(status_code=400, detail="无效的JSON数据")

        # 处理交互事件（按钮点击）
        if "header" in data and "event" in data:
            event_type = data["header"].get("event_type", "")

            if event_type == "im.message.receive_v1":
                print("收到消息事件")
                return {"code": 0}

            elif event_type == "card.action.trigger":
                print("收到卡片交互事件")

                # 获取交互数据
                action = data["event"].get("action", {})
                value = action.get("value", {})

                # 处理按钮点击
                if isinstance(value, dict) and "command" in value:
                    command = value["command"]
                    print(f"处理按钮命令: {command}")

                    # 异步执行监控命令
                    asyncio.create_task(handle_callback_command(command))

                    return {"code": 0, "msg": "ok", "data": {}}

        # 默认返回成功
        print("未识别的飞书回调事件，返回默认成功响应")
        return {"code": 0, "msg": "ok"}

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        print(f"处理飞书回调时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"处理回调失败: {str(e)}")


async def handle_callback_command(command: str):
    """
    处理飞书回调命令
    
    在后台异步执行监控命令，避免阻塞回调响应
    """
    try:
        print(f"开始执行回调命令: {command}")

        if command == "monitor_accounts":
            result = await _monitor_accounts('config.yaml', False)  # 回调不强制通知
            print(f"账户监控结果: {result.message}")

        elif command == "monitor_api_usage":
            result = await _monitor_api_usage('config.yaml', 'today',
                                              False)  # 回调不强制通知
            print(f"API监控结果: {result.message}")

        elif command == "full_monitor":
            result = await _full_monitor('config.yaml', 'today',
                                         False)  # 回调不强制通知
            print(f"完整监控结果: {result.message}")

        else:
            print(f"不支持的回调命令: {command}")

    except Exception as e:
        print(f"执行回调命令时发生错误: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_server:app", host="0.0.0.0", port=8000, reload=True)
