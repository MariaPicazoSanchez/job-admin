"""
Análisis de ofertas: extrae skills, detecta señales y genera un resumen descriptivo.
Sin LLM — todo regex + heurísticas sobre el texto disponible (título + descripción).
"""
import re
import html as _html
from collections import Counter
from dataclasses import dataclass, field
from .models import Job
from .salary import estimate_salary, SalaryEstimate


# ── Dataclasses de resultado ──────────────────────────────────────────────────

@dataclass
class Signal:
    emoji: str
    label: str
    detail: str
    kind: str   # "danger" | "warning" | "positive" | "info"


@dataclass
class JobAnalysis:
    hard_skills: list[str]              = field(default_factory=list)
    soft_skills: list[str]              = field(default_factory=list)
    company_type: str                   = ""
    signals: list[Signal]               = field(default_factory=list)
    junior_trap: bool                   = False
    seniority_detail: str               = ""
    ai_summary: str                     = ""
    clean_description: str              = ""
    has_rich_description: bool          = False
    description_blocks: dict[str, str]  = field(default_factory=dict)
    salary_estimate: SalaryEstimate | None = None


@dataclass
class MarketInsights:
    total: int                              = 0
    top_skills: list[tuple[str, int]]       = field(default_factory=list)  # (skill, %)
    avg_years: float | None                 = None
    median_salary: int | None               = None
    salary_currency: str                    = "EUR"


# ── Hard skills ───────────────────────────────────────────────────────────────
# Clave: nombre a mostrar · Valor: patrón regex (case-insensitive)

HARD_SKILLS: dict[str, str] = {
    # Lenguajes
    "Python":           r"\bpython\b",
    "JavaScript":       r"\bjavascript\b|\bjs\b(?=[\s,)])",
    "TypeScript":       r"\btypescript\b",
    "Java":             r"\bjava\b(?!script)",
    "C++":              r"\bc\+\+",
    "C#":               r"\bc#\b",
    "Go / Golang":      r"\bgolang\b|\bgo\b(?=\s+(developer|engineer|lang|backend))",
    "Rust":             r"\brust\b",
    "Scala":            r"\bscala\b",
    "R":                r"\br\b(?=\s+(programming|language|studio|shiny))",
    "SQL":              r"\bsql\b",
    "Bash / Shell":     r"\bbash\b|\bshell\s+scripting\b",
    "PHP":              r"\bphp\b",
    "Ruby":             r"\bruby\b",
    "Kotlin":           r"\bkotlin\b",
    "Swift":            r"\bswift\b",
    # ML / IA
    "TensorFlow":       r"\btensorflow\b",
    "PyTorch":          r"\bpytorch\b",
    "scikit-learn":     r"\bscikit[\-\s]?learn\b|\bsklearn\b",
    "Keras":            r"\bkeras\b",
    "Hugging Face":     r"\bhugging\s*face\b",
    "LangChain":        r"\blangchain\b",
    "LLMs":             r"\bllm[s]?\b|\blarge\s+language\s+model\b",
    "OpenAI API":       r"\bopenai\b",
    "NLP":              r"\bnlp\b|\bnatural\s+language\s+processing\b",
    "Computer Vision":  r"\bcomputer\s+vision\b",
    "MLflow":           r"\bmlflow\b",
    "Apache Airflow":   r"\bairflow\b",
    "Pandas":           r"\bpandas\b",
    "NumPy":            r"\bnumpy\b",
    "Apache Spark":     r"\bpyspark\b|\bapache\s+spark\b|\bspark(?=\s+(sql|streaming|ml))",
    "Apache Kafka":     r"\bkafka\b",
    "dbt":              r"\bdbt\b",
    "Elasticsearch":    r"\belasticsearch\b|\bopensearch\b",
    # Bases de datos
    "PostgreSQL":       r"\bpostgresql\b|\bpostgres\b",
    "MySQL":            r"\bmysql\b",
    "MongoDB":          r"\bmongodb\b|\bmongo\b",
    "Redis":            r"\bredis\b",
    "Snowflake":        r"\bsnowflake\b",
    "BigQuery":         r"\bbigquery\b",
    "Cassandra":        r"\bcassandra\b",
    # Cloud
    "AWS":              r"\baws\b|\bamazon\s+web\s+services\b",
    "GCP":              r"\bgcp\b|\bgoogle\s+cloud\b",
    "Azure":            r"\bazure\b|\bmicrosoft\s+azure\b",
    # DevOps / infra
    "Docker":           r"\bdocker\b",
    "Kubernetes":       r"\bkubernetes\b|\bk8s\b",
    "Terraform":        r"\bterraform\b",
    "CI/CD":            r"\bci/?cd\b|\bcontinuous\s+integration\b|\bgithub\s+actions\b|\bjenkins\b|\bgitlab\s+ci\b",
    "Git":              r"\bgit\b(?!hub|lab)",
    "GitHub":           r"\bgithub\b",
    "GitLab":           r"\bgitlab\b",
    "Linux":            r"\blinux\b|\bubuntu\b|\bdebian\b|\bcentos\b",
    # Web / frameworks
    "React":            r"\breact\b(?!\s*native)",
    "React Native":     r"\breact\s+native\b",
    "Vue.js":           r"\bvue\.?js\b",
    "Angular":          r"\bangular\b",
    "Node.js":          r"\bnode\.?js\b",
    "FastAPI":          r"\bfastapi\b",
    "Django":           r"\bdjango\b",
    "Flask":            r"\bflask\b",
    "Spring Boot":      r"\bspring\s+boot\b",
    "REST / GraphQL":   r"\brest\s+api\b|\brestful\b|\bgraphql\b",
    "Microservices":    r"\bmicroservice[s]?\b",
    # Metodologías
    "Agile / Scrum":    r"\bagile\b|\bscrum\b|\bkanban\b",
}

