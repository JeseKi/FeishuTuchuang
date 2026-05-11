# -*- coding: utf-8 -*-
"""
FastAPI 应用主入口。

负责应用的生命周期管理、中间件配置、API路由挂载以及前端SPA的集成。
"""

from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Scope

from src.server.config import global_config
from src.server.database import get_database_info, init_database
from src.server.logging_config import setup_logging
from src.server.providers.service import sync_external_providers

# 路由模块
from src.server.auth.router import router as auth_router
from src.server.example_module.router import router as example_router
from src.server.admin.router import router as admin_router
from src.server.scope_management.router import router as scope_management_router
from src.server.oauth.router import router as oauth_router
from src.server.oauth_provider.router import router as oauth_provider_router
from src.server.providers.router import router as provider_dev_router

# --- 配置与常量 ---
PROJECT_ROOT = Path(global_config.project_root)
DIST_DIR = PROJECT_ROOT / "dist"
INDEX_FILE = DIST_DIR / "index.html"
ASSETS_DIRNAME = "assets"  # Vite 默认的 hash 产物目录

setup_logging()


# --- 应用生命周期 ---
@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    应用生命周期管理：
    - 启动时检查并按需初始化数据库。
    """
    logger.info("应用启动中...")
    db_info = get_database_info()
    if not db_info.database_exists:
        logger.warning("数据库不存在，正在执行初始化...")
        init_database()
        logger.success("数据库初始化完成。")
    else:
        logger.info(f"数据库已存在，大小: {db_info.database_size} 字节。")

    from src.server.database import SessionLocal

    db = SessionLocal()
    try:
        sync_external_providers(db)
    finally:
        db.close()

    logger.success("应用启动完成。")
    yield
    logger.info("应用已关闭。")


# --- 应用实例与中间件 ---
fastapi_kwargs = {
    "title": "Fullstack Template Backend",
    "description": "提供身份验证、数据库交互及示例模块的后端服务。",
    "lifespan": lifespan,
}

if global_config.app_env == "prod":
    fastapi_kwargs["docs_url"] = None
    fastapi_kwargs["redoc_url"] = None
    fastapi_kwargs["openapi_url"] = None
    logger.info("生产环境：API 文档已禁用")

app = FastAPI(**fastapi_kwargs)  # type: ignore

app.add_middleware(
    CORSMiddleware,
    allow_origins=global_config.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    自定义中间件，为不同路径设置合适的 Cache-Control 响应头。
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        path = request.url.path

        # 对 Vite 构建的带 hash 的静态资源进行长期缓存
        if path.startswith(f"/{ASSETS_DIRNAME}/"):
            response.headers.setdefault(
                "Cache-Control", "public, max-age=31536000, immutable"
            )
        # 对 SPA 的入口文件和其它 HTML 页面禁用缓存，确保用户总能获取最新版本
        elif path == "/" or path.endswith(".html"):
            response.headers["Cache-Control"] = "no-cache"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    记录每个 HTTP 请求的关键元数据，便于本地排查问题。
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        client_ip = request.client.host if request.client else "-"
        request.state.request_id = request_id

        started_at = perf_counter()

        try:
            with logger.contextualize(
                request_id=request_id,
                client_ip=client_ip,
                user_id=getattr(request.state, "user_id", "-"),
            ):
                response: Response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - started_at) * 1000
            logger.bind(
                log_type="access",
                request_id=request_id,
                client_ip=client_ip,
                user_id=getattr(request.state, "user_id", "-"),
            ).exception(
                f"{request.method} {request.url.path} -> 500 in {duration_ms:.2f} ms"
            )
            raise

        duration_ms = (perf_counter() - started_at) * 1000
        user_id = getattr(request.state, "user_id", "-")
        response.headers["X-Request-ID"] = request_id

        access_message = (
            f"{request.method} {request.url.path} -> "
            f"{response.status_code} in {duration_ms:.2f} ms"
        )
        access_logger = logger.bind(
            log_type="access",
            request_id=request_id,
            client_ip=client_ip,
            user_id=user_id,
        )
        access_level = "ERROR" if response.status_code >= 500 else "INFO"
        access_logger.log(access_level, access_message)
        return response


app.add_middleware(CacheControlMiddleware)
app.add_middleware(RequestLoggingMiddleware)


# --- API 路由 ---
# API 路由建议统一使用 /api 前缀，以避免与前端路由冲突
@app.get("/api/health", summary="健康检查", tags=["系统"])
def health():
    """提供一个简单的健康检查端点，用于监控服务状态。"""
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(oauth_provider_router)
app.include_router(example_router)
app.include_router(admin_router)
app.include_router(scope_management_router)
if global_config.app_env == "dev":
    app.include_router(provider_dev_router)


# --- 前端 SPA 静态文件服务 ---
class SPAStaticFiles(StaticFiles):
    """
    专为单页应用（SPA）设计的静态文件服务。
    当请求的路径在文件系统中不存在时，会回退到服务 index.html，
    从而支持前端路由。
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            # 尝试像常规静态文件一样提供文件
            return await super().get_response(path, scope)
        except Exception:
            # 如果找不到文件 (Starlette 会抛出 RuntimeError, FastAPI 转为 404)
            # 并且请求的不是 API 路径，则返回 SPA 的入口 index.html
            if scope["path"].startswith("/api"):
                return Response(status_code=404)  # API 的 404 应该由 FastAPI 框架处理

            if INDEX_FILE.exists():
                return FileResponse(INDEX_FILE)
            else:
                logger.error(f"SPA 入口文件未找到: {INDEX_FILE}")
                return Response(
                    "Frontend entrypoint (index.html) not found.", status_code=500
                )


# 将前端构建产物目录挂载到根路径
# 注意：这必须在所有 API 路由之后挂载，以作为路径匹配的回退
if DIST_DIR.exists():
    app.mount(
        "/",
        SPAStaticFiles(directory=str(DIST_DIR), html=True),
        name="spa-frontend",
    )
else:
    logger.warning(
        f"前端构建目录 '{DIST_DIR}' 不存在，将不会提供前端页面。"
        "请确认是否已执行前端构建步骤。"
    )
