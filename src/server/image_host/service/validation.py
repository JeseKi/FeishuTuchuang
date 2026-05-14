# -*- coding: utf-8 -*-
"""图床上传校验与文件名解析。"""

from __future__ import annotations

from fastapi import HTTPException, status

from ..config import image_host_config
from .constants import (
    MAGIC_MIME,
    MAX_HEIC_BRAND_SCAN_BYTES,
    MAX_MP4_BRAND_SCAN_BYTES,
    MIME_TO_EXTENSION,
)


def validate_size(content: bytes) -> None:
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传文件不能为空",
        )
    max_bytes = image_host_config.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件不能超过 {image_host_config.max_upload_mb}MB",
        )


def detect_mime_type(content: bytes, declared_mime: str | None) -> str:
    detected = None
    for prefix, mime_type in MAGIC_MIME:
        if content.startswith(prefix):
            detected = mime_type
            break

    if detected is None and _looks_like_webp(content):
        detected = "image/webp"
    if detected is None and _looks_like_heic(content):
        detected = "image/heic"
    if detected is None:
        detected = _detect_iso_video_mime_type(content)
    if detected is None and _looks_like_avi(content):
        detected = "video/x-msvideo"

    mime_type = detected or (declared_mime or "").split(";")[0].strip().lower()
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"
    if mime_type == "video/ogv":
        mime_type = "video/ogg"
    if mime_type not in MIME_TO_EXTENSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持常见图片和视频文件",
        )
    return mime_type


def parse_public_filename(filename: str) -> tuple[str, str]:
    if "." not in filename:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    asset_id, extension = filename.rsplit(".", 1)
    if len(asset_id) != 32 or not all(char in "0123456789abcdef" for char in asset_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    extension = extension.lower()
    if extension not in set(MIME_TO_EXTENSION.values()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    return asset_id, extension


def _looks_like_webp(content: bytes) -> bool:
    return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"


def _looks_like_heic(content: bytes) -> bool:
    brands = (b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1")
    return len(content) >= 12 and b"ftyp" in content[:MAX_HEIC_BRAND_SCAN_BYTES] and any(
        brand in content[:MAX_HEIC_BRAND_SCAN_BYTES] for brand in brands
    )


def _detect_iso_video_mime_type(content: bytes) -> str | None:
    brands = (b"isom", b"iso2", b"mp41", b"mp42", b"avc1", b"m4v ", b"qt  ")
    if not (
        len(content) >= 12
        and content[4:8] == b"ftyp"
        and any(brand in content[:MAX_MP4_BRAND_SCAN_BYTES] for brand in brands)
    ):
        return None
    if b"qt  " in content[:MAX_MP4_BRAND_SCAN_BYTES]:
        return "video/quicktime"
    return "video/mp4"


def _looks_like_avi(content: bytes) -> bool:
    return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"AVI "
