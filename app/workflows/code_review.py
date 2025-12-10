import re
from typing import Dict, Any, List

from ..engine.graph import Graph
from ..engine.registry import tool_registry


# ---------- Tools / Node Functions ----------

def extract_functions_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Naive function extractor: looks for 'def name(' patterns.
    """
    code: str = state.get("code", "")
    pattern = r"def\s+([a-zA-Z_]\w*)\s*\("
    functions: List[str] = re.findall(pattern, code)

    state["functions"] = functions
    state.setdefault("quality_score", 50)  # start at 50 if not present
    state.setdefault("issues", 0)
    state.setdefault("suggestions", [])
    return state


def check_complexity_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Naive complexity:
      - count branching / loop keywords
      - add function count
    """
    code: str = state.get("code", "")
    functions = state.get("functions", [])

    complexity_signals = len(re.findall(r"\b(if|for|while|try|except)\b", code))
    complexity_score = complexity_signals + len(functions)

    state["complexity_score"] = complexity_score

    # Adjust quality_score: lower complexity => higher quality
    base_quality = state.get("quality_score", 50)
    bonus = max(0, 10 - complexity_score)  # more bonus if less complex
    state["quality_score"] = min(100, base_quality + bonus)

    return state


def detect_issues_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Naive issue detector:
      - counts TODOs
      - flags very long lines
    """
    code: str = state.get("code", "")
    lines = code.splitlines()

    todo_issues = len([ln for ln in lines if "TODO" in ln])
    long_line_issues = len([ln for ln in lines if len(ln) > 120])

    total_issues = todo_issues + long_line_issues
    state["issues"] = total_issues

    # Deduct some quality for issues
    quality = state.get("quality_score", 50)
    penalty = total_issues * 2
    state["quality_score"] = max(0, quality - penalty)

    issue_summaries = []
    if todo_issues:
        issue_summaries.append(f"{todo_issues} TODOs found")
    if long_line_issues:
        issue_summaries.append(f"{long_line_issues} overly long lines")

    state["issue_summary"] = ", ".join(issue_summaries) or "No obvious issues"
    return state


def suggest_improvements_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest small improvements and bump quality a bit each pass.
    This drives the loop: we keep 'improving' until threshold.
    """
    suggestions = state.setdefault("suggestions", [])

    complexity = state.get("complexity_score", 0)
    issues = state.get("issues", 0)

    if complexity > 10:
        suggestions.append("Consider breaking complex functions into smaller ones.")
    if issues > 0:
        suggestions.append("Address flagged TODOs and long lines.")
    if not suggestions:
        suggestions.append("Code looks clean. Minor refactoring only if necessary.")

    # Simulate improvement by increasing quality gradually
    quality = state.get("quality_score", 50)
    state["quality_score"] = min(100, quality + 5)

    return state


# ---------- Registration Helpers ----------

def register_code_review_tools() -> None:
    """
    Register all tools used by the Code Review workflow.
    """
    tool_registry.register("extract_functions", extract_functions_tool)
    tool_registry.register("check_complexity", check_complexity_tool)
    tool_registry.register("detect_issues", detect_issues_tool)
    tool_registry.register("suggest_improvements", suggest_improvements_tool)


def create_code_review_graph(graph_id: str = "code_review_example") -> Graph:
    """
    Build a graph:

      extract_functions
        -> check_complexity
        -> detect_issues
        -> suggest_improvements
        -> conditional:
             if quality_score >= threshold: stop
             else: loop back to check_complexity
    """
    # Node mapping: node_name -> tool function via registry
    nodes = {
        "extract_functions": tool_registry.get("extract_functions"),
        "check_complexity": tool_registry.get("check_complexity"),
        "detect_issues": tool_registry.get("detect_issues"),
        "suggest_improvements": tool_registry.get("suggest_improvements"),
    }

    # Threshold can be customized later by creating another graph,
    # but here we just hard-code 80 as a clear demo.
    edges = {
        "extract_functions": "check_complexity",
        "check_complexity": "detect_issues",
        "detect_issues": "suggest_improvements",
        "suggest_improvements": {
            "type": "conditional",
            "key": "quality_score",
            "op": ">=",
            "value": 80,        # threshold
            "true": None,       # None = stop execution
            "false": "check_complexity",  # loop back
        },
    }

    return Graph(
        graph_id=graph_id,
        nodes=nodes,
        edges=edges,
        start_node="extract_functions",
        max_steps=50,
    )
