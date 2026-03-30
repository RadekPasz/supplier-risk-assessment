import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.assessment import AnswerChoice, AssessmentQuestion, AssessmentResponse
from app.models.supplier import Supplier
from app.schemas.assessment import AssessmentSubmit, QuestionRead, ResponseRead
from app.services.scoring import recalculate_supplier_risk

router = APIRouter(prefix="/api/suppliers", tags=["assessment"])


@router.get("/{supplier_id}/questions", response_model=list[QuestionRead])
async def list_questions(
    supplier_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> list[QuestionRead]:
    s = await session.get(Supplier, supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    r = await session.execute(select(AssessmentQuestion).order_by(AssessmentQuestion.sort_order))
    return [QuestionRead.model_validate(q) for q in r.scalars().all()]


@router.get("/{supplier_id}/assessment", response_model=list[ResponseRead])
async def get_assessment(
    supplier_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> list[ResponseRead]:
    s = await session.get(Supplier, supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    q = (
        select(AssessmentResponse)
        .where(AssessmentResponse.supplier_id == supplier_id)
        .options(selectinload(AssessmentResponse.question))
    )
    r = await session.execute(q)
    rows = r.scalars().all()
    return [ResponseRead.model_validate(x) for x in rows]


@router.post("/{supplier_id}/assessment", response_model=list[ResponseRead])
async def submit_assessment(
    supplier_id: uuid.UUID, body: AssessmentSubmit, session: AsyncSession = Depends(get_session)
) -> list[ResponseRead]:
    s = await session.get(Supplier, supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")

    q_ids = {item.question_id for item in body.responses}
    r = await session.execute(select(AssessmentQuestion).where(AssessmentQuestion.id.in_(q_ids)))
    found = {q.id for q in r.scalars().all()}
    if q_ids != found:
        raise HTTPException(status_code=400, detail="Unknown question id in submission")

    await session.execute(delete(AssessmentResponse).where(AssessmentResponse.supplier_id == supplier_id))

    for item in body.responses:
        session.add(
            AssessmentResponse(
                supplier_id=supplier_id,
                question_id=item.question_id,
                answer=AnswerChoice(item.answer.value),
            )
        )
    await session.commit()

    s = await session.get(Supplier, supplier_id)
    assert s
    await recalculate_supplier_risk(session, s)
    await session.commit()
    await session.refresh(s)

    q = (
        select(AssessmentResponse)
        .where(AssessmentResponse.supplier_id == supplier_id)
        .options(selectinload(AssessmentResponse.question))
    )
    r2 = await session.execute(q)
    rows = r2.scalars().all()
    return [ResponseRead.model_validate(x) for x in rows]
