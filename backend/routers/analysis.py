from dataclasses import asdict

from fastapi import APIRouter

from search.analyzer import analyze_job
from search.models import Job

from ..schemas import AnalyzeRequest

router = APIRouter()


@router.post("/api/analyze")
def analyze_endpoint(req: AnalyzeRequest):
    job = Job(**req.job.model_dump())
    analysis = analyze_job(job, req.country)
    return asdict(analysis)
