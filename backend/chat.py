import os

import requests

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

SYSTEM_PROMPT = """Eres el asistente de búsqueda integrado en "Buscador de Empleo", una aplicación \
de búsqueda de ofertas de trabajo. Tu única función es ayudar con temas relacionados con la \
búsqueda de empleo: sugerir palabras clave o roles para buscar en un sector, explicar tendencias \
del mercado laboral, aconsejar sobre CVs o entrevistas, aclarar modalidades de trabajo, dudas \
sobre salarios orientativos, nombres alternativos de un puesto, etc.

Si te preguntan algo que NO tiene relación con empleo, búsqueda de trabajo o carrera profesional, \
recházalo amablemente en una frase y redirige la conversación hacia el buscador de empleo. No \
respondas preguntas de cultura general, código, matemáticas, entretenimiento u otros temas ajenos.

Responde siempre en español, de forma breve y directa (2-4 frases como máximo).

Cuando tenga sentido, sugiere hasta 5 palabras clave de búsqueda cortas y concretas (2-4 palabras \
cada una) que la persona podría escribir en el buscador de ofertas. Si la pregunta no da pie a \
sugerir palabras clave (p. ej. rechazas la pregunta por no ser de empleo), deja la lista vacía."""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "reply": {"type": "STRING"},
        "suggested_keywords": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
    },
    "required": ["reply", "suggested_keywords"],
}


class ChatError(Exception):
    pass


def is_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def send_message(message: str, history: list[dict]) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ChatError("GEMINI_API_KEY no configurada")

    contents = []
    for turn in history:
        role = "model" if turn.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": turn.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0.4,
            "maxOutputTokens": 512,
        },
    }

    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": api_key},
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ChatError(f"Error al contactar con Gemini: {exc}") from exc

    data = resp.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise ChatError("Respuesta inesperada de Gemini") from exc

    import json

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ChatError("No se pudo interpretar la respuesta de Gemini") from exc

    return {
        "reply": parsed.get("reply", ""),
        "suggested_keywords": parsed.get("suggested_keywords", []) or [],
    }
