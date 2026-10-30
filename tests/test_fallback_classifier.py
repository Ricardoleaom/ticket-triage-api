import logging

import pytest

from app.models import TicketCategory, TicketPriority, TriageSource
from app.triage.base import Classifier, TriageResult
from app.triage.fallback_classifier import FallbackClassifier
from app.triage.keyword_classifier import KeywordClassifier
from tests.utils import UnavailableClassifier

AI_RESULT = TriageResult(
    category=TicketCategory.HARDWARE,
    priority=TicketPriority.LOW,
    source=TriageSource.AI,
    reason="Pedido de periférico",
)


class FixedClassifier(Classifier):
    def classify(self, title: str, description: str) -> TriageResult:
        return AI_RESULT


class BrokenClassifier(Classifier):
    def classify(self, title: str, description: str) -> TriageResult:
        raise RuntimeError("bug no código")


def test_uses_primary_classifier_when_it_works():
    classifier = FallbackClassifier(primary=FixedClassifier(), fallback=KeywordClassifier())

    assert classifier.classify("Mouse novo", "Meu mouse parou") == AI_RESULT


def test_uses_fallback_when_primary_fails(caplog):
    classifier = FallbackClassifier(primary=UnavailableClassifier(), fallback=KeywordClassifier())

    with caplog.at_level(logging.WARNING):
        result = classifier.classify("Senha bloqueada", "Minha conta foi bloqueada")

    assert result.source == TriageSource.KEYWORDS
    assert result.category == TicketCategory.ACCESS
    assert "API fora do ar" in caplog.text


def test_unexpected_errors_are_not_hidden():
    classifier = FallbackClassifier(primary=BrokenClassifier(), fallback=KeywordClassifier())

    with pytest.raises(RuntimeError):
        classifier.classify("Senha bloqueada", "Minha conta foi bloqueada")
