# -*- coding: utf-8 -*-
"""图床存储后端测试。"""

from __future__ import annotations

from http import HTTPStatus

import httpx
import pytest
from fastapi import HTTPException

from src.server.image_host.storage import FeishuDriveStorageBackend


def test_json_or_error_includes_feishu_error_body_for_http_error():
    response = httpx.Response(
        HTTPStatus.BAD_REQUEST,
        json={"code": 1061045, "msg": "parent node is invalid"},
        request=httpx.Request(
            "POST",
            "https://open.feishu.cn/open-apis/drive/v1/files/upload_prepare",
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        FeishuDriveStorageBackend()._json_or_error(
            response,
            "飞书 Drive 文件预上传失败",
        )

    assert exc_info.value.status_code == HTTPStatus.BAD_GATEWAY
    assert exc_info.value.detail == (
        "飞书 Drive 文件预上传失败：HTTP 400，"
        "飞书 code=1061045, msg=parent node is invalid"
    )


def test_json_or_error_includes_feishu_code_for_successful_http_error_payload():
    response = httpx.Response(
        HTTPStatus.OK,
        json={"code": 99991672, "msg": "permission denied"},
        request=httpx.Request(
            "POST",
            "https://open.feishu.cn/open-apis/drive/v1/files/upload_prepare",
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        FeishuDriveStorageBackend()._json_or_error(
            response,
            "飞书 Drive 文件预上传失败",
        )

    assert exc_info.value.status_code == HTTPStatus.BAD_GATEWAY
    assert exc_info.value.detail == (
        "飞书 Drive 文件预上传失败：飞书 code=99991672, msg=permission denied"
    )
