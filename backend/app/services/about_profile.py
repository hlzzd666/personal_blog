from sqlalchemy.orm import Session

from backend.app.models.about_profile import AboutProfile
from backend.app.schemas.about_profile import AboutProfileResponse, AboutProfileUpdate


DEFAULT_ABOUT_PROFILE = AboutProfileUpdate(
    display_name="王路飞",
    role="全栈开发者 / 独立创作者",
    headline="把复杂问题拆成清晰产品，也把沿途的思考写成航海日志。",
    bio=(
        "我关注产品体验、前后端工程与长期可维护的软件设计。工作之外，我会记录技术实践、"
        "项目复盘和生活观察，希望这里不仅是一份履历，也是一张持续更新的个人航海图。"
    ),
    avatar_url="http://127.0.0.1:8000/uploads/eaed8b38790549ea926f1112d6435e46.jpg",
    resume_url="",
    resume_filename="",
    status_text="正在航行，欢迎交流",
    email=None,
    location_name="中国 · 上海",
    location_longitude=121.473701,
    location_latitude=31.230416,
    metrics=[
        {"value": "持续", "label": "写作状态"},
        {"value": "全栈", "label": "工程视角"},
        {"value": "开放", "label": "合作态度"},
    ],
    work_experiences=[
        {
            "organization": "独立开发与长期实践",
            "role": "产品工程师",
            "period": "现在",
            "summary": "围绕真实需求完成从产品梳理、界面设计到前后端交付的完整闭环。",
            "highlights": ["关注可维护架构与体验细节", "持续沉淀可复用的工程方法"],
        }
    ],
    project_experiences=[
        {
            "name": "个人航海日志",
            "role": "设计与全栈开发",
            "period": "持续维护",
            "summary": "一个以航海为叙事线索的个人博客，承载文章、项目复盘与个人档案。",
            "link_url": None,
            "technologies": ["Vue 3", "TypeScript", "FastAPI", "MySQL"],
        }
    ],
    skills=[
        {"name": "Vue", "icon_url": ""},
        {"name": "TypeScript", "icon_url": ""},
        {"name": "CSS", "icon_url": ""},
        {"name": "Vite", "icon_url": ""},
        {"name": "Python", "icon_url": ""},
        {"name": "FastAPI", "icon_url": ""},
        {"name": "SQLAlchemy", "icon_url": ""},
        {"name": "MySQL", "icon_url": ""},
    ],
    social_links=[],
    interests=["写作", "摄影", "旅行", "开源"],
    site_title="关于本站",
    site_description=(
        "这里是我的长期数字花园。文章不追求即时热度，更在意一次实践真正留下了什么。"
        "站点由前后台独立维护，所有公开内容都可以在管理端持续更新。"
    ),
    site_launched_at="持续迭代中",
    site_stack=["Vue 3", "TypeScript", "FastAPI", "SQLAlchemy", "MySQL"],
    site_repository_url=None,
)


def get_about_profile(session: Session) -> AboutProfile:
    profile = session.get(AboutProfile, 1)
    if profile is not None:
        return profile

    profile = AboutProfile(id=1, **DEFAULT_ABOUT_PROFILE.model_dump(mode="json"))
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def update_about_profile(session: Session, payload: AboutProfileUpdate) -> AboutProfile:
    profile = get_about_profile(session)
    for field, value in payload.model_dump(mode="json").items():
        setattr(profile, field, value)
    session.commit()
    session.refresh(profile)
    return profile


def serialize_about_profile(profile: AboutProfile) -> AboutProfileResponse:
    return AboutProfileResponse.model_validate(profile)
