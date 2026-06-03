# -*- coding: utf-8 -*-
"""图床存储后端。"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
import zlib
from collections.abc import Iterator
from typing import Any, Protocol

import httpx
from fastapi import HTTPException, status

from .config import image_host_config
from .oauth import get_valid_user_access_token

_UPLOAD_TIMEOUT = httpx.Timeout(180.0, connect=15.0)
_DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=15.0)
_UPLOAD_RETRY_COUNT = 3
_UPLOAD_RETRY_BACKOFF_SECONDS = 1.5
_upload_folder_token: ContextVar[str | None] = ContextVar(
    "feishu_upload_folder_token",
    default=None,
)


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

    async def move_image(self, file_token: str, *, folder_token: str) -> None:
        """移动后端资源到指定文件夹。"""
        ...

    async def create_folder(self, *, parent_folder_token: str, name: str) -> str:
        """在指定父文件夹下创建文件夹并返回新文件夹 token。"""
        ...

    async def count_folder_nodes(self, *, folder_token: str) -> int:
        """统计指定文件夹下的节点数量。"""
        ...


class FeishuDriveStorageBackend:
    """基于飞书 Drive 文件 API 的冷存储后端。"""

    def __init__(self) -> None:
        self._root_folder_token: str | None = None

    async def put_image(
        self, *, content: bytes, filename: str, mime_type: str
    ) -> str:
        return await self._put_image_chunked(
            content=content,
            filename=filename,
            mime_type=mime_type,
        )

    async def _put_image_chunked(
        self, *, content: bytes, filename: str, mime_type: str
    ) -> str:
        token = await get_valid_user_access_token()
        folder_token = await self._get_upload_folder_token()
        headers = {"Authorization": f"Bearer {token}"}
        prepare_url = f"{self._base_url}/drive/v1/files/upload_prepare"
        prepare_body = {
            "file_name": filename,
            "parent_type": "explorer",
            "parent_node": folder_token,
            "size": len(content),
        }

        async with httpx.AsyncClient(timeout=_UPLOAD_TIMEOUT, trust_env=True) as client:
            prepare_response = await self._post_with_retries(
                client,
                prepare_url,
                json=prepare_body,
                headers=headers,
                fallback_detail="飞书 Drive 文件预上传失败",
            )
            prepare_payload = self._json_or_error(
                prepare_response,
                "飞书 Drive 文件预上传失败",
            )
            prepare_data = prepare_payload.get("data", {})
            upload_id = prepare_data.get("upload_id")
            block_size = int(prepare_data.get("block_size") or 0)
            block_num = int(prepare_data.get("block_num") or 0)
            if not upload_id or block_size <= 0 or block_num <= 0:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="飞书 Drive 预上传响应缺少 upload_id/block_size/block_num",
                )

            part_url = f"{self._base_url}/drive/v1/files/upload_part"
            for seq in range(block_num):
                start = seq * block_size
                chunk = content[start : start + block_size]
                part_data = {
                    "upload_id": str(upload_id),
                    "seq": str(seq),
                    "size": str(len(chunk)),
                    "checksum": str(_adler32_checksum(chunk)),
                }
                part_files = {
                    "file": (filename, chunk, mime_type),
                }
                part_response = await self._post_with_retries(
                    client,
                    part_url,
                    data=part_data,
                    files=part_files,
                    headers=headers,
                    fallback_detail=f"飞书 Drive 文件分片上传失败 seq={seq}",
                )
                self._json_or_error(
                    part_response,
                    f"飞书 Drive 文件分片上传失败 seq={seq}",
                )

            finish_url = f"{self._base_url}/drive/v1/files/upload_finish"
            finish_response = await self._post_with_retries(
                client,
                finish_url,
                json={"upload_id": str(upload_id), "block_num": block_num},
                headers=headers,
                fallback_detail="飞书 Drive 文件完成上传失败",
            )

        payload = self._json_or_error(finish_response, "飞书 Drive 文件完成上传失败")
        file_token = payload.get("data", {}).get("file_token")
        if not file_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="飞书 Drive 完成上传响应缺少 file_token",
            )
        return str(file_token)

    async def get_image(self, file_token: str) -> bytes:
        token = await get_valid_user_access_token()
        url = f"{self._base_url}/drive/v1/files/{file_token}/download"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT, trust_env=True) as client:
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

        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT, trust_env=True) as client:
            response = await client.delete(url, params=params, headers=headers)

        self._json_or_error(response, "飞书 Drive 文件删除失败")

    async def move_image(self, file_token: str, *, folder_token: str) -> None:
        token = await get_valid_user_access_token()
        url = f"{self._base_url}/drive/v1/files/{file_token}/move"
        headers = {"Authorization": f"Bearer {token}"}
        body = {"type": "file", "folder_token": folder_token}

        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT, trust_env=True) as client:
            response = await client.post(url, json=body, headers=headers)

        self._json_or_error(response, "飞书 Drive 文件移动失败")

    async def create_folder(self, *, parent_folder_token: str, name: str) -> str:
        token = await get_valid_user_access_token()
        url = f"{self._base_url}/drive/v1/files/create_folder"
        headers = {"Authorization": f"Bearer {token}"}
        body = {"folder_token": parent_folder_token, "name": name}

        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT, trust_env=True) as client:
            response = await client.post(url, json=body, headers=headers)

        payload = self._json_or_error(response, "飞书 Drive 文件夹创建失败")
        folder_token = payload.get("data", {}).get("token")
        if not folder_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="飞书 Drive 文件夹创建响应缺少 token",
            )
        return str(folder_token)

    async def count_folder_nodes(self, *, folder_token: str) -> int:
        token = await get_valid_user_access_token()
        url = f"{self._base_url}/drive/v1/files"
        headers = {"Authorization": f"Bearer {token}"}
        params: dict[str, str | int] = {
            "folder_token": folder_token,
            "page_size": 200,
        }
        total = 0

        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT, trust_env=True) as client:
            while True:
                response = await client.get(url, params=params, headers=headers)
                payload = self._json_or_error(
                    response,
                    "飞书 Drive 文件夹节点统计失败",
                )
                data = payload.get("data", {})
                files = data.get("files") or []
                total += len(files)
                if not data.get("has_more"):
                    return total
                page_token = data.get("next_page_token")
                if not page_token:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="飞书 Drive 文件夹节点统计响应缺少 next_page_token",
                    )
                params["page_token"] = str(page_token)

    async def _get_upload_folder_token(self) -> str:
        configured_folder_token = _upload_folder_token.get()
        if configured_folder_token:
            return configured_folder_token
        if self._root_folder_token:
            return self._root_folder_token

        token = await get_valid_user_access_token()
        url = f"{self._base_url}/drive/explorer/v2/root_folder/meta"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT, trust_env=True) as client:
            response = await client.get(url, headers=headers)
        payload = self._json_or_error(response, "获取飞书 Drive 根目录失败")
        folder_token = payload.get("data", {}).get("token")
        if not folder_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "未配置启用的飞书文件夹，且无法获取 Drive 根目录。"
                    "请在飞书文件夹管理中配置 folder token。"
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

    async def _post_with_retries(
        self,
        client: httpx.AsyncClient,
        url: str,
        *,
        fallback_detail: str,
        data: dict[str, str] | None = None,
        files: Any | None = None,
        json: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        last_request_error: httpx.RequestError | None = None
        last_response: httpx.Response | None = None
        for attempt in range(_UPLOAD_RETRY_COUNT):
            try:
                response = await client.post(
                    url,
                    data=data,
                    files=files,
                    json=json,
                    headers=headers,
                )
            except httpx.RequestError as exc:
                last_request_error = exc
            else:
                if response.status_code < 500 and response.status_code != 429:
                    return response
                last_response = response

            if attempt < _UPLOAD_RETRY_COUNT - 1:
                await asyncio.sleep(_UPLOAD_RETRY_BACKOFF_SECONDS * (attempt + 1))

        if last_response is not None:
            return last_response
        detail = str(last_request_error) if last_request_error else "请求失败"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{fallback_detail}：{detail or '请求超时'}",
        )


_storage_backend: ImageStorageBackend = FeishuDriveStorageBackend()


def get_storage_backend() -> ImageStorageBackend:
    return _storage_backend


@contextmanager
def use_upload_folder_token(folder_token: str | None) -> Iterator[None]:
    token = _upload_folder_token.set(folder_token)
    try:
        yield
    finally:
        _upload_folder_token.reset(token)


def _adler32_checksum(content: bytes) -> int:
    return zlib.adler32(content) & 0xFFFFFFFF
