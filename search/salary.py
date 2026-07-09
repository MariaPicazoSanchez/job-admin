"""
Estimación salarial heurística.
No usa APIs externas: tabla base por (rol × seniority) en kEUR para el mercado
español, ajustada por país y por un pequeño bonus según el stack detectado.
Es una aproximación orientativa, NO un dato real.
"""
from dataclasses import dataclass
from .models import Job


@dataclass
class SalaryEstimate:
    low: int
    high: int
    currency: str
    basis: str                  # "Madrid · Backend · Junior"
    comparison: str = ""        # texto comparativo si la oferta indica salario
    comparison_kind: str = ""   # "positive" | "negative" | "neutral"
    mid_eur: float = 0.0        # punto medio en EUR (para agregados de mercado)

    @property
    def range_display(self) -> str:
        return f"{self.low:,} – {self.high:,} {self.currency}".replace(",", ".")


# ── Salario base anual bruto (miles de EUR) — baseline España ─────────────────
# Filas: categoría de rol · Columnas: nivel de seniority
_BASE_KEUR: dict[str, dict[str, float]] = {
    "machine_learning": {"internship": 18, "junior": 30, "mid": 45, "senior": 65, "lead": 88},
    "data":             {"internship": 17, "junior": 29, "mid": 42, "senior": 60, "lead": 82},
    "backend":          {"internship": 16, "junior": 28, "mid": 40, "senior": 58, "lead": 78},
    "frontend":         {"internship": 16, "junior": 27, "mid": 38, "senior": 54, "lead": 72},
    "fullstack":        {"internship": 16, "junior": 28, "mid": 40, "senior": 57, "lead": 76},
    "devops":           {"internship": 18, "junior": 32, "mid": 46, "senior": 64, "lead": 85},
    "security":         {"internship": 18, "junior": 32, "mid": 47, "senior": 66, "lead": 88},
    "mobile":           {"internship": 16, "junior": 28, "mid": 40, "senior": 56, "lead": 74},
    "qa":               {"internship": 14, "junior": 24, "mid": 34, "senior": 48, "lead": 64},
    "design":           {"internship": 14, "junior": 25, "mid": 36, "senior": 50, "lead": 66},
    "product":          {"internship": 18, "junior": 30, "mid": 45, "senior": 65, "lead": 90},
    "management":       {"internship": 22, "junior": 40, "mid": 55, "senior": 75, "lead": 98},
    "other":            {"internship": 15, "junior": 25, "mid": 36, "senior": 50, "lead": 68},
}

# ── Info por país: (multiplicador vs España, moneda, cambio EUR→moneda) ────────
_COUNTRY_INFO: dict[str, tuple[float, str, float]] = {
    "España":          (1.00, "EUR", 1.0),
    "Alemania":        (1.50, "EUR", 1.0),
    "Francia":         (1.35, "EUR", 1.0),
    "Países Bajos":    (1.45, "EUR", 1.0),
    "Italia":          (1.05, "EUR", 1.0),
    "Portugal":        (0.85, "EUR", 1.0),
    "Reino Unido":     (1.55, "GBP", 0.85),
    "Estados Unidos":  (2.10, "USD", 1.08),
    "Canadá":          (1.45, "CAD", 1.47),
    "Australia":       (1.55, "AUD", 1.63),
    "México":          (0.50, "MXN", 19.5),
    "Argentina":       (0.45, "USD", 1.08),
    "Colombia":        (0.45, "COP", 4300.0),
    "Chile":           (0.55, "CLP", 1000.0),
    "Brasil":          (0.48, "BRL", 5.8),
    "Uruguay":         (0.52, "USD", 1.08),
}

# Stacks que tiran del salario hacia arriba
_HIGH_VALUE_SKILLS = {
    "Rust", "Go / Golang", "Kubernetes", "Terraform", "LLMs", "LangChain",
    "TensorFlow", "PyTorch", "Apache Spark", "Apache Kafka", "AWS", "GCP",
    "Hugging Face", "Scala", "dbt",
}

