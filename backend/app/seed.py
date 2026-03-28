import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import AssessmentQuestion


def _questions() -> list[dict]:
    rows: list[tuple[str, str, int]] = [
        (
            "risk_management",
            "Do you maintain a documented cybersecurity risk management process covering assets, threats, and treatment measures?",
            0,
        ),
        (
            "incident_handling",
            "Do you have a tested incident response plan with defined roles, escalation paths, and communication procedures?",
            1,
        ),
        (
            "supply_chain",
            "Do you assess and manage security risks posed by your own suppliers and subprocessors (supply chain due diligence)?",
            2,
        ),
        (
            "access_control",
            "Do you enforce multi-factor authentication for privileged access and periodically review access rights?",
            3,
        ),
        (
            "encryption",
            "Do you encrypt sensitive data at rest and in transit using industry-accepted mechanisms?",
            4,
        ),
        (
            "business_continuity",
            "Do you maintain backups and test disaster recovery / business continuity arrangements?",
            5,
        ),
        (
            "network_security",
            "Do you segment networks, monitor for intrusions, and maintain secure configurations?",
            6,
        ),
        (
            "human_resources",
            "Do you provide regular cybersecurity awareness training and manage insider risk for privileged users?",
            7,
        ),
        (
            "incident_reporting",
            "Do you notify customers and regulators of significant incidents within contractual and legal timeframes?",
            8,
        ),
        (
            "compliance_evidence",
            "Can you provide independent assurance (e.g., ISO 27001 certification or equivalent) for your security controls?",
            9,
        ),
    ]
    out: list[dict] = []
    for cat, text, order in rows:
        out.append(
            {
                "id": uuid.uuid4(),
                "text": text,
                "category": cat,
                "sort_order": order,
                "max_points": 10,
            }
        )
    return out


async def seed_assessment_questions(session: AsyncSession) -> None:
    r = await session.execute(select(AssessmentQuestion).limit(1))
    if r.scalars().first() is not None:
        return
    for row in _questions():
        session.add(AssessmentQuestion(**row))
    await session.commit()
