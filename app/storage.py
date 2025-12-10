from typing import Dict, Any
from uuid import uuid4
from datetime import datetime

from .engine.graph import Graph, RunResult


# In-memory stores (fine for assignment)
GRAPHS: Dict[str, Graph] = {}
RUNS: Dict[str, Dict[str, Any]] = {}


def save_graph(graph: Graph) -> str:
    GRAPHS[graph.graph_id] = graph
    return graph.graph_id


def get_graph(graph_id: str) -> Graph:
    if graph_id not in GRAPHS:
        raise KeyError(f"Graph '{graph_id}' not found")
    return GRAPHS[graph_id]


def create_run(graph_id: str, result: RunResult) -> str:
    run_id = str(uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    RUNS[run_id] = {
        "graph_id": graph_id,
        "state": result.final_state,
        "log": result.log,
        "status": "completed",
        "created_at": now,
        "updated_at": now,
    }
    return run_id


def get_run(run_id: str) -> Dict[str, Any]:
    if run_id not in RUNS:
        raise KeyError(f"Run '{run_id}' not found")
    return RUNS[run_id]
