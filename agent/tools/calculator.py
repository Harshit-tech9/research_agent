import ast
import math as _math
import operator as _op

from tools.registry import register_tool

_OPERATORS = {
    ast.Add: _op.add,
    ast.Sub: _op.sub,
    ast.Mult: _op.mul,
    ast.Div: _op.truediv,
    ast.Pow: _op.pow,
    ast.Mod: _op.mod,
    ast.FloorDiv: _op.floordiv,
    ast.USub: _op.neg,
    ast.UAdd: _op.pos,
}

_NAMES = {
    "pi": _math.pi, "e": _math.e, "inf": float("inf"),
    "sqrt": _math.sqrt, "sin": _math.sin, "cos": _math.cos,
    "tan": _math.tan, "log": _math.log, "log10": _math.log10,
    "log2": _math.log2, "exp": _math.exp, "abs": abs,
    "round": round, "floor": _math.floor, "ceil": _math.ceil,
    "factorial": _math.factorial,
}


def _safe_eval(node: ast.AST):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op = type(node.op)
        if op not in _OPERATORS:
            raise ValueError(f"Operator {op.__name__} not allowed")
        return _OPERATORS[op](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op = type(node.op)
        if op not in _OPERATORS:
            raise ValueError(f"Operator {op.__name__} not allowed")
        return _OPERATORS[op](_safe_eval(node.operand))
    if isinstance(node, ast.Name):
        if node.id not in _NAMES:
            raise ValueError(f"Name '{node.id}' not allowed")
        return _NAMES[node.id]
    if isinstance(node, ast.Call):
        fn = _safe_eval(node.func)
        args = [_safe_eval(a) for a in node.args]
        return fn(*args)
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


@register_tool(
    name="calculator",
    description=(
        "Evaluate a mathematical expression safely. "
        "Supports +, -, *, /, **, %, //, and functions: "
        "sqrt, sin, cos, tan, log, log10, exp, abs, round, floor, ceil, factorial. "
        "Constants: pi, e."
    ),
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Math expression to evaluate, e.g. 'sqrt(144) + 2**10'",
            }
        },
        "required": ["expression"],
    },
)
def calculator(expression: str) -> str:
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"
