import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

from config import EPISODIC_DB_PATH

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    SQLite-backed session log.
    Every completed agent run is saved as an episode so you can
    review what the agent did, which tools it used, and what it answered.
    """

    def __init__(self, db_path: str = None):
        path = db_path or EPISODIC_DB_PATH
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._create_table()

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS episodes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                agent_name  TEXT,
                query       TEXT    NOT NULL,
                plan        TEXT,
                final_answer TEXT,
                steps_json  TEXT,
                tools_used  TEXT
            )
            """
        )
        self._conn.commit()

    # ── Write ─────────────────────────────────────────────────────────────────

    def save(
        self,
        query: str,
        plan: str,
        steps: list[dict],
        final_answer: str | None,
        agent_name: str = "general_agent",
    ) -> None:
        tools_used = list({s["tool"] for s in steps if s.get("type") == "action" and "tool" in s})
        try:
            self._conn.execute(
                """
                INSERT INTO episodes
                    (timestamp, agent_name, query, plan, final_answer, steps_json, tools_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    agent_name,
                    query,
                    plan,
                    final_answer,
                    json.dumps(steps),
                    json.dumps(tools_used),
                ),
            )
            self._conn.commit()
        except Exception as exc:
            logger.warning("EpisodicMemory save failed: %s", exc)

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_recent(self, n: int = 10) -> list[dict]:
        try:
            cur = self._conn.execute(
                """
                SELECT timestamp, agent_name, query, final_answer, tools_used
                FROM episodes
                ORDER BY id DESC
                LIMIT ?
                """,
                (n,),
            )
            return [
                {
                    "timestamp": r[0],
                    "agent": r[1],
                    "query": r[2],
                    "answer": r[3],
                    "tools": json.loads(r[4] or "[]"),
                }
                for r in cur.fetchall()
            ]
        except Exception:
            return []

    def count(self) -> int:
        try:
            return self._conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        except Exception:
            return 0
