from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from enum import Enum


class GuardrailDecision(str, Enum):
    course_inquiry = "COURSE_INQUIRY"
    page_inquiry = "PAGE_INQUIRY"
    lead_information = "LEAD_INFORMATION"
    greeting_or_small_talk = "GREETING_SMALLTALK"
    out_of_scope_technical = "OUT_OF_SCOPE_TECHNICAL"
    out_of_scope_general = "OUT_OF_SCOPE_GENERAL"
    unknown = "UNKNOWN"


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


class PreSalesCallAgentResponseSchema(BaseModel):
    speech: str = Field(title="Speech", description="The natural language response to be spoken or read by the user")



class GuardrailAgentResponse(BaseModel):
    """Guardrail classification response"""
    guardrail_decision: GuardrailDecision = Field(
        description="Classification of user intent"
    )
    reason: str = Field(
        description="Brief reason for classification (1 sentence)",
        max_length=150
    )
    speech: str = Field(
        default="",
        description="Response text. Empty string if routing to pre-sales agent, otherwise 1-2 sentence direct response"
    )

    @property
    def should_route_to_presales(self) -> bool:
        """Check if request should be routed to pre-sales agent"""
        return self.guardrail_decision in [
            GuardrailDecision.course_inquiry,
            GuardrailDecision.page_inquiry,
            GuardrailDecision.lead_information
        ]


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