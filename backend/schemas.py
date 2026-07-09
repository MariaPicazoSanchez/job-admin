from typing import Optional

from pydantic import BaseModel


class JobIn(BaseModel):
    title: str
    company: str = ""
    location: str = ""
    url: str
    source: str = ""
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "EUR"
    job_type: str = ""
    description: str = ""
    posted: str = ""
    tags: list[str] = []
    seniority_level: str = "unknown"
    seniority_score: float = 40.0
    years_required: Optional[int] = None
    role_category: str = "other"


class AnalyzeRequest(BaseModel):
    job: JobIn
    country: str = "España"


class SaveJobRequest(BaseModel):
    job: JobIn
    country: str = "España"


class JobUpdateRequest(BaseModel):
    status: Optional[str] = None
    interest: Optional[str] = None
    applied_date: Optional[str] = None
    interview_date: Optional[str] = None
    salary_offered: Optional[str] = None
    contact: Optional[str] = None
    notes: Optional[str] = None
