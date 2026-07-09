"""
Fase B — Reranking inteligente.
Puntúa cada oferta enriquecida respecto a la intención del usuario.
"""
from .models import Job
from .parser import ParsedQuery

# Mapa seniority_code → peso de match con el nivel pedido
_SENIORITY_COMPATIBILITY: dict[str, dict[str, float]] = {
    "no_exp": {
        "internship": 100,
        "junior":      40,
        "unknown":     20,
        "mid":        -20,
        "senior":     -80,
        "lead":      -120,
    },
    "junior": {
        "internship":  60,
        "junior":     100,
        "unknown":     25,
        "mid":         -5,
        "senior":     -60,
        "lead":      -100,
    },
    "mid": {
        "junior":      10,
        "mid":        100,
        "unknown":     30,
        "senior":     -20,
        "internship": -30,
        "lead":       -50,
    },
    "senior": {
        "mid":         20,
        "senior":     100,
        "unknown":     30,
        "lead":        10,
        "junior":     -30,
        "internship": -80,
    },
    "lead": {
        "senior":      30,
        "lead":       100,
        "unknown":     20,
        "mid":        -20,
        "junior":     -60,
        "internship": -100,
    },
}


def rerank(jobs: list[Job], q: ParsedQuery) -> list[Job]:
    if not jobs:
        return []

    scored = [(score(job, q), job) for job in jobs]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Filtro duro: descartar si el score de seniority es muy negativo
    # (solo cuando el usuario especificó un nivel de seniority)
    if q.experience:
        scored = [(s, j) for s, j in scored if s > -50]

    return [j for _, j in scored]


def score(job: Job, q: ParsedQuery) -> float:
    total = 0.0

    # ── 1. Relevancia de rol (keywords en título/desc) ────────
    title = job.title.lower()
    desc  = (job.description or "").lower()

    for kw in q.keywords:
        kl = kw.lower()
        if kl in title:
            total += 15
        elif kl in desc:
            total += 3

    # Bonus si ≥50% de keywords en título
    if q.keywords:
        hits = sum(1 for kw in q.keywords if kw.lower() in title)
        if hits / len(q.keywords) >= 0.5:
            total += 10

    # ── 2. Match de seniority ─────────────────────────────────
    if q.experience:
        compat = _SENIORITY_COMPATIBILITY.get(q.experience, {})
        total += compat.get(job.seniority_level, 0)
    else:
        # Sin nivel pedido: ligero bonus a los junior/internship
        if job.seniority_level in ("internship", "junior"):
            total += 5

    # ── 3. Match de rol (categoría inferida) ─────────────────
    if job.role_category and job.role_category != "other":
        # Si el rol del job coincide con las keywords del usuario
        role_words = set(job.role_category.replace("_", " ").split())
        kw_set     = {k.lower() for k in q.keywords}
        if role_words & kw_set:
            total += 8

    # ── 4. Bonus por salario indicado ────────────────────────
    if job.salary_min or job.salary_max:
        total += 5

    # ── 5. Penalización si no hay ningún keyword en todo el texto
    all_text = title + " " + desc
    if not any(kw.lower() in all_text for kw in q.keywords):
        total -= 999  # eliminar efectivamente

    return total
