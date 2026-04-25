from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field, model_validator

app = FastAPI(title="TimeBox Planner API", version="0.1.0")


class ProviderType(str, Enum):
    GOOGLE = "GOOGLE"
    KAKAO = "KAKAO"
    NAVER = "NAVER"


class User(BaseModel):
    id: str
    providerType: ProviderType
    providerUserId: str
    email: str
    nickname: str
    profileImageUrl: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class TemplateBlockIn(BaseModel):
    startTime: str
    endTime: str
    title: str = Field(min_length=1)
    memo: Optional[str] = None
    sortOrder: int = Field(ge=0)


class TemplateBlock(TemplateBlockIn):
    id: str
    templateId: str
    createdAt: datetime
    updatedAt: datetime


class TimeboxTemplateIn(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    isDefault: bool = False
    blocks: List[TemplateBlockIn] = Field(default_factory=list)


class TimeboxTemplate(TimeboxTemplateIn):
    id: str
    userId: str
    createdAt: datetime
    updatedAt: datetime
    blocks: List[TemplateBlock]


class DailyGoalIn(BaseModel):
    content: str = Field(min_length=1)
    isCompleted: bool = False
    sortOrder: int = Field(ge=0)


class DailyGoal(DailyGoalIn):
    id: str
    dailyPlanId: str
    createdAt: datetime
    updatedAt: datetime


class DailyTimeBlockIn(BaseModel):
    startTime: str
    endTime: str
    title: str = Field(min_length=1)
    memo: Optional[str] = None
    isCompleted: bool = False
    sortOrder: int = Field(ge=0)


class DailyTimeBlock(DailyTimeBlockIn):
    id: str
    dailyPlanId: str
    createdAt: datetime
    updatedAt: datetime


class DailyPlanIn(BaseModel):
    planDate: date
    templateId: Optional[str] = None
    goals: List[DailyGoalIn] = Field(default_factory=list)
    timeBlocks: List[DailyTimeBlockIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_goal_count(self) -> "DailyPlanIn":
        if not (1 <= len(self.goals) <= 5):
            raise ValueError("Goals must be between 1 and 5.")
        return self


class DailyPlan(BaseModel):
    id: str
    userId: str
    planDate: date
    templateId: Optional[str] = None
    goals: List[DailyGoal]
    timeBlocks: List[DailyTimeBlock]
    createdAt: datetime
    updatedAt: datetime


class DB:
    users: Dict[str, User] = {}
    templates: Dict[str, Dict[str, TimeboxTemplate]] = {}
    plans: Dict[str, Dict[str, DailyPlan]] = {}


def parse_hhmm_to_min(value: str) -> int:
    try:
        hh, mm = value.split(":")
        h, m = int(hh), int(mm)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {value}") from exc

    if h < 0 or h > 23 or m < 0 or m > 59:
        raise HTTPException(status_code=400, detail=f"Invalid time: {value}")
    if m % 10 != 0:
        raise HTTPException(status_code=400, detail="Time must be in 10-minute increments.")
    return h * 60 + m


def validate_non_overlapping(blocks: List[DailyTimeBlockIn | TemplateBlockIn]) -> None:
    ranges = []
    for block in blocks:
        start = parse_hhmm_to_min(block.startTime)
        end = parse_hhmm_to_min(block.endTime)
        if start >= end:
            raise HTTPException(status_code=400, detail="startTime must be earlier than endTime.")
        ranges.append((start, end))

    ranges.sort(key=lambda x: x[0])
    for i in range(1, len(ranges)):
        if ranges[i][0] < ranges[i - 1][1]:
            raise HTTPException(status_code=400, detail="Time blocks cannot overlap.")


def auth_required(x_user_id: Optional[str] = Header(default=None)) -> User:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    user = DB.users.get(x_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return user


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/auth/google")
def auth_google() -> dict:
    return {"message": "OAuth redirect endpoint placeholder for Google."}


@app.get("/api/auth/kakao")
def auth_kakao() -> dict:
    return {"message": "OAuth redirect endpoint placeholder for Kakao."}


@app.get("/api/auth/naver")
def auth_naver() -> dict:
    return {"message": "OAuth redirect endpoint placeholder for Naver."}


@app.post("/api/auth/logout")
def auth_logout(_: User = Depends(auth_required)) -> dict:
    return {"message": "Logged out"}


@app.get("/api/auth/me", response_model=User)
def auth_me(user: User = Depends(auth_required)) -> User:
    return user


class LoginRequest(BaseModel):
    providerType: ProviderType
    providerUserId: str
    email: str
    nickname: str
    profileImageUrl: Optional[str] = None


@app.post("/api/auth/mock-login", response_model=User)
def mock_login(req: LoginRequest) -> User:
    now = datetime.utcnow()
    user = User(
        id=str(uuid4()),
        providerType=req.providerType,
        providerUserId=req.providerUserId,
        email=req.email,
        nickname=req.nickname,
        profileImageUrl=req.profileImageUrl,
        createdAt=now,
        updatedAt=now,
    )
    DB.users[user.id] = user
    DB.templates.setdefault(user.id, {})
    DB.plans.setdefault(user.id, {})
    return user


@app.get("/api/templates", response_model=List[TimeboxTemplate])
def list_templates(user: User = Depends(auth_required)) -> List[TimeboxTemplate]:
    return list(DB.templates[user.id].values())


@app.post("/api/templates", response_model=TimeboxTemplate)
def create_template(payload: TimeboxTemplateIn, user: User = Depends(auth_required)) -> TimeboxTemplate:
    validate_non_overlapping(payload.blocks)
    now = datetime.utcnow()
    template_id = str(uuid4())

    if payload.isDefault:
        for tid, tpl in DB.templates[user.id].items():
            DB.templates[user.id][tid] = tpl.model_copy(update={"isDefault": False, "updatedAt": now})

    blocks = [
        TemplateBlock(
            id=str(uuid4()),
            templateId=template_id,
            startTime=b.startTime,
            endTime=b.endTime,
            title=b.title,
            memo=b.memo,
            sortOrder=b.sortOrder,
            createdAt=now,
            updatedAt=now,
        )
        for b in sorted(payload.blocks, key=lambda x: x.sortOrder)
    ]

    template = TimeboxTemplate(
        id=template_id,
        userId=user.id,
        name=payload.name,
        description=payload.description,
        isDefault=payload.isDefault,
        blocks=blocks,
        createdAt=now,
        updatedAt=now,
    )
    DB.templates[user.id][template_id] = template
    return template


@app.get("/api/templates/{template_id}", response_model=TimeboxTemplate)
def get_template(template_id: str, user: User = Depends(auth_required)) -> TimeboxTemplate:
    template = DB.templates[user.id].get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@app.put("/api/templates/{template_id}", response_model=TimeboxTemplate)
def update_template(template_id: str, payload: TimeboxTemplateIn, user: User = Depends(auth_required)) -> TimeboxTemplate:
    existing = DB.templates[user.id].get(template_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")

    validate_non_overlapping(payload.blocks)
    now = datetime.utcnow()
    if payload.isDefault:
        for tid, tpl in DB.templates[user.id].items():
            DB.templates[user.id][tid] = tpl.model_copy(update={"isDefault": False, "updatedAt": now})

    blocks = [
        TemplateBlock(
            id=str(uuid4()),
            templateId=template_id,
            startTime=b.startTime,
            endTime=b.endTime,
            title=b.title,
            memo=b.memo,
            sortOrder=b.sortOrder,
            createdAt=now,
            updatedAt=now,
        )
        for b in sorted(payload.blocks, key=lambda x: x.sortOrder)
    ]

    updated = existing.model_copy(
        update={
            "name": payload.name,
            "description": payload.description,
            "isDefault": payload.isDefault,
            "blocks": blocks,
            "updatedAt": now,
        }
    )
    DB.templates[user.id][template_id] = updated
    return updated


@app.delete("/api/templates/{template_id}")
def delete_template(template_id: str, user: User = Depends(auth_required)) -> dict:
    if template_id not in DB.templates[user.id]:
        raise HTTPException(status_code=404, detail="Template not found")
    del DB.templates[user.id][template_id]
    return {"deleted": True}


@app.post("/api/templates/{template_id}/copy", response_model=TimeboxTemplate)
def copy_template(template_id: str, user: User = Depends(auth_required)) -> TimeboxTemplate:
    template = DB.templates[user.id].get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    payload = TimeboxTemplateIn(
        name=f"{template.name} (copy)",
        description=template.description,
        isDefault=False,
        blocks=[
            TemplateBlockIn(
                startTime=b.startTime,
                endTime=b.endTime,
                title=b.title,
                memo=b.memo,
                sortOrder=b.sortOrder,
            )
            for b in template.blocks
        ],
    )
    return create_template(payload=payload, user=user)


@app.put("/api/templates/{template_id}/default", response_model=TimeboxTemplate)
def set_default_template(template_id: str, user: User = Depends(auth_required)) -> TimeboxTemplate:
    template = DB.templates[user.id].get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    now = datetime.utcnow()
    for tid, tpl in DB.templates[user.id].items():
        DB.templates[user.id][tid] = tpl.model_copy(update={"isDefault": tid == template_id, "updatedAt": now})
    return DB.templates[user.id][template_id]


def build_plan(plan_in: DailyPlanIn, user_id: str) -> DailyPlan:
    validate_non_overlapping(plan_in.timeBlocks)
    now = datetime.utcnow()
    plan_id = str(uuid4())
    goals = [
        DailyGoal(
            id=str(uuid4()),
            dailyPlanId=plan_id,
            content=g.content,
            isCompleted=g.isCompleted,
            sortOrder=g.sortOrder,
            createdAt=now,
            updatedAt=now,
        )
        for g in sorted(plan_in.goals, key=lambda x: x.sortOrder)
    ]
    blocks = [
        DailyTimeBlock(
            id=str(uuid4()),
            dailyPlanId=plan_id,
            startTime=b.startTime,
            endTime=b.endTime,
            title=b.title,
            memo=b.memo,
            isCompleted=b.isCompleted,
            sortOrder=b.sortOrder,
            createdAt=now,
            updatedAt=now,
        )
        for b in sorted(plan_in.timeBlocks, key=lambda x: x.sortOrder)
    ]
    return DailyPlan(
        id=plan_id,
        userId=user_id,
        planDate=plan_in.planDate,
        templateId=plan_in.templateId,
        goals=goals,
        timeBlocks=blocks,
        createdAt=now,
        updatedAt=now,
    )


@app.get("/api/daily-plans", response_model=List[DailyPlan])
def list_daily_plans(date_filter: Optional[date] = None, user: User = Depends(auth_required)) -> List[DailyPlan]:
    plans = list(DB.plans[user.id].values())
    if date_filter:
        plans = [p for p in plans if p.planDate == date_filter]
    return sorted(plans, key=lambda p: p.planDate)


@app.post("/api/daily-plans", response_model=DailyPlan)
def create_daily_plan(payload: DailyPlanIn, user: User = Depends(auth_required)) -> DailyPlan:
    plan = build_plan(payload, user.id)
    DB.plans[user.id][plan.id] = plan
    return plan


@app.get("/api/daily-plans/{daily_plan_id}", response_model=DailyPlan)
def get_daily_plan(daily_plan_id: str, user: User = Depends(auth_required)) -> DailyPlan:
    plan = DB.plans[user.id].get(daily_plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Daily plan not found")
    return plan


@app.put("/api/daily-plans/{daily_plan_id}", response_model=DailyPlan)
def update_daily_plan(daily_plan_id: str, payload: DailyPlanIn, user: User = Depends(auth_required)) -> DailyPlan:
    if daily_plan_id not in DB.plans[user.id]:
        raise HTTPException(status_code=404, detail="Daily plan not found")
    updated = build_plan(payload, user.id).model_copy(update={"id": daily_plan_id})
    DB.plans[user.id][daily_plan_id] = updated
    return updated


@app.delete("/api/daily-plans/{daily_plan_id}")
def delete_daily_plan(daily_plan_id: str, user: User = Depends(auth_required)) -> dict:
    if daily_plan_id not in DB.plans[user.id]:
        raise HTTPException(status_code=404, detail="Daily plan not found")
    del DB.plans[user.id][daily_plan_id]
    return {"deleted": True}


@app.post("/api/daily-plans/from-template/{template_id}", response_model=DailyPlan)
def create_daily_plan_from_template(
    template_id: str, planDate: date, user: User = Depends(auth_required)
) -> DailyPlan:
    template = DB.templates[user.id].get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    payload = DailyPlanIn(
        planDate=planDate,
        templateId=template_id,
        goals=[DailyGoalIn(content="", sortOrder=0)],
        timeBlocks=[
            DailyTimeBlockIn(
                startTime=b.startTime,
                endTime=b.endTime,
                title=b.title,
                memo=b.memo,
                isCompleted=False,
                sortOrder=b.sortOrder,
            )
            for b in template.blocks
        ],
    )
    # Ensure at least one non-empty goal for policy compliance.
    payload.goals[0].content = "오늘의 핵심 목표를 입력하세요"
    plan = build_plan(payload, user.id)
    DB.plans[user.id][plan.id] = plan
    return plan
