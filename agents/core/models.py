"""
agents/core/models.py
=====================
Shared data models for all AgentHire agents.

Uses Python dataclasses for lightweight domain objects and TypedDicts for
wire-format data (JSON payloads sent between agents / n8n workflows).

All monetary values are integers in the job's declared currency.
All timestamps are ISO-8601 strings when serialised over HTTP.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, TypedDict


# =============================================================================
# Enumerations — kept in sync with database/migrations/001_init.sql enums
# =============================================================================

class PortalName(str, Enum):
    """Supported job portals."""
    LINKEDIN = "linkedin"
    CHILETRABAJOS = "chiletrabajos"
    COMPUTRABAJO = "computrabajo"
    TRABAJANDO = "trabajando"
    LABORUM = "laborum"


class JobStatus(str, Enum):
    """Lifecycle status of a discovered job."""
    DISCOVERED = "discovered"
    RANKED = "ranked"
    QUEUED = "queued"
    APPLIED = "applied"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"
    DISCARDED = "discarded"


class DocType(str, Enum):
    """Type of a generated document."""
    CV = "cv"
    COVER_LETTER = "cover_letter"


class EventType(str, Enum):
    """Application lifecycle event types."""
    APPLIED = "applied"
    VIEWED = "viewed"
    REJECTED = "rejected"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    OFFER_RECEIVED = "offer_received"
    WITHDRAWN = "withdrawn"


class Recommendation(str, Enum):
    """LLM ranking recommendation."""
    APPLY = "apply"
    SKIP = "skip"
    MANUAL_REVIEW = "manual_review"


# =============================================================================
# Domain Dataclasses
# =============================================================================

@dataclass
class Job:
    """
    A job listing as stored in the jobs table.

    Instances are created by agent-discovery after scraping a portal and
    enriched by subsequent agents in the pipeline.
    """
    title: str
    company: str
    url: str
    portal: PortalName
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    external_id: Optional[str] = None
    location: Optional[str] = None
    modality: Optional[str] = None          # 'remote' | 'hybrid' | 'presencial'
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "CLP"
    description: Optional[str] = None
    requirements: Optional[str] = None
    posted_at: Optional[datetime] = None
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    status: JobStatus = JobStatus.DISCOVERED
    raw_json: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict suitable for JSON encoding."""
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "url": self.url,
            "portal": self.portal.value,
            "external_id": self.external_id,
            "location": self.location,
            "modality": self.modality,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "currency": self.currency,
            "description": self.description,
            "requirements": self.requirements,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "discovered_at": self.discovered_at.isoformat(),
            "status": self.status.value,
        }


@dataclass
class SkillsMatch:
    """Structured skills comparison produced by the ranking agent."""
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        return {"matched": self.matched, "missing": self.missing}


@dataclass
class JobRanking:
    """
    AI-generated ranking for a single job.

    score: 0–100. Scores ≥ 70 are typically auto-queued for application.
    """
    job_id: str
    score: int
    recommendation: Recommendation
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    skills_match: SkillsMatch = field(default_factory=SkillsMatch)
    cv_template: Optional[str] = None       # e.g. "backend", "fullstack"
    analysis: Optional[str] = None
    red_flags: list[str] = field(default_factory=list)
    ranked_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "score": self.score,
            "recommendation": self.recommendation.value,
            "skills_match": self.skills_match.to_dict(),
            "cv_template": self.cv_template,
            "analysis": self.analysis,
            "red_flags": self.red_flags,
            "ranked_at": self.ranked_at.isoformat(),
        }


@dataclass
class Document:
    """
    A generated PDF or Markdown document (CV or cover letter).

    path points to the file inside the app_outputs Docker volume.
    """
    job_id: str
    type: DocType
    filename: str
    path: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    template_used: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "type": self.type.value,
            "filename": self.filename,
            "path": self.path,
            "template_used": self.template_used,
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class Application:
    """
    A submitted job application, linking a job to its documents.

    human_approved tracks whether a human reviewed and approved the
    submission when REQUIRE_HUMAN_APPROVAL=true.
    """
    job_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cv_doc_id: Optional[str] = None
    cover_doc_id: Optional[str] = None
    applied_at: datetime = field(default_factory=datetime.utcnow)
    status: JobStatus = JobStatus.APPLIED
    confirmation_screenshot: Optional[str] = None
    notes: Optional[str] = None
    human_approved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "cv_doc_id": self.cv_doc_id,
            "cover_doc_id": self.cover_doc_id,
            "applied_at": self.applied_at.isoformat(),
            "status": self.status.value,
            "confirmation_screenshot": self.confirmation_screenshot,
            "notes": self.notes,
            "human_approved": self.human_approved,
        }


@dataclass
class ApplicationEvent:
    """
    An immutable event in the application lifecycle timeline.

    data carries arbitrary event-specific JSON payload (e.g. interview date).
    """
    application_id: str
    event_type: EventType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: Optional[dict[str, Any]] = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "application_id": self.application_id,
            "event_type": self.event_type.value,
            "data": self.data,
            "occurred_at": self.occurred_at.isoformat(),
        }


# =============================================================================
# Agent Wire Protocol (TypedDicts)
# These are the JSON payloads exchanged between agents and n8n webhooks.
# =============================================================================

class AgentRequest(TypedDict):
    """
    Standard request body accepted by every AgentHire FastAPI agent.

    task    -- a short identifier for the operation to perform,
               e.g. "discover", "rank_job", "generate_cv".
    context -- arbitrary key/value pairs providing task-specific inputs,
               e.g. { "job_id": "...", "portal": "linkedin" }.
    """
    task: str
    context: dict[str, Any]


class AgentResponse(TypedDict):
    """
    Standard response envelope returned by every AgentHire FastAPI agent.

    status    -- "success" | "error" | "pending"
    result    -- task-specific output payload
    artifacts -- absolute paths to any files produced (PDFs, screenshots, etc.)
    error     -- human-readable error message; None on success
    """
    status: str
    result: dict[str, Any]
    artifacts: list[str]
    error: Optional[str]


# =============================================================================
# Helper: build a success / error response
# =============================================================================

def ok(result: dict[str, Any], artifacts: list[str] | None = None) -> AgentResponse:
    """Construct a successful AgentResponse."""
    return AgentResponse(
        status="success",
        result=result,
        artifacts=artifacts or [],
        error=None,
    )


def err(message: str, result: dict[str, Any] | None = None) -> AgentResponse:
    """Construct an error AgentResponse."""
    return AgentResponse(
        status="error",
        result=result or {},
        artifacts=[],
        error=message,
    )
