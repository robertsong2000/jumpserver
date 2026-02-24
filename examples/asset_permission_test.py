#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JumpServer 资产授权 API 测试用例

演示如何通过 API 进行资产授权和回收操作

配置方式: 使用与 api_test.py 相同的配置 (.env 文件或环境变量)

依赖安装:
    pip install requests drf-httpsig python-dotenv

使用方式:
    # 运行所有测试
    python examples/asset_permission_test.py

    # 运行单个测试
    python examples/asset_permission_test.py --test list
    python examples/asset_permission_test.py --test create --user-id <user-id> --asset-id <asset-id>
    python examples/asset_permission_test.py --test get --permission-id <permission-id>

    # 查看可用测试
    python examples/asset_permission_test.py --help
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
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

    def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PATCH 请求"""
        return self.request("PATCH", endpoint, data=data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE 请求"""
        return self.request("DELETE", endpoint)


# ============================================================================
# 测试函数
# ============================================================================

def test_get_users(client: JumpServerAPIClient, username: Optional[str] = None, show_all: bool = False) -> Optional[str]:
    """获取用户列表，返回第一个用户的 ID"""
    print("\n=== 获取用户列表 ===")

    if show_all:
        params = {"limit": 9999}
    else:
        params = {"limit": 20}

    if username:
        params["username"] = username

    result = client.get("/api/v1/users/users/", params=params)
    users = result.get("results", [])

    if not users:
        print("未找到用户")
        return None

    print(f"用户数量: {result.get('count', 0)}")

    for user in users:
        print(f"  - {user.get('username')} ({user.get('name')}) | ID: {user.get('id')}")

    return users[0].get("id")


def test_get_assets(client: JumpServerAPIClient, name: Optional[str] = None, show_all: bool = False) -> Optional[str]:
    """获取资产列表，返回第一个资产的 ID"""
    print("\n=== 获取资产列表 ===")

    # 获取所有资产
    if show_all:
        params = {"limit": 9999}
    else:
        params = {"limit": 20}

    if name:
        params["search"] = name

    result = client.get("/api/v1/assets/assets/", params=params)
    assets = result.get("results", [])

    if not assets:
        print("未找到资产")
        return None

    print(f"资产数量: {result.get('count', 0)}")

    # 显示所有资产
    for asset in assets:
        print(f"  - {asset.get('name')} ({asset.get('address')}) | ID: {asset.get('id')}")

    return assets[0].get("id")


def test_get_user_groups(client: JumpServerAPIClient, name: Optional[str] = None, show_all: bool = False) -> Optional[str]:
    """获取用户组列表，返回第一个用户组的 ID"""
    print("\n=== 获取用户组列表 ===")

    if show_all:
        params = {"limit": 9999}
    else:
        params = {"limit": 20}

    if name:
        params["search"] = name

    result = client.get("/api/v1/users/groups/", params=params)
    groups = result.get("results", [])

    if not groups:
        print("未找到用户组")
        return None

    print(f"用户组数量: {result.get('count', 0)}")

    for group in groups:
        print(f"  - {group.get('name')} | ID: {group.get('id')}")

    return groups[0].get("id")


def test_get_nodes(client: JumpServerAPIClient, show_all: bool = False) -> Optional[str]:
    """获取资产节点列表，返回第一个节点的 ID"""
    print("\n=== 获取资产节点列表 ===")

    if show_all:
        params = {"limit": 9999}
    else:
        params = {"limit": 20}

    result = client.get("/api/v1/assets/nodes/", params=params)
    nodes = result.get("results", [])

    if not nodes:
        print("未找到节点")
        return None

    print(f"节点数量: {result.get('count', 0)}")

    for node in nodes:
        print(f"  - {node.get('full_name')} | ID: {node.get('id')}")

    return nodes[0].get("id")


