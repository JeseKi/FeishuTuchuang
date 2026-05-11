# -*- coding: utf-8 -*-
"""图床存储后端。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

import httpx
from fastapi import HTTPException, status

from .config import image_host_config


class ImageStorageBackend(Protocol):
    async def put_image(
        self, *, content: bytes, filename: str, mime_type: str
    ) -> str:
        """上传图片并返回后端资源 key。"""
        ...

    async def get_image(self, image_key: str) -> bytes:
        """按后端资源 key 下载图片内容。"""
        ...


@dataclass
class _TenantToken:
    value: str
    expires_at: float


class FeishuImageStorageBackend:
    """基于飞书 IM 图片 API 的冷存储后端。"""

    def __init__(self) -> None:
        self._token: _TenantToken | None = None

    async def put_image(
        self, *, content: bytes, filename: str, mime_type: str
    ) -> str:
        token = await self._get_tenant_access_token()
        url = f"{self._base_url}/im/v1/images"
        files = {
            "image": (filename, content, mime_type),
        }
        data = {"image_type": "message"}
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, data=data, files=files, headers=headers)

        payload = self._json_or_error(response, "飞书图片上传失败")
        image_key = payload.get("data", {}).get("image_key")
        if not image_key:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="飞书图片上传响应缺少 image_key",
            )
        return str(image_key)

    async def get_image(self, image_key: str) -> bytes:
        token = await self._get_tenant_access_token()
        url = f"{self._base_url}/im/v1/images/{image_key}"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"飞书图片下载失败：HTTP {response.status_code}",
            )
        return response.content

    async def _get_tenant_access_token(self) -> str:
        now = time.time()
        if self._token and self._token.expires_at > now + 60:
            return self._token.value

        if not image_host_config.feishu_app_id or not image_host_config.feishu_app_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="未配置 IMAGE_HOST_FEISHU_APP_ID/IMAGE_HOST_FEISHU_APP_SECRET",
            )

        url = f"{self._base_url}/auth/v3/tenant_access_token/internal"
        body = {
            "app_id": image_host_config.feishu_app_id,
            "app_secret": image_host_config.feishu_app_secret,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, json=body)

        payload = self._json_or_error(response, "获取飞书 tenant_access_token 失败")
        token = payload.get("tenant_access_token")
        expire = int(payload.get("expire") or 7200)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="飞书 token 响应缺少 tenant_access_token",
            )

        self._token = _TenantToken(value=str(token), expires_at=now + expire)
        return self._token.value

    @property
    def _base_url(self) -> str:
        return image_host_config.feishu_api_base_url.rstrip("/")

    def _json_or_error(self, response: httpx.Response, fallback_detail: str) -> dict:
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{fallback_detail}：HTTP {response.status_code}",
            )

        try:
            payload = response.json()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{fallback_detail}：响应不是 JSON",
            )

        if payload.get("code") not in (0, None):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{fallback_detail}：{payload.get('msg') or payload.get('code')}",
            )
        return payload


_storage_backend: ImageStorageBackend = FeishuImageStorageBackend()


def get_storage_backend() -> ImageStorageBackend:
    return _storage_backend
