from tools.registry import register_tool


@register_tool(
    name="wikipedia_search",
    description=(
        "Look up factual, encyclopedic information on Wikipedia. "
        "Best for: biographies, historical events, scientific concepts, "
        "definitions, geography, and organizations. "
        "Use tavily_search for recent news or live data instead."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Topic or person to look up on Wikipedia",
            }
        },
        "required": ["query"],
    },
)
def wikipedia_search(query: str) -> str:
    try:
        import wikipedia as _wiki
    except ImportError:
        return "wikipedia package not installed. Run: pip install wikipedia"

    _wiki.set_lang("en")

    try:
        # summary() is fuzzy and handles auto-suggest internally — much more
        # reliable than page() which requires near-exact title matches.
        return _wiki.summary(query, sentences=6, auto_suggest=True)

    except _wiki.exceptions.DisambiguationError as exc:
        # Try the first unambiguous option
        try:
            return _wiki.summary(exc.options[0], sentences=6, auto_suggest=False)
        except Exception:
            top = ", ".join(exc.options[:5])
            return f"Ambiguous query — did you mean one of: {top}? Please be more specific."

    except _wiki.exceptions.PageError:
        # Title not found — fall back to a keyword search
        try:
            hits = _wiki.search(query, results=3)
            if hits:
                return _wiki.summary(hits[0], sentences=6, auto_suggest=False)
            return f"No Wikipedia article found for '{query}'."
        except Exception as exc2:
            return f"Wikipedia search failed: {exc2}"

    except Exception as exc:
        return f"Wikipedia error: {exc}"