# ── Ciudades: substring → (nombre mostrado, país, factor vs media nacional) ───
# El factor refleja el coste/mercado local: SF >> resto de EE.UU., Madrid > resto de España.
_CITY_INFO: dict[str, tuple[str, str, float]] = {
    # España
    "madrid":        ("Madrid", "España", 1.12),
    "barcelona":     ("Barcelona", "España", 1.12),
    "valencia":      ("Valencia", "España", 0.98),
    "sevilla":       ("Sevilla", "España", 0.95),
    "bilbao":        ("Bilbao", "España", 1.04),
    "málaga":        ("Málaga", "España", 0.97),
    "malaga":        ("Málaga", "España", 0.97),
    "zaragoza":      ("Zaragoza", "España", 0.95),
    # Estados Unidos
    "san francisco": ("San Francisco", "Estados Unidos", 1.45),
    "bay area":      ("Bay Area", "Estados Unidos", 1.42),
    "silicon valley":("Silicon Valley", "Estados Unidos", 1.45),
    "new york":      ("Nueva York", "Estados Unidos", 1.32),
    "seattle":       ("Seattle", "Estados Unidos", 1.30),
    "boston":        ("Boston", "Estados Unidos", 1.22),
    "los angeles":   ("Los Ángeles", "Estados Unidos", 1.20),
    "austin":        ("Austin", "Estados Unidos", 1.12),
    "chicago":       ("Chicago", "Estados Unidos", 1.10),
    "denver":        ("Denver", "Estados Unidos", 1.08),
    "atlanta":       ("Atlanta", "Estados Unidos", 1.02),
    # Reino Unido
    "london":        ("Londres", "Reino Unido", 1.28),
    "manchester":    ("Manchester", "Reino Unido", 1.02),
    "edinburgh":     ("Edimburgo", "Reino Unido", 1.04),
    # Alemania
    "munich":        ("Múnich", "Alemania", 1.15),
    "münchen":       ("Múnich", "Alemania", 1.15),
    "munchen":       ("Múnich", "Alemania", 1.15),
    "frankfurt":     ("Fráncfort", "Alemania", 1.12),
    "berlin":        ("Berlín", "Alemania", 1.04),
    "hamburg":       ("Hamburgo", "Alemania", 1.06),
    # Francia
    "paris":         ("París", "Francia", 1.18),
    "lyon":          ("Lyon", "Francia", 1.00),
    # Países Bajos
    "amsterdam":     ("Ámsterdam", "Países Bajos", 1.12),
    "rotterdam":     ("Róterdam", "Países Bajos", 1.02),
    # Canadá
    "toronto":       ("Toronto", "Canadá", 1.12),
    "vancouver":     ("Vancouver", "Canadá", 1.12),
    "montreal":      ("Montreal", "Canadá", 1.00),
    # Australia
    "sydney":        ("Sídney", "Australia", 1.15),
    "melbourne":     ("Melbourne", "Australia", 1.08),
    # LATAM
    "cdmx":          ("Ciudad de México", "México", 1.10),
    "ciudad de méxico": ("Ciudad de México", "México", 1.10),
    "mexico city":   ("Ciudad de México", "México", 1.10),
    "monterrey":     ("Monterrey", "México", 1.08),
    "guadalajara":   ("Guadalajara", "México", 1.02),
    "buenos aires":  ("Buenos Aires", "Argentina", 1.10),
    "bogotá":        ("Bogotá", "Colombia", 1.08),
    "bogota":        ("Bogotá", "Colombia", 1.08),
    "medellín":      ("Medellín", "Colombia", 1.02),
    "medellin":      ("Medellín", "Colombia", 1.02),
    "santiago":      ("Santiago", "Chile", 1.08),
    "são paulo":     ("São Paulo", "Brasil", 1.15),
    "sao paulo":     ("São Paulo", "Brasil", 1.15),
    "rio de janeiro":("Río de Janeiro", "Brasil", 1.08),
    "montevideo":    ("Montevideo", "Uruguay", 1.05),
}

# ── Países: substring → país canónico (cuando no hay ciudad reconocible) ──────
_COUNTRY_HINTS: dict[str, set[str]] = {
    "España":         {"españa", "spain"},
    "México":         {"méxico", "mexico"},
    "Argentina":      {"argentina"},
    "Colombia":       {"colombia"},
    "Chile":          {"chile"},
    "Estados Unidos": {"united states", "usa", "u.s.", "ee.uu", "estados unidos"},
    "Reino Unido":    {"united kingdom", "uk", "reino unido", "england", "scotland"},
    "Alemania":       {"germany", "deutschland", "alemania"},
    "Francia":        {"france", "francia"},
    "Países Bajos":   {"netherlands", "holanda", "países bajos", "the netherlands"},
    "Italia":         {"italy", "italia"},
    "Portugal":       {"portugal"},
    "Canadá":         {"canada", "canadá"},
    "Australia":      {"australia"},
    "Brasil":         {"brasil", "brazil"},
    "Uruguay":        {"uruguay"},
}


