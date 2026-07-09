import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from .routers import analysis, config, jobs, search

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Buscador de Empleo API")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(analysis.router)
app.include_router(jobs.router)
app.include_router(config.router)


@app.get("/health")
def health():
    return {"status": "ok"}
