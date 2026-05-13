# 模块：api_v2

## 公开接口
- GET `/api/v2/folders`
- POST `/api/v2/images`
- DELETE `/api/v2/images/{asset_id}`

## 业务定位
- 面向外部客户端的 v2 图床 API。
- 上传时客户端通过 `folder_name` 指定飞书目标文件夹。
- 文件夹名称来自 `GET /api/v2/folders`，响应格式为 `str[]`。
- 删除时客户端传入上传响应中的 `id`，默认删除飞书 Drive 文件、本地缓存和数据库记录。
