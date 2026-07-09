"""
Pipeline completo:
  Fase A — Recuperación amplia con query expansion
  Enriquecimiento — seniority + rol por job
  Fase B — Reranking inteligente
"""
import re
import concurrent.futures
from .models import Job
from .parser import ParsedQuery, parse_prompt
from .expander import expand
from .enricher import enrich
from .reranker import rerank
from . import remotive, adzuna, arbeitnow, linkedin
from .scraper import search_computrabajo

LATAM_COUNTRIES = {
    "México", "Colombia", "Argentina", "Chile", "Uruguay",
    "Perú", "Venezuela", "Ecuador", "Brasil",
}
EUROPE_COUNTRIES = {
    "España", "Alemania", "Francia", "Reino Unido", "Países Bajos",
    "Italia", "Portugal", "Suecia", "Noruega", "Dinamarca",
}

_EXP_UI_MAP = {
    "Sin experiencia":              "no_exp",
    "Junior (0-2 años)":           "junior",
    "Mid (2-5 años)":              "mid",
    "Senior (5-10 años)":          "senior",
    "Lead / Principal (10+ años)": "lead",
}

_COUNTRY_LOCATION_HINTS: dict[str, set[str]] = {
    "España":          {"españa", "spain", "madrid", "barcelona", "valencia",
                        "sevilla", "bilbao", "málaga", "malaga", "zaragoza"},
    "México":          {"méxico", "mexico", "cdmx", "monterrey", "guadalajara"},
    "Argentina":       {"argentina", "buenos aires", "córdoba", "rosario"},
    "Colombia":        {"colombia", "bogotá", "bogota", "medellín", "medellin"},
    "Chile":           {"chile", "santiago"},
    "Estados Unidos":  {"united states", "usa", "u.s.", "new york", "san francisco",
                        "seattle", "austin", "chicago", "boston"},
    "Reino Unido":     {"united kingdom", "uk", "london", "manchester", "edinburgh"},
    "Alemania":        {"germany", "deutschland", "berlin", "munich", "hamburg"},
    "Francia":         {"france", "paris", "lyon", "marseille"},
    "Países Bajos":    {"netherlands", "amsterdam", "rotterdam"},
    "Canadá":          {"canada", "toronto", "vancouver", "montreal"},
    "Australia":       {"australia", "sydney", "melbourne", "brisbane"},
    "Brasil":          {"brasil", "brazil", "são paulo", "sao paulo", "rio de janeiro"},
    "Uruguay":         {"uruguay", "montevideo"},
}
_GLOBAL_LOCATIONS = {
    "worldwide", "anywhere", "global", "remote", "remoto",
    "international", "internacional", "europe", "europa", "latam",
    "america latina", "latin america", "",
}


def search_jobs(
    prompt: str,
    country: str = "Cualquier país",
    job_type: str = "",
    salary_min: int = 0,
    currency: str = "EUR",
    experience: str = "",
) -> list[Job]:
    # ── Parsear intención ──────────────────────────────────────
    q = parse_prompt(prompt)

    if job_type and job_type != "Todos":
        q.job_type = {"Remoto": "remote", "Híbrido": "hybrid", "Presencial": "onsite"}.get(job_type, "")
    if salary_min > 0:
        q.salary_min = salary_min
        q.currency = currency
    if experience and experience != "Cualquier nivel":
        q.experience = _EXP_UI_MAP.get(experience, experience)
    if country and country != "Cualquier país":
        q.country = country

    # ── Fase A: Recuperación amplia ───────────────────────────
    # Expandir la query en múltiples queries de rol
    api_queries = expand(q)
    if not api_queries:
        api_queries = [q.keyword_string] if q.keyword_string else ["developer"]

    raw_jobs: list[Job] = []
    tasks = _build_tasks(q, country, api_queries)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(len(tasks), 1)) as ex:
        futures = {ex.submit(fn, *args): name for name, fn, args in tasks}
        for future in concurrent.futures.as_completed(futures, timeout=25):
            try:
                raw_jobs.extend(future.result())
            except Exception:
                pass

    # ── Enriquecimiento ───────────────────────────────────────
    enriched = [enrich(job) for job in raw_jobs]

    # ── Filtros duros (país, modalidad, salario) ──────────────
    filtered = _apply_hard_filters(enriched, q, country)

    # ── Deduplicación ─────────────────────────────────────────
    deduped = _deduplicate(filtered)

    # ── Fase B: Reranking inteligente ─────────────────────────
    ranked = rerank(deduped, q)

    return ranked


def _prepare_query(prompt, country, job_type, salary_min, currency, experience):
    """Parsea el prompt y aplica los overrides de la UI. Devuelve (q, api_queries)."""
    q = parse_prompt(prompt)

    if job_type and job_type != "Todos":
        q.job_type = {"Remoto": "remote", "Híbrido": "hybrid", "Presencial": "onsite"}.get(job_type, "")
    if salary_min > 0:
        q.salary_min = salary_min
        q.currency = currency
    if experience and experience != "Cualquier nivel":
        q.experience = _EXP_UI_MAP.get(experience, experience)
    if country and country != "Cualquier país":
        q.country = country

    api_queries = expand(q)
    if not api_queries:
        api_queries = [q.keyword_string] if q.keyword_string else ["developer"]

    return q, api_queries


