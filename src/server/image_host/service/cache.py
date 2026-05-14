# -*- coding: utf-8 -*-
"""图床本地缓存文件工具。"""

from __future__ import annotations

from pathlib import Path

from src.server.config import global_config

from ..config import image_host_config
from ..models import ImageAsset


def build_cache_path(asset_id: str, extension: str) -> Path:
    return Path(asset_id[:2]) / f"{asset_id}.{extension}"


def cache_root() -> Path:
    root = image_host_config.cache_dir
    if not root.is_absolute():
        root = Path(global_config.project_root) / root
    return root


def write_cache_file(relative_path: Path, content: bytes) -> None:
    cache_file = cache_root() / relative_path
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(content)


def ensure_cache_file(asset: ImageAsset, content: bytes) -> None:
    cache_file = cache_root() / asset.cache_path
    if not cache_file.exists():
        write_cache_file(Path(asset.cache_path), content)
