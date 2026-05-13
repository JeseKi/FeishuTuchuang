# -*- coding: utf-8 -*-
"""图床模块配置。"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ImageHostConfig(BaseSettings):
    """图床配置。"""

    feishu_app_id: str = Field(default="", title="飞书应用 App ID")
    feishu_app_secret: str = Field(default="", title="飞书应用 App Secret")
    feishu_api_base_url: str = Field(
        default="https://open.feishu.cn/open-apis",
        title="飞书开放平台 API Base URL",
    )
    feishu_oauth_scope: str = Field(
        default="offline_access drive:drive",
        title="飞书 OAuth 授权范围",
    )
    feishu_oauth_refresh_before_expiry_seconds: int = Field(
        default=3600,
        ge=60,
        title="飞书 OAuth 主动刷新提前量秒数",
    )
    cache_dir: Path = Field(
        default=Path("data") / "image_cache",
        title="图片本地缓存目录",
    )
    max_upload_mb: int = Field(default=100, ge=1, le=100, title="最大上传大小 MB")
    cache_ttl_hours: int = Field(
        default=168,
        ge=1,
        title="本地图片缓存保留小时数",
    )
    access_flush_interval_seconds: int = Field(
        default=60,
        ge=1,
        title="图片访问时间落库间隔秒数",
    )
    public_base_url: str = Field(
        default="",
        title="图床外部访问 Base URL",
        description="例如 https://img.example.com；留空时使用当前请求域名",
    )

    model_config = SettingsConfigDict(
        env_prefix="IMAGE_HOST_",
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


image_host_config = ImageHostConfig()
