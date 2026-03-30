from typing import Any

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database_sync import get_sync_session
from app.models.assessment import AssessmentQuestion, AssessmentResponse
from app.models.supplier import Supplier
from app.services.rag import search_document_chunks

SYSTEM_PROMPT = """You are a NIS2 supplier risk analyst for a compliance platform. Your role is to help users \
understand supplier cybersecurity posture, assessment gaps, and document evidence.

Rules:
- Ground answers in tool outputs. If tools return no data, say so clearly.
- Always cite sources: name the assessment question text or document filename and chunk when using tool results.
- Risk scores are 0–100 where higher means greater risk (more gaps).
- When recommending mitigations, reference NIS2 supply-chain due diligence context (e.g. Article 21) when relevant.
- Be concise and actionable."""


@tool
def list_suppliers(
    min_risk: float | None = None,
    max_risk: float | None = None,
    tier: str | None = None,
    name_contains: str | None = None,
) -> str:
    """List suppliers with optional filters: min_risk, max_risk (0-100), tier (critical|high|medium|low), name_contains."""
    with get_sync_session() as s:
        q = select(Supplier).order_by(Supplier.risk_score.desc())
        rows = s.execute(q).scalars().all()
        out: list[Supplier] = []
        for sup in rows:
            if min_risk is not None and sup.risk_score < min_risk:
                continue
            if max_risk is not None and sup.risk_score > max_risk:
                continue
            if tier and sup.tier.value != tier:
                continue
            if name_contains and name_contains.lower() not in sup.name.lower():
                continue
            out.append(sup)
        if not out:
            return "No suppliers matched the filters."
        lines = []
        for sup in out:
            lines.append(
                f"- id={sup.id} name={sup.name!r} tier={sup.tier.value} risk_score={sup.risk_score} status={sup.status.value}"
            )
        return "\n".join(lines)


@tool
def get_supplier_detail(supplier_id: str) -> str:
    """Get full supplier record by UUID."""
    from uuid import UUID

    try:
        sid = UUID(supplier_id)
    except ValueError:
        return f"Invalid supplier id: {supplier_id}"
    with get_sync_session() as s:
        sup = s.get(Supplier, sid)
        if not sup:
            return f"No supplier with id {supplier_id}."
        return (
            f"name={sup.name!r}\n"
            f"description={sup.description}\n"
            f"website={sup.website}\n"
            f"tier={sup.tier.value}\n"
            f"risk_score={sup.risk_score}\n"
            f"status={sup.status.value}\n"
            f"id={sup.id}"
        )


@tool
def get_assessment_for_supplier(supplier_id: str) -> str:
    """Get all assessment question texts and answers for a supplier. Use for citations."""
    from uuid import UUID

    try:
        sid = UUID(supplier_id)
    except ValueError:
        return f"Invalid supplier id: {supplier_id}"
    with get_sync_session() as s:
        q = (
            select(AssessmentResponse)
            .where(AssessmentResponse.supplier_id == sid)
            .options(selectinload(AssessmentResponse.question))
        )
        rows = s.execute(q).scalars().all()
        if not rows:
            return "No assessment responses for this supplier."
        parts: list[str] = []
        for r in sorted(rows, key=lambda x: (x.question.sort_order, x.question.text)):
            qtext = r.question.text
            parts.append(
                f"[Question: {qtext}] category={r.question.category} answer={r.answer.value} (source: assessment question id={r.question_id})"
            )
        return "\n".join(parts)


@tool
def search_uploaded_documents(query: str, supplier_id: str | None = None) -> str:
    """Semantic search over uploaded supplier documents. Pass supplier_id to scope to one vendor."""
    from uuid import UUID

    uid = None
    if supplier_id and str(supplier_id).strip():
        try:
            uid = UUID(str(supplier_id).strip())
        except ValueError:
            return f"Invalid supplier_id for document search: {supplier_id!r}"
    try:
        docs = search_document_chunks(query, supplier_id=uid, k=6)
    except Exception as e:
        return f"Document search failed (embeddings/index): {e}"
    if not docs:
        return "No relevant document chunks found."
    parts: list[str] = []
    for d in docs:
        meta = d.metadata or {}
        parts.append(
            f"---\nDocument: {meta.get('document_name', 'unknown')} (chunk {meta.get('chunk_index', '?')})\n{d.page_content[:2000]}"
        )
    return "\n".join(parts)


def build_executor() -> AgentExecutor:
    tools = [list_suppliers, get_supplier_detail, get_assessment_for_supplier, search_uploaded_documents]
    llm = ChatOpenAI(model=settings.chat_model, temperature=0.2, api_key=settings.openai_api_key or None)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=8)


_executor: AgentExecutor | None = None


def get_executor() -> AgentExecutor:
    global _executor
    if _executor is None:
        _executor = build_executor()
    return _executor


def run_chat(input_text: str, extra_context: str | None = None) -> str:
    ex = get_executor()
    text = input_text
    if extra_context:
        text = f"Context (optional supplier focus): {extra_context}\n\nUser question: {input_text}"
    result: dict[str, Any] = ex.invoke({"input": text})
    return str(result.get("output", ""))
