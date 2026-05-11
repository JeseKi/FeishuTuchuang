# 外部 Provider 开发规范

创建时间：2026-05-01  
更新时间：2026-05-01

## 目标

`src/server/providers` 用来隔离外部依赖服务，例如 GitHub OAuth、Google OAuth、Cloudflare Turnstile、SMTP 和示例外部 API。

provider 的核心原则是：业务代码只依赖 provider 抽象，不直接散落第三方 SDK、URL、token 交换逻辑或 mock 判断。测试和本地开发使用 mock provider 时，后端仍然发起真实的 HTTP/SMTP 请求，只是目标地址由 dev runtime config 指向本机 mock service。

## 运行方式

在 `.env` 中指定需要 mock 的 provider：

```env
APP_ENV=dev
EXTERNAL_PROVIDER_MOCK_LIST=["github_oauth","google_oauth","turnstile","mail","example_external_api"]
MOCK_PROVIDER_BACKEND_URL=http://localhost:8000
```

启动后端后，另开终端启动 mock services：

```bash
.venv/bin/python scripts/mock_provider_services.py
```

脚本会为每个 mock service 绑定随机端口，并周期性调用：

```text
POST /api/dev/providers/runtime-config
```

该 dev-only 接口把 mock service 的 `base_url`、SMTP 端口、mock key 等配置写入后端内存。前端需要读取的配置通过：

```text
GET /api/dev/providers/frontend-config
```

由后端统一提供，避免开发者手动填写随机端口。

## 目录结构

每个外部服务必须拥有独立目录。目录名按服务归属或供应商命名，具体能力放在文件名中：

```text
src/server/providers/
├── base.py                  # provider 基类与通用类型
├── constants.py             # provider key 与注册元数据
├── service.py               # provider registry / factory
├── runtime.py               # dev runtime config 内存存储
├── router.py                # dev-only runtime config 路由
├── mock_server.py           # mock service 公共工具
├── github/
│   ├── oauth.py             # GitHub OAuth real/mock provider
│   ├── server.py            # GitHub OAuth mock service
│   └── README.md
├── google/
│   ├── oauth.py
│   ├── server.py
│   └── README.md
├── cloudflare/
│   ├── turnstile.py
│   ├── server.py
│   └── README.md
├── smtp/
│   ├── mail.py
│   ├── server.py
│   └── README.md
└── example_external_api/
    ├── api.py
    ├── server.py
    └── README.md
```

新增服务时不要把多个外部服务混在一个文件里。推荐结构：

```text
providers/{vendor}/{capability}.py
providers/{vendor}/server.py
providers/{vendor}/README.md
```

例如：

```text
providers/stripe/payment.py
providers/stripe/server.py
providers/stripe/README.md
```

## Provider 抽象

所有 provider 都应继承或间接继承 `ExternalProvider`：

```python
class ExternalProvider(ABC):
    key: str
    label: str
    kind: str
    implementation: Literal["real", "mock"]

    @abstractmethod
    def is_configured(self) -> bool:
        ...
```

开发具体 provider 时，建议先定义该服务自己的抽象基类，再分别实现 real/mock：

```python
class ExampleProvider(ExternalProvider):
    @abstractmethod
    def fetch_status(self) -> ExampleExternalStatus:
        ...


class RealExampleProvider(ExampleProvider):
    implementation = "real"


class MockExampleProvider(ExampleProvider):
    implementation = "mock"
```

业务模块只调用 `get_xxx_provider()`，不直接实例化 `RealXxxProvider` 或 `MockXxxProvider`。

## Real 与 Mock 职责

real provider：

- 读取真实环境变量或配置对象。
- 按官方 API 文档构造请求。
- 设置合理 timeout。
- 对 HTTP provider 使用结构化 JSON 解析，不靠字符串拼接解析响应。
- 将第三方错误转换成本项目可处理的异常或返回值。

mock provider：

- 不在 provider 方法里直接返回假数据。
- 从 `runtime.py` 读取 mock service 推送的配置。
- 使用和 real provider 相同或尽量接近的协议发起真实请求，例如 HTTP、SMTP。
- 只实现当前后端实际用到的第三方端点和字段。
- mock token、mock user、mock response 的行为应写入该 provider 子目录 README。

如果外部服务需要浏览器参与，例如 OAuth 授权页、Turnstile widget、邮件 inbox，mock service 应提供最小可用前端页面，而不是侵入业务前端页面。

## 新增 Provider Checklist

新增一个 provider 时，应完成以下事项：

