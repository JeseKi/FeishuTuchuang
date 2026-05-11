# Example External API Provider

创建时间：2026-05-01  
更新时间：2026-05-01

## Provider

- Provider key: `example_external_api`
- Real provider: `api.py`
- Mock service: `server.py`
- 后端请求协议：HTTP

## Mock Service

mock service 实现模板项目示例外部 API：

- `GET /status`

后端在 mock 模式下仍然通过 HTTP 调用该端点，并把响应映射为 `ExampleExternalStatus`。

## 官方文档

这是模板项目内置的示例服务，没有外部官方文档。
