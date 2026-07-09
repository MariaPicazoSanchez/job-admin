"""
Persistencia local de candidaturas ("Mis Ofertas").
Guarda en un JSON junto al proyecto. Sin backend, privado y exportable.
"""
import json
import hashlib
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

STORE_FILE = Path(__file__).parent.parent / "saved_jobs.json"

# ── Estados del proceso de selección (en orden de avance) ─────────────────────
ESTADOS = [
    "Guardada",
    "Pendiente de aplicar",
    "Solicitud enviada",
    "CV revisado",
    "Respuesta recibida",
    "Entrevista HR",
    "Entrevista técnica",
    "Prueba técnica",
    "Oferta recibida",
    "Rechazada",
    "Aceptada",
    "Ghosted",
]
INTERES = ["Bajo", "Medio", "Alto"]

# Conjuntos derivados para estadísticas
_APPLIED_PLUS  = set(ESTADOS[2:9]) | {"Aceptada"}                       # ya enviada
_RESPONSE_PLUS = set(ESTADOS[4:9]) | {"Aceptada", "Rechazada"}          # hubo respuesta
_INTERVIEW     = {"Entrevista HR", "Entrevista técnica", "Prueba técnica",
                  "Oferta recibida", "Aceptada"}
_CLOSED        = {"Rechazada", "Aceptada", "Ghosted"}


@dataclass
class SavedJob:
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    job_type: str = ""
    salary_display: str = ""
    salary_estimate: str = ""
    description: str = ""
    skills: list = field(default_factory=list)
    signals: list = field(default_factory=list)   # [{emoji, label, detail, kind}]
    seniority: str = ""
    saved_at: str = ""
    # ── Seguimiento editable ──
    status: str = "Guardada"
    applied_date: str = ""
    salary_offered: str = ""
    contact: str = ""
    interview_date: str = ""
    notes: str = ""
    interest: str = "Medio"
    timeline: list = field(default_factory=list)   # [{date, event}]


# ── Utilidades de id / fecha ──────────────────────────────────────────────────

def make_id(url: str, title: str) -> str:
    return hashlib.md5(f"{url}|{title}".encode("utf-8")).hexdigest()[:12]


def today() -> str:
    return date.today().isoformat()


# ── Carga / guardado en disco ─────────────────────────────────────────────────

def _load_raw() -> list[dict]:
    if STORE_FILE.exists():
        try:
            return json.loads(STORE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def load_all() -> list[SavedJob]:
    out: list[SavedJob] = []
    for d in _load_raw():
        try:
            out.append(SavedJob(**d))
        except Exception:
            continue
    return out


def _save_all(jobs: list[SavedJob]) -> None:
    STORE_FILE.write_text(
        json.dumps([asdict(j) for j in jobs], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── CRUD ──────────────────────────────────────────────────────────────────────

def is_saved(url: str, title: str) -> bool:
    jid = make_id(url, title)
    return any(j.id == jid for j in load_all())


def get(jid: str) -> SavedJob | None:
    return next((j for j in load_all() if j.id == jid), None)


def upsert(job: SavedJob) -> None:
    jobs = load_all()
    for i, j in enumerate(jobs):
        if j.id == job.id:
            jobs[i] = job
            _save_all(jobs)
            return
    jobs.append(job)
    _save_all(jobs)


def update_fields(jid: str, **fields) -> SavedJob | None:
    jobs = load_all()
    for j in jobs:
        if j.id == jid:
            for k, v in fields.items():
                if hasattr(j, k):
                    setattr(j, k, v)
            _save_all(jobs)
            return j
    return None


def delete(jid: str) -> None:
    _save_all([j for j in load_all() if j.id != jid])


def add_timeline(jid: str, event: str) -> None:
    jobs = load_all()
    for j in jobs:
        if j.id == jid:
            j.timeline.append({"date": today(), "event": event})
            _save_all(jobs)
            return


# ── Estadísticas personales ─────────────────────────────────────────────────--

def compute_stats(jobs: list[SavedJob]) -> dict:
    total       = len(jobs)
    enviadas    = sum(1 for j in jobs if j.status in _APPLIED_PLUS)
    respuestas  = sum(1 for j in jobs if j.status in _RESPONSE_PLUS)
    entrevistas = sum(1 for j in jobs if j.status in _INTERVIEW)
    activas     = sum(1 for j in jobs if j.status not in _CLOSED)
    ratio       = round(respuestas / enviadas * 100) if enviadas else 0

    companies = Counter(j.company for j in jobs if j.company)
    skills    = Counter(s for j in jobs for s in (j.skills or []))

    return {
        "total":        total,
        "enviadas":     enviadas,
        "entrevistas":  entrevistas,
        "activas":      activas,
        "ratio":        ratio,
        "top_companies": companies.most_common(3),
        "top_skills":    skills.most_common(5),
    }


def is_applied_status(status: str) -> bool:
    return status in _APPLIED_PLUS
