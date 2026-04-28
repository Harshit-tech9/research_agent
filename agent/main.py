import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

from core.orchestrator import Orchestrator


def main():
    orchestrator = Orchestrator()
    print("\n=== AI Agent (Phase 4 — Multi-Agent) ===")
    stats = orchestrator.memory_stats()
    print(f"Memory: {stats['long_term_items']} long-term items · {stats['episodes']} episodes\n")

    query = input("Enter your query: ").strip()
    if not query:
        print("No query entered.")
        return

    print("\n" + "─" * 60)
    for event in orchestrator.run_stream(query):
        etype = event["type"]

        if etype == "plan":
            print("\n[PLAN]\n" + event["content"])

        elif etype == "routing":
            print(f"\n[ROUTING] → {event['agent']}")

        elif etype == "thought":
            print(f"\n[THOUGHT | step {event['step']} | {event['agent']}]\n{event['content']}")

        elif etype == "action":
            print(f"\n[ACTION  | step {event['step']}] {event['tool']}({event['input']})")

        elif etype == "observation":
            preview = event["content"][:300]
            print(f"[OBS     | step {event['step']}] {preview}")

        elif etype == "final_answer":
            print("\n" + "─" * 60)
            print("[FINAL ANSWER]\n" + event["content"])
            print("─" * 60)

        elif etype == "max_steps_reached":
            print("\n[WARNING] Agent reached maximum steps without a final answer.")

        elif etype == "error":
            print(f"\n[ERROR | step {event['step']}] {event['content']}")

    print()


if __name__ == "__main__":
    main()
