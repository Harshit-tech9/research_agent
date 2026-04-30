import json
import logging
from typing import Generator

from core.llm import call_llm
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from tools.registry import get_schemas, get_tool
from config import MAX_STEPS

logger = logging.getLogger(__name__)

# Special tool that tells the model how to exit the loop and deliver its answer.
# LLaMA 3.3 70B in tool-calling mode rarely returns a text-only response;
# giving it a structured exit route is the reliable fix.
_FINAL_ANSWER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "final_answer",
        "description": (
            "Call this tool to deliver your final answer to the user. "
            "Use it once you have gathered all the information you need "
            "and are ready to respond. Do NOT call any other tool after this."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "Your complete, well-formatted answer to the user's question.",
                }
            },
            "required": ["answer"],
        },
    },
}


class Agent:
    """
    ReAct-style agent using Groq's structured tool-calling API.

    Exit strategy (most → least preferred):
      1. Model calls final_answer tool        → clean exit, captured immediately
      2. Model returns text with no tool_calls → treated as final answer
      3. max_steps reached                    → force one synthesis call (tool_choice=none)
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

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _build_messages(self, query: str, plan: str, memories: list[str]) -> list[dict]:
        system_content = self.system_prompt
        if plan:
            system_content += f"\n\nExecution plan:\n{plan}"
        if memories:
            system_content += "\n\nRelevant past context:\n" + "\n---\n".join(memories)

        msgs: list[dict] = [{"role": "system", "content": system_content}]
        msgs.extend(self.short_term.get_messages())
        msgs.append({"role": "user", "content": query})
        return msgs

    def _force_final_answer(self, messages: list[dict]) -> str:
        """Call LLM with no tools to force a plain-text synthesis."""
        try:
            msg = call_llm(messages, tools=None)
            return (msg.content or "").strip() or "Unable to produce a final answer."
        except Exception as exc:
            return f"Error generating final answer: {exc}"

    # ── Public API ────────────────────────────────────────────────────────────

    def run_stream(self, query: str, plan: str = "") -> Generator[dict, None, None]:
        # 1. Retrieve relevant long-term memories
        memories: list[str] = []
        if self.long_term and self.long_term.count() > 0:
            memories = self.long_term.retrieve(query, top_k=3)

        messages = self._build_messages(query, plan, memories)

        # Always include final_answer as an option alongside real tools
        real_schemas = get_schemas(self.tool_names) if self.tool_names else []
        all_schemas = real_schemas + [_FINAL_ANSWER_SCHEMA]

        # 2. ReAct loop
        for step in range(1, self.max_steps + 1):
            try:
                response_msg = call_llm(messages, tools=all_schemas)
            except Exception as exc:
                yield {"type": "error", "step": step, "content": str(exc), "agent": self.name}
                return

            thought = (response_msg.content or "").strip()
            if thought:
                yield {"type": "thought", "step": step, "content": thought, "agent": self.name}

            # ── Case A: model returned text only → final answer ───────────
            if not response_msg.tool_calls:
                final = thought or "No answer generated."
                self.short_term.add("user", query)
                self.short_term.add("assistant", final)
                yield {"type": "final_answer", "content": final, "agent": self.name}
                return

            # ── Case B: model called tools ────────────────────────────────
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

            for tc in response_msg.tool_calls:
                tool_name = tc.function.name

                try:
                    tool_args: dict = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                # ── Special: final_answer tool ────────────────────────────
                if tool_name == "final_answer":
                    final = tool_args.get("answer", thought) or thought or "No answer generated."
                    self.short_term.add("user", query)
                    self.short_term.add("assistant", final)
                    # Still need a tool result in messages to keep the conversation valid
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": "done"})
                    yield {"type": "final_answer", "content": final, "agent": self.name}
                    return

                # ── Regular tool ──────────────────────────────────────────
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
                    obs = str(get_tool(tool_name)(**tool_args))
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
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": obs})

        # ── Case C: max steps reached — force a synthesis call ────────────
        final = self._force_final_answer(messages)
        self.short_term.add("user", query)
        self.short_term.add("assistant", final)
        yield {"type": "final_answer", "content": final, "agent": self.name}
