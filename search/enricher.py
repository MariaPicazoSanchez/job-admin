"""
Enriquece cada Job con metadata inferida:
- seniority_level: internship | junior | mid | senior | lead | unknown
- seniority_score: 0-100 (cuanto mayor, más junior)
- years_required: años de experiencia detectados en el texto
- role_category: ml | frontend | backend | devops | data | ...
"""
import re
from .models import Job
from .taxonomies import SENIORITY_LEVELS, ROLE_GROUPS, YEARS_REQUIRED_PATTERNS, NEGATIVE_SENIORITY_SIGNALS


def enrich(job: Job) -> Job:
    text_title = job.title.lower()
    text_full  = (job.title + " " + job.description).lower()

    job.years_required   = _extract_years(text_full)
    job.seniority_level  = _classify_seniority(text_title, text_full, job.years_required)
    job.seniority_score  = _seniority_score(job.seniority_level)
    job.role_category    = _classify_role(text_full)
    return job


# ──────────────────────────────────────────────────────────────
#  Extracción de años requeridos
# ──────────────────────────────────────────────────────────────

def _extract_years(text: str) -> int | None:
    for pattern in YEARS_REQUIRED_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except (ValueError, IndexError):
                pass
    return None


# ──────────────────────────────────────────────────────────────
#  Clasificador de seniority — scoring híbrido
# ──────────────────────────────────────────────────────────────

def _classify_seniority(title: str, full_text: str, years: int | None) -> str:
    scores: dict[str, float] = {level: 0.0 for level in SENIORITY_LEVELS}

    for level, data in SENIORITY_LEVELS.items():
        # Título — señal más fuerte
        for kw in data["title_keywords"]:
            if kw in title:
                scores[level] += 10

        # Descripción
        for kw in data["desc_keywords"]:
            if kw in full_text:
                scores[level] += 4

        # Señales positivas en texto
        for signal in data["positive_signals"]:
            if signal in full_text:
                scores[level] += 6

    # Años de experiencia requeridos
    if years is not None:
        if years == 0:
            scores["internship"] += 8
        elif years <= 1:
            scores["internship"] += 5
            scores["junior"]     += 3
        elif years <= 2:
            scores["junior"]     += 8
        elif years <= 4:
            scores["mid"]        += 8
        elif years <= 7:
            scores["senior"]     += 8
        else:
            scores["lead"]       += 8

    # Señales negativas → bajar score de junior/internship
    for signal in NEGATIVE_SENIORITY_SIGNALS:
        if signal in full_text:
            scores["internship"] -= 10
            scores["junior"]     -= 6

    # Nivel con mayor puntuación gana
    best = max(scores, key=lambda k: scores[k])
    if scores[best] <= 0:
        # Sin señales claras → inferir por años si los hay
        if years is not None:
            if years <= 1: return "junior"
            if years <= 4: return "mid"
            return "senior"
        return "unknown"
    return best


def _seniority_score(level: str) -> float:
    return SENIORITY_LEVELS.get(level, {}).get("score_base", 40.0)


# ──────────────────────────────────────────────────────────────
#  Clasificador de categoría de rol
# ──────────────────────────────────────────────────────────────

def _classify_role(text: str) -> str:
    best_cat   = "other"
    best_score = 0

    for category, data in ROLE_GROUPS.items():
        score = sum(1 for term in data["terms"] if term in text)
        if score > best_score:
            best_score = score
            best_cat   = category

    return best_cat
