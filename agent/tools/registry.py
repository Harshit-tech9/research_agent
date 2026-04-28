from typing import Callable, Dict, Any

_REGISTRY: Dict[str, dict] = {}


def register_tool(name: str, description: str, parameters: dict) -> Callable:
    """Decorator that registers a function as a callable agent tool."""
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[name] = {
            "fn": fn,
            "description": description,
            "parameters": parameters,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
        }
        return fn
    return decorator


def get_tool(name: str) -> Callable:
    if name not in _REGISTRY:
        raise KeyError(f"Tool '{name}' not registered. Available: {list_tools()}")
    return _REGISTRY[name]["fn"]


def get_schemas(names: list[str] | None = None) -> list[dict]:
    """Return OpenAI-compatible tool schemas for the given names (or all)."""
    if names is None:
        return [t["schema"] for t in _REGISTRY.values()]
    return [_REGISTRY[n]["schema"] for n in names if n in _REGISTRY]


def list_tools() -> list[str]:
    return list(_REGISTRY.keys())


def tool_info() -> list[dict]:
    return [
        {"name": k, "description": v["description"]}
        for k, v in _REGISTRY.items()
    ]
