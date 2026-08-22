from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class ProfileMetric(BaseModel):
    value: str = Field(..., min_length=1, max_length=20)
    label: str = Field(..., min_length=1, max_length=30)


class WorkExperience(BaseModel):
    organization: str = Field(..., min_length=1, max_length=120)
    role: str = Field(..., min_length=1, max_length=120)
    period: str = Field(..., min_length=1, max_length=60)
    summary: str = Field(..., min_length=1, max_length=500)
    highlights: list[str] = Field(default_factory=list, max_length=8)


class ProjectExperience(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    role: str = Field(..., min_length=1, max_length=120)
    period: str = Field(..., min_length=1, max_length=60)
    summary: str = Field(..., min_length=1, max_length=500)
    link_url: HttpUrl | None = None
    technologies: list[str] = Field(default_factory=list, max_length=12)


class SkillItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    icon_url: str = Field(default="", max_length=2048)


class SocialLink(BaseModel):
    platform: str = Field(..., min_length=1, max_length=40)
    label: str = Field(..., min_length=1, max_length=80)
    url: HttpUrl


class AboutProfileBase(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=80)
    role: str = Field(..., min_length=1, max_length=120)
    headline: str = Field(..., min_length=1, max_length=160)
    bio: str = Field(..., min_length=1, max_length=2000)
    avatar_url: str = Field(..., min_length=1, max_length=2048)
    resume_url: str = Field(default="", max_length=2048)
    resume_filename: str = Field(default="", max_length=255)
    status_text: str = Field(..., min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=254)
    location_name: str = Field(..., min_length=1, max_length=100)
    location_longitude: float | None = Field(default=None, ge=-180, le=180)
    location_latitude: float | None = Field(default=None, ge=-90, le=90)
    metrics: list[ProfileMetric] = Field(default_factory=list, max_length=6)
    work_experiences: list[WorkExperience] = Field(default_factory=list, max_length=20)
    project_experiences: list[ProjectExperience] = Field(default_factory=list, max_length=20)
    skills: list[SkillItem] = Field(default_factory=list, max_length=60)
    social_links: list[SocialLink] = Field(default_factory=list, max_length=12)
    interests: list[str] = Field(default_factory=list, max_length=20)
    site_title: str = Field(..., min_length=1, max_length=120)
    site_description: str = Field(..., min_length=1, max_length=1200)
    site_launched_at: str = Field(..., min_length=1, max_length=40)
    site_stack: list[str] = Field(default_factory=list, max_length=20)
    site_repository_url: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_location_coordinates(self) -> "AboutProfileBase":
        if (self.location_latitude is None) != (self.location_longitude is None):
            raise ValueError("位置经纬度必须同时填写")
        skill_names = [skill.name.strip().casefold() for skill in self.skills]
        if len(skill_names) != len(set(skill_names)):
            raise ValueError("技术栈名称不能重复")
        return self


class AboutProfileUpdate(AboutProfileBase):
    pass


class AboutProfileResponse(AboutProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime
