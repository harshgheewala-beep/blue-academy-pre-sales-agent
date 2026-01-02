from pydantic import BaseModel
from typing import Literal, Optional, List


class CourseRef(BaseModel):
    id: str
    title: str
    slug: str


class LessonRef(BaseModel):
    id: str
    name: str


class AgentAction(BaseModel):
    type: Literal["details", "alternatives", "interest"]
    label: str
    course: CourseRef
    # target_slug: Optional[str]


class PreSalesAgentResponseSchema(BaseModel):
    speech: str
    intent: str
    confidence: Literal["low", "medium", "high"]
    actions: Optional[List[AgentAction]] = []


class PostSalesAgentResponseSchema(BaseModel):
    speech: str
    intent: str
    confidence: Literal["low", "medium", "high"]
    lesson: Optional[List[LessonRef]] = []
    actions: Optional[List[AgentAction]] = []

