import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.supplier import Supplier, SupplierStatus, SupplierTier
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


def _to_read(s: Supplier) -> SupplierRead:
    return SupplierRead.model_validate(s)


@router.get("", response_model=list[SupplierRead])
async def list_suppliers(session: AsyncSession = Depends(get_session)) -> list[SupplierRead]:
    r = await session.execute(select(Supplier).order_by(Supplier.name))
    return [_to_read(x) for x in r.scalars().all()]


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
async def create_supplier(body: SupplierCreate, session: AsyncSession = Depends(get_session)) -> SupplierRead:
    s = Supplier(
        name=body.name,
        description=body.description,
        website=body.website,
        tier=SupplierTier(body.tier.value),
        status=SupplierStatus(body.status.value),
    )
    session.add(s)
    await session.commit()
    await session.refresh(s)
    return _to_read(s)


@router.get("/{supplier_id}", response_model=SupplierRead)
async def get_supplier(supplier_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> SupplierRead:
    s = await session.get(Supplier, supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _to_read(s)


@router.put("/{supplier_id}", response_model=SupplierRead)
async def update_supplier(
    supplier_id: uuid.UUID, body: SupplierUpdate, session: AsyncSession = Depends(get_session)
) -> SupplierRead:
    s = await session.get(Supplier, supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    data = body.model_dump(exclude_unset=True)
    if "tier" in data and data["tier"] is not None:
        data["tier"] = SupplierTier(data["tier"])
    if "status" in data and data["status"] is not None:
        data["status"] = SupplierStatus(data["status"])
    for k, v in data.items():
        setattr(s, k, v)
    await session.commit()
    await session.refresh(s)
    return _to_read(s)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(supplier_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> None:
    s = await session.get(Supplier, supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    await session.delete(s)
    await session.commit()
