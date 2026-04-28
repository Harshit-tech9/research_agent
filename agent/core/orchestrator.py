import logging
from typing import Generator

import tools  # noqa: F401 — triggers tool registration

from core.agent import Agent
from core.planner import create_plan
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.episodic import EpisodicMemory

logger = logging.getLogger(__name__)

# ── Agent system prompts ──────────────────────────────────────────────────────

_RESEARCH_SYSTEM = """You are a research specialist agent.
Your job is to find accurate, up-to-date information from the web.
Use tavily_search for current events, prices, news, and factual questions.
Use wikipedia_search for encyclopedic knowledge, history, and concepts.
Always base your answer on what you find — do not fabricate facts.
"""

_MATH_SYSTEM = """You are a mathematical computation specialist agent.
Your job is to perform precise numerical calculations.
Use the calculator tool for all arithmetic, algebra, or scientific computations.
Show your reasoning clearly before and after using the tool.
"""

_GENERAL_SYSTEM = """You are a capable general-purpose AI agent.
You have access to web search, Wikipedia, and a calculator.
Reason step by step. Use tools when you need external information or precise computation.
Give a clear, concise final answer.
"""


class Orchestrator:
    """
    Routes every incoming query to the most appropriate specialized agent.

    Agents:
      • research_agent  — web + Wikipedia search
      • math_agent      — calculator only
      • general_agent   — all tools (default / fallback)

    All three agents share the same LongTermMemory so recalled context
    is consistent regardless of which agent handles the query.
    Completed runs are saved to EpisodicMemory.
    """

    def __init__(self):
        shared_lt = LongTermMemory()
        self.episodic = EpisodicMemory()

        self.research_agent = Agent(
            name="research_agent",
            system_prompt=_RESEARCH_SYSTEM,
            tool_names=["tavily_search", "wikipedia_search"],
            long_term=shared_lt,
        )
        self.math_agent = Agent(
            name="math_agent",
            system_prompt=_MATH_SYSTEM,
            tool_names=["calculator"],
            long_term=shared_lt,
        )
        self.general_agent = Agent(
            name="general_agent",
            system_prompt=_GENERAL_SYSTEM,
            tool_names=["tavily_search", "wikipedia_search", "calculator"],
            long_term=shared_lt,
        )

        self._long_term = shared_lt
        self._agents = {
            "research_agent": self.research_agent,
            "math_agent":     self.math_agent,
            "general_agent":  self.general_agent,
        }

    # ── Routing ───────────────────────────────────────────────────────────────

    def _route(self, query: str) -> Agent:
        """Keyword-based routing. Fast and deterministic."""
        q = query.lower()

        _web_signals  = {"latest", "current", "news", "price", "today", "recent",
                         "who is", "where is", "when did", "what happened",
                         "weather", "stock", "trending"}
        _math_signals = {"calculat", "comput", "how much is", "what is the value",
                         "solve", "factorial", "sqrt", "equation", "formula",
                         "percent", "multiply", "divide", "sum of"}

        needs_web  = any(kw in q for kw in _web_signals)
        needs_math = any(kw in q for kw in _math_signals) or any(
            op in query for op in ["+", "-", "*", "/", "**", "%", "="]
        )

        if needs_web and needs_math:
            return self.general_agent
        if needs_math:
            return self.math_agent
        if needs_web:
            return self.research_agent
        return self.general_agent

    # ── Public API ────────────────────────────────────────────────────────────

    def run_stream(self, query: str) -> Generator[dict, None, None]:
        """
        Full pipeline:
          plan → route → agent execution → persist to memory
        """
        # 1. Plan
        plan = create_plan(query)
        yield {"type": "plan", "content": plan}

        # 2. Route
        agent = self._route(query)
        yield {"type": "routing", "agent": agent.name}

        # 3. Run agent
        steps: list[dict] = []
        final_answer: str | None = None

        for event in agent.run_stream(query, plan=plan):
            steps.append(event)
            yield event
            if event["type"] == "final_answer":
                final_answer = event["content"]

        # 4. Persist episode + long-term memory
        if final_answer:
            self.episodic.save(query, plan, steps, final_answer, agent.name)
            self._long_term.store(
                f"Q: {query}\nA: {final_answer}",
                metadata={"agent": agent.name, "type": "qa_pair"},
            )

    # ── Inspection helpers ────────────────────────────────────────────────────

    def memory_stats(self) -> dict:
        return {
            "long_term_items": self._long_term.count(),
            "episodes": self.episodic.count(),
            "long_term_available": self._long_term.is_available,
        }

    def recent_episodes(self, n: int = 8) -> list[dict]:
        return self.episodic.get_recent(n)