1. 在 `constants.py` 增加稳定的 provider key 和 `ProviderDefinition`。
2. 新建独立目录，例如 `providers/vendor/`。
3. 在目录中实现 `{capability}.py`，包含服务级抽象、real provider、mock provider。
4. 在目录中实现 `server.py`，提供本地 mock service 的 `start() -> RunningMockService`。
5. 在 `service.py` 注册 factory，例如 `get_vendor_provider()`。
6. 如果需要真实配置，在 `src/server/config.py` 和 `.env.example` 增加配置项。
7. 如果 mock service 需要由一键脚本启动，在 `scripts/mock_provider_services.py` 的 `SERVICE_MODULES` 中注册。
8. 如果前端需要 dev runtime 配置，在 `router.py` 的 `frontend-config` 中暴露必要字段。
9. 在对应业务模块中通过 `get_vendor_provider()` 使用 provider。
10. 增加测试，覆盖 real/mock provider 的关键行为和业务模块调用路径。
11. 添加 `providers/vendor/README.md`，记录官方文档、mock service 行为、创建/更新时间。

## Mock Service 规范

mock service 是独立本地服务，不应依赖后端进程内部状态。`server.py` 必须提供：

```python
def start() -> RunningMockService:
    ...
```

返回值应包含：

- `provider_key`：必须等于 `constants.py` 中注册的 key。
- `name`：便于脚本输出的人类可读名称。
- `config`：需要推送给后端的 runtime config。
- `shutdown`：停止 mock service 的回调。

HTTP mock service 优先使用 `start_http_mock_service()`。非 HTTP 服务可以直接使用 `RunningMockService`，但也必须绑定随机本地端口，不能要求开发者手动分配端口。

mock service 可以把数据存储在进程内存中。重启后清空是预期行为。需要人工查看的数据应提供本地 UI，例如 SMTP mock 的 inbox 页面。

## Runtime Config 规范

runtime config 只用于 dev 和测试场景，存储在内存中：

- 重启后端后会丢失。
- 由 `scripts/mock_provider_services.py` 周期性重新推送。
- 只在 `APP_ENV=dev` 下开放写入路由。
- provider 读取时必须使用 `get_provider_runtime_config(provider_key)`。

runtime config 中可以包含：

- mock service `base_url`
- mock API key / site key
- mock SMTP host / port
- 仅本地 UI 使用的 URL，例如 `inbox_url`

不要把生产 secret、长期 token 或用户真实凭据写入 runtime config。

## 文档规范

根 README 只说明 provider 的开发规范和统一运行方式。每个 provider 子目录必须维护自己的 README，并包含：

- provider 名称。
- 创建时间和更新时间。
- real provider 文件位置。
- mock service 文件位置。
- mock service 已实现的端点、页面或协议行为。
- 与官方文档的差异或未实现范围。
- 官方文档地址；如果是项目内示例服务，应明确写明没有外部官方文档。

当前 provider 文档：

- [github/README.md](./github/README.md)
- [google/README.md](./google/README.md)
- [cloudflare/README.md](./cloudflare/README.md)
- [smtp/README.md](./smtp/README.md)
- [example_external_api/README.md](./example_external_api/README.md)

## 测试规范

测试应验证“业务代码通过 provider 发起真实协议请求”这一点：

- HTTP provider 测试应启动本地 mock HTTP server，再让 provider 通过 `base_url` 请求它。
- SMTP provider 测试应启动本地 mock SMTP server，再让邮件服务通过 `smtplib` 发送邮件。
- OAuth provider 测试应覆盖 authorize URL、callback token exchange、userinfo 获取和用户绑定路径。
- Turnstile provider 测试应覆盖 action 校验、成功 token、失败 token。
- 测试结束后必须清理 runtime config，避免影响后续用例。

后端测试命令：

```bash
.venv/bin/python -m pytest . -q
```

类型和格式检查：

```bash
.venv/bin/ruff check --fix
.venv/bin/mypy .
```

## 实现约束

- 不要在业务模块中写 `if provider_key in EXTERNAL_PROVIDER_MOCK_LIST`，mock/real 选择只应存在于 provider registry。
- 不要在业务前端中硬编码 mock service 随机端口；需要浏览器配置时从后端 dev runtime config 读取。
- 不要为 mock 模式增加绕过真实调用路径的兼容性补丁。
- 不要在 provider 内吞掉第三方错误后返回误导性的成功结果。
- 不要让 mock service 依赖固定端口，避免本地并行开发和测试冲突。
- 如果官方文档定义了字段名、状态码或错误格式，应尽量按官方形状实现 mock response。
