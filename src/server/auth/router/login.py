"""Login and token refresh routes."""

from fastapi.responses import JSONResponse

from fastapi import Depends, HTTPException, Request, Response, Security, status
from jose import jwt
from sqlalchemy.orm import Session

from src.server.database import get_db
from .. import service
from ..config import auth_config
from ..dependencies import (
    CurrentRefreshSession,
    get_current_refresh_session,
    get_current_user,
)
from ..models import User
from ..schemas import LoginChallengeResponse, MessageResponse, TokenResponse, UserLogin
from .base import router


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=auth_config.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=auth_config.refresh_cookie_secure,
        samesite=auth_config.refresh_cookie_samesite,  # type: ignore
        max_age=auth_config.refresh_token_ttl_days * 24 * 60 * 60,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=auth_config.refresh_cookie_name,
        path="/api/auth",
        secure=auth_config.refresh_cookie_secure,
        samesite=auth_config.refresh_cookie_samesite,  # type: ignore
    )


def _build_token_response(access_token: str, user: User) -> dict[str, str]:
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "scope": service.serialize_scopes(service.get_user_scopes(user)),
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
    description="用户通过用户名或邮箱以及密码进行身份验证，获取访问令牌和刷新令牌",
    response_description="返回访问令牌和刷新令牌",
    responses={
        200: {"description": "登录成功"},
        202: {"model": LoginChallengeResponse, "description": "需要继续完成 2FA"},
        401: {"description": "用户名/邮箱或密码错误"},
    },
)
async def login_for_access_token(
    request: Request,
    login_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    await service.verify_turnstile_token(
        request=request,
        token=login_data.turnstile_token,
        action="auth_login",
    )
    user = service.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="不正确的用户名/邮箱或密码",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if service.is_user_disabled(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被停用",
        )

    if service.is_two_factor_enabled(user):
        challenge_token = service.begin_login_challenge(db, user)
        payload = LoginChallengeResponse(challenge_token=challenge_token)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED, content=payload.model_dump()
        )

    access_token, refresh_token = service.issue_token_pair(db, user)
    _set_refresh_cookie(response, refresh_token)
    return _build_token_response(access_token, user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新访问令牌",
    description="使用刷新令牌获取新的访问令牌和刷新令牌对",
    response_description="返回新的访问令牌和刷新令牌",
    responses={
        200: {"description": "令牌刷新成功"},
        401: {"description": "无效的刷新令牌"},
    },
)
async def refresh_access_token(
    response: Response,
    db: Session = Depends(get_db),
    current_session: CurrentRefreshSession = Depends(get_current_refresh_session),
):
    new_access_token, new_refresh_token = service.rotate_refresh_token(
        db, current_session.user, current_session.refresh_token
    )
    _set_refresh_cookie(response, new_refresh_token)
    return _build_token_response(new_access_token, current_session.user)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="退出当前设备",
    description="撤销当前设备的 refresh token，并清理认证 cookie",
    response_description="返回退出结果",
    responses={200: {"description": "退出成功"}},
)
async def logout_current_device(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get(auth_config.refresh_cookie_name)
    if refresh_token:
        try:
            payload = jwt.decode(
                refresh_token,
                auth_config.jwt_secret_key,
                algorithms=[auth_config.jwt_algorithm],
            )
            refresh_jti = payload.get("jti")
            if isinstance(refresh_jti, str) and refresh_jti:
                service.revoke_refresh_token(db, refresh_jti)
        except Exception:
            pass

    _clear_refresh_cookie(response)
    return {"message": "已退出当前设备"}


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="退出所有设备",
    description="撤销当前用户的全部会话，并使所有旧 token 立即失效",
    response_description="返回退出结果",
    responses={
        200: {"description": "已退出所有设备"},
        401: {"description": "未认证或令牌无效"},
    },
)
async def logout_all_devices(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[service.SCOPE_PROFILE_READ]
    ),
):
    service.revoke_all_user_sessions(db, current_user)
    _clear_refresh_cookie(response)
    return {"message": "已退出所有设备"}
