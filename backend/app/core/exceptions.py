from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.schemas.common import ApiResponse, ErrorDetail


def _request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", uuid4().hex)


def _error_response(
    request: Request,
    status_code: int,
    message: str,
    detail: object,
) -> JSONResponse:
    payload = ApiResponse[ErrorDetail](
        code=status_code,
        status=status_code,
        message=message,
        data=ErrorDetail(detail=detail),
        request_id=_request_id_from(request),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(request, exc.status_code, str(exc.detail), exc.detail)

    @app.exception_handler(StarletteHTTPException)
    async def handle_starlette_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _error_response(request, exc.status_code, str(exc.detail), exc.detail)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "request validation failed",
            exc.errors(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal server error",
            str(exc),
        )
