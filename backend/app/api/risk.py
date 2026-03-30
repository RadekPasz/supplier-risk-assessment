from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierRead

router = APIRouter(prefix="/api", tags=["risk"])


@router.get("/risk-summary", response_model=list[SupplierRead])
async def risk_summary(session: AsyncSession = Depends(get_session)) -> list[SupplierRead]:
    r = await session.execute(select(Supplier).order_by(Supplier.risk_score.desc()))
    return [SupplierRead.model_validate(x) for x in r.scalars().all()]
