from typing import Callable, Dict, Any

ToolFn = Callable[[Dict[str, Any]], Any]


class ToolRegistry:
    """
    Simple global registry for reusable tools (node functions).
    Nodes look up tools by name instead of hard-coding functions.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolFn] = {}

    def register(self, name: str, fn: ToolFn) -> None:
        self._tools[name] = fn

    def get(self, name: str) -> ToolFn:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered")
        return self._tools[name]

    def list_tools(self) -> Dict[str, str]:
        return {name: fn.__name__ for name, fn in self._tools.items()}


# Global registry instance
tool_registry = ToolRegistry()
