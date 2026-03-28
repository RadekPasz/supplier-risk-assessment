import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class SupplierTierSchema(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class SupplierStatusSchema(str, Enum):
    active = "active"
    pending = "pending"
    archived = "archived"


class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    website: str | None = None
    tier: SupplierTierSchema = SupplierTierSchema.medium
    status: SupplierStatusSchema = SupplierStatusSchema.pending


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    website: str | None = None
    tier: SupplierTierSchema | None = None
    status: SupplierStatusSchema | None = None


class SupplierRead(SupplierBase):
    id: uuid.UUID
    risk_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
