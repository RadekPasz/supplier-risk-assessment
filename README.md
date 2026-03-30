# Supplier Risk Assessment (NIS2) — Intern Assignment

Full-stack prototype: **PostgreSQL** + **FastAPI** (async SQLAlchemy) + **React (TypeScript)** + **LangChain** with **OpenAI** embeddings/chat and a **FAISS** vector store for document RAG. The AI assistant uses **tool calling** to read suppliers/assessments from the database and **semantic search** over uploaded document chunks.

## Quick start (Docker)

1. In `.env`, set `OPENAI_API_KEY` to a key from the OpenAI website.
2. From this directory:

```bash
docker compose up --build
```

3. Open **http://localhost:5174**. The API is proxied to the backend on the same origin (`/api/...`).

## Data model (decisions)

- **Supplier**: identity (`name`, `description`, `website`), **tier** (`critical` → `low`), **risk_score** (0–100, higher = more gaps), **status** (`active` / `pending` / `archived`). Tier is organizational criticality; risk_score is derived from the questionnaire.
- **AssessmentQuestion**: canonical NIS2-aligned prompts (10 topics: risk management, incidents, supply chain, access, encryption, continuity, network, awareness, reporting, assurance). Each has **max_points** (default 10) for scoring.
- **AssessmentResponse**: one row per (supplier, question) with **answer** `yes` / `partial` / `no`. **Risk score** = sum of weighted gap points / max possible × 100 (capped at 100). `yes` = 0 points, `partial` = half of `max_points`, `no` = `max_points`.
- **Document**: file metadata + path on disk; text is extracted (PDF via `pypdf`), chunked, embedded, and indexed for RAG.

## AI retrieval pipeline

1. **Structured data**: LangChain **tool-calling agent** (`gpt-4o-mini`) with tools that run **sync SQLAlchemy** queries: list/filter suppliers, load one supplier, load full assessment with question text (for citations).
2. **Documents**: On upload, text → **RecursiveCharacterTextSplitter** → **OpenAI `text-embedding-3-small`** → **FAISS** index persisted under `UPLOAD_DIR/faiss_index`. Search tool runs similarity search and returns chunk text + **document name** + **chunk index** for citations.
3. **System prompt**: frames the model as a **NIS2 supplier risk analyst**, requires citing assessment questions or document chunks when used.

I chose FAISS over Chroma for this repo to avoid extra containers and heavy optional ONNX defaults in some `chromadb` installs.

## What I’d improve/add with more time

- SSE streaming for chat assistant, login option, incremental vector deletes without full FAISS rebuild, better risk score calculation system, tests, audit logs.

## AI usage

I used cursor as the main AI development tool for this project, as I don't have access to the paid version of claude. It did a great job at setting the structure of the project and implementing the core functionalities, but it struggled with 

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/suppliers` | List / create suppliers |
| GET/PUT/DELETE | `/api/suppliers/{id}` | CRUD one supplier |
| GET | `/api/suppliers/{id}/questions` | Questionnaire template |
| GET/POST | `/api/suppliers/{id}/assessment` | Read / submit responses |
| GET/POST | `/api/suppliers/{id}/documents` | List / upload file |
| DELETE | `/api/suppliers/{id}/documents/{doc_id}` | Remove file + rebuild index |
| GET | `/api/risk-summary` | Suppliers sorted by risk (desc) |
| POST | `/api/chat` | `{ "message", "supplier_id?" }` |

