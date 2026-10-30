from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api import ai, benchmark, dashboard, data, export, health, history, issues, proposals, rules, search, sessions, verify
from app.config import settings
from app.core.session_store import purge_expired
from app.db import init_db
from app.errors import install_error_handlers

logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("csvrescue")

app = FastAPI(title="CSV Rescue", version="1.0.0", openapi_url="/api/v1/openapi.json")
install_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SecurityHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        )
        return response


app.add_middleware(SecurityHeaders)

prefix = "/api/v1"
for r in (
    health.router,
    sessions.router,
    dashboard.router,
    data.router,
    issues.router,
    proposals.router,
    history.router,
    rules.router,
    verify.router,
    export.router,
    ai.router,
    search.router,
    benchmark.router,
):
    app.include_router(r, prefix=prefix)


@app.on_event("startup")
def startup():
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    purge_expired()
    log.info("csv-rescue ready")


static_dir = Path(settings.STATIC_DIR) if settings.STATIC_DIR else None
if static_dir and static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    @app.exception_handler(404)
    async def spa_fallback(request: Request, exc):
        if request.url.path.startswith("/api"):
            from app.errors import envelope
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=404, content=envelope("SESSION_NOT_FOUND", "Not found", ""))
        index = static_dir / "index.html"
        if index.exists():
            return FileResponse(index)
        from app.errors import envelope
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=404, content=envelope("SESSION_NOT_FOUND", "Not found", ""))
