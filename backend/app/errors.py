from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, hint: str = "", status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.status = status
        self.details = details or {}


def envelope(code: str, message: str, hint: str = "", details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "hint": hint, "details": details or {}}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=envelope(exc.code, exc.message, exc.hint, exc.details))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=envelope("INTERNAL", "Something went wrong on our side.", "Try again in a moment."),
        )
