# -*- coding: utf-8 -*-
"""
全局配置（极简）

公开接口：
- `global_config`: 全局配置实例

内部方法：
- 无

说明：
- 支持 .env 与 .env.{APP_ENV} 加载
- 提供 CORS 允许源解析
"""

import json
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_TEST_MOCK_PROVIDERS = [
    "github_oauth",
    "google_oauth",
    "turnstile",
    "mail",
    "example_external_api",
]

# 先加载 .env 和 .env.{APP_ENV}
load_dotenv(".env")
app_env = os.getenv("APP_ENV", "dev")
load_dotenv(f".env.{app_env}", override=True)


class GlobalConfig(BaseSettings):
    """全局配置"""

    app_env: str = Field(default="dev", title="应用环境")

    database_protocol: str = Field(default="sqlite", title="数据库协议")

    database_path: Path = Field(
        default=Path("data") / "database.db",
        title="数据库路径",
        description="相对项目根目录的相对路径",
    )

    app_secret_key: str = Field(
        default="dev_secret_key_for_testing_only",
        title="应用密钥",
        description="用于会话/签名等场景（可选）",
    )

    app_domain: str = Field(
        default="",
        title="应用域名",
        description="用于生成对外访问的链接（例如重置密码链接）",
    )

    project_root: Path = Field(
        default=Path.cwd(),
        title="项目根目录",
        description="相对项目根目录的相对路径",
    )

    log_level: str = Field(default="info", title="日志级别")

    log_dir: Path = Field(
        default=Path("logs"),
        title="日志目录",
        description="相对项目根目录的相对路径",
    )

    log_rotation: str = Field(
        default="20 MB",
        title="日志轮转策略",
        description="Loguru rotation 配置",
    )

    log_retention: str = Field(
        default="14 days",
        title="日志保留策略",
        description="Loguru retention 配置",
    )

    log_serialize: bool = Field(
        default=False,
        title="是否输出 JSON 日志",
    )

    def _parse_env_list(self, env_name: str, default: list[str]) -> list[str]:
        """解析环境变量列表，支持 JSON、逗号分隔或单值。"""
        env_value = os.getenv(env_name)
        if not env_value:
            return default
        try:
            parsed = json.loads(env_value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
        if "," in env_value:
            return [item.strip() for item in env_value.split(",") if item.strip()]
        return [env_value.strip()] if env_value.strip() else default

    @property
    def allowed_origins(self) -> List[str]:
        """允许的跨域来源

        支持格式：
        1. JSON：ALLOWED_ORIGINS='["http://localhost:5173"]'
        2. 逗号分隔：ALLOWED_ORIGINS="http://localhost:5173,https://example.com"
        3. 单个值：ALLOWED_ORIGINS="*"
        4. 未设置：默认为 ["*"]
        """
        return self._parse_env_list("ALLOWED_ORIGINS", ["*"])

    @property
    def oauth_list(self) -> list[str]:
        """启用的 OAuth 渠道列表，格式同 ALLOWED_ORIGINS。"""
        return [
            provider.strip().upper()
            for provider in self._parse_env_list("OAUTH_LIST", [])
            if provider.strip()
        ]

    @property
    def external_provider_mock_list(self) -> list[str]:
        """使用 mock service 的外部 provider 列表，格式同 ALLOWED_ORIGINS。"""
        default = DEFAULT_TEST_MOCK_PROVIDERS if self.app_env == "test" else []
        return [
            provider.strip().lower()
            for provider in self._parse_env_list("EXTERNAL_PROVIDER_MOCK_LIST", default)
            if provider.strip()
        ]

    example_external_api_base_url: str = Field(
        default="",
        title="示例外部 API Base URL",
    )

    model_config = SettingsConfigDict(
        env_file=None, env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


global_config = GlobalConfig()
