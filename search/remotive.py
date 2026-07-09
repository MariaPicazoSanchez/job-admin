"""
Fuente: Remotive API — gratuita, sin clave, solo empleos remotos tech.
NOTA: el parámetro 'search' de la API está roto (ignora el valor).
Estrategia: buscar por categoría + filtrar localmente por keywords.
"""
import requests
from .models import Job
from .parser import ParsedQuery

API_URL = "https://remotive.com/api/remote-jobs"
TIMEOUT = 10

# Mapa keyword → categorías Remotive
_CATEGORY_MAP = {
    "software":    "software-dev",
    "developer":   "software-dev",
    "engineer":    "software-dev",
    "backend":     "software-dev",
    "frontend":    "software-dev",
    "fullstack":   "software-dev",
    "python":      "software-dev",
    "java":        "software-dev",
    "javascript":  "software-dev",
    "typescript":  "software-dev",
    "react":       "software-dev",
    "angular":     "software-dev",
    "node":        "software-dev",
    "rails":       "software-dev",
    "golang":      "software-dev",
    "rust":        "software-dev",
    "mobile":      "software-dev",
    "ios":         "software-dev",
    "android":     "software-dev",
    "ml":          "data",
    "machine":     "data",
    "learning":    "data",
    "data":        "data",
    "scientist":   "data",
    "analytics":   "data",
    "ai":          "data",
    "nlp":         "data",
    "spark":       "data",
    "sql":         "data",
    "devops":      "devops",
    "sre":         "devops",
    "cloud":       "devops",
    "kubernetes":  "devops",
    "docker":      "devops",
    "aws":         "devops",
    "infrastructure": "devops",
    "design":      "design",
    "ux":          "design",
    "ui":          "design",
    "product":     "product",
    "pm":          "product",
    "qa":          "qa",
    "testing":     "qa",
    "security":    "software-dev",
    "marketing":   "marketing",
    "sales":       "sales",
    "finance":     "finance",
    "hr":          "hr",
    "recruiter":   "hr",
    "writing":     "writing",
    "content":     "writing",
}


def _pick_categories(keywords: list[str]) -> list[str]:
    cats: set[str] = set()
    for kw in keywords:
        cat = _CATEGORY_MAP.get(kw.lower())
        if cat:
            cats.add(cat)
    return list(cats) if cats else ["software-dev", "data"]  # default tech


def search(query: ParsedQuery) -> list[Job]:
    categories = _pick_categories(query.keywords)
    jobs: list[Job] = []

    for cat in categories[:3]:  # hasta 3 categorías
        jobs.extend(_fetch_category(cat))

    # Filtrar localmente por keywords (la API ignora el search param)
    if query.keywords:
        jobs = _filter_by_keywords(jobs, query.keywords)

    return jobs


def _fetch_category(category: str) -> list[Job]:
    try:
        r = requests.get(
            API_URL,
            params={"category": category, "limit": 50},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    jobs = []
    for item in data.get("jobs", []):
        jobs.append(Job(
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            location=item.get("candidate_required_location", "Remoto"),
            url=item.get("url", ""),
            source="Remotive",
            salary_min=None,
            salary_max=None,
            currency="USD",
            job_type="remote",
            description=_strip_html(item.get("description", ""))[:500],
            tags=["Remoto"],
        ))
    return jobs


def _filter_by_keywords(jobs: list[Job], keywords: list[str]) -> list[Job]:
    kws = [k.lower() for k in keywords]
    result = []
    for job in jobs:
        text = (job.title + " " + job.description).lower()
        if any(k in text for k in kws):
            result.append(job)
    return result


def _strip_html(html: str) -> str:
    import re
    return re.sub(r"<[^>]+>", " ", html).strip()
