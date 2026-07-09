from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import chat

router = APIRouter()


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = []


@router.get("/api/chat/status")
def chat_status():
    return {"configured": chat.is_configured()}


@router.post("/api/chat")
def send_chat_message(req: ChatRequest):
    if not chat.is_configured():
        raise HTTPException(status_code=503, detail="El chat no está configurado en el servidor.")
    try:
        return chat.send_message(req.message, [t.model_dump() for t in req.history])
    except chat.ChatError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
