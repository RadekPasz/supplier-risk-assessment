import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AnswerChoiceSchema(str, Enum):
    yes = "yes"
    partial = "partial"
    no = "no"


class QuestionRead(BaseModel):
    id: uuid.UUID
    text: str
    category: str
    sort_order: int
    max_points: int

    model_config = {"from_attributes": True}


class ResponseItem(BaseModel):
    question_id: uuid.UUID
    answer: AnswerChoiceSchema


class AssessmentSubmit(BaseModel):
    responses: list[ResponseItem] = Field(..., min_length=1)


class ResponseRead(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    answer: AnswerChoiceSchema
    question: QuestionRead
    updated_at: datetime

    model_config = {"from_attributes": True}
