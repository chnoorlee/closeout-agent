from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StageStatus(StrEnum):
    WAITING = "waiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class Verdict(StrEnum):
    QUEUED = "queued"
    VERIFIED = "verified"
    REPAIRED = "repaired"
    BLOCKED = "blocked"


class Artifact(BaseModel):
    id: str
    name: str
    media_type: str
    size_bytes: int
    sha256: str
    source: str = "workspace"


class Requirement(BaseModel):
    id: str
    title: str
    source: str
    evidence: list[str] = Field(default_factory=list)
    verdict: Verdict = Verdict.QUEUED
    confidence: float = Field(default=0, ge=0, le=1)
    action: str | None = None


class TimelineEvent(BaseModel):
    id: str
    stage: str
    title: str
    detail: str
    actor: str
    status: StageStatus
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Stage(BaseModel):
    id: str
    label: str
    status: StageStatus = StageStatus.WAITING
    summary: str = "Waiting"


class RunMetrics(BaseModel):
    requirements: int = 0
    verified: int = 0
    repaired: int = 0
    blocked: int = 0
    evidence_coverage: int = Field(default=0, ge=0, le=100)
    autonomous_actions: int = 0


class CloseoutRun(BaseModel):
    id: str
    name: str
    scenario: str
    status: RunStatus = RunStatus.QUEUED
    mode: str = "deterministic-demo"
    model: str
    framework: str = "Google ADK 2"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    idempotency_key: str
    stages: list[Stage] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    events: list[TimelineEvent] = Field(default_factory=list)
    metrics: RunMetrics = Field(default_factory=RunMetrics)
    generated_artifacts: dict[str, str] = Field(default_factory=dict)
    planned_actions: list[str] = Field(default_factory=list)
    bundle_ready: bool = False
    bundle_sha256: str | None = None
    error: str | None = None


class CreateDemoRun(BaseModel):
    scenario: str = "hackathon-closeout"


class HealthResponse(BaseModel):
    status: str
    service: str
    model: str
    framework: str
    ai_mode: str
    store: str
    dispatcher: str
    timestamp: datetime = Field(default_factory=utc_now)
