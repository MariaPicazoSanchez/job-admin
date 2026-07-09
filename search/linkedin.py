"""
Fuente: LinkedIn Jobs (scraping público, sin login).
LinkedIn tiene anti-bot agresivo; si bloquea devuelve lista vacía sin error.
"""
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from .models import Job
from .parser import ParsedQuery

BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
TIMEOUT = 12

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.linkedin.com/jobs/search/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

COUNTRY_GEOS = {
    "España":          "105646813",
    "México":          "103323778",
    "Argentina":       "100446943",
    "Colombia":        "100876405",
    "Chile":           "104621616",
    "Estados Unidos":  "103644278",
    "Reino Unido":     "101165590",
    "Alemania":        "101282230",
    "Francia":         "105015875",
    "Países Bajos":    "102890719",
    "Canadá":          "101174742",
    "Australia":       "101452733",
    "Brasil":          "106057199",
    "Uruguay":         "100867946",
}


def search(query: ParsedQuery, country: str = "Cualquier país") -> list[Job]:
    keyword = query.keyword_string or "developer"
    geo_id = COUNTRY_GEOS.get(country, "")

    params: dict = {
        "keywords": keyword,
        "start": 0,
        "count": 25,
        "f_TPR": "",
    }
    if geo_id:
        params["geoId"] = geo_id
    if query.job_type == "remote":
        params["f_WT"] = "2"     # LinkedIn: 2 = remote
    elif query.job_type == "hybrid":
        params["f_WT"] = "3"
    elif query.job_type == "onsite":
        params["f_WT"] = "1"

    # Pequeño delay para parecer humano
    time.sleep(random.uniform(0.5, 1.2))

    try:
        r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code in (429, 403, 999):
            return []
        r.raise_for_status()
    except Exception:
        return []

    return _parse_cards(r.text)


def _parse_cards(html: str) -> list[Job]:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for card in soup.select("li"):
        title_el   = card.select_one("h3.base-search-card__title")
        company_el = card.select_one("h4.base-search-card__subtitle")
        loc_el     = card.select_one("span.job-search-card__location")
        link_el    = card.select_one("a.base-card__full-link")
        listed_el  = card.select_one("time")

        if not title_el or not link_el:
            continue

        title    = title_el.get_text(strip=True)
        company  = company_el.get_text(strip=True) if company_el else ""
        location = loc_el.get_text(strip=True) if loc_el else ""
        url      = link_el.get("href", "").split("?")[0]
        posted   = listed_el.get("datetime", "") if listed_el else ""

        job_type = _detect_type(title)
        tags = [{"remote": "Remoto", "hybrid": "Híbrido", "onsite": "Presencial"}.get(job_type, "")]

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=url,
            source="LinkedIn",
            job_type=job_type,
            posted=posted,
            tags=[t for t in tags if t],
        ))

    return jobs


def _detect_type(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ("remote", "remoto", "teletrabajo")):
        return "remote"
    if any(k in lower for k in ("hybrid", "híbrido", "hibrido")):
        return "hybrid"
    return "onsite"
