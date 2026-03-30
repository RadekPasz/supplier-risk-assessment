import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.supplier import Supplier
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_agent import run_chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, session: AsyncSession = Depends(get_session)) -> ChatResponse:
    if not (settings.openai_api_key or "").strip():
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not set. Add it to your .env (or Docker Compose environment) and restart the backend.",
        )
    extra = None
    if body.supplier_id:
        try:
            sid = uuid.UUID(body.supplier_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid supplier_id") from e
        s = await session.get(Supplier, sid)
        if not s:
            raise HTTPException(status_code=404, detail="Supplier not found")
        extra = f"Focused supplier: {s.name} (id={s.id})"
    try:
        reply = run_chat(body.message, extra_context=extra)
    except Exception as e:
        logger.exception("Chat failed")
        msg = str(e).strip() or type(e).__name__
        raise HTTPException(
            status_code=502,
            detail=f"AI request failed: {msg}. Check OPENAI_API_KEY, billing, and backend logs.",
        ) from e
    return ChatResponse(reply=reply)
