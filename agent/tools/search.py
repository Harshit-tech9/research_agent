import requests

from config import TAVILY_API_KEY
from tools.registry import register_tool

_TAVILY_URL = "https://api.tavily.com/search"


@register_tool(
    name="tavily_search",
    description=(
        "Search the web for current, real-time information. "
        "Use for news, prices, recent events, factual questions about the world."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            }
        },
        "required": ["query"],
    },
)
def tavily_search(query: str) -> str:
    try:
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "max_results": 5,
        }
        response = requests.post(_TAVILY_URL, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "answer" in data and data["answer"]:
            return data["answer"]

        # Fallback: concatenate top result snippets
        results = data.get("results", [])
        if results:
            return "\n\n".join(
                f"[{r.get('title', '')}] {r.get('content', '')[:300]}"
                for r in results[:3]
            )
        return "No results found."
    except Exception as exc:
        return f"Search error: {exc}"
