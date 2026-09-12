from datetime import date, datetime, time, timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from backend.app.models.visitor_record import VisitorRecord
from backend.app.schemas.visitor_location import VisitorLocation
from backend.app.schemas.visitor_record import (
    VisitorRecordCreate,
    VisitorDailyCount,
    VisitorDailyStatsResponse,
    VisitorRecordListResponse,
    VisitorRecordResponse,
)


def detect_device_type(user_agent: str | None) -> str:
    value = (user_agent or "").lower()
    if any(token in value for token in ("bot", "spider", "crawler", "slurp")):
        return "bot"
    if "ipad" in value or "tablet" in value:
        return "tablet"
    if any(token in value for token in ("mobile", "iphone", "android")):
        return "mobile"
    return "desktop"


def create_visitor_record(
    session: Session,
    payload: VisitorRecordCreate,
    *,
    ip: str,
    referer: str | None,
    user_agent: str | None,
    location: VisitorLocation,
) -> VisitorRecordResponse:
    record = VisitorRecord(
        ip=ip[:64],
        city=location.city,
        region=location.region,
        country=location.country,
        page_path=payload.page_path,
        referer=referer[:2048] if referer else None,
        user_agent=user_agent[:4096] if user_agent else None,
        device_type=detect_device_type(user_agent),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return VisitorRecordResponse.model_validate(record)


def _date_bounds(visited_from: date | None, visited_to: date | None) -> tuple[datetime | None, datetime | None]:
    return (
        datetime.combine(visited_from, time.min) if visited_from else None,
        datetime.combine(visited_to, time.max) if visited_to else None,
    )


def list_visitor_records(
    session: Session,
    *,
    page: int,
    page_size: int,
    ip: str | None = None,
    city: str | None = None,
    page_path: str | None = None,
    visited_from: date | None = None,
    visited_to: date | None = None,
) -> VisitorRecordListResponse:
    start, end = _date_bounds(visited_from, visited_to)
    filters = []
    if ip:
        filters.append(VisitorRecord.ip.like(f"%{ip.strip()}%"))
    if city:
        filters.append(VisitorRecord.city.like(f"%{city.strip()}%"))
    if page_path:
        filters.append(VisitorRecord.page_path.like(f"%{page_path.strip()}%"))
    if start:
        filters.append(VisitorRecord.visited_at >= start)
    if end:
        filters.append(VisitorRecord.visited_at <= end)

    total = session.scalar(select(func.count(VisitorRecord.id)).where(*filters)) or 0
    items = list(
        session.scalars(
            select(VisitorRecord)
            .where(*filters)
            .order_by(VisitorRecord.visited_at.desc(), VisitorRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    today_start = datetime.combine(date.today(), time.min)
    today_visits = session.scalar(
        select(func.count(VisitorRecord.id)).where(VisitorRecord.visited_at >= today_start)
    ) or 0
    total_visits = session.scalar(select(func.count(VisitorRecord.id))) or 0
    unique_ips = session.scalar(select(func.count(distinct(VisitorRecord.ip)))) or 0
    return VisitorRecordListResponse(
        items=[VisitorRecordResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_visits=total_visits,
        today_visits=today_visits,
        unique_ips=unique_ips,
    )


def get_visitor_daily_stats(session: Session, *, range_days: int = 7) -> VisitorDailyStatsResponse:
    end_date = date.today()
    start_date = end_date - timedelta(days=range_days - 1)
    date_column = func.date(VisitorRecord.visited_at)
    rows = session.execute(
        select(date_column, func.count(VisitorRecord.id))
        .where(
            VisitorRecord.visited_at >= datetime.combine(start_date, time.min),
            VisitorRecord.visited_at < datetime.combine(end_date + timedelta(days=1), time.min),
        )
        .group_by(date_column)
    ).all()
    counts = {str(day): int(count) for day, count in rows}
    days = [
        VisitorDailyCount(date=day, visits=counts.get(day.isoformat(), 0))
        for day in (start_date + timedelta(days=offset) for offset in range(range_days))
    ]
    return VisitorDailyStatsResponse(days=days, today_visits=days[-1].visits)


def delete_visitor_record(session: Session, record: VisitorRecord) -> None:
    session.delete(record)
    session.commit()


def delete_visitor_records(
    session: Session,
    *,
    visited_from: date | None,
    visited_to: date | None,
) -> int:
    start, end = _date_bounds(visited_from, visited_to)
    filters = []
    if start:
        filters.append(VisitorRecord.visited_at >= start)
    if end:
        filters.append(VisitorRecord.visited_at <= end)
    deleted_count = session.query(VisitorRecord).filter(*filters).delete(synchronize_session=False)
    session.commit()
    return deleted_count