def search_jobs_streaming(
    prompt: str,
    country: str = "Cualquier país",
    job_type: str = "",
    salary_min: int = 0,
    currency: str = "EUR",
    experience: str = "",
    on_update=None,    # callback(ranked_jobs)  → tras cada fuente que llega
    on_done=None,      # callback(ranked_jobs, market)  → al terminar todo
):
    """
    Búsqueda incremental: lanza todas las fuentes en paralelo y, conforme cada
    una responde, enriquece + filtra + dedup + rerank el acumulado y lo emite
    por on_update. Al terminar (o timeout) calcula el mercado y llama on_done.
    """
    q, api_queries = _prepare_query(prompt, country, job_type, salary_min, currency, experience)
    tasks = _build_tasks(q, country, api_queries)

    accumulated: list[Job] = []
    last_ranked: list[Job] = []

    ex = concurrent.futures.ThreadPoolExecutor(max_workers=max(len(tasks), 1))
    futures = {ex.submit(fn, *args): name for name, fn, args in tasks}
    try:
        for future in concurrent.futures.as_completed(futures, timeout=25):
            try:
                raw = future.result()
            except Exception:
                raw = []
            if not raw:
                continue
            accumulated.extend(enrich(job) for job in raw)
            filtered = _apply_hard_filters(accumulated, q, country)
            deduped = _deduplicate(filtered)
            last_ranked = rerank(deduped, q)
            if on_update:
                try:
                    on_update(last_ranked)
                except Exception:
                    pass
    except concurrent.futures.TimeoutError:
        pass
    finally:
        ex.shutdown(wait=False)

    market = None
    try:
        from .analyzer import compute_market
        mkt_country = country if country and country != "Cualquier país" else "España"
        market = compute_market(last_ranked, mkt_country)
    except Exception:
        pass

    if on_done:
        on_done(last_ranked, market)


# ──────────────────────────────────────────────────────────────
#  Construcción de tareas (una por query × fuente)
# ──────────────────────────────────────────────────────────────

def _build_tasks(q: ParsedQuery, country: str, api_queries: list[str]) -> list[tuple]:
    tasks = []

    for api_q in api_queries:
        q_variant = _query_variant(q, api_q)

        if not q.job_type or q.job_type == "remote":
            tasks.append((f"remotive_{api_q}", remotive.search, (q_variant,)))

        if adzuna.is_configured():
            tasks.append((f"adzuna_{api_q}", adzuna.search, (q_variant, country)))

        if country in EUROPE_COUNTRIES or country == "Cualquier país" or q.job_type == "remote":
            tasks.append((f"arbeitnow_{api_q}", arbeitnow.search, (q_variant, country)))

        # LinkedIn: siempre (maneja anti-bot internamente, devuelve [] si bloquea)
        tasks.append((f"linkedin_{api_q}", linkedin.search, (q_variant, country)))

        if country in LATAM_COUNTRIES:
            tasks.append((f"ct_{api_q}", search_computrabajo, (q_variant, country)))

    if not tasks:
        tasks.append(("arbeitnow_default", arbeitnow.search, (q, "Cualquier país")))

    return tasks


def _query_variant(q: ParsedQuery, keyword_string: str) -> ParsedQuery:
    """Crea una copia de ParsedQuery con keywords sustituidas."""
    from copy import copy
    v = copy(q)
    v.keywords = keyword_string.split()
    return v


# ──────────────────────────────────────────────────────────────
#  Filtros duros
# ──────────────────────────────────────────────────────────────

def _apply_hard_filters(jobs: list[Job], q: ParsedQuery, country: str) -> list[Job]:
    result = []
    for job in jobs:
        if q.job_type and job.job_type and job.job_type != q.job_type:
            continue
        if q.salary_min and job.salary_max and job.salary_max < q.salary_min:
            continue
        if country and country != "Cualquier país":
            if not _location_matches_country(job.location, country, job.job_type):
                continue
        result.append(job)
    return result


def _location_matches_country(location: str, country: str, job_type: str) -> bool:
    loc = location.lower().strip()
    if job_type == "remote" and any(g in loc for g in _GLOBAL_LOCATIONS):
        return True
    hints = _COUNTRY_LOCATION_HINTS.get(country, set())
    return any(h in loc for h in hints)


# ──────────────────────────────────────────────────────────────
#  Deduplicación por título normalizado
# ──────────────────────────────────────────────────────────────

def _normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-záéíóúüñ0-9\s]", " ", t)
    noise = {"de", "the", "a", "an", "and", "or", "for", "at", "in",
             "el", "la", "los", "las", "y", "en", "con", "para"}
    words = [w for w in t.split() if w not in noise and len(w) > 1]
    return " ".join(sorted(words))


def _deduplicate(jobs: list[Job]) -> list[Job]:
    seen: dict[str, Job] = {}
    unique: list[Job] = []

    for job in jobs:
        norm = _normalize_title(job.title)
        if norm not in seen:
            seen[norm] = job
            unique.append(job)
        else:
            existing = seen[norm]
            # Preferir el que tenga más información útil
            has_salary = job.salary_min or job.salary_max
            existing_salary = existing.salary_min or existing.salary_max
            if has_salary and not existing_salary:
                seen[norm] = job
                unique[unique.index(existing)] = job

    return unique