def test_create_asset_permission(
    client: JumpServerAPIClient,
    name: str,
    user_id: str,
    asset_id: str,
    actions: Optional[list[str]] = None,
) -> str:
    """
    创建资产授权规则

    Args:
        client: API 客户端
        name: 授权规则名称
        user_id: 用户 ID
        asset_id: 资产 ID
        actions: 授权动作列表 (默认全部)

    Returns:
        创建的授权规则 ID
    """
    print("\n=== 创建资产授权规则 ===")

    if actions is None:
        actions = ["connect", "upload", "download"]

    # 计算过期时间 (30天后)
    date_expired = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    data = {
        "name": name,
        "users": [user_id],
        "assets": [asset_id],
        "actions": actions,
        "accounts": ["@ALL"],  # 允许使用所有账号
        "protocols": ["all"],  # 允许所有协议
        "date_expired": date_expired,
        "is_active": True,
        "comment": "通过 API 创建的测试授权规则",
    }

    print(f"授权名称: {name}")
    print(f"用户 ID: {user_id}")
    print(f"资产 ID: {asset_id}")
    print(f"授权动作: {', '.join(actions)}")
    print(f"过期时间: {date_expired}")

    result = client.post("/api/v1/perms/asset-permissions/", data)

    print(f"✓ 授权规则创建成功!")
    print(f"  规则 ID: {result.get('id')}")
    print(f"  用户数: {result.get('users_amount')}")
    print(f"  资产数: {result.get('assets_amount')}")

    return result.get("id")


def test_list_asset_permissions(client: JumpServerAPIClient, show_all: bool = False) -> None:
    """查询资产授权规则列表"""
    print("\n=== 查询资产授权规则列表 ===")

    if show_all:
        params = {"limit": 9999}
    else:
        params = {"limit": 20}

    result = client.get("/api/v1/perms/asset-permissions/", params=params)

    permissions = result.get("results", [])
    print(f"授权规则数量: {result.get('count', 0)}")

    for perm in permissions:
        status = "✓ 激活" if perm.get('is_active') else "✗ 禁用"
        print(f"\n  [{status}] {perm.get('name')}")
        print(f"    ID: {perm.get('id')}")
        print(f"    用户数: {perm.get('users_amount')} | 资产数: {perm.get('assets_amount')}")
        print(f"    有效期: {perm.get('date_start')} ~ {perm.get('date_expired')}")


def test_get_asset_permission(client: JumpServerAPIClient, permission_id: str) -> None:
    """查询单个授权规则详情"""
    print(f"\n=== 查询授权规则详情 ===")
    result = client.get(f"/api/v1/perms/asset-permissions/{permission_id}/")

    print(f"规则名称: {result.get('name')}")
    print(f"规则 ID: {result.get('id')}")
    print(f"用户数: {result.get('users_amount')}")
    print(f"用户组数: {result.get('user_groups_amount')}")
    print(f"资产数: {result.get('assets_amount')}")
    print(f"节点数: {result.get('nodes_amount')}")
    print(f"动作: {result.get('actions')}")
    print(f"账号: {result.get('accounts')}")
    print(f"协议: {result.get('protocols')}")
    print(f"状态: {'激活' if result.get('is_active') else '禁用'}")
    print(f"是否有效: {result.get('is_valid')}")
    print(f"是否过期: {result.get('is_expired')}")


def test_update_asset_permission(
    client: JumpServerAPIClient,
    permission_id: str,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    comment: Optional[str] = None,
) -> None:
    """更新资产授权规则"""
    print(f"\n=== 更新资产授权规则 ===")

    data = {}
    if name is not None:
        data["name"] = name
    if is_active is not None:
        data["is_active"] = is_active
    if comment is not None:
        data["comment"] = comment

    if not data:
        print("没有需要更新的字段")
        return

    result = client.patch(f"/api/v1/perms/asset-permissions/{permission_id}/", data)

    print(f"✓ 授权规则更新成功!")
    print(f"  规则名称: {result.get('name')}")
    print(f"  状态: {'激活' if result.get('is_active') else '禁用'}")


def test_disable_asset_permission(client: JumpServerAPIClient, permission_id: str) -> None:
    """禁用资产授权规则"""
    print(f"\n=== 禁用资产授权规则 ===")
    test_update_asset_permission(
        client,
        permission_id,
        is_active=False,
        comment="已通过 API 禁用",
    )


def test_enable_asset_permission(client: JumpServerAPIClient, permission_id: str) -> None:
    """启用资产授权规则"""
    print(f"\n=== 启用资产授权规则 ===")
    test_update_asset_permission(
        client,
        permission_id,
        is_active=True,
        comment="已通过 API 启用",
    )


