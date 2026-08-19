from starlette.requests import Request

from backend.app.schemas.common import ApiResponse


def build_success_response(
    request: Request,
    data: object = None,
    message: str = "ok",
    status_code: int = 200,
) -> ApiResponse[object]:
    return ApiResponse(
        code=status_code,
        status=status_code,
        message=message,
        data=data,
        request_id=request.state.request_id,
    )
