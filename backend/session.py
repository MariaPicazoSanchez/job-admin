import uuid

from fastapi import Request, Response

COOKIE_NAME = "buscador_session"
MAX_AGE = 60 * 60 * 24 * 365  # 1 año


def get_session_id(request: Request, response: Response) -> str:
    sid = request.cookies.get(COOKIE_NAME)
    if not sid:
        sid = uuid.uuid4().hex
        response.set_cookie(
            COOKIE_NAME,
            sid,
            httponly=True,
            samesite="lax",
            max_age=MAX_AGE,
            path="/",
        )
    return sid
