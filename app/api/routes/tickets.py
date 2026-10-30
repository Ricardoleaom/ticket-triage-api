from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, StaffUser, TicketServiceDep
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.ticket import (
    StatusUpdate,
    TicketCreate,
    TicketFilters,
    TicketPage,
    TicketResponse,
    TicketUpdate,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def open_ticket(data: TicketCreate, user: CurrentUser, service: TicketServiceDep) -> Ticket:
    return service.open_ticket(data, user)


@router.get("", response_model=TicketPage)
def list_tickets(
    filters: Annotated[TicketFilters, Query()], user: CurrentUser, service: TicketServiceDep
) -> TicketPage:
    tickets, total = service.search_tickets(filters, user)
    return TicketPage(
        items=[TicketResponse.model_validate(ticket) for ticket in tickets],
        total=total,
        limit=filters.limit,
        offset=filters.offset,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, user: CurrentUser, service: TicketServiceDep) -> Ticket:
    return service.get_ticket(ticket_id, user)


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int, data: TicketUpdate, agent: StaffUser, service: TicketServiceDep
) -> Ticket:
    return service.update_ticket(ticket_id, data, agent)


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
def change_status(
    ticket_id: int, data: StatusUpdate, agent: StaffUser, service: TicketServiceDep
) -> Ticket:
    return service.change_status(ticket_id, data.status, agent)


@router.get("/{ticket_id}/comments", response_model=list[CommentResponse])
def list_comments(ticket_id: int, user: CurrentUser, service: TicketServiceDep) -> list[Comment]:
    return service.list_comments(ticket_id, user)


@router.post(
    "/{ticket_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    ticket_id: int, data: CommentCreate, user: CurrentUser, service: TicketServiceDep
) -> Comment:
    return service.add_comment(ticket_id, data, user)
