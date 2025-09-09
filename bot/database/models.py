"""
Модели данных для StudHelper Bot.

Определяет Pydantic модели для объектов базы данных.
"""

import uuid
import datetime
import pydantic


class Student(pydantic.BaseModel):
    id: uuid.UUID
    tg_id: int
    name: str
    group_num: str | None = None


class Team(pydantic.BaseModel):
    id: uuid.UUID
    team_name: str
    product_name: str
    invite_code: str
    admin_id: uuid.UUID


class TeamMember(pydantic.BaseModel):
    team_id: uuid.UUID
    student_id: uuid.UUID
    role: str


class SprintReport(pydantic.BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    sprint_num: int
    report_date: datetime.datetime
    report_text: str


class TeamMemberRating(pydantic.BaseModel):
    id: uuid.UUID
    assessor_id: uuid.UUID
    assessed_id: uuid.UUID
    overall_rating: int
    advantages: str
    disadvantages: str
    rate_date: datetime.datetime