# ── Soft skills ───────────────────────────────────────────────────────────────

SOFT_SKILLS: list[tuple[str, str]] = [
    ("Comunicación",            r"\bcommunication\b|\bcomunicaci[oó]n\b"),
    ("Trabajo en equipo",       r"\bteam[\s\-]?player\b|\bteamwork\b|\btrabajo\s+en\s+equipo\b|\bcollaborat\w+\b"),
    ("Autonomía",               r"\bautonom\w+\b|\bindependent\w*\b|\bself[\-\s]?motivated\b"),
    ("Liderazgo",               r"\bleadership\b|\bliderazgo\b"),
    ("Proactividad",            r"\bproactiv\w+\b"),
    ("Resolución de problemas", r"\bproblem[\-\s]?solving\b|\bresoluc\w+\s+de\s+problemas\b"),
    ("Mentoría",                r"\bmentor\w*\b"),
    ("Inglés avanzado",         r"\benglish\s+(required|fluent|advanced|c1|b2)\b|\bfull\s+english\b|\bingles\s+(requerido|avanzado)\b"),
    ("Adaptabilidad",           r"\badaptab\w+\b|\bflexib\w+\b"),
    ("Orientación a resultados",r"\bresult[\-\s]?oriented\b|\bdata[\-\s]?driven\b|\borientad\w+\s+a\s+resultados\b"),
]

# ── Tipo de empresa ───────────────────────────────────────────────────────────

COMPANY_TYPES: list[tuple[str, str]] = [
    ("Startup",      r"\bstartup\b|\bseed\s+stage\b|\bserie\s+[a-c]\b|\bequity\b|\bstock\s+options?\b|\bfounding\s+team\b|\bventure[\-\s]backed\b"),
    ("Consultora",   r"\bconsult\w+\b|\boutsorc\w+\b|\bstaffing\b|\bstaff\s+augment\w+\b"),
    ("SaaS",         r"\bsaas\b|\bsoftware\s+as\s+a\s+service\b"),
    ("Fintech",      r"\bfintech\b|\bpayment\b|\bbanking\b|\binsurtech\b|\bcrypto\b|\bblockchain\b"),
    ("E-commerce",   r"\becommerce\b|\be[\-\s]commerce\b|\bmarketplace\b|\bretail\s+tech\b"),
    ("Corporación",  r"\bmultinacional\b|\bmultinational\b|\bcorporate\b|\benterprise\b|\bfortune\s*\d+\b"),
    ("Healthtech",   r"\bhealthtech\b|\bmedtech\b|\bhealth\s+tech\b|\bhealthcare\b"),
    ("Edtech",       r"\bedtech\b|\beducation\s+tech\b|\be[\-\s]?learning\b"),
    ("Gamedev",      r"\bgame\s+(developer|studio|company)\b|\bgaming\b|\bunity\b|\bunreal\b"),
]