def test_delete_asset_permission(client: JumpServerAPIClient, permission_id: str) -> None:
    """
    删除资产授权规则 (永久回收)

    警告: 此操作不可逆
    """
    print(f"\n=== 删除资产授权规则 ===")
    print(f"警告: 此操作将永久删除授权规则 {permission_id}")
    client.delete(f"/api/v1/perms/asset-permissions/{permission_id}/")
    print("✓ 授权规则已删除")


def test_get_permission_assets(client: JumpServerAPIClient, permission_id: str, show_all: bool = False) -> None:
    """获取授权规则中的所有资产"""
    print(f"\n=== 获取授权规则中的资产 ===")

    if show_all:
        params = {"limit": 9999}
    else:
        params = {"limit": 20}

    result = client.get(f"/api/v1/perms/asset-permissions/{permission_id}/assets/all/", params=params)

    assets = result.get("results", [])
    print(f"授权资产数量: {result.get('count', 0)}")

    for asset in assets:
        # API 返回字段: asset (UUID), asset_display (显示名称)
        asset_id = asset.get('asset')
        asset_display = asset.get('asset_display', '')
        print(f"  - {asset_display} | ID: {asset_id}")


def test_get_permission_users(client: JumpServerAPIClient, permission_id: str, show_all: bool = False) -> None:
    """获取授权规则中的所有用户"""
    print(f"\n=== 获取授权规则中的用户 ===")

    if show_all:
        params = {"limit": 9999}
    else:
        params = {"limit": 20}

    result = client.get(f"/api/v1/perms/asset-permissions/{permission_id}/users/all/", params=params)

    users = result.get("results", [])
    print(f"授权用户数量: {result.get('count', 0)}")

    for user in users:
        # API 返回字段: user (UUID), user_display (显示名称)
        user_id = user.get('user')
        user_display = user.get('user_display', '')
        print(f"  - {user_display} | ID: {user_id}")


# ============================================================================
# 主程序
# ============================================================================

def run_all_tests(client: JumpServerAPIClient) -> None:
    """运行所有测试 (完整流程)"""
    print("=" * 60)
    print("运行所有测试 - 完整授权流程")
    print("=" * 60)

    # 1. 查询现有数据
    print("\n" + "=" * 60)
    print("步骤 1: 查询现有用户和资产")
    print("=" * 60)

    user_id = test_get_users(client)
    if not user_id:
        print("❌ 未找到用户，请先创建用户")
        return

    asset_id = test_get_assets(client)
    if not asset_id:
        print("❌ 未找到资产，请先创建资产")
        return

    # 2. 创建资产授权
    print("\n" + "=" * 60)
    print("步骤 2: 创建资产授权规则")
    print("=" * 60)

    permission_name = f"API测试授权-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    permission_id = test_create_asset_permission(
        client,
        name=permission_name,
        user_id=user_id,
        asset_id=asset_id,
        actions=["connect", "upload", "download"],
    )

    # 3. 查询授权规则列表
    print("\n" + "=" * 60)
    print("步骤 3: 查询授权规则列表")
    print("=" * 60)
    test_list_asset_permissions(client)

    # 4. 查询授权规则详情
    print("\n" + "=" * 60)
    print("步骤 4: 查询授权规则详情")
    print("=" * 60)
    test_get_asset_permission(client, permission_id)

    # 5. 查询授权的资产和用户
    print("\n" + "=" * 60)
    print("步骤 5: 查询授权的资产和用户")
    print("=" * 60)
    test_get_permission_assets(client, permission_id)
    test_get_permission_users(client, permission_id)

    # 6. 禁用授权规则
    print("\n" + "=" * 60)
    print("步骤 6: 禁用授权规则")
    print("=" * 60)
    test_disable_asset_permission(client, permission_id)

    # 完成
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
    print(f"\n创建的授权规则:")
    print(f"  - ID: {permission_id}")
    print(f"  - 名称: {permission_name}")
    print("  - 状态: 已禁用")
    print("=" * 60)


