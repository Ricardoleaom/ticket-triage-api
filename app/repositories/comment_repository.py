from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.comment import Comment


class CommentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_ticket(self, ticket_id: int) -> list[Comment]:
        query = (
            select(Comment)
            .where(Comment.ticket_id == ticket_id)
            .options(joinedload(Comment.author))
            .order_by(Comment.id)
        )
        return list(self.db.scalars(query))

    def add(self, comment: Comment) -> None:
        self.db.add(comment)
