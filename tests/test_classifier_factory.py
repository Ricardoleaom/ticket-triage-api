import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.triage.factory import build_classifier
from app.triage.fallback_classifier import FallbackClassifier
from app.triage.keyword_classifier import KeywordClassifier
from app.triage.llm_classifier import LLMClassifier

SECRET = "x" * 32


def make_settings(**values) -> Settings:
    return Settings(_env_file=None, jwt_secret_key=SECRET, **values)


def test_keywords_provider():
    classifier = build_classifier(make_settings(triage_provider="keywords"))

    assert isinstance(classifier, KeywordClassifier)


def test_anthropic_provider_falls_back_to_keywords():
    settings = make_settings(triage_provider="anthropic", anthropic_api_key="chave-de-teste")

    classifier = build_classifier(settings)

    assert isinstance(classifier, FallbackClassifier)
    assert isinstance(classifier.primary, LLMClassifier)
    assert isinstance(classifier.fallback, KeywordClassifier)


def test_anthropic_provider_requires_api_key():
    with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY"):
        make_settings(triage_provider="anthropic", anthropic_api_key="")


def test_jwt_secret_must_be_long():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret_key="curta")
