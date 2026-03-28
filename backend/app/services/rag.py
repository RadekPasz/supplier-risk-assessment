import shutil
import uuid
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LCDocument
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select

from app.config import settings
from app.database_sync import get_sync_session
from app.models.document import Document as SupplierDocument
from app.services.ingestion import chunk_text, extract_text_from_file

INDEX_DIR = Path(settings.upload_dir) / "faiss_index"


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key or None)


def _load_or_empty() -> FAISS:
    embeddings = get_embeddings()
    INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
    if (INDEX_DIR / "index.faiss").exists():
        return FAISS.load_local(
            str(INDEX_DIR),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    return FAISS.from_documents([], embeddings)


def _save(vs: FAISS) -> None:
    INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
    vs.save_local(str(INDEX_DIR))


def ingest_document_chunks(
    supplier_id: uuid.UUID,
    document_id: uuid.UUID,
    original_filename: str,
    docs: list[LCDocument],
) -> None:
    vs = _load_or_empty()
    for d in docs:
        d.metadata["supplier_id"] = str(supplier_id)
        d.metadata["document_id"] = str(document_id)
        d.metadata["document_name"] = original_filename
    vs.add_documents(docs, ids=[str(uuid.uuid4()) for _ in docs])
    _save(vs)


def search_document_chunks(query: str, supplier_id: uuid.UUID | None = None, k: int = 6) -> list[LCDocument]:
    if not (INDEX_DIR / "index.faiss").exists():
        return []
    vs = _load_or_empty()
    docs = vs.similarity_search(query, k=k * 4)
    if not supplier_id:
        return docs[:k]
    sid = str(supplier_id)
    filtered = [d for d in docs if (d.metadata or {}).get("supplier_id") == sid]
    return (filtered or docs)[:k]


def rebuild_faiss_from_database() -> None:
    """Rebuild the FAISS index from all stored documents (used after deletes)."""
    embeddings = get_embeddings()
    INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
    vs = FAISS.from_documents([], embeddings)
    with get_sync_session() as s:
        rows = list(s.execute(select(SupplierDocument)).scalars().all())
    for doc in rows:
        path = Path(doc.stored_path)
        if not path.is_file():
            continue
        text = extract_text_from_file(path, doc.content_type)
        if not text.strip():
            continue
        chunks = chunk_text(text, source_label=doc.original_filename)
        for d in chunks:
            d.metadata["supplier_id"] = str(doc.supplier_id)
            d.metadata["document_id"] = str(doc.id)
            d.metadata["document_name"] = doc.original_filename
        if chunks:
            vs.add_documents(chunks, ids=[str(uuid.uuid4()) for _ in chunks])
    if not rows:
        if INDEX_DIR.exists():
            shutil.rmtree(INDEX_DIR)
        return
    _save(vs)


def delete_document_chunks(_document_id: uuid.UUID) -> None:
    rebuild_faiss_from_database()
