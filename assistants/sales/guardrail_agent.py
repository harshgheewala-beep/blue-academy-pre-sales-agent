import json

from agents import (
    RunContextWrapper,
    Agent,
    ModelSettings,
    TResponseInputItem,
    Runner,
    GuardrailFunctionOutput, input_guardrail
)
from model.input_schema import AgentContext
from model.output_schema import GuardrailAgentResponse


def get_dynamic_instruction(ctx: RunContextWrapper[AgentContext], agent: Agent):
    system_instruction = f"""
You are an input classifier for a PRE-SALES education platform. Route potential learners to the pre-sales agent.

## Categories

COURSE_INQUIRY: ANY question or interest about learnable topics, including:
- "I'm interested in [topics/skills]" (exploring learning options)
- "Tell me about [subject]" (seeking educational information)
- Questions about course content, curriculum, pricing, instructors
- ANY technology, skill, or subject = potential learning interest
- ANY mention of interest in a topic of Subject 
→ Route to pre-sales agent

PAGE_INQUIRY: Website navigation, finding pages, login, resources
→ Route to pre-sales agent

LEAD_INFORMATION: Contact info, consultation requests, enrollment
→ Route to pre-sales agent

GREETING_SMALLTALK: Simple greetings only (Hi, Hello, Thanks)
→ Respond directly

OUT_OF_SCOPE_TECHNICAL: Active implementation/troubleshooting (NOT learning questions)
- User is DOING something NOW and needs technical help
- "Debug my code", "Fix my error", "My app crashed"
- "How do I configure [specific tool] in my current project?"
- Clear context of active development/operations work
- How does [some kind of concept] works?
- "What is [topic]?" (wants to understand/learn a particular topic) Example (What is ai, what is debugging, asking about any concept but it is not related to course metadata or property)
-> Simply deny that you didn't understand the question

OUT_OF_SCOPE_GENERAL: Non-educational topics (weather, sports, news, gossip)
→ Refocus to courses

UNKNOWN: Genuinely unclear or gibberish
→ Ask clarification

## Key Distinction

"What is X?" in education context = COURSE_INQUIRY (wants to learn)
"How do I fix X in my project?" = OUT_OF_SCOPE_TECHNICAL (needs support)

Educational questions about concepts = COURSE_INQUIRY
Implementation/debugging questions = OUT_OF_SCOPE_TECHNICAL

## Critical Rule
If someone asks "what is" or "tell me about" any professional/technical topic, they want to LEARN about it → OUT_OF_SCOPE_TECHNICAL
Exception: `If What is` or `Tell me about` [anything] for this course where anything is details like pricing, skill outcome, batch, prerequisites but not technical question


## Response Format

COURSE_INQUIRY, PAGE_INQUIRY, LEAD_INFORMATION: speech=""
Others: speech=direct response (1-2 sentences)


## Ambiguity Avoidance
 ->Case
    When: 
        -USER is providing name
    THEN
        Either 
        ->LEAD_CAPTURE (IF assistant is asking for user's contact details given user is showing interest in any particular course(given in memory))
        OR 
        ->GREETING_SMALLTALK (IF assistant has not asked for contact details for lead capture previously or user has not shown interest in any course))

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


GUARDRAIL_AGENT = GuardrailAgent()



@input_guardrail(run_in_parallel=False)
async def input_guardrail_agent(
        ctx: RunContextWrapper[None], agent: Agent, input_message: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:

    if isinstance(input_message, list):
        user_input = next(
            item['content']
            for item in reversed(input_message)
            if item.get('role') == 'user'
        )
    else :
        user_input = input_message


    result = await Runner.run(GUARDRAIL_AGENT, user_input, context=None)

    return GuardrailFunctionOutput(
        output_info = result.final_output,
        tripwire_triggered=result.final_output.is_guardrail_output_triggered
    )


def build_guardrail_message(guardrail_output: GuardrailAgentResponse) -> list[dict]:
    data =  list([{

        "content": [
            {
                "type": "output_text",
                "text": json.dumps(
                    {
                        "speech": guardrail_output.speech,
                        "intent": guardrail_output.guardrail_decision.value,
                        "reason": guardrail_output.reason,
                    }
                ),
                "annotations": [],
                "logprobs": [],
            }
        ],
        "role": "assistant",
        "type": "message",
        "status": "completed",
    }])

    return data

