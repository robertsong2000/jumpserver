# JumpServer API 测试用例示例

本目录包含 JumpServer Open API 调用的测试用例示例。

## 目录结构

```
examples/
├── .env.example         # 配置文件模板
├── README.md            # 本文件
└── api_test.py          # AccessKey 签名认证测试
```

## 快速开始

### 1. 创建 AccessKey

在 JumpServer Web 界面中创建 AccessKey：

1. 登录 JumpServer
2. 点击右上角头像 → **用户设置**
3. 选择左侧菜单 **AccessKey**
4. 点击 **创建 AccessKey**
5. 保存显示的 `AccessKeyID` 和 `AccessKeySecret`

### 2. 配置环境 (推荐使用 .env 文件)

```bash
# 复制配置模板
cp examples/.env.example examples/.env

# 编辑 .env 文件，填入实际值
# JUMPSERVER_URL=http://localhost:8080
# JUMPSERVER_ACCESS_KEY_ID=your-access-key-id
# JUMPSERVER_ACCESS_KEY_SECRET=your-access-key-secret
```

### 3. 安装依赖

```bash
pip install requests drf-httpsig python-dotenv
```

### 4. 运行测试

```bash
python examples/api_test.py
```

## 配置方式 (优先级从高到低)

1. **代码参数传入** - 直接在代码中指定
2. **环境变量** - 使用 `export` 设置环境变量
3. **.env 文件** - 从 `examples/.env` 文件读取 (推荐)

### 方式一：使用 .env 文件 (推荐)

```bash
# 1. 复制配置模板
cp examples/.env.example examples/.env

# 2. 编辑 .env 文件
vim examples/.env
```

.env 文件内容：
```bash
JUMPSERVER_URL=http://localhost:8080
JUMPSERVER_ACCESS_KEY_ID=your-access-key-id-here
JUMPSERVER_ACCESS_KEY_SECRET=your-access-key-secret-here
JUMPSERVER_ORG_ID=00000000-0000-0000-0000-000000000002
```

```bash
# 3. 运行测试
python examples/api_test.py
```

### 方式二：使用环境变量

```bash
export JUMPSERVER_URL=http://localhost:8080
export JUMPSERVER_ACCESS_KEY_ID=<your-access-key-id>
export JUMPSERVER_ACCESS_KEY_SECRET=<your-access-key-secret>
export JUMPSERVER_ORG_ID=00000000-0000-0000-0000-000000000002

python examples/api_test.py
```

### 方式三：直接修改代码

```python
from examples.api_test import JumpServerAPIClient

client = JumpServerAPIClient(
    base_url="http://localhost:8080",
    access_key_id="<your-access-key-id>",
    access_key_secret="<your-access-key-secret>",
    org_id="00000000-0000-0000-0000-000000000002"
)
```

## 测试用例

`api_test.py` 包含以下测试用例：

| 测试函数 | API 端点 | 说明 |
|---------|----------|------|
| `test_get_user_info` | `/api/v1/users/profile/` | 获取当前用户信息 |
| `test_get_users` | `/api/v1/users/users/` | 获取用户列表 |
| `test_get_assets` | `/api/v1/assets/assets/` | 获取资产列表 |

## API 认证方式

### AccessKey 签名认证 (推荐)

```python
from httpsig.requests_auth import HTTPSignatureAuth

auth = HTTPSignatureAuth(
    key_id=KEY_ID,
    secret=SECRET,
    algorithm='hmac-sha256',
    headers=['(request-target)', 'accept', 'date', 'x-jms-org']
)
```

## API 文档

- **Swagger UI**: `http://<your-jumpserver>/api/swagger/`
- **ReDoc**: `http://<your-jumpserver>/api/redoc/`
- **在线文档**: https://jumpserver.com/docs

## 常见问题

### Q: 如何获取组织 ID (ORG_ID)?

A: 默认组织 ID 为 `00000000-0000-0000-0000-000000000002`。如需使用其他组织，请从 JumpServer 管理界面获取。

### Q: 签名认证失败怎么办?

A: 请检查：
1. 系统时间是否同步
2. AccessKey ID 和 Secret 是否正确
3. 请求头中是否包含必需的签名字段

### Q: .env 文件不生效?

A: 请确保：
1. 已安装 `python-dotenv`: `pip install python-dotenv`
2. .env 文件位于 `examples/` 目录下
3. .env 文件格式正确（无引号、无多余空格）

### Q: 如何调试 API 请求?

A: 添加日志输出：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 扩展阅读

- [JumpServer REST API 文档](https://jumpserver.com/docs)
- [HTTP Signature 规范](https://datatracker.ietf.org/doc/html/draft-cavage-http-signatures)
