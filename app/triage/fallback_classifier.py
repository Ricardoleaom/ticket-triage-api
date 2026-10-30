import logging

from app.triage.base import Classifier, TriageError, TriageResult

logger = logging.getLogger(__name__)


class FallbackClassifier(Classifier):
    def __init__(self, primary: Classifier, fallback: Classifier) -> None:
        self.primary = primary
        self.fallback = fallback

    def classify(self, title: str, description: str) -> TriageResult:
        try:
            return self.primary.classify(title, description)
        except TriageError as error:
            logger.warning("Triagem principal falhou, usando a alternativa: %s", error)
            return self.fallback.classify(title, description)
