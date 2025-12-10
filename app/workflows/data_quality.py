from typing import Dict, Any, List

from ..engine.graph import Graph
from ..engine.registry import tool_registry


# ---------- Node / Tool Functions ----------

def profile_data_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    data: List[Any] = state.get("data", [])
    state["row_count"] = len(data)
    return state


def identify_anomalies_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    data = state.get("data", [])
    anomalies = [x for x in data if x is None or x == ""]
    state["anomalies"] = anomalies
    state["anomaly_count"] = len(anomalies)
    return state


def generate_rules_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    rules = ["No nulls allowed"]
    state["rules"] = rules
    return state


def apply_rules_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    data = state.get("data", [])
    cleaned = [x for x in data if x not in (None, "")]
    state["data"] = cleaned
    state["anomaly_count"] = 0
    return state


# ---------- Registration ----------

def register_data_quality_tools():
    tool_registry.register("profile_data", profile_data_tool)
    tool_registry.register("identify_anomalies", identify_anomalies_tool)
    tool_registry.register("generate_rules", generate_rules_tool)
    tool_registry.register("apply_rules", apply_rules_tool)


def create_data_quality_graph(graph_id: str = "data_quality_example") -> Graph:
    nodes = {
        "profile_data": tool_registry.get("profile_data"),
        "identify_anomalies": tool_registry.get("identify_anomalies"),
        "generate_rules": tool_registry.get("generate_rules"),
        "apply_rules": tool_registry.get("apply_rules"),
    }

    edges = {
        "profile_data": "identify_anomalies",
        "identify_anomalies": {
            "type": "conditional",
            "key": "anomaly_count",
            "op": "<=",
            "value": 1,
            "true": None,
            "false": "generate_rules",
        },
        "generate_rules": "apply_rules",
        "apply_rules": "identify_anomalies",
    }

    return Graph(
        graph_id=graph_id,
        nodes=nodes,
        edges=edges,
        start_node="profile_data",
        max_steps=20,
    )
