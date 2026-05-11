# -*- coding: utf-8 -*-
"""图床存储后端。"""

from __future__ import annotations

from typing import Protocol

import httpx
from fastapi import HTTPException, status

from .config import image_host_config
from .oauth import get_valid_user_access_token


class ImageStorageBackend(Protocol):
    async def put_image(
        self, *, content: bytes, filename: str, mime_type: str
    ) -> str:
        """上传图片并返回后端资源 key。"""
        ...

    async def get_image(self, file_token: str) -> bytes:
        """按后端资源 key 下载图片内容。"""
        ...

    async def delete_image(self, file_token: str) -> None:
        """删除后端资源。"""
        ...


class FeishuDriveStorageBackend:
    """基于飞书 Drive 文件 API 的冷存储后端。"""

    def __init__(self) -> None:
        self._root_folder_token: str | None = None

    async def put_image(
        self, *, content: bytes, filename: str, mime_type: str
    ) -> str:
        token = await get_valid_user_access_token()
        folder_token = await self._get_upload_folder_token()
        url = f"{self._base_url}/drive/v1/files/upload_all"
        data = {
            "file_name": filename,
            "parent_type": "explorer",
            "parent_node": folder_token,
            "size": str(len(content)),
        }
        files = {
            "file": (filename, content, mime_type),
        }
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, data=data, files=files, headers=headers)

        payload = self._json_or_error(response, "飞书 Drive 文件上传失败")
        file_token = payload.get("data", {}).get("file_token")
        if not file_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="飞书 Drive 文件上传响应缺少 file_token",
            )
        return str(file_token)

    async def get_image(self, file_token: str) -> bytes:
        token = await get_valid_user_access_token()
        url = f"{self._base_url}/drive/v1/files/{file_token}/download"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url, headers=headers)

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"飞书 Drive 文件下载失败：HTTP {response.status_code}",
            )
        return response.content

    async def delete_image(self, file_token: str) -> None:
        token = await get_valid_user_access_token()
        url = f"{self._base_url}/drive/v1/files/{file_token}"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"type": "file"}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(url, params=params, headers=headers)

        self._json_or_error(response, "飞书 Drive 文件删除失败")

    async def _get_upload_folder_token(self) -> str:
        if image_host_config.feishu_drive_folder_token:
            return image_host_config.feishu_drive_folder_token
        if self._root_folder_token:
            return self._root_folder_token

        token = await get_valid_user_access_token()
        url = f"{self._base_url}/drive/explorer/v2/root_folder/meta"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=headers)
        payload = self._json_or_error(response, "获取飞书 Drive 根目录失败")
        folder_token = payload.get("data", {}).get("token")
        if not folder_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "未配置 IMAGE_HOST_FEISHU_DRIVE_FOLDER_TOKEN，且无法获取 "
                    "Drive 根目录。请创建图床专用文件夹并将 folder token "
                    "配置到该环境变量。"
                ),
            )
        self._root_folder_token = str(folder_token)
        return self._root_folder_token

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


_storage_backend: ImageStorageBackend = FeishuDriveStorageBackend()


def get_storage_backend() -> ImageStorageBackend:
    return _storage_backend
