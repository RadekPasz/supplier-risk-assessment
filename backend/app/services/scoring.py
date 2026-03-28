from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import AnswerChoice, AssessmentQuestion, AssessmentResponse
from app.models.supplier import Supplier


def points_for_answer(answer: AnswerChoice, max_points: int) -> float:
    if answer == AnswerChoice.yes:
        return 0.0
    if answer == AnswerChoice.partial:
        return max_points / 2.0
    return float(max_points)


async def recalculate_supplier_risk(session: AsyncSession, supplier: Supplier) -> float:
    q = await session.execute(
        select(AssessmentQuestion).order_by(AssessmentQuestion.sort_order)
    )
    questions = q.scalars().all()
    if not questions:
        supplier.risk_score = 0.0
        return 0.0

    r = await session.execute(
        select(AssessmentResponse)
        .where(AssessmentResponse.supplier_id == supplier.id)
        .options(selectinload(AssessmentResponse.question))
    )
    responses = {resp.question_id: resp for resp in r.scalars().all()}

    total_points = 0.0
    max_possible = sum(float(qs.max_points) for qs in questions)

    for qs in questions:
        resp = responses.get(qs.id)
        if resp:
            total_points += points_for_answer(resp.answer, qs.max_points)

    if max_possible <= 0:
        supplier.risk_score = 0.0
        return 0.0

    supplier.risk_score = round(min(100.0, (total_points / max_possible) * 100.0), 2)
    return supplier.risk_score
