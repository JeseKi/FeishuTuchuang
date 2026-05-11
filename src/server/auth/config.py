# -*- coding: utf-8 -*-
"""
认证相关配置（模板版）

公开接口：
- `auth_config`
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    """认证配置"""

    jwt_secret_key: str = Field(
        default="dev_secret_key_for_testing_only",
        title="JWT 密钥",
        description="生产务必通过环境变量覆盖",
    )
    jwt_algorithm: str = Field(default="HS256", title="JWT 算法")
    access_token_ttl_minutes: int = Field(default=15, title="Access Token 有效期(分钟)")
    refresh_token_ttl_days: int = Field(default=7, title="Refresh Token 有效期(天)")
    refresh_cookie_name: str = Field(
        default="fullstack_template_refresh_token", title="Refresh Cookie 名称"
    )
    refresh_cookie_samesite: str = Field(default="lax", title="Refresh Cookie SameSite")
    refresh_cookie_secure: bool = Field(
        default=False, title="Refresh Cookie 是否仅 HTTPS"
    )
    test_token: str = Field(
        default="KISPACE_TEST_TOKEN",
        title="测试 Token",
        description="dev/test 环境用于便捷鉴权",
    )
    init_admin_name: str = Field(
        default="admin",
        title="初始化管理员用户名",
        description="生产务必通过环境变量覆盖",
    )
    init_admin_password: str = Field(
        default="admin123",
        title="初始化管理员密码",
        description="生产务必通过环境变量覆盖",
    )
    init_admin_email: str = Field(
        default="admin@example.com",
        title="初始化管理员邮箱",
        description="生产务必通过环境变量覆盖",
    )
    two_factor_challenge_ttl_minutes: int = Field(
        default=5, title="2FA 登录挑战有效期(分钟)"
    )
    two_factor_setup_ttl_minutes: int = Field(
        default=10, title="2FA 绑定确认有效期(分钟)"
    )
    two_factor_issuer_name: str = Field(
        default="Fullstack Template", title="TOTP Issuer 名称"
    )
    two_factor_encryption_key: str = Field(
        default="fullstack-template-2fa-dev-key-change-me",
        title="2FA secret 加密密钥",
        description="生产务必通过环境变量覆盖",
    )
    two_factor_backup_code_count: int = Field(default=8, title="backup code 数量")
    two_factor_max_verify_attempts: int = Field(default=5, title="登录挑战最大校验次数")
    turnstile_enabled: bool = Field(
        default=False, title="是否开启 Cloudflare Turnstile"
    )
    turnstile_secret_key: str = Field(
        default="",
        title="Cloudflare Turnstile Secret Key",
        description="启用 Turnstile 时必填。",
    )
    turnstile_verify_timeout_seconds: int = Field(
        default=4, title="Turnstile 校验超时秒数"
    )


auth_config = AuthConfig()
