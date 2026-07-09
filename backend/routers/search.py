import json
import queue
import threading
from dataclasses import asdict

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse

from search.aggregator import search_jobs_streaming

from ..session import get_session_id

router = APIRouter()

_SENTINEL = object()


@router.get("/api/search")
def search_endpoint(
    request: Request,
    response: Response,
    prompt: str,
    country: str = "Cualquier país",
    job_type: str = "",
    salary_min: int = 0,
    currency: str = "EUR",
    experience: str = "",
):
    # Asegura la cookie de sesión también en este endpoint (aunque no guarde nada aquí).
    get_session_id(request, response)

    def event_stream():
        q: "queue.Queue" = queue.Queue()

        def on_update(jobs):
            q.put(("update", [asdict(j) for j in jobs]))

        def on_done(jobs, market):
            q.put((
                "done",
                {
                    "jobs": [asdict(j) for j in jobs],
                    "market": asdict(market) if market else None,
                },
            ))
            q.put(_SENTINEL)

        def run():
            try:
                search_jobs_streaming(
                    prompt,
                    country,
                    job_type,
                    salary_min,
                    currency,
                    experience,
                    on_update=on_update,
                    on_done=on_done,
                )
            except Exception as exc:
                q.put(("error", str(exc)))
                q.put(_SENTINEL)

        threading.Thread(target=run, daemon=True).start()

        while True:
            item = q.get()
            if item is _SENTINEL:
                break
            event, data = item
            yield f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    stream = StreamingResponse(event_stream(), media_type="text/event-stream")
    if "set-cookie" in response.headers:
        stream.headers["set-cookie"] = response.headers["set-cookie"]
    stream.headers["Cache-Control"] = "no-cache"
    stream.headers["X-Accel-Buffering"] = "no"
    return stream
