from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.ticket import TicketCategory, TicketPriority, TriageSource


class TriageError(Exception):
    pass


@dataclass(frozen=True)
class TriageResult:
    category: TicketCategory
    priority: TicketPriority
    source: TriageSource
    reason: str


class Classifier(ABC):
    @abstractmethod
    def classify(self, title: str, description: str) -> TriageResult: ...
