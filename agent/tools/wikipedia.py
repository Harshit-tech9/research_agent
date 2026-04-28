from tools.registry import register_tool


@register_tool(
    name="wikipedia_search",
    description=(
        "Search Wikipedia for encyclopedic, factual information about people, "
        "places, concepts, history, and science."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Topic to look up on Wikipedia",
            }
        },
        "required": ["query"],
    },
)
def wikipedia_search(query: str) -> str:
    try:
        import wikipedia as _wiki
        _wiki.set_lang("en")
        try:
            page = _wiki.page(query, auto_suggest=True)
            return page.summary[:1200]
        except _wiki.exceptions.DisambiguationError as exc:
            try:
                page = _wiki.page(exc.options[0])
                return page.summary[:1200]
            except Exception:
                return f"Ambiguous query. Possible topics: {', '.join(exc.options[:6])}"
    except ImportError:
        return "wikipedia package not installed. Run: pip install wikipedia"
    except Exception as exc:
        return f"Wikipedia error: {exc}"
