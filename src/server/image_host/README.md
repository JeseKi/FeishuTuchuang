# 模块：image_host

## 公开接口
- POST `/api/images`
- GET `/api/images`
- GET `/i/{filename}`

## 业务定位
- 以飞书 Drive 文件接口作为冷存储。
- 以本机磁盘作为热缓存。
- 对外提供本站稳定图片 URL。

## 数据流
- 上传：路由 -> 登录校验 -> MIME/大小校验 -> hash 去重 -> 飞书 Drive 上传 -> 本地缓存 -> SQLite 元数据。
- 访问：公开 URL -> SQLite 元数据 -> 本地缓存命中直接返回 -> 缺失时从飞书下载并回填缓存。

## 环境变量
- `IMAGE_HOST_FEISHU_APP_ID`
- `IMAGE_HOST_FEISHU_APP_SECRET`
- `IMAGE_HOST_CACHE_DIR`，默认 `data/image_cache`
- `IMAGE_HOST_MAX_UPLOAD_MB`，默认 `100`
- `IMAGE_HOST_CACHE_TTL_HOURS`，默认 `168`
- `IMAGE_HOST_PUBLIC_BASE_URL`，例如 `https://img.example.com`

飞书上传目录通过 `/api/feishu/folders` 写入数据库管理；迁移
`20260513_0007` 会把历史 `.env` 中的 `IMAGE_HOST_FEISHU_DRIVE_FOLDER_TOKEN`
导入为名为“图床”的启用文件夹。

## 飞书 Drive 权限
- 上传：`POST /drive/v1/files/upload_all`
- 下载：`GET /drive/v1/files/{file_token}/download`
- 删除：`DELETE /drive/v1/files/{file_token}?type=file`

应用需要开通 Drive 文件上传、下载和管理相关权限。企业自建应用使用
`tenant_access_token` 时，建议在飞书云空间创建专用文件夹，再通过飞书
文件夹管理接口配置 folder token。

## 用法示例
```bash
curl "http://localhost:8000/api/images?filename=demo&feishu_file_token={file_token}" \
  -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:8000/api/images \
  -H "Authorization: Bearer $TOKEN" \
  -F "folder_id=1" \
  -F "image=@./demo.png"

curl http://localhost:8000/i/{filename}
```
