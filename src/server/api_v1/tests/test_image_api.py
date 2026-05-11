# -*- coding: utf-8 -*-
"""v1 图床 API 测试。"""

from __future__ import annotations

from http import HTTPStatus

import pytest

from src.server.image_host.config import image_host_config

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xe2&\xb5"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)
MP4_BYTES = (
    b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41"
    b"\x00\x00\x00\x08free"
)


class FakeImageStorageBackend:
    def __init__(self) -> None:
        self.upload_count = 0
        self.objects: dict[str, bytes] = {}

    async def put_image(
        self, *, content: bytes, filename: str, mime_type: str
    ) -> str:
        self.upload_count += 1
        key = f"fake-file-token-{self.upload_count}"
        self.objects[key] = content
        return key

    async def get_image(self, file_token: str) -> bytes:
        return self.objects[file_token]

    async def delete_image(self, file_token: str) -> None:
        self.objects.pop(file_token, None)


@pytest.fixture
def fake_storage(monkeypatch: pytest.MonkeyPatch, tmp_path):
    storage = FakeImageStorageBackend()
    monkeypatch.setattr(
        "src.server.image_host.service.get_storage_backend",
        lambda: storage,
    )
    monkeypatch.setattr(image_host_config, "cache_dir", tmp_path / "image_cache")
    return storage


def _login_admin(test_client):
    resp = test_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == HTTPStatus.OK, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_api_key(test_client) -> str:
    headers = _login_admin(test_client)
    resp = test_client.post(
        "/api/auth/api-keys",
        headers=headers,
        json={"name": "PicGo"},
    )
    assert resp.status_code == HTTPStatus.CREATED, resp.text
    return resp.json()["key"]


def test_upload_image_with_api_key_header(
    test_client,
    init_test_database,
    fake_storage,
):
    api_key = _create_api_key(test_client)

    upload_resp = test_client.post(
        "/api/v1/images",
        headers={"X-API-Key": api_key},
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    data = upload_resp.json()
    assert data["filename"].endswith(".png")
    assert data["url"].endswith(f"/i/{data['filename']}")
    assert data["mime_type"] == "image/png"
    assert fake_storage.upload_count == 1


def test_upload_image_with_bearer_api_key(
    test_client,
    init_test_database,
    fake_storage,
):
    api_key = _create_api_key(test_client)

    upload_resp = test_client.post(
        "/api/v1/images",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text


def test_upload_video_with_api_key_header(
    test_client,
    init_test_database,
    fake_storage,
):
    api_key = _create_api_key(test_client)

    upload_resp = test_client.post(
        "/api/v1/images",
        headers={"X-API-Key": api_key},
        files={"image": ("clip.mp4", MP4_BYTES, "video/mp4")},
    )

    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    data = upload_resp.json()
    assert data["filename"].endswith(".mp4")
    assert data["mime_type"] == "video/mp4"


def test_upload_image_rejects_revoked_api_key(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)
    create_resp = test_client.post(
        "/api/auth/api-keys",
        headers=headers,
        json={"name": "PicGo"},
    )
    api_key = create_resp.json()["key"]
    key_id = create_resp.json()["id"]
    revoke_resp = test_client.delete(f"/api/auth/api-keys/{key_id}", headers=headers)
    assert revoke_resp.status_code == HTTPStatus.NO_CONTENT, revoke_resp.text

    upload_resp = test_client.post(
        "/api/v1/images",
        headers={"X-API-Key": api_key},
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.UNAUTHORIZED
    assert fake_storage.upload_count == 0


def test_upload_image_requires_api_key(test_client, init_test_database, fake_storage):
    upload_resp = test_client.post(
        "/api/v1/images",
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.UNAUTHORIZED
