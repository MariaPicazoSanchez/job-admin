"""
Fuente: Adzuna API — gratuita con registro.
Registro en: https://developer.adzuna.com/
Configura APP_ID y APP_KEY en config.json o variables de entorno.
"""
import os
import json
import requests
from pathlib import Path
from .models import Job
from .parser import ParsedQuery


TIMEOUT = 10
BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"

COUNTRY_CODES = {
    "España": "es", "México": "mx", "Argentina": "ar",
    "Reino Unido": "gb", "Estados Unidos": "us", "Alemania": "de",
    "Francia": "fr", "Países Bajos": "nl", "Canadá": "ca",
    "Australia": "au", "Brasil": "br",
}


def _load_credentials() -> tuple[str, str]:
    # 1) .env en la raíz del proyecto
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

    # 2) config.json (guardado desde la UI)
    config_path = Path(__file__).parent.parent / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)
            app_id = cfg.get("adzuna_app_id", "")
            app_key = cfg.get("adzuna_app_key", "")
            if app_id and app_key:
                return app_id, app_key

    # 3) variables de entorno del sistema
    return os.getenv("ADZUNA_APP_ID", ""), os.getenv("ADZUNA_APP_KEY", "")


def is_configured() -> bool:
    app_id, app_key = _load_credentials()
    return bool(app_id and app_key)


def search(query: ParsedQuery, country: str = "España") -> list[Job]:
    if country == "Cualquier país":
        return _search_multi(query, ["España", "Reino Unido", "Estados Unidos"])
    app_id, app_key = _load_credentials()
    if not app_id or not app_key:
        return []

    country_code = COUNTRY_CODES.get(country, "es")
    url = BASE_URL.format(country=country_code)

    base_params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": 50,
        "what": query.keyword_string or "developer",
        "content-type": "application/json",
    }
    if query.salary_min:
        base_params["salary_min"] = query.salary_min
    if query.salary_max:
        base_params["salary_max"] = query.salary_max
    if query.job_type == "remote":
        base_params["where"] = "remote"

    # Paginación: hasta 3 páginas = 150 resultados máx.
    raw_items = []
    for page in range(1, 4):
        page_url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/{page}"
        try:
            r = requests.get(page_url, params=base_params, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            items = data.get("results", [])
            if not items:
                break
            raw_items.extend(items)
        except Exception:
            break

    jobs = []
    for item in raw_items:
        salary_min = int(item.get("salary_min") or 0) or None
        salary_max = int(item.get("salary_max") or 0) or None

        loc_data = item.get("location", {})
        location = loc_data.get("display_name", "") or ", ".join(loc_data.get("area", []))

        # Añadir el nombre del país a la location si no está ya incluido
        if country and country not in location:
            location = f"{location}, {country}".strip(", ")

        job_type = _detect_type(item.get("title", "") + " " + item.get("description", ""))
        tags = [{"remote": "Remoto", "hybrid": "Híbrido", "onsite": "Presencial"}.get(job_type, "")] if job_type else []

        jobs.append(Job(
            title=item.get("title", ""),
            company=item.get("company", {}).get("display_name", ""),
            location=location,
            url=item.get("redirect_url", ""),
            source="Adzuna",
            salary_min=salary_min,
            salary_max=salary_max,
            currency="EUR" if country_code in ("es",) else "USD",
            job_type=job_type,
            description=item.get("description", "")[:300],
            posted=item.get("created", ""),
            tags=[t for t in tags if t],
        ))

    return jobs


def _search_multi(query: ParsedQuery, countries: list[str]) -> list[Job]:
    import concurrent.futures
    jobs: list[Job] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(countries)) as ex:
        futures = [ex.submit(search, query, c) for c in countries]
        for f in concurrent.futures.as_completed(futures, timeout=15):
            try:
                jobs.extend(f.result())
            except Exception:
                pass
    return jobs


def _detect_type(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ("remoto", "remote", "teletrabajo")):
        return "remote"
    if any(k in lower for k in ("híbrido", "hibrido", "hybrid")):
        return "hybrid"
    return "onsite"
