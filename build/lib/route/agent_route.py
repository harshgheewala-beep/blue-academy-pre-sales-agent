import inspect
import os
import logging
import uuid
from agents import Runner, SQLiteSession, RunConfig
from agents.extensions.memory import SQLAlchemySession
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from assistants.sales.general_agent import PreSalesAgent
from uuid import uuid4, uuid5
import time

from model.input_schema import ChatPayload
from model.output_schema import PreSalesAgentResponseSchema
from services.data_handler import clean_chat
from services.page_data_handler import extract_page_info_from_url
from services.redis_service import update_session_navigation, redis_client



logger = logging.getLogger("Agent Handler")


router = APIRouter(
    tags=["Agent"],
    prefix="/agent",
)



DEV_MODE = os.getenv("DEV_MODE", True)


SESSION_TTL = 30 * 60  # 30 minutes
SESSIONS = {}


def build_run_config(session_id: str) -> RunConfig:
    return RunConfig(
        workflow_name="Pre-sales chatbot",
        group_id=session_id,
        trace_metadata={
            "session_id": session_id,
            "agent": "pre_sales_chatbot",
            "source": "chat-widget",
        },
        trace_include_sensitive_data=True,
    )


def get_session(session_id=None):
    now = time.time()

    # cleanup expired sessions
    for sid in list(SESSIONS.keys()):
        if now - SESSIONS[sid]["last_used"] > SESSION_TTL:
            del SESSIONS[sid]
    if session_id and session_id in SESSIONS:
        SESSIONS[session_id]["last_used"] = now
        return session_id, SESSIONS[session_id]

    # create new
    session_id = str(uuid4())
    SESSIONS[session_id] = {
        "history": [],
        "last_used": now,
    }
    return session_id, SESSIONS[session_id]


async def get_custom_session(session_id: str)-> SQLAlchemySession | SQLiteSession:
    if DEV_MODE:
        return SQLiteSession(
            session_id=session_id,
            db_path="agents_history.db")
    return SQLAlchemySession.from_url(
        session_id=session_id,
        url=os.getenv("SQLALCHEMY_URL"),
        create_tables = True,
    )


async def make_message_id(session_id: str,message: str)-> str:
    normalized = message.lower().strip()
    name = f"{session_id}:{normalized}"

    return str(uuid5(
        namespace=uuid.NAMESPACE_DNS,
        name=name
    ))


async def close_session(session):
    if session is None:
        return

    close = getattr(session, "close", None)
    if callable(close):
        result = close()
        if inspect.isawaitable(result):
            await result


# def get_agent_config(agent_type: str, context = Optional[dict])->dict:
#     match agent_type:
#         case "pre_sales_agent":
#             print("Hit Pre sales_agents")
#             return {
#                 "assistants": PreSalesAgent(),
#                 "agent_output_schema": PreSalesAgentResponseSchema,
#             }
#         case "post_sales_agent":
#             print("Hit Post sales_agents")
#             return {
#                 "assistants": PostSalesAgent(),
#                 "agent_output_schema": PostSalesAgentResponseSchema,
#                 "context": context
#             }
#         case _:
#             return {
#             "assistants": PreSalesAgent(),
#             "agent_output_schema": PreSalesAgentResponseSchema,
#             }


@router.post("/chat",
             deprecated=True)
def chat(payload: dict):
    print(f"Payload: {payload}")
    agent_type = payload.get("agent_type","pre_sales_agent")
    print(f"agent_type: {agent_type}")

    # agent_config = get_agent_config(agent_type)
    # agent = agent_config["assistants"]
    # agent_output_schema = agent_config["agent_output_schema"]

    if agent_type == "post_sales_agent":
        context = {"current_course_id": payload.get("current_course_id",[])}
    else:
        context = {}

    message = payload.get("message", "")
    session_id = payload.get("session_id")
    session_id, session = get_session(session_id)

    session["history"].append({
        "role": "user",
        "content": message
    })

    llm_history = []

    for msg in session["history"]:
        if msg["role"] == "user":
            llm_history.append(msg)
        else:
            content = msg["content"]

            if isinstance(content, dict) and "speech" in content:
                llm_history.append({
                    "role": "assistant",
                    "content": content["speech"]
                })
            else:
                llm_history.append({
                    "role": "assistant",
                    "content": str(content)
                })


    response = Runner.run_sync(PreSalesAgent(), llm_history)
    print(response)

    raw_output = response.final_output

    if isinstance(raw_output, PreSalesAgentResponseSchema):
        reply = raw_output.model_dump()
    elif isinstance(raw_output, dict):
        reply = raw_output
    else:
        reply = {
            "speech": str(raw_output),
            "intent": "unknown",
            "actions": []
        }

    session["history"].append({
        "role": "assistant",
        "content": reply
    })

    print(session)
    return {
        "reply": reply,
        "session_id": session_id
    }



