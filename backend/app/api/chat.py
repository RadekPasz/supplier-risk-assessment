import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.supplier import Supplier
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_agent import run_chat

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, session: AsyncSession = Depends(get_session)) -> ChatResponse:
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
    reply = run_chat(body.message, extra_context=extra)
    return ChatResponse(reply=reply)
