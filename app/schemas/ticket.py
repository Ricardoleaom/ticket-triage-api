from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ticket import TicketCategory, TicketPriority, TicketStatus, TriageSource
from app.schemas.user import UserSummary


class TicketCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=5, max_length=150)
    description: str = Field(min_length=10, max_length=5000)


class TicketUpdate(BaseModel):
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    assignee_id: int | None = None


class StatusUpdate(BaseModel):
    status: TicketStatus


class TicketFilters(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    category: TicketCategory | None = None
    assignee_id: int | None = None
    overdue: bool = False
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    triage_source: TriageSource
    triage_reason: str
    triage_overridden: bool
    requester: UserSummary
    assignee: UserSummary | None
    sla_due_at: datetime
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TicketPage(BaseModel):
    items: list[TicketResponse]
    total: int
    limit: int
    offset: int
