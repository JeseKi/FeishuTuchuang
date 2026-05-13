# -*- coding: utf-8 -*-
"""飞书文件夹管理路由测试。"""

from __future__ import annotations

from http import HTTPStatus

from sqlalchemy.orm import Session

from src.server.feishu_folder.models import FeishuFolder


def _login_admin(test_client):
    resp = test_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == HTTPStatus.OK, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_create_list_and_activate_feishu_folders(
    test_client,
    init_test_database,
    test_db_session: Session,
):
    headers = _login_admin(test_client)

    first_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={
            "name": "图床",
            "folder_token": "folder-token-1",
            "is_active": True,
        },
    )
    second_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={
            "name": "备用",
            "folder_token": "folder-token-2",
            "is_active": True,
        },
    )

    assert first_resp.status_code == HTTPStatus.CREATED, first_resp.text
    assert second_resp.status_code == HTTPStatus.CREATED, second_resp.text
    assert first_resp.json()["is_active"] is True
    assert second_resp.json()["is_active"] is True

    first = (
        test_db_session.query(FeishuFolder)
        .filter(FeishuFolder.folder_token == "folder-token-1")
        .one()
    )
    second = (
        test_db_session.query(FeishuFolder)
        .filter(FeishuFolder.folder_token == "folder-token-2")
        .one()
    )
    assert first.is_active is False
    assert second.is_active is True

    list_resp = test_client.get("/api/feishu/folders", headers=headers)
    active_resp = test_client.get("/api/feishu/folders/active", headers=headers)

    assert list_resp.status_code == HTTPStatus.OK, list_resp.text
    assert [item["folder_token"] for item in list_resp.json()] == [
        "folder-token-2",
        "folder-token-1",
    ]
    assert active_resp.status_code == HTTPStatus.OK, active_resp.text
    assert active_resp.json()["folder_token"] == "folder-token-2"


def test_update_folder_rejects_duplicate_token(test_client, init_test_database):
    headers = _login_admin(test_client)
    first_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "图床", "folder_token": "folder-token-1"},
    )
    second_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "备用", "folder_token": "folder-token-2"},
    )

    update_resp = test_client.put(
        f"/api/feishu/folders/{second_resp.json()['id']}",
        headers=headers,
        json={
            "name": "备用",
            "folder_token": first_resp.json()["folder_token"],
            "is_active": False,
        },
    )

    assert update_resp.status_code == HTTPStatus.BAD_REQUEST
    assert update_resp.json()["detail"] == "文件夹 token 已存在"


def test_delete_folder(test_client, init_test_database):
    headers = _login_admin(test_client)
    create_resp = test_client.post(
        "/api/feishu/folders",
        headers=headers,
        json={"name": "图床", "folder_token": "folder-token-1"},
    )

    delete_resp = test_client.delete(
        f"/api/feishu/folders/{create_resp.json()['id']}",
        headers=headers,
    )
    list_resp = test_client.get("/api/feishu/folders", headers=headers)

    assert delete_resp.status_code == HTTPStatus.NO_CONTENT, delete_resp.text
    assert list_resp.json() == []
