from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    code: int = Field(..., examples=[200])
    status: int = Field(..., examples=[200])
    message: str = Field(..., examples=["ok"])
    data: DataT | None = None
    request_id: str = Field(..., examples=["b51f8d5f6a4b4b3ea03f69e9976db6bb"])


class ErrorDetail(BaseModel):
    detail: object
