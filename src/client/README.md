# 前端模块概览

## 公开接口
- `App`：应用入口，统一挂载路由、鉴权上下文，并在 Ant Design `ConfigProvider` 下提供现代化主题。
- `AuthProvider` / `useAuth` / `RequireAuth`：维护登录态及用户资料，暴露登录、资料更新、登出、改密等公开行为。
- `MainLayout`：受保护区域的骨架布局，内置品牌导航与用户下拉菜单。
- `LoginPage` / `ImageHostPage`：分别对接后端认证和图床管理接口，并以 Antd 表单组件承载交互流程。
- `lib/auth`、`lib/imageHost`：封装与后端的 HTTP 调用，是页面访问后端的主要入口。

## 业务逻辑
该模块通过 `AuthProvider` 驱动鉴权逻辑和用户状态同步，将登录后的用户数据传递给 `MainLayout` 与各业务页面。登录、图片上传、文件夹管理和 API Key 管理借助 Antd 组件实现校验与反馈。所有请求都统一依赖 `lib/api` 注入的 Axios 拦截器处理令牌刷新，使前端专注于业务交互与状态展示。

## 数据流
```mermaid
graph LR
    A[用户操作] --> B[页面组件 (Login/ImageHost)]
    B --> C[Antd Form 校验]
    C --> D[lib 层 API 调用]
    D -->|Axios| E[后端服务]
    E --> F[响应体]
    F --> G[AuthProvider/页面状态]
    G --> H[Antd 组件渲染]
    G --> I[消息反馈 App.message]
```

## 用法示例
```tsx
// 受保护页面中调用后端并使用 Antd 消息
import { App, Button } from 'antd'
import { useAuth } from '../providers/AuthProvider'
import { listImageAssets } from '../lib/imageHost'

export function WelcomeSection() {
  const { message } = App.useApp()
  const { user } = useAuth()

  const handleLoad = async () => {
    const result = await listImageAssets(10, 0)
    message.success(`已加载 ${result.items.length} 张图片`)
  }

  return (
    <Button type="primary" onClick={handleLoad}>
      {`欢迎回来，${user?.username ?? '访客'}`}
    </Button>
  )
}
```

## 设计原因
- 通过 Antd `ConfigProvider` 与 `App` 容器统一基础配色、圆角与消息反馈，页面间保持一致的交互密度与响应时机。
- `MainLayout` 采用 Antd `Layout`、`Dropdown`、`Avatar` 组合，既保留 Tailwind 的轻量布局能力，也能快速对接更多导航项。
- 表单、查询、通知全面引入 Antd 组件，减少自定义样式，同时确保校验与异常反馈具备可访问性标准。
- 数据交互依旧集中在 `lib` 层，便于在不影响 UI 的前提下替换或扩展后端接口，实现前后端解耦。
