#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JumpServer API 基础测试用例

使用 AccessKey 签名认证方式调用 JumpServer API

配置方式 (优先级从高到低):
    1. 代码参数传入
    2. 环境变量
    3. .env 文件 (位于 examples/.env)

依赖安装:
    pip install requests drf-httpsig python-dotenv
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from httpsig.requests_auth import HTTPSignatureAuth

# 尝试导入 dotenv，如果不可用则跳过
try:
    from dotenv import load_dotenv

    # 加载 .env 文件 (从 examples 目录)
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        DOTENV_LOADED = True
    else:
        DOTENV_LOADED = False
except ImportError:
    DOTENV_LOADED = False


class JumpServerAPIClient:
    """JumpServer API 客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        org_id: Optional[str] = None,
    ):
        """
        初始化 API 客户端

        Args:
            base_url: JumpServer 服务地址
            access_key_id: AccessKey ID
            access_key_secret: AccessKey Secret
            org_id: 组织 ID (默认使用 Default 组织)
        """
        self.base_url = base_url or os.getenv(
            "JUMPSERVER_URL", "http://localhost:8080"
        )
        self.access_key_id = access_key_id or os.getenv("JUMPSERVER_ACCESS_KEY_ID", "")
        self.access_key_secret = access_key_secret or os.getenv(
            "JUMPSERVER_ACCESS_KEY_SECRET", ""
        )
        self.org_id = org_id or os.getenv(
            "JUMPSERVER_ORG_ID", "00000000-0000-0000-0000-000000000002"
        )

        # 验证配置
        if not self.access_key_id or not self.access_key_secret:
            raise ValueError(
                "请配置 AccessKey:\n"
                "  方式1: 复制 examples/.env.example 为 examples/.env 并填入值\n"
                "  方式2: 设置环境变量 JUMPSERVER_ACCESS_KEY_ID 和 JUMPSERVER_ACCESS_KEY_SECRET\n"
                "  方式3: 直接传入参数"
            )

        # HTTP Signature 签名认证
        self.auth = HTTPSignatureAuth(
            key_id=self.access_key_id,
            secret=self.access_key_secret,
            algorithm="hmac-sha256",
            headers=["(request-target)", "accept", "date", "x-jms-org"],
        )

    def _get_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            "Accept": "application/json",
            "X-JMS-ORG": self.org_id,
            "Date": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        }

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        发送 API 请求

        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE 等)
            endpoint: API 端点路径
            params: URL 查询参数
            data: 请求体数据

        Returns:
            响应 JSON 数据
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                headers=headers,
                params=params,
                json=data,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP 错误: {e}")
            print(f"响应内容: {e.response.text if e.response else '无'}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
            raise

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET 请求"""
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST 请求"""
        return self.request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PUT 请求"""
        return self.request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE 请求"""
        return self.request("DELETE", endpoint)


def test_get_users(client: JumpServerAPIClient) -> None:
    """测试获取用户列表"""
    print("\n=== 测试获取用户列表 ===")
    result = client.get("/api/v1/users/users/", params={"limit": 5})
    print(f"用户数量: {result.get('count', 0)}")
    if result.get("results"):
        print("用户列表:")
        for user in result["results"][:3]:
            print(f"  - {user.get('username')} ({user.get('name')})")


def test_get_assets(client: JumpServerAPIClient) -> None:
    """测试获取资产列表"""
    print("\n=== 测试获取资产列表 ===")
    result = client.get("/api/v1/assets/assets/", params={"limit": 5})
    print(f"资产数量: {result.get('count', 0)}")
    if result.get("results"):
        print("资产列表 (前3个):")
        for asset in result["results"][:3]:
            print(f"  - {asset.get('name')} ({asset.get('ip')})")


def test_get_user_info(client: JumpServerAPIClient) -> None:
    """测试获取当前用户信息"""
    print("\n=== 测试获取当前用户信息 ===")
    result = client.get("/api/v1/users/profile/")
    print(f"当前用户: {result.get('username')}")
    print(f"用户名: {result.get('name')}")
    print(f"邮箱: {result.get('email')}")


def main():
    """主测试函数"""
    print("=" * 50)
    print("JumpServer API 测试用例")
    print("=" * 50)

    if DOTENV_LOADED:
        print("✓ 已从 .env 文件加载配置")
    else:
        print("ℹ 未找到 .env 文件，使用环境变量或默认值")

    try:
        # 初始化客户端
        client = JumpServerAPIClient()
        print(f"\n连接到: {client.base_url}")
        print(f"使用 AccessKey: {client.access_key_id}")

        # 执行测试
        test_get_user_info(client)
        test_get_users(client)
        test_get_assets(client)

        print("\n" + "=" * 50)
        print("所有测试完成!")
        print("=" * 50)

    except ValueError as e:
        print(f"\n❌ 配置错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
