from typing import Dict, Any, List

from ..engine.graph import Graph
from ..engine.registry import tool_registry


# ---------- Node / Tool Functions ----------

def split_text_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    text = state.get("text", "")
    chunk_size = state.get("chunk_size", 100)

    words = text.split()
    chunks = [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]

    state["chunks"] = chunks
    state["partial_summaries"] = []
    state.setdefault("summary", "")
    return state


def summarize_chunks_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    summaries = []
    for chunk in state.get("chunks", []):
        words = chunk.split()
        summaries.append(" ".join(words[:20]) + "...")

    state["partial_summaries"] = summaries
    return state


def merge_summaries_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    merged = " ".join(state.get("partial_summaries", []))
    state["summary"] = merged
    return state


def refine_summary_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    summary = state.get("summary", "")
    target_length = state.get("max_length", 150)

    words = summary.split()
    if len(words) > target_length:
        words = words[:target_length]

    state["summary"] = " ".join(words)
    state["summary_length"] = len(words)
    return state


# ---------- Registration ----------

def register_summarization_tools():
    tool_registry.register("split_text", split_text_tool)
    tool_registry.register("summarize_chunks", summarize_chunks_tool)
    tool_registry.register("merge_summaries", merge_summaries_tool)
    tool_registry.register("refine_summary", refine_summary_tool)


def create_summarization_graph(graph_id: str = "summarization_example") -> Graph:
    nodes = {
        "split_text": tool_registry.get("split_text"),
        "summarize_chunks": tool_registry.get("summarize_chunks"),
        "merge_summaries": tool_registry.get("merge_summaries"),
        "refine_summary": tool_registry.get("refine_summary"),
    }

    edges = {
        "split_text": "summarize_chunks",
        "summarize_chunks": "merge_summaries",
        "merge_summaries": "refine_summary",
        "refine_summary": {
            "type": "conditional",
            "key": "summary_length",
            "op": "<=",
            "value": 150,
            "true": None,                # stop
            "false": "refine_summary",   # loop
        },
    }

    return Graph(
        graph_id=graph_id,
        nodes=nodes,
        edges=edges,
        start_node="split_text",
        max_steps=20,
    )
