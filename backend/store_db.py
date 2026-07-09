from datetime import date

from sqlalchemy.orm import Session

from .models_db import SavedJobDB


def _to_dict(row: SavedJobDB) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "company": row.company,
        "location": row.location,
        "url": row.url,
        "source": row.source,
        "job_type": row.job_type,
        "salary_display": row.salary_display,
        "salary_estimate": row.salary_estimate,
        "description": row.description,
        "skills": row.skills or [],
        "signals": row.signals or [],
        "seniority": row.seniority,
        "saved_at": row.saved_at,
        "status": row.status,
        "applied_date": row.applied_date,
        "salary_offered": row.salary_offered,
        "contact": row.contact,
        "interview_date": row.interview_date,
        "notes": row.notes,
        "interest": row.interest,
        "timeline": row.timeline or [],
    }


def load_all(db: Session, session_id: str) -> list[dict]:
    rows = db.query(SavedJobDB).filter_by(session_id=session_id).all()
    return [_to_dict(r) for r in rows]


def get(db: Session, session_id: str, jid: str) -> dict | None:
    row = db.query(SavedJobDB).filter_by(session_id=session_id, id=jid).first()
    return _to_dict(row) if row else None


def is_saved(db: Session, session_id: str, jid: str) -> bool:
    return db.query(SavedJobDB).filter_by(session_id=session_id, id=jid).first() is not None


def upsert(db: Session, session_id: str, data: dict) -> dict:
    row = db.query(SavedJobDB).filter_by(session_id=session_id, id=data["id"]).first()
    if row:
        for k, v in data.items():
            setattr(row, k, v)
    else:
        row = SavedJobDB(session_id=session_id, status="Guardada", interest="Medio", timeline=[], **data)
        db.add(row)
    db.commit()
    db.refresh(row)
    return _to_dict(row)


def update_fields(db: Session, session_id: str, jid: str, **fields) -> dict | None:
    row = db.query(SavedJobDB).filter_by(session_id=session_id, id=jid).first()
    if not row:
        return None
    for k, v in fields.items():
        if hasattr(row, k):
            setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return _to_dict(row)


def delete(db: Session, session_id: str, jid: str) -> None:
    db.query(SavedJobDB).filter_by(session_id=session_id, id=jid).delete()
    db.commit()


def add_timeline(db: Session, session_id: str, jid: str, event: str) -> None:
    row = db.query(SavedJobDB).filter_by(session_id=session_id, id=jid).first()
    if row:
        tl = list(row.timeline or [])
        tl.append({"date": date.today().isoformat(), "event": event})
        row.timeline = tl
        db.commit()


def compute_stats(db: Session, session_id: str) -> dict:
    from search.store import SavedJob
    from search.store import compute_stats as _compute_stats

    rows = load_all(db, session_id)
    jobs = [SavedJob(**r) for r in rows]
    return _compute_stats(jobs)
