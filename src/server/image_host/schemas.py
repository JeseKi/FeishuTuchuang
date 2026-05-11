# -*- coding: utf-8 -*-
"""图床接口模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

IMAGE_ASSET_ID_PATTERN = r"^[a-f0-9]{32}$"
IMAGE_FILENAME_PATTERN = r"^[a-f0-9]{32}\.[a-z0-9]{2,5}$"


class ImageAssetOut(BaseModel):
    id: str = Field(..., pattern=IMAGE_ASSET_ID_PATTERN)
    filename: str
    url: str
    feishu_image_key: str
    feishu_download_url: str
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    created_at: datetime
    last_accessed_at: datetime
    reused_existing: bool = False

    model_config = ConfigDict(from_attributes=True)


class ImageAssetListOut(BaseModel):
    items: list[ImageAssetOut]
    limit: int
    offset: int
