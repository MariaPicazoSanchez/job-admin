"""
Fuente: Arbeitnow API — gratuita, sin clave, trabajos en Europa y remoto.
https://arbeitnow.com/api
"""
from datetime import datetime, timezone

import requests
from .models import Job
from .parser import ParsedQuery

API_URL = "https://arbeitnow.com/api/job-board-api"
TIMEOUT = 10


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

        # El filtrado por país se aplica de forma centralizada en
        # aggregator._apply_hard_filters, a partir de la ubicación real.
        jobs.append(Job(
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            location=location,
            url=item.get("url", ""),
            source="Arbeitnow",
            job_type=job_type,
            description=item.get("description", "")[:300],
            tags=[t for t in tags if t],
            posted=_format_created_at(item.get("created_at")),
        ))

    return jobs


def _format_created_at(created_at) -> str:
    if not created_at:
        return ""
    try:
        return datetime.fromtimestamp(int(created_at), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def _detect_type(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ("remote", "remoto", "teletrabajo")):
        return "remote"
    if any(k in lower for k in ("hybrid", "híbrido", "hibrido")):
        return "hybrid"
    return "onsite"
