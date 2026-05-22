# 首次初始化

完成部署后，按下面步骤初始化图床。

## 登录管理后台

打开：

```text
https://img.example.com
```

使用 `.env` 中的管理员账号登录：

```ini
INIT_ADMIN_NAME=admin
INIT_ADMIN_PASSWORD=替换成强密码
```

## 完成飞书授权

进入“飞书图床”，点击飞书授权，完成 Drive OAuth 授权。

授权成功后，应用才能把图片上传到当前用户可访问的飞书 Drive。

## 配置飞书文件夹

进入“飞书文件夹”，添加可上传的 folder token。

如果没有配置飞书文件夹，系统会尝试使用 Drive 根目录；更推荐创建专用文件夹并在后台配置 folder token。

## 验证上传

上传一张图片，确认返回的公开 URL 可以访问：

```text
https://img.example.com/i/{filename}
```

如果公开 URL 不能访问，优先检查 `IMAGE_HOST_PUBLIC_BASE_URL` 和反向代理配置。
