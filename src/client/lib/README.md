# lib 模块说明

## 公开接口
- `api`：预配置的 axios 实例，负责统一的请求头追加与令牌刷新逻辑。
- `auth`：登录、注册、获取用户资料、更新资料、修改密码、登出等方法。
- `example`：示例模块的 ping、创建条目、查询条目方法。
- `tokenStorage`：浏览器端的令牌读写工具，提供获取、设置、清空与检测令牌的能力。
- `types`：前端消费接口时使用的公共类型定义。

## 业务逻辑
`lib` 目录承担“前端数据访问层”的职责，统一处理与后端 API 的通信：
- `api` 负责基础 axios 配置、请求拦截以及 401 自动刷新重试。
- `tokenStorage` 在本地缓存令牌，供请求拦截器和业务逻辑复用。
- 业务方法（`auth`、`example`）屏蔽具体 URL 与请求细节，为上层提供语义化接口。

## 数据流
1. 页面或 Provider 调用 `lib/auth`、`lib/example`。
2. 方法内部使用统一的 `api` 实例发起 HTTP 请求。
3. `api` 拦截器在请求阶段为其追加 `Authorization` 头，在响应阶段执行 401 刷新逻辑。
4. 接口返回数据直接由调用方消费，若刷新失败会触发 `tokenStorage.clearTokens`，调用方按需处理登出流程。

## 用法示例
```ts
import { login } from '../lib/auth'
import { createItem } from '../lib/example'

async function bootstrap() {
  await login({ username: 'demo', password: 'password123' })
  const item = await createItem({ name: '示例条目' })
  console.log(item)
}
```

## 设计原因
- 请求与令牌逻辑集中维护，防止在组件层出现散落的 axios 配置。
- 将接口分模块封装，使页面专注于状态与展示，便于未来扩展更多模块。
- 类型定义集中共享，避免不同文件重复声明接口结构。