@router.post("/chat/v2",
             description="Prototype of assistants with page context understanding",
             deprecated=True)
def chat_v2(payload: dict):
    print(f"Payload: {payload}")
    # agent_type = payload.get("agent_type","pre_sales_agent")
    # print(f"agent_type: {agent_type}")
    #
    # agent_config = get_agent_config(agent_type)
    # assistants = agent_config["assistants"]
    # agent_output_schema = agent_config["agent_output_schema"]
    #
    # if agent_type == "post_sales_agent":
    #     context = {"current_course_id": payload.get("current_course_id",[])}
    # else:
    #     context = {}

    message = payload.get("message", "")
    session_id = payload.get("session_id")
    session_id, session = get_session(session_id)

    context_data = payload.get("context", {})

    session["history"].append({
        "role": "user",
        "content": message
    })

    llm_history = []

    for msg in session["history"]:
        if msg["role"] == "user":
            llm_history.append(msg)
        else:
            content = msg["content"]

            if isinstance(content, dict) and "speech" in content:
                llm_history.append({
                    "role": "assistant",
                    "content": content["speech"]
                })
            else:
                llm_history.append({
                    "role": "assistant",
                    "content": str(content)
                })


    response = Runner.run_sync(PreSalesAgent(), llm_history, context=context_data)
    print(response)

    raw_output = response.final_output

    if isinstance(raw_output, PreSalesAgentResponseSchema):
        reply = raw_output.model_dump()
    elif isinstance(raw_output, dict):
        reply = raw_output
    else:
        reply = {
            "speech": str(raw_output),
            "intent": "unknown",
            "actions": []
        }

    session["history"].append({
        "role": "assistant",
        "content": reply
    })

    print(session)
    print(f"LLM History: {llm_history}")
    return {
        "reply": reply,
        "session_id": session_id
    }


@router.get("/chat",
            description="Load chats",
            deprecated=True)
def get_chat(session_id: str | None = None):
    if not session_id or session_id not in SESSIONS:
        return {
            "session_id": None,
            "history": []
        }


    session = SESSIONS[session_id]

    return {
        "session_id": session_id,
        "history": session["history"]
    }



#Use this updated versions (Above are deprecated)

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):

    session = await get_custom_session(session_id)
    try:
        items = await session.get_items()
        formatted_history = clean_chat(items)
        return {"history": formatted_history}
    finally:
        await close_session(session)


@router.post("/chat/v2/with_history")
async def chat_v2_session(chat_payload: ChatPayload):
    payload = chat_payload.model_dump()
    session_id = payload.get("session_id")
    if not session_id:
        return JSONResponse(status_code=404,
                            content={"details": "Session ID not provided"})
    message = payload.get("message", "")
    context_data = payload.get("context", {})


    if context_data.get("page_context",{}):

        url = context_data.get("page_context",{}).get("url")
        page_info = await extract_page_info_from_url(page_url=url) if url else {}

        if page_info.get("page_type") == "particular_course_page":
            context_data["page_context"]["slug"] = page_info.get("slug")
            context_data["page_context"]["page_type"] = page_info.get("page_type")


        print(context_data)
    session = await get_custom_session(session_id)
    try:
        async with redis_client.lock(
                f"lock:session:{session_id}",
                timeout=15,  # auto-release safety
                blocking_timeout=15  # wait for other request
        ):
            # if url:
            #     await update_session_navigation(session_id, url, page_info.get("slug"))

            response = await Runner.run(
                PreSalesAgent(),
                message,
                session=session,
                context=context_data,
                run_config=build_run_config(session_id)
            )

            raw_output = response.final_output
            if isinstance(raw_output, PreSalesAgentResponseSchema):
                reply = raw_output.model_dump()
            elif isinstance(raw_output, dict):
                reply = raw_output
            else:
                reply = {
                    "speech": str(raw_output),
                    "intent": "unknown",
                    "actions": []
                }

            print(f"Reply : {reply}")


            return {
                "reply": reply,
                "session_id": session_id
            }
    except Exception:
        logger.exception(f"Agent Execution Failed")
        return {"error":"Internal Server Error"}