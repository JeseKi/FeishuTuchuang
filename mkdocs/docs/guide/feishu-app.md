# 飞书应用

在飞书开放平台创建企业自建应用，并完成这些配置。

## 应用凭据

记录应用的 `App ID` 和 `App Secret`，分别填入：

```ini
IMAGE_HOST_FEISHU_APP_ID=飞书应用 App ID
IMAGE_HOST_FEISHU_APP_SECRET=飞书应用 App Secret
```

## 重定向地址

生产环境使用：

```text
https://img.example.com/api/images/feishu/oauth/callback
```

本地测试使用：

```text
http://localhost:8000/api/images/feishu/oauth/callback
```

## 权限

需要开通 Drive 文件上传、下载、删除、移动相关权限。

权限变更后，需要发布或启用应用权限变更，确保当前企业内可授权。
