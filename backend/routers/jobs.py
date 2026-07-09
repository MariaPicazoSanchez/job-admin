from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from search.analyzer import analyze_job
from search.models import Job
from search.store import ESTADOS, INTERES, is_applied_status, make_id, today

from .. import store_db
from ..db import get_db
from ..schemas import JobUpdateRequest, SaveJobRequest
from ..session import get_session_id

router = APIRouter()


@router.get("/api/jobs")
def list_jobs(request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = get_session_id(request, response)
    return store_db.load_all(db, session_id)


@router.get("/api/jobs/stats")
def jobs_stats(request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = get_session_id(request, response)
    return store_db.compute_stats(db, session_id)


@router.get("/api/jobs/meta")
def jobs_meta():
    return {"estados": ESTADOS, "interes": INTERES}


@router.post("/api/jobs")
def save_job(
    req: SaveJobRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    session_id = get_session_id(request, response)
    job = Job(**req.job.model_dump())
    ana = analyze_job(job, req.country)
    jid = make_id(job.url, job.title)

    data = {
        "id": jid,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "url": job.url,
        "source": job.source,
        "job_type": job.job_type,
        "salary_display": job.salary_display,
        "salary_estimate": ana.salary_estimate.range_display if ana.salary_estimate else "",
        "description": ana.clean_description,
        "skills": ana.hard_skills,
        "signals": [asdict(s) for s in ana.signals],
        "seniority": job.seniority_label,
        "saved_at": today(),
    }
    return store_db.upsert(db, session_id, data)


@router.patch("/api/jobs/{jid}")
def update_job(
    jid: str,
    req: JobUpdateRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    session_id = get_session_id(request, response)
    current = store_db.get(db, session_id, jid)
    if not current:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")

    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    status_changed = "status" in fields and fields["status"] != current["status"]

    if (
        status_changed
        and is_applied_status(fields["status"])
        and not current.get("applied_date")
        and not fields.get("applied_date")
    ):
        fields["applied_date"] = today()

    updated = store_db.update_fields(db, session_id, jid, **fields)
    if status_changed:
        store_db.add_timeline(db, session_id, jid, f"Estado → {fields['status']}")
        updated = store_db.get(db, session_id, jid)
    return updated


@router.delete("/api/jobs/{jid}")
def delete_job(jid: str, request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = get_session_id(request, response)
    store_db.delete(db, session_id, jid)
    return {"ok": True}
