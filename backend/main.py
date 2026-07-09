import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .db import Base, engine  # noqa: E402
from .routers import analysis, chat, config, jobs, search  # noqa: E402

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
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
