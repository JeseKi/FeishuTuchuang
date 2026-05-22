# API Key

API Key 用于让外部工具调用图片上传接口。

网页管理接口需要登录态；外部集成接口使用 `X-API-Key` 或 `Authorization: Bearer <api_key>`。

## 接口

当前支持：

- `POST /api/v1/images`
- `POST /api/v2/images`

v2 接口支持通过 `folder_name` 指定飞书目标文件夹。文件夹名称来自：

```text
GET /api/v2/folders
```

删除图片使用：

```text
DELETE /api/v2/images/{asset_id}
```

其中 `asset_id` 来自上传响应中的 `id`。

## 上传示例

```bash
curl -X POST https://img.example.com/api/v2/images \
  -H "X-API-Key: $API_KEY" \
  -F "folder_name=default" \
  -F "image=@./demo.png"
```

也可以使用 Bearer Token：

```bash
curl -X POST https://img.example.com/api/v2/images \
  -H "Authorization: Bearer $API_KEY" \
  -F "folder_name=default" \
  -F "image=@./demo.png"
```

图片公开访问地址形如：

```text
https://img.example.com/i/{filename}
```

## 使用建议

- 给不同客户端创建不同 API Key，便于后续撤销和审计。
- 不要把 API Key 写入公开仓库。
- 如果怀疑泄露，应立即在管理台中删除旧 Key 并重新创建。
