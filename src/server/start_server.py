#!/usr/bin/env python3
"""
FastAPI服务器启动脚本
"""

import uvicorn
import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='启动Claude监控API服务器')
    parser.add_argument('--host', default='0.0.0.0', help='绑定主机地址')
    parser.add_argument('--port', type=int, default=8155, help='绑定端口')
    parser.add_argument('--reload', action='store_true', help='启用热重载（开发模式）')
    parser.add_argument('--workers', type=int, default=1, help='工作进程数')

    args = parser.parse_args()

    # 确保数据目录存在
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    print(f"启动Claude监控API服务器...")
    print(f"地址: http://{args.host}:{args.port}")
    print(f"文档: http://{args.host}:{args.port}/docs")
    print(f"健康检查: http://{args.host}:{args.port}/health")

    uvicorn.run("src.server.fastapi_server:app",
                host=args.host,
                port=args.port,
                reload=args.reload,
                workers=args.workers if not args.reload else 1)


if __name__ == "__main__":
    main()
