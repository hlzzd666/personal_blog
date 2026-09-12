from datetime import date, datetime

from pydantic import BaseModel, Field


class VisitorRecordCreate(BaseModel):
    page_path: str = Field(..., min_length=1, max_length=2048, pattern=r"^/")


class VisitorRecordResponse(BaseModel):
    id: int
    ip: str
    city: str | None = None
    region: str | None = None
    country: str | None = None
    page_path: str
    referer: str | None = None
    user_agent: str | None = None
    device_type: str
    visited_at: datetime

    model_config = {"from_attributes": True}


class VisitorRecordListResponse(BaseModel):
    items: list[VisitorRecordResponse]
    total: int
    page: int
    page_size: int
    total_visits: int
    today_visits: int
    unique_ips: int


class VisitorDailyCount(BaseModel):
    date: date
    visits: int


class VisitorDailyStatsResponse(BaseModel):
    days: list[VisitorDailyCount]
    today_visits: int


class VisitorRecordDeleteResponse(BaseModel):
    deleted_count: int
    visited_from: date | None = None
    visited_to: date | None = None
