import re
import unicodedata

from app.models.ticket import TicketCategory, TicketPriority, TriageSource
from app.triage.base import Classifier, TriageResult

# Em caso de empate vence a categoria que aparece primeiro.
# SOFTWARE fica por último porque "erro" e "sistema" aparecem em quase todo chamado.
CATEGORY_KEYWORDS = {
    TicketCategory.ACCESS: [
        "senha",
        "login",
        "acesso",
        "conta",
        "bloqueado",
        "bloqueada",
        "permissao",
        "autenticacao",
    ],
    TicketCategory.NETWORK: [
        "internet",
        "rede",
        "wifi",
        "wi-fi",
        "vpn",
        "conexao",
        "dns",
        "sem sinal",
    ],
    TicketCategory.HARDWARE: [
        "impressora",
        "monitor",
        "teclado",
        "mouse",
        "notebook",
        "computador",
        "bateria",
        "headset",
        "webcam",
    ],
    TicketCategory.SOFTWARE: [
        "sistema",
        "aplicativo",
        "programa",
        "instalar",
        "instalacao",
        "atualizacao",
        "licenca",
        "excel",
        "outlook",
        "teams",
        "erro",
    ],
}

# A ordem importa: a primeira prioridade com alguma palavra encontrada é a escolhida.
PRIORITY_KEYWORDS = {
    TicketPriority.CRITICAL: [
        "fora do ar",
        "parado",
        "parada",
        "producao",
        "todos os usuarios",
        "ninguem consegue",
    ],
    TicketPriority.HIGH: [
        "urgente",
        "bloqueado",
        "bloqueada",
        "nao consigo trabalhar",
        "nao consigo acessar",
        "cliente esperando",
    ],
    TicketPriority.LOW: [
        "duvida",
        "sugestao",
        "melhoria",
        "quando possivel",
        "quando puder",
    ],
}


class KeywordClassifier(Classifier):
    def classify(self, title: str, description: str) -> TriageResult:
        text = normalize(f"{title} {description}")
        category, category_matches = self._choose_category(text)
        priority, priority_matches = self._choose_priority(text)

        matches = list(dict.fromkeys(category_matches + priority_matches))
        if matches:
            reason = f"Palavras-chave encontradas: {', '.join(matches)}"
        else:
            reason = "Nenhuma palavra-chave conhecida, classificação padrão aplicada"

        return TriageResult(
            category=category,
            priority=priority,
            source=TriageSource.KEYWORDS,
            reason=reason,
        )

    @staticmethod
    def _choose_category(text: str) -> tuple[TicketCategory, list[str]]:
        best_category, best_matches = TicketCategory.OTHER, []
        for category, keywords in CATEGORY_KEYWORDS.items():
            matches = find_keywords(text, keywords)
            if len(matches) > len(best_matches):
                best_category, best_matches = category, matches
        return best_category, best_matches

    @staticmethod
    def _choose_priority(text: str) -> tuple[TicketPriority, list[str]]:
        for priority, keywords in PRIORITY_KEYWORDS.items():
            matches = find_keywords(text, keywords)
            if matches:
                return priority, matches
        return TicketPriority.MEDIUM, []


def normalize(text: str) -> str:
    without_accents = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return without_accents.lower()


def find_keywords(text: str, keywords: list[str]) -> list[str]:
    # \b evita falsos positivos como "rede" dentro de "redefinir"
    return [word for word in keywords if re.search(rf"\b{re.escape(word)}\b", text)]
