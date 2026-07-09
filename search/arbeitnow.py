"""
Fuente: Arbeitnow API — gratuita, sin clave, trabajos en Europa y remoto.
https://arbeitnow.com/api
"""
import requests
from .models import Job
from .parser import ParsedQuery

API_URL = "https://arbeitnow.com/api/job-board-api"
TIMEOUT = 10

COUNTRY_HINTS = {
    "España":        ["spain", "españa", "madrid", "barcelona", "valencia", "es"],
    "Alemania":      ["germany", "deutschland", "berlin", "munich", "hamburg", "de"],
    "Reino Unido":   ["uk", "united kingdom", "london", "manchester", "gb"],
    "Francia":       ["france", "paris", "fr"],
    "Países Bajos":  ["netherlands", "amsterdam", "nl"],
}


def search(query: ParsedQuery, country: str = "Cualquier país") -> list[Job]:
    base_params: dict = {}
    if query.keywords:
        base_params["search"] = query.keyword_string
    if query.job_type == "remote":
        base_params["remote"] = "true"

    # Hasta 3 páginas de 100 resultados
    raw_items = []
    for page in range(1, 4):
        try:
            params = {**base_params, "page": page}
            r = requests.get(API_URL, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            items = data.get("data", [])
            if not items:
                break
            raw_items.extend(items)
        except Exception:
            break

    jobs = []
    for item in raw_items:
        location = item.get("location", "")
        remote = item.get("remote", False)
        job_type = "remote" if remote else _detect_type(item.get("title", ""))
        tags = [{"remote": "Remoto", "hybrid": "Híbrido", "onsite": "Presencial"}.get(job_type, "")]

        if country != "Cualquier país" and not _location_ok(location, country, remote):
            continue

        jobs.append(Job(
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            location=location,
            url=item.get("url", ""),
            source="Arbeitnow",
            job_type=job_type,
            description=item.get("description", "")[:300],
            tags=[t for t in tags if t],
        ))

    return jobs


def _location_ok(location: str, country: str, remote: bool) -> bool:
    if remote:
        return True
    loc = location.lower()
    hints = COUNTRY_HINTS.get(country, [country.lower()])
    return any(h in loc for h in hints)


def _detect_type(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ("remote", "remoto", "teletrabajo")):
        return "remote"
    if any(k in lower for k in ("hybrid", "híbrido", "hibrido")):
        return "hybrid"
    return "onsite"
