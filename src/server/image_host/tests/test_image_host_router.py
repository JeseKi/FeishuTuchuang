# -*- coding: utf-8 -*-
"""图床路由测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from http import HTTPStatus

import pytest
from sqlalchemy.orm import Session

from src.server.image_host import service
from src.server.image_host.config import image_host_config
from src.server.image_host.models import ImageAsset, ImageHostFeishuFolderBucket
from src.server.image_host.storage import _upload_folder_token

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
        self.folder_tokens: list[str | None] = []
        self.objects: dict[str, bytes] = {}
        self.deleted_keys: list[str] = []
        self.moved_keys: list[tuple[str, str]] = []
        self.created_folders: list[tuple[str, str, str]] = []
        self.folder_node_counts: dict[str, int] = {}

    async def put_image(
        self, *, content: bytes, filename: str, mime_type: str
    ) -> str:
        self.upload_count += 1
        folder_token = _upload_folder_token.get()
        self.folder_tokens.append(folder_token)
        if folder_token is not None:
            self.folder_node_counts[folder_token] = (
                self.folder_node_counts.get(folder_token, 0) + 1
            )
        key = f"fake-file-token-{self.upload_count}"
        self.objects[key] = content
        return key

    async def get_image(self, file_token: str) -> bytes:
        return self.objects[file_token]

    async def delete_image(self, file_token: str) -> None:
        self.deleted_keys.append(file_token)
        self.objects.pop(file_token, None)

    async def move_image(self, file_token: str, *, folder_token: str) -> None:
        self.moved_keys.append((file_token, folder_token))
        self.folder_node_counts[folder_token] = (
            self.folder_node_counts.get(folder_token, 0) + 1
        )

    async def create_folder(self, *, parent_folder_token: str, name: str) -> str:
        token = f"bucket-token-{len(self.created_folders) + 1}"
        self.created_folders.append((parent_folder_token, name, token))
        self.folder_node_counts[parent_folder_token] = (
            self.folder_node_counts.get(parent_folder_token, 0) + 1
        )
        self.folder_node_counts[token] = 0
        return token

    async def count_folder_nodes(self, *, folder_token: str) -> int:
        return self.folder_node_counts.get(folder_token, 0)


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
    access_token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_upload_image_and_get_public_url(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)

    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    data = upload_resp.json()
    assert data["filename"].endswith(".png")
    assert data["url"].endswith(f"/i/{data['filename']}")
    assert data["feishu_file_token"] == "fake-file-token-1"
    assert data["feishu_download_url"].endswith(
        "/drive/v1/files/fake-file-token-1/download"
    )
    assert data["mime_type"] == "image/png"
    assert data["size_bytes"] == len(PNG_BYTES)
    assert data["last_accessed_at"]
    assert data["reused_existing"] is False
    assert fake_storage.upload_count == 1

    image_resp = test_client.get(f"/i/{data['filename']}")

    assert image_resp.status_code == HTTPStatus.OK, image_resp.text
    assert image_resp.headers["content-type"].startswith("image/png")
    assert image_resp.content == PNG_BYTES
    assert image_resp.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert image_resp.headers["access-control-allow-origin"] == "*"


def test_public_image_uses_admin_cors_setting(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)
    custom_origin = "https://43.139.69.53:20194"
    settings_resp = test_client.patch(
        "/api/admin/settings",
        headers=headers,
        json={"image_cors_allowed_origin": custom_origin},
    )
    assert settings_resp.status_code == HTTPStatus.OK, settings_resp.text

    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    filename = upload_resp.json()["filename"]

    allowed_resp = test_client.get(f"/i/{filename}", headers={"Origin": custom_origin})
    assert allowed_resp.status_code == HTTPStatus.OK, allowed_resp.text
    assert allowed_resp.headers["access-control-allow-origin"] == custom_origin

    blocked_resp = test_client.get(
        f"/i/{filename}", headers={"Origin": "https://example.com"}
    )
    assert blocked_resp.status_code == HTTPStatus.OK, blocked_resp.text
    assert blocked_resp.headers["access-control-allow-origin"] == custom_origin


def test_upload_duplicate_reuses_existing_asset(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)

    first_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("first.png", PNG_BYTES, "image/png")},
    )
    second_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("second.png", PNG_BYTES, "image/png")},
    )

    assert first_resp.status_code == HTTPStatus.CREATED, first_resp.text
    assert second_resp.status_code == HTTPStatus.CREATED, second_resp.text
    assert second_resp.json()["id"] == first_resp.json()["id"]
    assert second_resp.json()["reused_existing"] is True
    assert fake_storage.upload_count == 1


def test_upload_image_uses_requested_folder(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)
    active_folder_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "图床", "folder_token": "folder-token-1", "is_active": True},
    )
    target_folder_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "归档", "folder_token": "folder-token-2", "is_active": False},
    )
    assert active_folder_resp.status_code == HTTPStatus.CREATED, active_folder_resp.text
    assert target_folder_resp.status_code == HTTPStatus.CREATED, target_folder_resp.text

    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        data={"folder_id": str(target_folder_resp.json()["id"])},
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    data = upload_resp.json()
    assert data["feishu_folder_id"] == target_folder_resp.json()["id"]
    assert data["feishu_folder_name"] == "归档"
    assert fake_storage.created_folders == [
        ("folder-token-2", "image-host-bucket-0001", "bucket-token-1")
    ]
    assert fake_storage.folder_tokens == ["bucket-token-1"]


def test_upload_image_reuses_auto_subfolder(
    test_client,
    init_test_database,
    test_db_session: Session,
    fake_storage,
):
    headers = _login_admin(test_client)
    folder_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "图床", "folder_token": "folder-token-1", "is_active": True},
    )
    assert folder_resp.status_code == HTTPStatus.CREATED, folder_resp.text

    first_upload = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    second_upload = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("video.mp4", MP4_BYTES, "video/mp4")},
    )

    assert first_upload.status_code == HTTPStatus.CREATED, first_upload.text
    assert second_upload.status_code == HTTPStatus.CREATED, second_upload.text
    assert fake_storage.created_folders == [
        ("folder-token-1", "image-host-bucket-0001", "bucket-token-1")
    ]
    assert fake_storage.folder_tokens == ["bucket-token-1", "bucket-token-1"]
    bucket = test_db_session.query(ImageHostFeishuFolderBucket).one()
    assert bucket.assigned_count == 2


def test_upload_image_creates_next_auto_subfolder_when_latest_is_full(
    test_client,
    init_test_database,
    test_db_session: Session,
    fake_storage,
):
    headers = _login_admin(test_client)
    folder_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "图床", "folder_token": "folder-token-1", "is_active": True},
    )
    assert folder_resp.status_code == HTTPStatus.CREATED, folder_resp.text
    test_db_session.add(
        ImageHostFeishuFolderBucket(
            feishu_folder_id=folder_resp.json()["id"],
            name="image-host-bucket-0001",
            folder_token="bucket-token-old",
            sequence=1,
            assigned_count=1500,
        )
    )
    test_db_session.commit()
    fake_storage.folder_node_counts["bucket-token-old"] = 1500
    fake_storage.folder_node_counts["folder-token-1"] = 1

    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    assert fake_storage.created_folders == [
        ("folder-token-1", "image-host-bucket-0002", "bucket-token-1")
    ]
    assert fake_storage.folder_tokens == ["bucket-token-1"]
    buckets = (
        test_db_session.query(ImageHostFeishuFolderBucket)
        .order_by(ImageHostFeishuFolderBucket.sequence.asc())
        .all()
    )
    assert [bucket.assigned_count for bucket in buckets] == [1500, 1]


def test_upload_image_rejects_when_parent_folder_cannot_create_more_buckets(
    test_client,
    init_test_database,
    test_db_session: Session,
    fake_storage,
):
    headers = _login_admin(test_client)
    folder_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "图床", "folder_token": "folder-token-1", "is_active": True},
    )
    assert folder_resp.status_code == HTTPStatus.CREATED, folder_resp.text
    test_db_session.add(
        ImageHostFeishuFolderBucket(
            feishu_folder_id=folder_resp.json()["id"],
            name="image-host-bucket-0001",
            folder_token="bucket-token-old",
            sequence=1,
            assigned_count=1500,
        )
    )
    test_db_session.commit()
    fake_storage.folder_node_counts["bucket-token-old"] = 1500
    fake_storage.folder_node_counts["folder-token-1"] = 1500

    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.CONFLICT, upload_resp.text
    assert upload_resp.json()["detail"] == "飞书主文件夹节点已满，无法创建新的自动子文件夹"
    assert fake_storage.upload_count == 0


def test_upload_image_rejects_unknown_folder(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)

    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        data={"folder_id": "999"},
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )

    assert upload_resp.status_code == HTTPStatus.NOT_FOUND, upload_resp.text
    assert upload_resp.json()["detail"] == "文件夹不存在"
    assert fake_storage.upload_count == 0


def test_list_images_returns_database_assets(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)

    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    uploaded = upload_resp.json()

    list_resp = test_client.get("/api/images", headers=headers)

    assert list_resp.status_code == HTTPStatus.OK, list_resp.text
    data = list_resp.json()
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == uploaded["id"]
    assert data["items"][0]["url"].endswith(f"/i/{uploaded['filename']}")
    assert data["items"][0]["feishu_file_token"] == "fake-file-token-1"
    assert data["items"][0]["feishu_download_url"].endswith(
        "/drive/v1/files/fake-file-token-1/download"
    )


def test_list_images_filters_by_uploaded_date_and_folder(
    test_client,
    init_test_database,
    fake_storage,
    test_db_session: Session,
):
    headers = _login_admin(test_client)
    folder_a_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "图床", "folder_token": "folder-token-1", "is_active": True},
    )
    assert folder_a_resp.status_code == HTTPStatus.CREATED, folder_a_resp.text
    folder_a_id = folder_a_resp.json()["id"]

    first_upload = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert first_upload.status_code == HTTPStatus.CREATED, first_upload.text

    folder_b_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "归档", "folder_token": "folder-token-2", "is_active": True},
    )
    assert folder_b_resp.status_code == HTTPStatus.CREATED, folder_b_resp.text
    folder_b_id = folder_b_resp.json()["id"]

    second_upload = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("clip.mp4", MP4_BYTES, "video/mp4")},
    )
    assert second_upload.status_code == HTTPStatus.CREATED, second_upload.text

    first_asset = test_db_session.query(ImageAsset).filter(
        ImageAsset.id == first_upload.json()["id"]
    ).one()
    second_asset = test_db_session.query(ImageAsset).filter(
        ImageAsset.id == second_upload.json()["id"]
    ).one()
    first_asset.created_at = datetime(2026, 5, 1, 8, tzinfo=timezone.utc)
    second_asset.created_at = datetime(2026, 5, 2, 8, tzinfo=timezone.utc)
    test_db_session.commit()

    folder_resp = test_client.get(
        f"/api/images?folder_id={folder_a_id}",
        headers=headers,
    )
    assert folder_resp.status_code == HTTPStatus.OK, folder_resp.text
    folder_data = folder_resp.json()
    assert folder_data["total"] == 1
    assert folder_data["items"][0]["id"] == first_upload.json()["id"]
    assert folder_data["items"][0]["feishu_folder_id"] == folder_a_id
    assert folder_data["items"][0]["feishu_folder_name"] == "图床"

    date_resp = test_client.get(
        f"/api/images?uploaded_from=2026-05-02&uploaded_to=2026-05-02&folder_id={folder_b_id}",
        headers=headers,
    )
    assert date_resp.status_code == HTTPStatus.OK, date_resp.text
    date_data = date_resp.json()
    assert date_data["total"] == 1
    assert date_data["items"][0]["id"] == second_upload.json()["id"]
    assert date_data["items"][0]["feishu_folder_id"] == folder_b_id
    assert date_data["items"][0]["feishu_folder_name"] == "归档"


def test_list_images_searches_by_feishu_file_token_and_filename(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)
    first_upload = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    second_upload = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("Clip.MP4", MP4_BYTES, "video/mp4")},
    )
    assert first_upload.status_code == HTTPStatus.CREATED, first_upload.text
    assert second_upload.status_code == HTTPStatus.CREATED, second_upload.text
    first_asset = first_upload.json()
    second_asset = second_upload.json()

    token_resp = test_client.get(
        "/api/images",
        headers=headers,
        params={"feishu_file_token": second_asset["feishu_file_token"]},
    )
    assert token_resp.status_code == HTTPStatus.OK, token_resp.text
    token_data = token_resp.json()
    assert token_data["total"] == 1
    assert token_data["items"][0]["id"] == second_asset["id"]

    original_filename_resp = test_client.get(
        "/api/images",
        headers=headers,
        params={"filename": "clip"},
    )
    assert (
        original_filename_resp.status_code == HTTPStatus.OK
    ), original_filename_resp.text
    original_filename_data = original_filename_resp.json()
    assert original_filename_data["total"] == 1
    assert original_filename_data["items"][0]["id"] == second_asset["id"]

    public_filename_resp = test_client.get(
        "/api/images",
        headers=headers,
        params={"filename": first_asset["filename"]},
    )
    assert public_filename_resp.status_code == HTTPStatus.OK, public_filename_resp.text
    public_filename_data = public_filename_resp.json()
    assert public_filename_data["total"] == 1
    assert public_filename_data["items"][0]["id"] == first_asset["id"]


def test_public_url_refills_cache_from_feishu_backend(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)
    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    filename = upload_resp.json()["filename"]

    cache_files = list(image_host_config.cache_dir.rglob("*.png"))
    assert len(cache_files) == 1
    cache_files[0].unlink()

    image_resp = test_client.get(f"/i/{filename}")

    assert image_resp.status_code == HTTPStatus.OK, image_resp.text
    assert image_resp.content == PNG_BYTES
    assert cache_files[0].exists()


def test_upload_rejects_non_image(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)

    resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("note.txt", b"hello", "text/plain")},
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert fake_storage.upload_count == 0


def test_upload_video_and_get_public_url(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)

    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("clip.mp4", MP4_BYTES, "video/mp4")},
    )

    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    data = upload_resp.json()
    assert data["filename"].endswith(".mp4")
    assert data["mime_type"] == "video/mp4"
    assert data["size_bytes"] == len(MP4_BYTES)
    assert fake_storage.upload_count == 1

    video_resp = test_client.get(f"/i/{data['filename']}")

    assert video_resp.status_code == HTTPStatus.OK, video_resp.text
    assert video_resp.headers["content-type"].startswith("video/mp4")
    assert video_resp.content == MP4_BYTES


def test_delete_image_removes_remote_local_cache_and_database(
    test_client,
    init_test_database,
    fake_storage,
    test_db_session: Session,
):
    headers = _login_admin(test_client)
    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    asset_id = upload_resp.json()["id"]
    asset = test_db_session.query(ImageAsset).filter(ImageAsset.id == asset_id).one()
    cache_file = image_host_config.cache_dir / asset.cache_path
    assert cache_file.exists()

    delete_resp = test_client.delete(f"/api/images/{asset_id}", headers=headers)

    assert delete_resp.status_code == HTTPStatus.NO_CONTENT, delete_resp.text
    assert fake_storage.deleted_keys == ["fake-file-token-1"]
    assert not cache_file.exists()
    assert test_db_session.query(ImageAsset).filter(ImageAsset.id == asset_id).first() is None


def test_move_image_updates_remote_and_database_folder(
    test_client,
    init_test_database,
    fake_storage,
    test_db_session: Session,
):
    headers = _login_admin(test_client)
    source_folder_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "图床", "folder_token": "folder-token-1", "is_active": True},
    )
    target_folder_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "归档", "folder_token": "folder-token-2", "is_active": False},
    )
    assert source_folder_resp.status_code == HTTPStatus.CREATED, source_folder_resp.text
    assert target_folder_resp.status_code == HTTPStatus.CREATED, target_folder_resp.text
    target_folder = target_folder_resp.json()
    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        data={"folder_id": str(source_folder_resp.json()["id"])},
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text
    asset_id = upload_resp.json()["id"]

    move_resp = test_client.patch(
        f"/api/images/{asset_id}/folder",
        headers=headers,
        json={"folder_id": target_folder["id"]},
    )

    assert move_resp.status_code == HTTPStatus.OK, move_resp.text
    assert move_resp.json()["feishu_folder_id"] == target_folder["id"]
    assert move_resp.json()["feishu_folder_name"] == "归档"
    assert fake_storage.created_folders == [
        ("folder-token-1", "image-host-bucket-0001", "bucket-token-1"),
        ("folder-token-2", "image-host-bucket-0001", "bucket-token-2"),
    ]
    assert fake_storage.moved_keys == [("fake-file-token-1", "bucket-token-2")]
    asset = test_db_session.query(ImageAsset).filter(ImageAsset.id == asset_id).one()
    assert asset.feishu_folder_id == target_folder["id"]
    assert asset.feishu_folder_bucket_id is not None


def test_move_image_rejects_unknown_folder(
    test_client,
    init_test_database,
    fake_storage,
):
    headers = _login_admin(test_client)
    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    assert upload_resp.status_code == HTTPStatus.CREATED, upload_resp.text

    move_resp = test_client.patch(
        f"/api/images/{upload_resp.json()['id']}/folder",
        headers=headers,
        json={"folder_id": 999},
    )

    assert move_resp.status_code == HTTPStatus.NOT_FOUND, move_resp.text
    assert move_resp.json()["detail"] == "文件夹不存在"
    assert fake_storage.moved_keys == []


def test_access_time_flushes_from_memory_to_database(
    test_client,
    init_test_database,
    fake_storage,
    test_db_session: Session,
):
    headers = _login_admin(test_client)
    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    asset_id = upload_resp.json()["id"]
    accessed_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    service.record_image_access(asset_id, accessed_at)
    flushed_count = service.flush_pending_image_accesses(test_db_session)
    flushed_again_count = service.flush_pending_image_accesses(test_db_session)

    asset = test_db_session.query(ImageAsset).filter(ImageAsset.id == asset_id).one()
    assert flushed_count == 1
    assert flushed_again_count == 0
    assert asset.last_accessed_at.replace(tzinfo=timezone.utc) == accessed_at


def test_cleanup_expired_cache_files_removes_only_stale_local_cache(
    test_client,
    init_test_database,
    fake_storage,
    test_db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    headers = _login_admin(test_client)
    upload_resp = test_client.post(
        "/api/images",
        headers=headers,
        files={"image": ("pixel.png", PNG_BYTES, "image/png")},
    )
    asset_id = upload_resp.json()["id"]
    asset = test_db_session.query(ImageAsset).filter(ImageAsset.id == asset_id).one()
    cache_file = image_host_config.cache_dir / asset.cache_path
    assert cache_file.exists()

    monkeypatch.setattr(image_host_config, "cache_ttl_hours", 168)
    asset.last_accessed_at = datetime.now(timezone.utc) - timedelta(hours=169)
    test_db_session.commit()

    deleted_count = service.cleanup_expired_cache_files(test_db_session)

    assert deleted_count == 1
    assert not cache_file.exists()