def create_client() -> JumpServerAPIClient:
    """创建 API 客户端"""
    return JumpServerAPIClient()


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="JumpServer 资产授权 API 测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有测试
  %(prog)s

  # 查询用户列表
  %(prog)s --test users

  # 查询资产列表
  %(prog)s --test assets

  # 查询用户组
  %(prog)s --test groups

  # 查询节点
  %(prog)s --test nodes

  # 查询授权规则列表
  %(prog)s --test list

  # 创建授权规则
  %(prog)s --test create --user-id <user-id> --asset-id <asset-id> --name "测试授权"

  # 查询授权规则详情
  %(prog)s --test get --permission-id <permission-id>

  # 启用授权规则
  %(prog)s --test enable --permission-id <permission-id>

  # 禁用授权规则
  %(prog)s --test disable --permission-id <permission-id>

  # 删除授权规则
  %(prog)s --test delete --permission-id <permission-id>

  # 查询授权的资产
  %(prog)s --test assets --permission-id <permission-id>

  # 查询授权的用户
  %(prog)s --test users --permission-id <permission-id>
        """
    )

    parser.add_argument(
        "--test", "-t",
        choices=[
            "all", "users", "assets", "groups", "nodes",
            "list", "create", "get", "enable", "disable", "delete",
            "perm-assets", "perm-users"
        ],
        help="要运行的测试"
    )

    parser.add_argument("--user-id", help="用户 ID")
    parser.add_argument("--asset-id", help="资产 ID")
    parser.add_argument("--permission-id", help="授权规则 ID")
    parser.add_argument("--name", help="授权规则名称")
    parser.add_argument("--username", help="用户名 (用于查询)")
    parser.add_argument("--asset-name", help="资产名称 (用于查询)")
    parser.add_argument("--all", "-a", action="store_true", help="显示所有结果 (不限制数量)")

    return parser.parse_args()


def main():
    """主测试函数"""
    args = parse_args()

    print("=" * 60)
    print("JumpServer 资产授权 API 测试")
    print("=" * 60)

    if DOTENV_LOADED:
        print("✓ 已从 .env 文件加载配置")
    else:
        print("ℹ 未找到 .env 文件，使用环境变量或默认值")

    try:
        # 初始化客户端
        client = create_client()
        print(f"\n连接到: {client.base_url}")
        print(f"使用 AccessKey: {client.access_key_id}")

        # 根据参数运行相应测试
        test = args.test

        if test == "all":
            run_all_tests(client)

        elif test == "users":
            test_get_users(client, args.username, show_all=args.all)

        elif test == "assets":
            test_get_assets(client, args.asset_name, show_all=args.all)

        elif test == "groups":
            test_get_user_groups(client, show_all=args.all)

        elif test == "nodes":
            test_get_nodes(client, show_all=args.all)

        elif test == "list":
            test_list_asset_permissions(client, show_all=args.all)

        elif test == "create":
            if not args.user_id or not args.asset_id:
                print("❌ 创建授权需要 --user-id 和 --asset-id 参数")
                sys.exit(1)
            name = args.name or f"API授权-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            permission_id = test_create_asset_permission(
                client, name=name, user_id=args.user_id, asset_id=args.asset_id
            )
            print(f"\n创建的授权规则 ID: {permission_id}")

        elif test == "get":
            if not args.permission_id:
                print("❌ 需要 --permission-id 参数")
                sys.exit(1)
            test_get_asset_permission(client, args.permission_id)

        elif test == "enable":
            if not args.permission_id:
                print("❌ 需要 --permission-id 参数")
                sys.exit(1)
            test_enable_asset_permission(client, args.permission_id)

        elif test == "disable":
            if not args.permission_id:
                print("❌ 需要 --permission-id 参数")
                sys.exit(1)
            test_disable_asset_permission(client, args.permission_id)

        elif test == "delete":
            if not args.permission_id:
                print("❌ 需要 --permission-id 参数")
                sys.exit(1)
            test_delete_asset_permission(client, args.permission_id)

        elif test == "perm-assets":
            if not args.permission_id:
                print("❌ 需要 --permission-id 参数")
                sys.exit(1)
            test_get_permission_assets(client, args.permission_id, show_all=args.all)

        elif test == "perm-users":
            if not args.permission_id:
                print("❌ 需要 --permission-id 参数")
                sys.exit(1)
            test_get_permission_users(client, args.permission_id, show_all=args.all)

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)

    except ValueError as e:
        print(f"\n❌ 配置错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
