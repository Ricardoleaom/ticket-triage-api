from pydantic import BaseModel, Field

from app.models.ticket import TicketPriority, TicketStatus


class SummaryReport(BaseModel):
    total_tickets: int
    by_status: dict[TicketStatus, int]
    by_priority: dict[TicketPriority, int]
    overdue: int = Field(description="Chamados em aberto com o SLA vencido")
    sla_compliance_rate: float | None = Field(
        description="Percentual de chamados resolvidos dentro do SLA"
    )
    triage_override_rate: float | None = Field(
        description="Percentual de chamados em que o atendente corrigiu a triagem automática"
    )
