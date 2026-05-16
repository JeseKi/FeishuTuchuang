# -*- coding: utf-8 -*-
"""开源默认配置测试。"""

from fastapi import FastAPI
from starlette.routing import Route

from src.server.auth.config import auth_config
from src.server.config import GlobalConfig
from src.server.main import include_api_routers


def test_default_feature_flags_keep_template_routes_disabled(
    monkeypatch,
) -> None:
    env_names = [
        "ENABLE_EXAMPLE_MODULE",
        "ENABLE_OAUTH_LOGIN",
        "ENABLE_OAUTH_PROVIDER",
        "ENABLE_SCOPE_MANAGEMENT",
        "ENABLE_DEV_PROVIDER_RUNTIME",
        "ENABLE_EXTERNAL_PROVIDER_REGISTRY",
    ]
    for env_name in env_names:
        monkeypatch.delenv(env_name, raising=False)

    config = GlobalConfig()

    assert config.enable_example_module is False
    assert config.enable_oauth_login is False
    assert config.enable_oauth_provider is False
    assert config.enable_scope_management is False
    assert config.enable_dev_provider_runtime is False
    assert config.enable_external_provider_registry is False


def test_disabled_optional_routes_are_not_mounted(monkeypatch) -> None:
    monkeypatch.setattr("src.server.main.global_config.enable_example_module", False)
    monkeypatch.setattr("src.server.main.global_config.enable_oauth_login", False)
    monkeypatch.setattr("src.server.main.global_config.enable_oauth_provider", False)
    monkeypatch.setattr("src.server.main.global_config.enable_scope_management", False)
    monkeypatch.setattr("src.server.main.global_config.enable_dev_provider_runtime", False)
    monkeypatch.setattr("src.server.main.global_config.app_env", "dev")

    app = FastAPI()
    include_api_routers(app)
    paths = {route.path for route in app.routes if isinstance(route, Route)}

    assert "/api/images" in paths
    assert "/api/v2/images" in paths
    assert "/i/{filename}" in paths
    assert "/api/example/ping" not in paths
    assert "/api/oauth/providers" not in paths
    assert "/api/oauth-provider/clients" not in paths
    assert "/api/admin/scopes" not in paths
    assert "/api/dev/providers/runtime-config" not in paths


def test_public_registration_is_disabled_when_configured(
    test_client,
    monkeypatch,
) -> None:
    monkeypatch.setattr(auth_config, "enable_public_registration", False)

    response = test_client.post(
        "/api/auth/send-verification-code",
        json={"email": "blocked@example.com"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "公开注册已关闭，请联系管理员创建账号"
