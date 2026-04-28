# Importing each module triggers @register_tool decorators, populating the registry.
from tools import calculator, search, wikipedia  # noqa: F401
