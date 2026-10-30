import pytest

from app.models import TicketCategory, TicketPriority, TriageSource
from app.triage.keyword_classifier import KeywordClassifier

classifier = KeywordClassifier()


@pytest.mark.parametrize(
    ("title", "description", "category", "priority"),
    [
        (
            "Senha bloqueada",
            "Errei a senha várias vezes e minha conta ficou bloqueada",
            TicketCategory.ACCESS,
            TicketPriority.HIGH,
        ),
        (
            "Sistema de vendas fora do ar",
            "Ninguém consegue registrar pedidos desde as 9h",
            TicketCategory.SOFTWARE,
            TicketPriority.CRITICAL,
        ),
        (
            "Impressora falhando",
            "A impressora do segundo andar está imprimindo com manchas",
            TicketCategory.HARDWARE,
            TicketPriority.MEDIUM,
        ),
        (
            "VPN caindo",
            "A conexão da VPN cai a cada dez minutos",
            TicketCategory.NETWORK,
            TicketPriority.MEDIUM,
        ),
        (
            "Dúvida sobre o Excel",
            "Como faço uma tabela dinâmica no Excel?",
            TicketCategory.SOFTWARE,
            TicketPriority.LOW,
        ),
        (
            "Cadeira quebrada",
            "A cadeira da minha mesa está com a roda solta",
            TicketCategory.OTHER,
            TicketPriority.MEDIUM,
        ),
    ],
)
def test_classifies_by_keywords(title, description, category, priority):
    result = classifier.classify(title, description)

    assert result.category == category
    assert result.priority == priority
    assert result.source == TriageSource.KEYWORDS


def test_ignores_accents_and_case():
    result = classifier.classify("CONEXÃO LENTA", "A INTERNET ESTÁ LENTA HOJE")

    assert result.category == TicketCategory.NETWORK


def test_does_not_match_part_of_a_word():
    result = classifier.classify(
        "Redefinir assinatura", "Quero redefinir a assinatura das minhas mensagens"
    )

    assert result.category == TicketCategory.OTHER


def test_reason_lists_keywords_found():
    result = classifier.classify("Senha expirada", "Preciso trocar a senha, é urgente")

    assert result.reason == "Palavras-chave encontradas: senha, urgente"


def test_reason_when_nothing_matches():
    result = classifier.classify("Cadeira quebrada", "A roda da cadeira soltou")

    assert "classificação padrão" in result.reason
