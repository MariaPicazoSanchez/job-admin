"""
Extrae filtros de búsqueda a partir de texto libre en español/inglés.
"""
import re
from dataclasses import dataclass, field
from typing import Optional


REMOTE_KEYWORDS = {
    "remoto", "remote", "teletrabajo", "trabajo remoto", "100% remoto",
    "trabajo desde casa", "wfh", "full remote",
}
HYBRID_KEYWORDS = {
    "híbrido", "hibrido", "hybrid", "semipresencial",
}
ONSITE_KEYWORDS = {
    "presencial", "oficina", "onsite", "on-site", "in-office",
}

# Orden: más largo primero para evitar match parcial ("semi senior" antes de "senior")
EXPERIENCE_MAP = {
    "sin experiencia": "no_exp",
    "sin exp":         "no_exp",
    "semi senior":     "mid",
    "semi-senior":     "mid",
    "entry level":     "junior",
    "becario":         "no_exp",
    "beca":            "no_exp",
    "intern":          "no_exp",
    "trainee":         "no_exp",
    "aprendiz":        "no_exp",
    "graduate":        "no_exp",
    "junior":          "junior",
    "jr.":             "junior",
    " jr ":            "junior",
    "entry":           "junior",
    "middle":          "mid",
    " mid ":           "mid",
    "senior":          "senior",
    "sr.":             "senior",
    " sr ":            "senior",
    "lead":            "lead",
    "principal":       "lead",
    "staff":           "lead",
}

# Palabras de seniority/modalidad que NO deben ir en la query a las APIs
_NOISE_WORDS = re.compile(
    r"\b("
    # Seniority / tipo de beca
    r"becario|becaria|beca|intern|trainee|aprendiz|graduate|"
    r"junior|jr|senior|sr|lead|principal|staff|mid|middle|level|"
    r"semi[\s\-]?senior|entry[\s\-]?level|sin\s+experiencia|"
    # Modalidad
    r"remoto|remote|teletrabajo|h[íi]brido|hybrid|presencial|onsite|"
    # Preposiciones y artículos
    r"de|entre|from|hasta|m[íi]nimo|minimo|m[áa]ximo|con|para|"
    r"en|el|la|los|las|un|una|y|o|a|"
    # Monedas
    r"eur|usd|gbp|mxn|ars|cop|clp|brl|euros?|d[óo]lares?|"
    # Países
    r"espa[nñ]a|spain|m[eé]xico|mexico|argentina|colombia|chile|"
    r"estados\s+unidos|usa|reino\s+unido|alemania|germany|"
    r"francia|france|pa[íi]ses\s+bajos|netherlands|canada|canad[aá]|"
    r"australia|brasil|brazil|uruguay|"
    # Ciudades frecuentes
    r"madrid|barcelona|valencia|sevilla|bilbao|m[áa]laga|zaragoza|"
    r"cdmx|monterrey|guadalajara|bogot[aá]|medellin|santiago|"
    r"buenos\s+aires|s[aã]o\s+paulo|montevideo|london|berlin|paris|amsterdam"
    r")\b",
    re.IGNORECASE,
)

CURRENCY_HINTS = {
    "€": "EUR", "eur": "EUR",
    "$": "USD", "usd": "USD",
    "£": "GBP", "gbp": "GBP",
    "mxn": "MXN", "pesos": "MXN",
    "ars": "ARS",
    "cop": "COP",
    "clp": "CLP",
    "brl": "BRL",
}


@dataclass
class ParsedQuery:
    keywords: list[str] = field(default_factory=list)
    job_type: str = ""       # remote | hybrid | onsite | ""
    country: str = ""
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "EUR"
    experience: str = ""     # no_exp | junior | mid | senior | lead | ""

    @property
    def keyword_string(self) -> str:
        return " ".join(self.keywords)


def parse_prompt(text: str) -> ParsedQuery:
    q = ParsedQuery()
    lower = text.lower()

    # ── Modalidad ──────────────────────────────────────────
    if any(k in lower for k in REMOTE_KEYWORDS):
        q.job_type = "remote"
    elif any(k in lower for k in HYBRID_KEYWORDS):
        q.job_type = "hybrid"
    elif any(k in lower for k in ONSITE_KEYWORDS):
        q.job_type = "onsite"

    # ── Experiencia ────────────────────────────────────────
    for phrase, level in sorted(EXPERIENCE_MAP.items(), key=lambda x: -len(x[0])):
        if phrase in lower:
            q.experience = level
            break

    # ── Moneda ─────────────────────────────────────────────
    for hint, currency in CURRENCY_HINTS.items():
        if hint in lower or hint in text:
            q.currency = currency
            break

    # ── Salario ────────────────────────────────────────────
    range_match = re.search(
        r"(?:de|entre|from)\s*(\d+)\s*[k€$]?\s*(?:a|y|to|[-–])\s*(\d+)\s*[k€$]?",
        lower
    )
    if range_match:
        a, b = int(range_match.group(1)), int(range_match.group(2))
        if a < 1000: a *= 1000
        if b < 1000: b *= 1000
        q.salary_min, q.salary_max = min(a, b), max(a, b)
    else:
        single = re.search(r"(\d+)\s*k\b", lower)
        if single:
            q.salary_min = int(single.group(1)) * 1000

    # ── Keywords — quitar ruido, quedarse solo con el rol/tecnología ──
    cleaned = _NOISE_WORDS.sub(" ", text)
    cleaned = re.sub(r"\d+\s*[k€$£]", " ", cleaned)   # cifras de salario
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

    keywords = [w for w in cleaned.split() if len(w) > 2]
    q.keywords = keywords[:6]  # máximo 6 palabras clave para no saturar la query

    return q
