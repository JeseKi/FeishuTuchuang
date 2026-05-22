# 飞书应用

在[飞书开放平台](https://open.feishu.cn/app?lang=zh-CN)创建企业自建应用，并完成这些配置。

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

### 添加应用能力

该应用需要机器人能力，因此需要在 `添加应用能力` 这里，选择 `机器人`，并进行添加：

![机器人能力添加](https://fstc.kispace.cc/i/639ac0ada73d55d12541edb6b5082023.png)

### 开通所需权限

除了机器人能力以外，也需要对应的权限：

![权限入口布局](https://fstc.kispace.cc/i/6e55b5e3c8d8b00d17ddb9a1122a7570.png)

我们需要 `drive:drive` 的权限，应用身份而权限和用户身份权限这里都要开启。

![权限列表](https://fstc.kispace.cc/i/a10471333a75812890dca1475bfa4cc3.png)

除此之外，我们还需要 `offline_access` 这一用户身份权限：

![离线访问权限](https://fstc.kispace.cc/i/bed4d0c6d9125d32d3e18cd15f70cc81.png)

以上三个权限均开启，并正确配置了重定向地址后，应用才能正常工作。