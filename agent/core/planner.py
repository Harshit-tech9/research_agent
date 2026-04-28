import logging
from core.llm import call_llm

logger = logging.getLogger(__name__)

_SYSTEM = """You are a planning agent.
Given a user query, break it into clear numbered steps that an AI agent should follow.
Each step should be a concrete, actionable task.
Return ONLY the numbered steps — no preamble, no commentary.
"""


def create_plan(query: str) -> str:
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Query: {query}"},
    ]
    try:
        msg = call_llm(messages)
        return (msg.content or "").strip()
    except Exception as exc:
        logger.error("Planner failed: %s", exc)
        return "1. Answer the user query directly."
