# Supplier Risk Assessment (NIS2) — Intern Assignment

Full-stack prototype: **PostgreSQL** + **FastAPI** (async SQLAlchemy) + **React (TypeScript)** + **LangChain** with **OpenAI** embeddings/chat and a **FAISS** vector store for document RAG. The AI assistant uses **tool calling** to read suppliers/assessments from the database and **semantic search** over uploaded document chunks.

## Quick start (Docker)

1. Copy `.env.example` to `.env` in this directory and set `OPENAI_API_KEY`.
2. From this directory:

```bash
docker compose up --build
```

3. Open **http://localhost:5174** (frontend). The API is proxied to the backend on the same origin (`/api/...`).

Sanity checks from the assignment:

1. Full stack starts without errors.
2. Create a supplier in the UI.
3. Fill the assessment and save — risk score updates.
4. Upload a PDF or `.txt` for that supplier.
5. Use the chat panel — ask about assessment gaps.
6. Ask about wording in the uploaded document (RAG over chunks).

Local dev without Docker: run PostgreSQL locally, `CREATE DATABASE supplier_risk`, set `DATABASE_URL`, install backend `requirements.txt`, run `alembic upgrade head`, `uvicorn app.main:app --reload` from `backend/`; run `npm run dev` in `frontend/` (Vite proxies `/api` to port 8000).

## Data model (decisions)

- **Supplier**: identity (`name`, `description`, `website`), **tier** (`critical` → `low`), **risk_score** (0–100, higher = more gaps), **status** (`active` / `pending` / `archived`). Tier is organizational criticality; risk_score is derived from the questionnaire.
- **AssessmentQuestion**: canonical NIS2-aligned prompts (10 topics: risk management, incidents, supply chain, access, encryption, continuity, network, awareness, reporting, assurance). Each has **max_points** (default 10) for scoring.
- **AssessmentResponse**: one row per (supplier, question) with **answer** `yes` / `partial` / `no`. **Risk score** = sum of weighted gap points / max possible × 100 (capped at 100). `yes` = 0 points, `partial` = half of `max_points`, `no` = full `max_points`.
- **Document**: file metadata + path on disk; text is extracted (PDF via `pypdf`), chunked, embedded, and indexed for RAG.

## AI retrieval pipeline

1. **Structured data**: LangChain **tool-calling agent** (`gpt-4o-mini`) with tools that run **sync SQLAlchemy** queries: list/filter suppliers, load one supplier, load full assessment with question text (for citations).
2. **Documents**: On upload, text → **RecursiveCharacterTextSplitter** → **OpenAI `text-embedding-3-small`** → **FAISS** index persisted under `UPLOAD_DIR/faiss_index`. Search tool runs similarity search and returns chunk text + **document name** + **chunk index** for citations.
3. **System prompt**: frames the model as a **NIS2 supplier risk analyst**, requires citing assessment questions or document chunks when used.

FAISS was chosen over Chroma for this repo to avoid extra containers and heavy optional ONNX defaults in some `chromadb` installs; the same RAG idea applies (chunk → embed → retrieve → augment).

## What we’d improve with more time

- SSE streaming for chat; stricter auth/tenancy; pgvector or managed vector DB; incremental vector deletes without full FAISS rebuild; richer assessment weighting and evidence attachments; pytest + CI; OAuth and audit logs.

## Claude / AI-assisted development (placeholder)

Document your own experience here: what you asked the agent to scaffold, where you intervened (e.g. data model, Docker, RAG store choice), and what you learned about agentic coding workflows.

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

## License

Prototype for evaluation — not production-hardened.
