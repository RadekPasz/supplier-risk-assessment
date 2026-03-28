import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.document import Document as SupplierDocument
from app.models.supplier import Supplier
from app.schemas.document import DocumentRead
from app.services.ingestion import chunk_text, extract_text_from_file
from app.services.rag import ingest_document_chunks, rebuild_faiss_from_database

router = APIRouter(prefix="/api/suppliers", tags=["documents"])


@router.get("/{supplier_id}/documents", response_model=list[DocumentRead])
async def list_documents(
    supplier_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> list[DocumentRead]:
    s = await session.get(Supplier, supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    r = await session.execute(
        select(SupplierDocument)
        .where(SupplierDocument.supplier_id == supplier_id)
        .order_by(SupplierDocument.created_at.desc())
    )
    return [DocumentRead.model_validate(x) for x in r.scalars().all()]


@router.post("/{supplier_id}/documents", response_model=DocumentRead, status_code=201)
async def upload_document(
    supplier_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    file: UploadFile = File(...),
) -> DocumentRead:
    s = await session.get(Supplier, supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")

    base = Path(settings.upload_dir)
    base.mkdir(parents=True, exist_ok=True)
    doc_id = uuid.uuid4()
    safe_name = (file.filename or "upload").replace("\\", "_").replace("/", "_")
    dest = base / f"{doc_id}_{safe_name}"
    content = await file.read()
    dest.write_bytes(content)

    text = extract_text_from_file(dest, file.content_type)
    if not text.strip():
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Could not extract text from file (empty or unsupported)")

    chunks = chunk_text(text, source_label=safe_name)
    doc = SupplierDocument(
        id=doc_id,
        supplier_id=supplier_id,
        original_filename=safe_name,
        stored_path=str(dest),
        content_type=file.content_type,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)

    ingest_document_chunks(supplier_id, doc_id, safe_name, chunks)

    return DocumentRead.model_validate(doc)


@router.delete("/{supplier_id}/documents/{document_id}", status_code=204)
async def delete_document(
    supplier_id: uuid.UUID, document_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> None:
    d = await session.get(SupplierDocument, document_id)
    if not d or d.supplier_id != supplier_id:
        raise HTTPException(status_code=404, detail="Document not found")
    stored = d.stored_path
    await session.delete(d)
    await session.commit()
    Path(stored).unlink(missing_ok=True)
    rebuild_faiss_from_database()
