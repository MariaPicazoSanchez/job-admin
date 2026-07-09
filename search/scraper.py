"""
Scraping directo de portales de empleo.
Fuentes: InfoJobs (España) y Computrabajo (LATAM).
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from .models import Job
from .parser import ParsedQuery


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 12


# ──────────────────────────────────────────────────────────────
#  InfoJobs
# ──────────────────────────────────────────────────────────────
def search_infojobs(query: ParsedQuery, country: str = "España") -> list[Job]:
    if country not in ("España", "Cualquier país"):
        return []

    keywords = query.keyword_string.replace(" ", "+")
    url = f"https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword={keywords}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []

    for card in soup.select("li.ij-OfferCard")[:15]:
        title_el = card.select_one("h2.ij-OfferCard-description-title a, a.ij-OfferCard-description-title")
        company_el = card.select_one(".ij-OfferCard-description-subtitle")
        location_el = card.select_one(".ij-OfferCard-description-list-item--location")
        salary_el = card.select_one(".ij-OfferCard-description-list-item--salary")

        if not title_el:
            continue

        href = title_el.get("href", "")
        if href and not href.startswith("http"):
            href = "https://www.infojobs.net" + href

        salary_text = salary_el.get_text(strip=True) if salary_el else ""
        salary_min, salary_max = _parse_salary_text(salary_text)

        title = title_el.get_text(strip=True)
        job_type = _detect_type(title + " " + salary_text)

        if not _passes_filters(query, salary_min, salary_max, job_type):
            continue

        jobs.append(Job(
            title=title,
            company=company_el.get_text(strip=True) if company_el else "",
            location=location_el.get_text(strip=True) if location_el else "España",
            url=href,
            source="InfoJobs",
            salary_min=salary_min,
            salary_max=salary_max,
            currency="EUR",
            job_type=job_type,
            tags=[_type_label(job_type)] if job_type else [],
        ))

    return jobs


# ──────────────────────────────────────────────────────────────
#  Computrabajo
# ──────────────────────────────────────────────────────────────
COMPUTRABAJO_COUNTRIES = {
    "México": "mx", "Colombia": "co", "Argentina": "ar",
    "Chile": "cl", "Uruguay": "uy", "Perú": "pe",
    "Venezuela": "ve", "Ecuador": "ec",
}


def search_computrabajo(query: ParsedQuery, country: str = "México") -> list[Job]:
    code = COMPUTRABAJO_COUNTRIES.get(country)
    if not code:
        return []

    keywords = query.keyword_string.replace(" ", "+")
    url = f"https://www.computrabajo.com.{code}/trabajo-de-{keywords.lower()}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []

    for card in soup.select("article.box_offer")[:15]:
        title_el = card.select_one("h2.js-o-title a, .title_offer a")
        company_el = card.select_one(".fc_base.fs14")
        location_el = card.select_one(".fs13.fc_base")
        salary_el = card.select_one(".salary, .fc_2")

        if not title_el:
            continue

        href = title_el.get("href", "")
        if href and not href.startswith("http"):
            href = f"https://www.computrabajo.com.{code}" + href

        salary_text = salary_el.get_text(strip=True) if salary_el else ""
        salary_min, salary_max = _parse_salary_text(salary_text)

        title = title_el.get_text(strip=True)
        job_type = _detect_type(title)

        if not _passes_filters(query, salary_min, salary_max, job_type):
            continue

        jobs.append(Job(
            title=title,
            company=company_el.get_text(strip=True) if company_el else "",
            location=location_el.get_text(strip=True) if location_el else country,
            url=href,
            source="Computrabajo",
            salary_min=salary_min,
            salary_max=salary_max,
            currency="USD",
            job_type=job_type,
            tags=[_type_label(job_type)] if job_type else [],
        ))

    return jobs


# ──────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────
def _parse_salary_text(text: str) -> tuple[int | None, int | None]:
    numbers = re.findall(r"\d[\d\.]+", text.replace(",", "."))
    nums = []
    for n in numbers:
        clean = n.replace(".", "")
        try:
            v = int(clean)
            if v > 500:
                nums.append(v)
        except ValueError:
            pass
    if len(nums) >= 2:
        return min(nums[:2]), max(nums[:2])
    if len(nums) == 1:
        return nums[0], None
    return None, None


def _detect_type(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ("remoto", "remote", "teletrabajo", "desde casa")):
        return "remote"
    if any(k in lower for k in ("híbrido", "hibrido", "hybrid")):
        return "hybrid"
    return "onsite"


def _type_label(job_type: str) -> str:
    return {"remote": "Remoto", "hybrid": "Híbrido", "onsite": "Presencial"}.get(job_type, "")


def _passes_filters(q: ParsedQuery, sal_min, sal_max, job_type) -> bool:
    if q.job_type and q.job_type != job_type:
        return False
    if q.salary_min and sal_max and sal_max < q.salary_min:
        return False
    return True
