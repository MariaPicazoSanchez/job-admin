from sqlalchemy import JSON, Column, Float, Integer, String

from .db import Base


class SavedJobDB(Base):
    __tablename__ = "saved_jobs"

    id = Column(String, primary_key=True)
    session_id = Column(String, primary_key=True)

    title = Column(String, nullable=False)
    company = Column(String, default="")
    location = Column(String, default="")
    url = Column(String, nullable=False)
    source = Column(String, default="")
    job_type = Column(String, default="")
    salary_display = Column(String, default="")
    salary_estimate = Column(String, default="")
    description = Column(String, default="")
    skills = Column(JSON, default=list)
    signals = Column(JSON, default=list)
    seniority = Column(String, default="")
    saved_at = Column(String, default="")

    status = Column(String, default="Guardada")
    applied_date = Column(String, default="")
    salary_offered = Column(String, default="")
    contact = Column(String, default="")
    interview_date = Column(String, default="")
    notes = Column(String, default="")
    interest = Column(String, default="Medio")
    timeline = Column(JSON, default=list)
