# providers 模块说明

## 公开接口
- `AuthProvider`：包裹应用，初始化并维护登录状态。
- `useAuth`：获取当前用户、登录/注册/登出等操作的自定义 Hook。
- `RequireAuth`：路由守卫组件，确保受保护页面在鉴权成功后渲染。

## 业务逻辑
`AuthProvider` 在应用启动时读取本地令牌并尝试获取用户资料；后续登录会刷新令牌并同步用户信息，登出则清空令牌并回收状态。所有鉴权相关的方法统一通过上下文暴露，消费方无需关心底层的 axios/令牌细节。

## 数据流
1. Provider 启动时读取 `tokenStorage` 中的令牌，若存在则调用 `lib/auth.fetchProfile`。
2. 登录/注册/更新等动作调用 `lib/auth`，成功后更新上下文中的用户数据。
3. 页面或组件通过 `useAuth` 访问用户信息或操作方法，`RequireAuth` 根据上下文判断是否放行。

## 用法示例
```tsx
import { RequireAuth, useAuth } from '../providers/AuthProvider'

function ProtectedContent() {
  const { user } = useAuth()
  return <div>当前用户：{user?.username}</div>
}

// 路由中
<Route
  path="/dashboard"
  element={
    <RequireAuth>
      <ProtectedContent />
    </RequireAuth>
  }
/>
```

## 设计原因
- 使用 React Context 可在任意层访问鉴权信息，无需层层传递属性。
- 将路由守卫抽象为组件，方便在路由配置中直观地声明受保护区域。
- Provider 内聚登录相关副作用，减少页面层的重复代码。
