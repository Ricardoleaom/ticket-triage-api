import anthropic

from app.core.config import Settings
from app.triage.base import Classifier
from app.triage.fallback_classifier import FallbackClassifier
from app.triage.keyword_classifier import KeywordClassifier
from app.triage.llm_classifier import LLMClassifier


def build_classifier(settings: Settings) -> Classifier:
    keywords = KeywordClassifier()
    if settings.triage_provider == "keywords":
        return keywords

    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key.get_secret_value(),
        timeout=settings.triage_timeout_seconds,
        max_retries=1,
    )
    return FallbackClassifier(
        primary=LLMClassifier(client, settings.anthropic_model),
        fallback=keywords,
    )
