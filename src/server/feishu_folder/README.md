# 模块：feishu_folder

## 公开接口
- GET `/api/feishu/folders`
- GET `/api/feishu/folders/active`
- POST `/api/feishu/folders`
- PUT `/api/feishu/folders/{folder_id}`
- DELETE `/api/feishu/folders/{folder_id}`

## 业务定位
- 管理飞书 Drive 文件夹名称与 folder token。
- 图床上传时优先使用数据库中启用的文件夹 token。
- 不在运行时从 `.env` 读取上传文件夹 token。

## 迁移
- `20260513_0007_create_feishu_folders` 创建 `feishu_folders` 表。
- 升级时会读取历史 `.env` 中的 `IMAGE_HOST_FEISHU_DRIVE_FOLDER_TOKEN`，并导入为名为“图床”的启用文件夹。