def _resolve_location(location: str, fallback: str) -> tuple[str, str, float]:
    """
    Devuelve (país, etiqueta_mostrada, factor_ciudad) a partir del texto de
    ubicación de la oferta. Prioriza ciudad reconocida; luego país; luego el
    filtro del usuario; por último España.
    """
    loc = (location or "").lower()

    # 1. Ciudad reconocida (implica también el país)
    for key, (disp, country, factor) in _CITY_INFO.items():
        if key in loc:
            return country, disp, factor

    # 2. País mencionado
    for country, hints in _COUNTRY_HINTS.items():
        if any(h in loc for h in hints):
            return country, country, 1.0

    # 3. Filtro del usuario / España por defecto
    fb = fallback if fallback not in ("", "Cualquier país") else "España"
    return fb, fb, 1.0


def estimate_salary(
    job: Job,
    country: str = "España",
    skills: list[str] | None = None,
) -> SalaryEstimate | None:
    """
    Devuelve una estimación salarial basada en el país y la ciudad reales de la
    oferta (inferidos desde job.location). El argumento `country` es solo un
    fallback cuando la ubicación no aporta información.
    """
    role = job.role_category if job.role_category in _BASE_KEUR else "other"

    level = job.seniority_level
    if level not in ("internship", "junior", "mid", "senior", "lead"):
        level = "mid"   # asunción razonable cuando es desconocido

    base_keur = _BASE_KEUR.get(role, _BASE_KEUR["other"]).get(level)
    if base_keur is None:
        return None

    # Ubicación real de la oferta (ciudad + país); fallback al filtro del usuario
    resolved_country, loc_label, city_factor = _resolve_location(job.location, country)
    mult, currency, fx = _COUNTRY_INFO.get(resolved_country, _COUNTRY_INFO["España"])

    # Bonus por stack de alto valor (máx +12%)
    skills = skills or []
    hv = sum(1 for s in skills if s in _HIGH_VALUE_SKILLS)
    skill_factor = 1.0 + min(hv, 4) * 0.03

    # Estimación central en EUR (incluye país + ciudad + stack), luego a moneda local
    central_eur = base_keur * 1000 * mult * city_factor * skill_factor
    central_local = central_eur * fx

    low = int(round(central_local * 0.85 / 1000) * 1000)
    high = int(round(central_local * 1.18 / 1000) * 1000)

    est = SalaryEstimate(
        low=low, high=high, currency=currency,
        basis=f"{loc_label} · {_role_label(role)} · {_level_label(level)}",
        mid_eur=central_eur,
    )

    # ── Comparativa si la oferta sí indica salario (misma moneda) ─────────
    actual = _actual_midpoint(job)
    if actual and job.currency == currency:
        est_mid = (low + high) / 2
        if est_mid > 0:
            diff = (actual - est_mid) / est_mid * 100
            if diff >= 8:
                est.comparison = f"+{diff:.0f}% sobre la estimación de mercado"
                est.comparison_kind = "positive"
            elif diff <= -8:
                est.comparison = f"{diff:.0f}% bajo la estimación de mercado"
                est.comparison_kind = "negative"
            else:
                est.comparison = "En línea con el mercado"
                est.comparison_kind = "neutral"

    return est


def _actual_midpoint(job: Job) -> float | None:
    if job.salary_min and job.salary_max:
        return (job.salary_min + job.salary_max) / 2
    if job.salary_min:
        return float(job.salary_min)
    if job.salary_max:
        return float(job.salary_max)
    return None


def _role_label(role: str) -> str:
    return {
        "machine_learning": "Machine Learning",
        "data": "Data",
        "backend": "Backend",
        "frontend": "Frontend",
        "fullstack": "Fullstack",
        "devops": "DevOps",
        "security": "Seguridad",
        "mobile": "Mobile",
        "qa": "QA",
        "design": "Diseño",
        "product": "Producto",
        "management": "Management",
        "other": "Tech",
    }.get(role, "Tech")


def _level_label(level: str) -> str:
    return {
        "internship": "Prácticas",
        "junior": "Junior",
        "mid": "Mid",
        "senior": "Senior",
        "lead": "Lead",
    }.get(level, "Mid")
