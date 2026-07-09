from fastapi import APIRouter

from search import adzuna

router = APIRouter()


@router.get("/api/sources")
def sources_endpoint():
    return {
        "linkedin": True,
        "remotive": True,
        "arbeitnow": True,
        "computrabajo": True,
        "adzuna": adzuna.is_configured(),
    }