# ── Stack legacy ──────────────────────────────────────────────────────────────

LEGACY_TECH: list[tuple[str, str]] = [
    ("COBOL",       r"\bcobol\b"),
    ("VBA",         r"\bvba\b|\bvisual\s+basic\b"),
    ("ASP clásico", r"\bclassic\s+asp\b|\basp\s+(?!\.net)\b"),
    ("jQuery",      r"\bjquery\b"),
    ("Delphi",      r"\bdelphi\b"),
    ("SVN",         r"\bsvn\b|\bsubversion\b"),
    ("ColdFusion",  r"\bcoldfusion\b"),
]

# ── Tecnologías en auge ───────────────────────────────────────────────────────

HOT_TECH: list[tuple[str, str]] = [
    ("LangChain",       r"\blangchain\b"),
    ("LLMs",            r"\bllm[s]?\b"),
    ("Rust",            r"\brust\b"),
    ("Go / Golang",     r"\bgolang\b"),
    ("dbt",             r"\bdbt\b"),
    ("Airflow",         r"\bairflow\b"),
    ("Kubernetes",      r"\bkubernetes\b|\bk8s\b"),
    ("Terraform",       r"\bterraform\b"),
    ("Hugging Face",    r"\bhugging\s*face\b"),
    ("MCP",             r"\bmcp\b"),
    ("Ray",             r"\bray\.io\b|\bray\s+distributed\b"),
    ("Weaviate",        r"\bweaviate\b"),
    ("Pinecone",        r"\bpinecone\b"),
]


# ── Funciones auxiliares ──────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Elimina etiquetas HTML y decodifica entidades."""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "\n• ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _match_any(patterns: list[tuple[str, str]], text: str) -> list[str]:
    return [name for name, pat in patterns if re.search(pat, text, re.IGNORECASE)]


# ── Separación de la descripción en bloques temáticos ─────────────────────────

_SECTION_PATTERNS: list[tuple[str, str]] = [
    ("Requisitos",        r"(requisitos|requirements|qualifications|lo que buscamos|what we['’]?re looking for|what you['’]?ll need|must[\- ]have|imprescindible|perfil buscado|skills required|your profile|tu perfil)"),
    ("Responsabilidades", r"(responsabilidades|responsibilities|what you['’]?ll do|funciones|tus tareas|your role|day[\- ]to[\- ]day|qué harás|the role|misión)"),
    ("Beneficios",        r"(beneficios|benefits|what we offer|perks|qué ofrecemos|we offer|ofrecemos|nice to have|se ofrece)"),
    ("Sobre la empresa",  r"(about us|about the company|sobre nosotros|quiénes somos|who we are|la empresa|about the team)"),
]


def _split_sections(text: str) -> dict[str, str]:
    """
    Best-effort: localiza cabeceras conocidas y trocea el texto.
    Si no encuentra cabeceras devuelve {} (se mostrará como bloque único).
    """
    hits: list[tuple[int, int, str]] = []   # (start, header_end, label)
    for label, pat in _SECTION_PATTERNS:
        m = re.search(r"\b" + pat + r"\b\s*:?", text, re.IGNORECASE)
        if m:
            hits.append((m.start(), m.end(), label))

    if len(hits) < 2:
        return {}

    hits.sort(key=lambda h: h[0])
    blocks: dict[str, str] = {}
    for i, (start, hend, label) in enumerate(hits):
        nxt = hits[i + 1][0] if i + 1 < len(hits) else len(text)
        body = text[hend:nxt].strip(" :·-–—\n\t")
        if body and label not in blocks:
            blocks[label] = body[:900]
    return blocks


# ── Análisis principal ────────────────────────────────────────────────────────

