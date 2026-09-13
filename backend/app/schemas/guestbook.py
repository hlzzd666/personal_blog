from datetime import datetime
from typing import Literal
import unicodedata

from pydantic import BaseModel, Field, field_validator


GuestbookStatus = Literal["pending", "approved", "rejected", "spam", "deleted"]


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\x00", "").split())


class GuestbookCreate(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=40)
    content: str = Field(..., min_length=1, max_length=2000)
    honeypot: str = Field(default="", max_length=100)

    @field_validator("nickname", "content")
    @classmethod
    def normalize(cls, value: str) -> str:
        cleaned = unicodedata.normalize("NFKC", value)
        cleaned = "".join(char for char in cleaned if char in "\n\t" or not unicodedata.category(char).startswith("C")).strip()
        if not cleaned:
            raise ValueError("不能为空")
        return cleaned


class GuestbookPublicItem(BaseModel):
    id: int
    nickname: str
    content: str
    created_at: datetime
    admin_reply: str = ""

    model_config = {"from_attributes": True}


class GuestbookPublicList(BaseModel):
    items: list[GuestbookPublicItem]
    total: int
    page: int
    page_size: int


class GuestbookManageItem(GuestbookPublicItem):
    status: GuestbookStatus
    visitor_hash: str
    risk_score: int
    admin_note: str
    reviewed_at: datetime | None
    updated_at: datetime
    deleted_at: datetime | None


class GuestbookManageList(BaseModel):
    items: list[GuestbookManageItem]
    total: int
    page: int
    page_size: int
    pending_count: int


class GuestbookStatusUpdate(BaseModel):
    status: GuestbookStatus
    reason: str = Field(default="", max_length=500)


class GuestbookReplyUpdate(BaseModel):
    admin_reply: str = Field(default="", max_length=2000)
