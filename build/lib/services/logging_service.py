import time
import logging

logger = logging.getLogger("agent_tools")

def observe_tool(tool_name: str):
    def wrapper(fn):
        async def inner(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await fn(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                logger.info(
                    "tool_success",
                    extra={
                        "tool": tool_name,
                        "duration_ms": round(duration, 2),
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                logger.error(
                    "tool_failure",
                    extra={
                        "tool": tool_name,
                        "duration_ms": round(duration, 2),
                        "error": str(e)
                    }
                )
                raise
        return inner
    return wrapper
