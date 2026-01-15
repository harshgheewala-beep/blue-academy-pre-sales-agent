from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, AnyStr
from datetime import datetime
from typing_extensions import Any
import re

from model.output_schema import CourseRef


class Course(BaseModel):
    title: str
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    price: float | int
    duration_weeks: int
    prerequisites: List[str] = Field(default_factory=list)
    skills: List[str] = []
    category: str
    mode: Literal["online", "offline", "hybrid"] = "online",
    # description: str | None = "",
    # curriculum: str | None = "",
    # faq: str | None = "",


    # created_at: datetime = datetime.now().isoformat()
    # updated_at: datetime = datetime.now().isoformat()


class CourseChunk(BaseModel):
    course_id: str | UUID
    chunk_index: int
    content: str
    embedding: list[float]



class CourseDetails(BaseModel):
    course_id: str | UUID
    description: str
    curriculum: str
    faq: str
    outcomes: str
    additional_info: str


class UpdateCourseMetaData(BaseModel):
    level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    price: Optional[int] = None
    duration_weeks: Optional[int] = None
    prerequisites: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    category: Optional[str] = None
    mode: Optional[Literal["online", "offline", "hybrid"]] = None


class UpdateCourseDetails(BaseModel):
    description: Optional[str] = None
    curriculum: Optional[str] = None
    faq: Optional[str] = None
    outcomes: Optional[str] = None
    additional_info: Optional[str] = None


class UserDetails(BaseModel):
    name: str
    email: str
    contact_number: str
    
    @field_validator("contact_number")
    def validate_contact_number(cls, v):
        if not (v[1::].isdigit() or v.startswith('+')) or len(v) < 7 or len(v) > 15 or not v.startswith(('+')):
            raise ValueError("Invalid contact number")
        print("Validated contact number:", v)
        return v


class UserRegistration(UserDetails):
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str

class ModuleDetails(BaseModel):
    name: str


class LessonDetails(BaseModel):
    name: str
    lesson_content: str = Field(...)


class VideoDetails(BaseModel):
    lesson_id: str | UUID
    video_url: Optional[str] = None
    transcription_mode: Literal["No", "Manual", "Auto"] = "No"


class VideoTranscription(BaseModel):
    video_id : str | UUID
    transcription: str


class LessonDetailsChunk(BaseModel):
    lesson_id: str | UUID


class PageContext(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None


class UserContext(BaseModel):
    action: Optional[str] = None
    course: Optional[CourseRef] = None


class AgentContext(BaseModel):
    page_context: Optional[PageContext] = None
    user_context: Optional[UserContext] = None

#API Schema
class ChatPayload(BaseModel):
    session_id: str
    message: str
    context: Optional[AgentContext] = None


class UserContactDetails(BaseModel):
    name: str
    email: str
    contact_number: str


#Tool Schema
class LeadDetails(BaseModel):
    name: str = Field(..., description="The full name of the user. Do not guess.")
    email: str = Field(..., description="A valid email address provided by the user.")
    contact: str = Field(..., description="The phone number starting with +.")
    slug: str = Field(..., description="The slug of the course the user is interested in.")

    # @field_validator('email')
    # def validate_email(cls, v):
    #     if not re.match(
    #             r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
    #         raise "Invalid email"
    #     return v
    #
    # @field_validator('contact')
    # def validate_contact_number(cls, v):
    #     if not v.startswith('+') or len(v) < 7:
    #         return 'Invalid contact number'
    #     if not v[1:].isdigit():
    #         return 'Invalid contact number'
    #
    #     if re.match(r'^\+?\(?\d{1,3}\)?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', v):
    #         return v
    #
    #     return v