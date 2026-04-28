import time
import logging
from groq import Groq

from config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE

logger = logging.getLogger(__name__)

_client = Groq(api_key=GROQ_API_KEY)


def call_llm(
    messages: list[dict],
    tools: list[dict] | None = None,
    tool_choice: str = "auto",
    max_retries: int = 3,
):
    """
    Call the LLM with automatic retry + exponential back-off.
    Returns the raw ChatCompletionMessage object so callers can inspect
    both `.content` and `.tool_calls`.
    """
    delay = 1.0
    last_exc = None
    for attempt in range(max_retries):
        try:
            kwargs: dict = {
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": TEMPERATURE,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice

            response = _client.chat.completions.create(**kwargs)
            return response.choices[0].message

        except Exception as exc:
            last_exc = exc
            logger.warning("LLM attempt %d/%d failed: %s", attempt + 1, max_retries, exc)
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2

    raise RuntimeError(f"LLM call failed after {max_retries} attempts") from last_exc