def analyze_job(job: Job, country: str = "España") -> JobAnalysis:
    if country in ("", "Cualquier país"):
        country = "España"
    clean_desc  = _strip_html(job.description or "")
    full_text   = f"{job.title} {job.company or ''} {clean_desc}"
    full_lower  = full_text.lower()
    title_lower = job.title.lower()
    has_rich    = len(clean_desc) > 120

    # ── Hard skills ───────────────────────────────────────
    hard_skills = [
        name for name, pat in HARD_SKILLS.items()
        if re.search(pat, full_text, re.IGNORECASE)
    ][:18]

    # ── Soft skills ───────────────────────────────────────
    soft_skills = _match_any(SOFT_SKILLS, full_text)

    # ── Tipo de empresa ───────────────────────────────────
    company_type = next(
        (ct for ct, pat in COMPANY_TYPES if re.search(pat, full_lower, re.IGNORECASE)),
        ""
    )

    # ── Señales ───────────────────────────────────────────
    signals: list[Signal] = []

    # — Junior trap —
    junior_trap = False
    is_junior_title = bool(re.search(
        r"\bjunior\b|\bbecario\b|\bentry[\-\s]?level\b|\bintern\b|\bgrad(uate)?\b",
        title_lower
    ))
    years_nums = [int(m) for m in re.findall(
        r"(\d+)\+?\s*(?:años?|years?)\s+(?:de\s+)?(?:experiencia|experience)", full_lower
    )]
    if years_nums:
        max_yr = max(years_nums)
        if is_junior_title and max_yr >= 3:
            junior_trap = True
            signals.append(Signal("🚩", "Junior Trap",
                f'Título "junior" pero exige {max_yr}+ años de experiencia. Cuidado.',
                "danger"))
        elif job.seniority_level in ("junior", "internship") and max_yr >= 3:
            junior_trap = True
            signals.append(Signal("🚩", "Junior Trap",
                f"Detectado como junior pero pide {max_yr} años reales.",
                "danger"))

    # — Remoto —
    if job.job_type == "remote":
        if re.search(r"\bpresencial\b|\bon[\-\s]?site\b|\boffice\b|\boficina\b", full_lower):
            signals.append(Signal("⚠️", "Remoto dudoso",
                "Dice remoto pero hay indicios de presencialidad en la descripción.",
                "warning"))
        else:
            signals.append(Signal("🌍", "Remoto real",
                "Posición 100% remota sin contradicciones detectadas.", "positive"))

    # — Stack legacy —
    legacy = _match_any(LEGACY_TECH, full_text)
    if legacy:
        signals.append(Signal("🏛️", "Stack legacy",
            f"Tecnología obsoleta detectada: {', '.join(legacy)}.", "warning"))

    # — Tecnologías en auge —
    hot = _match_any(HOT_TECH, full_text)
    if hot:
        signals.append(Signal("🔥", "Stack en auge",
            f"Tecnologías muy demandadas: {', '.join(hot)}.", "positive"))

    # — Sin salario —
    if not (job.salary_min or job.salary_max):
        signals.append(Signal("💸", "Salario no publicado",
            "La empresa no ha indicado rango salarial.", "info"))

    # — Equity —
    if re.search(r"\bequity\b|\bstock[\s\-]options?\b|\bparticipaci[oó]n\b", full_lower):
        signals.append(Signal("📈", "Equity / Stock options",
            "La empresa ofrece participación accionarial.", "positive"))

    # — Inglés —
    if re.search(r"\benglish\s+(required|fluent|c1|b2|advanced|mandatory)\b|\bfull\s+english\b", full_lower):
        signals.append(Signal("🇬🇧", "Inglés requerido",
            "Se exige nivel de inglés avanzado (B2/C1 o superior).", "info"))

    # — Titulación —
    if re.search(r"\bdegree\s+required\b|\btitulaci[oó]n\s+requerida\b|\bgraduate\s+degree\b", full_lower):
        signals.append(Signal("🎓", "Titulación universitaria",
            "Se pide titulación universitaria como requisito.", "info"))

    # — Urgente / gran rotación —
    if re.search(r"\basap\b|\bimmediate(ly)?\b|\burgent\b|\burgente\b|\bincorporaci[oó]n\s+inmediata\b", full_lower):
        signals.append(Signal("⚡", "Incorporación inmediata",
            "La empresa busca incorporación urgente.", "info"))

    # ── Detalle de seniority ───────────────────────────────
    seniority_detail = _seniority_detail(job, years_nums)

    # ── Resumen automático ────────────────────────────────
    ai_summary = _build_summary(job, hard_skills, company_type, signals, junior_trap)

    # ── Bloques de la descripción ──────────────────────────
    blocks = _split_sections(clean_desc) if has_rich else {}

    # ── Estimación salarial ────────────────────────────────
    sal_est = estimate_salary(job, country, hard_skills)

    return JobAnalysis(
        hard_skills=hard_skills,
        soft_skills=soft_skills,
        company_type=company_type,
        signals=signals,
        junior_trap=junior_trap,
        seniority_detail=seniority_detail,
        ai_summary=ai_summary,
        clean_description=clean_desc,
        has_rich_description=has_rich,
        description_blocks=blocks,
        salary_estimate=sal_est,
    )


