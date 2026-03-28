"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-03-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    suppliertier = postgresql.ENUM(
        "critical", "high", "medium", "low", name="suppliertier", create_type=False
    )
    supplierstatus = postgresql.ENUM(
        "active", "pending", "archived", name="supplierstatus", create_type=False
    )
    answerchoice = postgresql.ENUM("yes", "partial", "no", name="answerchoice", create_type=False)

    suppliertier.create(bind, checkfirst=True)
    supplierstatus.create(bind, checkfirst=True)
    answerchoice.create(bind, checkfirst=True)

    op.create_table(
        "suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("tier", suppliertier, nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("status", supplierstatus, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_suppliers_name"), "suppliers", ["name"], unique=False)

    op.create_table(
        "assessment_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("max_points", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "assessment_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer", answerchoice, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["question_id"], ["assessment_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplier_id", "question_id", name="uq_supplier_question"),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("stored_path", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("assessment_responses")
    op.drop_table("assessment_questions")
    op.drop_index(op.f("ix_suppliers_name"), table_name="suppliers")
    op.drop_table("suppliers")
    op.execute("DROP TYPE IF EXISTS answerchoice")
    op.execute("DROP TYPE IF EXISTS supplierstatus")
    op.execute("DROP TYPE IF EXISTS suppliertier")
