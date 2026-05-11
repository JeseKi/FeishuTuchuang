# 模块：image_host

## 公开接口
- POST `/api/images`
- GET `/i/{filename}`

## 业务定位
- 以飞书 IM 图片接口作为冷存储。
- 以本机磁盘作为热缓存。
- 对外提供本站稳定图片 URL。

## 数据流
- 上传：路由 -> 登录校验 -> MIME/大小校验 -> hash 去重 -> 飞书上传 -> 本地缓存 -> SQLite 元数据。
- 访问：公开 URL -> SQLite 元数据 -> 本地缓存命中直接返回 -> 缺失时从飞书下载并回填缓存。

## 环境变量
- `IMAGE_HOST_FEISHU_APP_ID`
- `IMAGE_HOST_FEISHU_APP_SECRET`
- `IMAGE_HOST_CACHE_DIR`，默认 `data/image_cache`
- `IMAGE_HOST_MAX_UPLOAD_MB`，默认 `10`
- `IMAGE_HOST_PUBLIC_BASE_URL`，例如 `https://img.example.com`

## 用法示例
```bash
curl -X POST http://localhost:8000/api/images \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@./demo.png"

curl http://localhost:8000/i/{filename}
```
