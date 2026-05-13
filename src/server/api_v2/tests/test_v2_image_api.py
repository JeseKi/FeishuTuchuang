# -*- coding: utf-8 -*-
"""v2 图床 API 测试。"""

from __future__ import annotations

from http import HTTPStatus

import pytest

from src.server.feishu_folder.models import FeishuFolder
from src.server.image_host.config import image_host_config
from src.server.image_host.models import ImageAsset
from src.server.image_host.storage import _upload_folder_token

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xe2&\xb5"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeImageStorageBackend:
    def __init__(self) -> None:
        self.upload_count = 0
        self.folder_tokens: list[str | None] = []
        self.objects: dict[str, bytes] = {}
        self.deleted_keys: list[str] = []

    async def put_image(
        self, *, content: bytes, filename: str, mime_type: str
    ) -> str:
        self.upload_count += 1
        self.folder_tokens.append(_upload_folder_token.get())
        key = f"fake-file-token-{self.upload_count}"
        self.objects[key] = content
        return key

    async def get_image(self, file_token: str) -> bytes:
        return self.objects[file_token]

    async def delete_image(self, file_token: str) -> None:
        self.deleted_keys.append(file_token)
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


def _create_folder(test_db_session, *, name: str, folder_token: str) -> None:
    test_db_session.add(
        FeishuFolder(
            name=name,
            folder_token=folder_token,
            is_active=False,
        )
    )
    test_db_session.commit()


def test_list_folder_names_returns_string_array(
    test_client,
    init_test_database,
    test_db_session,
):
    api_key = _create_api_key(test_client)
    _create_folder(test_db_session, name="图床", folder_token="folder-token-1")
    _create_folder(test_db_session, name="归档", folder_token="folder-token-2")

    resp = test_client.get("/api/v2/folders", headers={"X-API-Key": api_key})

    assert resp.status_code == HTTPStatus.OK, resp.text
    assert resp.json() == ["图床", "归档"]


def test_upload_image_v2_uses_requested_folder(
    test_client,
    init_test_database,
    test_db_session,
    fake_storage,
):
    api_key = _create_api_key(test_client)
    _create_folder(test_db_session, name="图床", folder_token="folder-token-1")
    _create_folder(test_db_session, name="归档", folder_token="folder-token-2")

    upload_resp = test_client.post(
        "/api/v2/images",
        headers={"X-API-Key": api_key},
        data={"folder_name": "归档"},
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    assert upload_resp.json()["filename"].endswith(".png")
    assert upload_resp.json()["feishu_folder_name"] == "归档"
    assert fake_storage.upload_count == 1
    assert fake_storage.folder_tokens == ["folder-token-2"]


def test_upload_image_v2_rejects_unknown_folder(
    test_client,
    init_test_database,
    fake_storage,
):
    api_key = _create_api_key(test_client)

    upload_resp = test_client.post(
        "/api/v2/images",
        headers={"X-API-Key": api_key},
        data={"folder_name": "不存在"},
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.NOT_FOUND
    assert upload_resp.json()["detail"] == "文件夹不存在"
    assert fake_storage.upload_count == 0


def test_delete_image_v2_removes_remote_local_cache_and_database(
    test_client,
    init_test_database,
    test_db_session,
    fake_storage,
):
    api_key = _create_api_key(test_client)
    _create_folder(test_db_session, name="图床", folder_token="folder-token-1")
    upload_resp = test_client.post(
        "/api/v2/images",
        headers={"X-API-Key": api_key},
        data={"folder_name": "图床"},
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    asset_id = upload_resp.json()["id"]
    asset = test_db_session.query(ImageAsset).filter(ImageAsset.id == asset_id).one()
    cache_file = image_host_config.cache_dir / asset.cache_path
    assert cache_file.exists()

    delete_resp = test_client.delete(
        f"/api/v2/images/{asset_id}",
        headers={"X-API-Key": api_key},
    )

    assert delete_resp.status_code == HTTPStatus.NO_CONTENT, delete_resp.text
    assert fake_storage.deleted_keys == ["fake-file-token-1"]
    assert not cache_file.exists()
    assert (
        test_db_session.query(ImageAsset).filter(ImageAsset.id == asset_id).first()
        is None
    )


def test_delete_image_v2_requires_api_key(
    test_client,
    init_test_database,
    test_db_session,
    fake_storage,
):
    api_key = _create_api_key(test_client)
    _create_folder(test_db_session, name="图床", folder_token="folder-token-1")
    upload_resp = test_client.post(
        "/api/v2/images",
        headers={"X-API-Key": api_key},
        data={"folder_name": "图床"},
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text

    delete_resp = test_client.delete(f"/api/v2/images/{upload_resp.json()['id']}")

    assert delete_resp.status_code == HTTPStatus.UNAUTHORIZED
    assert fake_storage.deleted_keys == []
