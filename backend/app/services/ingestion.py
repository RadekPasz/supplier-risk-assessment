from pathlib import Path

from langchain_core.documents import Document as LCDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


def extract_text_from_file(path: Path, content_type: str | None) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf" or (content_type and "pdf" in content_type):
        reader = PdfReader(str(path))
        parts: list[str] = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n\n".join(parts)
    return path.read_text(encoding="utf-8", errors="replace")


def chunk_text(text: str, source_label: str) -> list[LCDocument]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
    chunks = splitter.split_text(text)
    return [
        LCDocument(page_content=c, metadata={"source": source_label, "chunk_index": i})
        for i, c in enumerate(chunks)
    ]
