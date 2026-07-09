"""
Fase A — Recuperación amplia.
Expande el query del usuario en múltiples queries para las APIs,
separando la dimensión de ROL de la dimensión de SENIORITY.
"""
from .parser import ParsedQuery
from .taxonomies import ROLE_GROUPS, SENIORITY_LEVELS


def expand(q: ParsedQuery) -> list[str]:
    """
    Devuelve lista de query strings para enviar a las APIs.
    La búsqueda debe ser amplia; el reranker decide la precisión.
    """
    role_queries = _role_queries(q.keywords)
    if not role_queries:
        role_queries = [q.keyword_string] if q.keyword_string else ["developer"]

    return role_queries[:3]  # máximo 3 queries distintas por búsqueda


def detect_requested_seniority(q: ParsedQuery) -> str:
    """
    Devuelve el nivel de seniority que el usuario está pidiendo,
    ya sea explícito (filtro UI) o implícito (keywords del prompt).
    """
    if q.experience:
        return q.experience  # viene del filtro UI o del parser

    # Inferir desde keywords del prompt original (antes de limpiar)
    return ""


def _role_queries(keywords: list[str]) -> list[str]:
    """
    Detecta el grupo de rol y devuelve sus queries alternativas para las APIs.
    """
    kw_set = {k.lower() for k in keywords}
    matched_groups: list[str] = []

    for group_name, data in ROLE_GROUPS.items():
        for term in data["terms"]:
            # Comprobar si alguna keyword del usuario coincide con algún término del grupo
            term_words = set(term.split())
            if term_words & kw_set or any(k in term for k in kw_set):
                matched_groups.append(group_name)
                break

    if not matched_groups:
        return []

    queries: list[str] = []
    seen: set[str] = set()
    for group in matched_groups[:2]:  # máx 2 grupos
        for q in ROLE_GROUPS[group]["api_queries"]:
            if q not in seen:
                seen.add(q)
                queries.append(q)

    return queries
