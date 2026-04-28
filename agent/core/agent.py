import json
import logging
from typing import Generator

from core.llm import call_llm
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from tools.registry import get_schemas, get_tool
from config import MAX_STEPS

logger = logging.getLogger(__name__)


class Agent:
    """
    ReAct-style agent that uses Groq's structured tool-calling API
    instead of fragile string parsing.

    Flow per step:
      1. Build messages (system + long-term recall + short-term + user query)
      2. Call LLM with tool schemas
      3a. If tool_calls → execute tools → append observations → loop
      3b. If content only → yield final_answer → stop
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tool_names: list[str] | None = None,
        short_term: ShortTermMemory | None = None,
        long_term: LongTermMemory | None = None,
        max_steps: int | None = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tool_names = tool_names or []
        self.short_term = short_term or ShortTermMemory()
        self.long_term = long_term
        self.max_steps = max_steps or MAX_STEPS

    # ── Public API ────────────────────────────────────────────────────────────

    def run_stream(self, query: str, plan: str = "") -> Generator[dict, None, None]:
        """Yield structured event dicts as the agent reasons and acts."""
        # 1. Pull relevant long-term memories
        memories: list[str] = []
        if self.long_term and self.long_term.count() > 0:
            memories = self.long_term.retrieve(query, top_k=3)

        # 2. Build system message
        system_content = self.system_prompt
        if plan:
            system_content += f"\n\nExecution plan to follow:\n{plan}"
        if memories:
            system_content += "\n\nRelevant past context:\n" + "\n---\n".join(memories)

        # 3. Assemble initial messages
        messages: list[dict] = [{"role": "system", "content": system_content}]
        messages.extend(self.short_term.get_messages())
        messages.append({"role": "user", "content": query})

        tool_schemas = get_schemas(self.tool_names) if self.tool_names else None

        # 4. ReAct loop
        for step in range(1, self.max_steps + 1):
            try:
                response_msg = call_llm(messages, tools=tool_schemas)
            except Exception as exc:
                yield {"type": "error", "step": step, "content": str(exc), "agent": self.name}
                return

            thought = (response_msg.content or "").strip()

            # Yield thought if the model produced reasoning text
            if thought:
                yield {
                    "type": "thought",
                    "step": step,
                    "content": thought,
                    "agent": self.name,
                }

            if response_msg.tool_calls:
                # ── Append assistant message with tool calls ──────────────
                messages.append(
                    {
                        "role": "assistant",
                        "content": response_msg.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in response_msg.tool_calls
                        ],
                    }
                )

                # ── Execute each tool call ────────────────────────────────
                for tc in response_msg.tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_args: dict = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    # Display-friendly single-string input
                    input_display = (
                        next(iter(tool_args.values()), "")
                        if len(tool_args) == 1
                        else json.dumps(tool_args)
                    )

                    yield {
                        "type": "action",
                        "step": step,
                        "tool": tool_name,
                        "input": str(input_display),
                        "agent": self.name,
                    }

                    try:
                        tool_fn = get_tool(tool_name)
                        obs = str(tool_fn(**tool_args))
                    except KeyError:
                        obs = f"Unknown tool: {tool_name}"
                    except Exception as exc:
                        obs = f"Tool error ({tool_name}): {exc}"
                        logger.error("Tool %s failed: %s", tool_name, exc)

                    yield {
                        "type": "observation",
                        "step": step,
                        "tool": tool_name,
                        "content": obs,
                        "agent": self.name,
                    }

                    messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": obs}
                    )

            else:
                # ── No tool call → final answer ───────────────────────────
                final = thought or "No answer generated."
                self.short_term.add("user", query)
                self.short_term.add("assistant", final)
                yield {"type": "final_answer", "content": final, "agent": self.name}
                return

            # ── Loop-detection: stop if last two steps both had no tool call ─
            # (handled implicitly — if tool_calls is empty we already returned)

        yield {"type": "max_steps_reached", "agent": self.name}
