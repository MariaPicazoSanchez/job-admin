import json
import os
import re

import requests

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

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
sugerir palabras clave (p. ej. rechazas la pregunta por no ser de empleo), deja la lista vacía.

Responde ÚNICAMENTE con un objeto JSON, sin texto adicional ni bloques de código, con esta forma \
exacta: {"reply": "tu respuesta en texto", "suggested_keywords": ["palabra 1", "palabra 2"]}"""


class ChatError(Exception):
    pass


def is_configured() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def _extract_json(text: str) -> dict:
    text = text.strip()
    # Algunos modelos envuelven el JSON en un bloque ```json ... ```
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    return json.loads(text)


def send_message(message: str, history: list[dict]) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ChatError("OPENROUTER_API_KEY no configurada")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history:
        role = "assistant" if turn.get("role") == "assistant" else "user"
        messages.append({"role": role, "content": turn.get("content", "")})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.4,
        "max_tokens": 512,
    }

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://buscador-empleo.app",
                "X-Title": "Buscador de Empleo",
            },
            json=payload,
            timeout=25,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ChatError(f"Error al contactar con OpenRouter: {exc}") from exc

    data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise ChatError("Respuesta inesperada de OpenRouter") from exc

    try:
        parsed = _extract_json(text)
    except json.JSONDecodeError:
        # El modelo no siguió el formato JSON; devolvemos el texto tal cual.
        return {"reply": text.strip(), "suggested_keywords": []}

    return {
        "reply": parsed.get("reply", ""),
        "suggested_keywords": parsed.get("suggested_keywords", []) or [],
    }
