import os
import uuid

from fastapi import Request, Response

COOKIE_NAME = "buscador_session"
MAX_AGE = 60 * 60 * 24 * 365  # 1 año

# En local, frontend y backend comparten "localhost" (SameSite=Lax basta).
# En producción están en dominios distintos (vercel.app / onrender.com), así
# que la cookie de sesión necesita SameSite=None + Secure para viajar entre
# ellos en peticiones fetch con credentials: "include".
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def get_session_id(request: Request, response: Response) -> str:
    sid = request.cookies.get(COOKIE_NAME)
    if not sid:
        sid = uuid.uuid4().hex
        response.set_cookie(
            COOKIE_NAME,
            sid,
            httponly=True,
            samesite=COOKIE_SAMESITE,
            secure=COOKIE_SECURE,
            max_age=MAX_AGE,
            path="/",
        )
    return sid
