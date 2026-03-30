import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: uuid.UUID
    supplier_id: uuid.UUID
    original_filename: str
    content_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