# ── Insights de mercado sobre el conjunto de resultados ───────────────────────

def compute_market(jobs: list[Job], country: str = "España") -> MarketInsights:
    """Agrega estadísticas sobre todas las ofertas de una búsqueda."""
    n = len(jobs)
    if n == 0:
        return MarketInsights()

    skill_counts: Counter = Counter()
    years: list[int] = []
    mids_local: list[float] = []      # punto medio en moneda local de cada oferta
    mids_eur: list[float] = []        # punto medio en EUR (comparable entre países)
    currencies: set[str] = set()

    for j in jobs:
        ana = analyze_job(j, country)
        for sk in ana.hard_skills:
            skill_counts[sk] += 1
        if j.years_required:
            years.append(j.years_required)
        if ana.salary_estimate:
            est = ana.salary_estimate
            mids_local.append((est.low + est.high) / 2)
            mids_eur.append(est.mid_eur)
            currencies.add(est.currency)

    top_skills = [
        (sk, round(cnt / n * 100))
        for sk, cnt in skill_counts.most_common(8)
    ]
    avg_years = round(sum(years) / len(years), 1) if years else None

    # Si todas las ofertas comparten moneda → mediana en local; si no → EUR
    median_salary = None
    salary_currency = "EUR"
    if mids_eur:
        if len(currencies) == 1:
            values = mids_local
            salary_currency = next(iter(currencies))
        else:
            values = mids_eur
            salary_currency = "EUR"
        values = sorted(values)
        mid = len(values) // 2
        median_salary = int(
            values[mid] if len(values) % 2
            else (values[mid - 1] + values[mid]) / 2
        )

    return MarketInsights(
        total=n,
        top_skills=top_skills,
        avg_years=avg_years,
        median_salary=median_salary,
        salary_currency=salary_currency,
    )


def _seniority_detail(job: Job, years_found: list[int]) -> str:
    lv = job.seniority_level
    yr = job.years_required or (max(years_found) if years_found else None)

    if lv == "internship":
        return "Prácticas / Trainee"
    if lv == "junior":
        return "Junior exigente" if yr and yr >= 3 else "Junior real"
    if lv == "mid":
        return "Mid accesible" if yr and yr <= 2 else "Mid"
    if lv == "senior":
        return "Senior"
    if lv == "lead":
        return "Lead / Staff"
    return "Nivel no especificado"


def _build_summary(
    job: Job,
    skills: list[str],
    company_type: str,
    signals: list[Signal],
    junior_trap: bool,
) -> str:
    parts: list[str] = []

    # Tipo de empresa + categoría de rol
    role_map = {
        "machine_learning": "de IA/ML",
        "frontend":  "de frontend",
        "backend":   "de backend",
        "fullstack": "fullstack",
        "devops":    "de DevOps/infraestructura",
        "data":      "de datos",
        "mobile":    "móvil",
        "security":  "de ciberseguridad",
        "qa":        "de QA/testing",
        "design":    "de diseño",
        "product":   "de producto",
        "management":"de gestión técnica",
    }
    seniority_map = {
        "internship": "para prácticas",
        "junior":  "buscando perfil junior",
        "mid":     "buscando un mid",
        "senior":  "para un senior",
        "lead":    "para un lead/principal",
    }

    company_part   = company_type or ("Empresa" if job.company else "Puesto")
    role_part      = role_map.get(job.role_category, "")
    seniority_part = seniority_map.get(job.seniority_level, "")

    line = company_part
    if role_part:
        line += f" {role_part}"
    if seniority_part:
        line += f", {seniority_part}"
    line += "."
    parts.append(line)

    # Stack
    if skills:
        parts.append(f"Stack principal: {', '.join(skills[:6])}.")

    # Señal destacada
    if junior_trap:
        parts.append("⚠️ Los requisitos reales no cuadran con el nivel anunciado.")
    else:
        danger_sigs = [s for s in signals if s.kind in ("danger", "warning") and "remoto" not in s.label.lower()]
        if danger_sigs:
            parts.append(f"Nota: {danger_sigs[0].detail}")

    return " ".join(parts)
