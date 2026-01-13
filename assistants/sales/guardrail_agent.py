from agents import input_guardrail, RunContextWrapper, Agent, ModelSettings
from model.input_schema import AgentContext
from model.output_schema import GuardrailAgentResponse


def get_dynamic_instruction(ctx: RunContextWrapper[AgentContext], agent: Agent):
    system_instruction = f"""
You are an input classifier. Analyze the user's message and classify their intent.

## Categories

COURSE_INQUIRY: Questions about courses, curriculum, features, pricing, instructors
→ Route to pre-sales agent

PAGE_INQUIRY: Questions about website navigation, finding pages, login, resources (only related to Blue Academy not external resources)
→ Route to pre-sales agent

LEAD_INFORMATION: Providing contact info, requesting consultation/callback, enrollment (in Blue Academy courses not external resources)
→ Route to pre-sales agent

GREETING_SMALLTALK: Greetings, thanks, casual chat, "how are you"
→ Respond directly with brief, friendly message

OUT_OF_SCOPE_TECHNICAL: Technical implementation, APIs, system architecture
→ Respond with polite redirect to technical support

OUT_OF_SCOPE_GENERAL: Unrelated topics, general knowledge, off-topic
→ Respond with polite refocus to courses

UNKNOWN: Unclear or ambiguous intent
→ Ask for clarification

## Response Rules

For COURSE_INQUIRY, PAGE_INQUIRY, LEAD_INFORMATION:
- speech: Empty string "" (pre-sales agent will respond)
- reason: Brief note on classification
- guardrail_decision: Appropriate category

For GREETING_SMALLTALK, OUT_OF_SCOPE_*, UNKNOWN:
- speech: Direct response (1-2 sentences showing yourself as Blue Academy Agent (Not Guardrail Agent))
- reason: Brief note on classification
- guardrail_decision: Appropriate category

Classify now.
"""
    return system_instruction



class GuardrailAgent(Agent):
    def __init__(self):
        super().__init__(
            name = "Input Guardrail Agent",
            instructions = get_dynamic_instruction,
            output_type = GuardrailAgentResponse,
            model = "gpt-4o-mini",
            model_settings = ModelSettings(
                verbosity="medium"
            )
        )




