from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class CourseRef(BaseModel):
    id: str = Field(title="Course ID", description="The unique database UUID for the course")
    title: str = Field(title="Course Title", description="The title of the course")
    slug: str = Field(title="Course Slug", description="The slug of the course")


class LessonRef(BaseModel):
    id: str
    name: str



class AgentAction(BaseModel):
    type: Literal["details", "interest"] = Field(title="Action Type", description="The type of UI component to render.")
    label: str = Field(description = "The CTA text to show on the button")
    course: CourseRef


class PreSalesAgentResponseSchema(BaseModel):
    speech: str = Field(title="Agent Response", description="The natural language response to be spoken or read by the user")
    intent: str = Field(title="Intent", description="The classified user intent")
    confidence: Literal["low", "medium", "high"] = Field(title="Intent Certainty Score", description="The model's certainty in its intent classification.")
    actions: Optional[List[AgentAction]] = Field(
        default=[],
        description="A list of suggested next steps or interactive buttons for the user.")


class PostSalesAgentResponseSchema(BaseModel):
    speech: str
    intent: str
    confidence: Literal["low", "medium", "high"]
    lesson: Optional[List[LessonRef]] = []
    actions: Optional[List[AgentAction]] = []



OUTPUT_SCHEMA ={
  "title": "PreSalesAgentResponseSchema",
  "type": "object",
  "properties": {
    "speech": {
      "title": "Speech",
      "type": "string"
    },
    "intent": {
      "title": "Intent",
      "type": "string"
    },
    "confidence": {
      "enum": ["low", "medium", "high"],
      "title": "Confidence",
      "type": "string"
    },
    "actions": {
      "default": [],
      "items": {
        "title": "AgentAction",
        "type": "object",
        "properties": {
          "type": {
            "enum": ["details", "interest"],
            "title": "Type",
            "type": "string"
          },
          "label": {
            "title": "Label",
            "type": "string"
          },
          "course": {
            "title": "CourseRef",
            "type": "object",
            "properties": {
              "id": { "title": "Id", "type": "string" },
              "title": { "title": "Title", "type": "string" },
              "slug": { "title": "Slug", "type": "string" }
            },
            "required": ["id", "title", "slug"]
          }
        },
        "required": ["type", "label", "course"]
      },
      "title": "Actions",
      "type": "array"
    }
  },
  "required": ["speech", "intent", "confidence"]
}