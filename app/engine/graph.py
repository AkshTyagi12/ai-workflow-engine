from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Callable
import inspect


NodeFn = Callable[[Dict[str, Any]], Any]
ConditionSpec = Dict[str, Any]


@dataclass
class Graph:
    """
    Minimal graph representation.

    - nodes: mapping of node name -> Python callable
    - edges: mapping of node name -> next node name or conditional spec
    """
    graph_id: str
    nodes: Dict[str, NodeFn]
    edges: Dict[str, Union[str, ConditionSpec]]
    start_node: str
    max_steps: int = 100


@dataclass
class RunResult:
    final_state: Dict[str, Any]
    log: List[str] = field(default_factory=list)


def _evaluate_condition(state: Dict[str, Any], spec: ConditionSpec) -> bool:
    """
    Evaluate a simple condition against the state.
    Spec format:
      {
        "type": "conditional",
        "key": "quality_score",
        "op": ">=",
        "value": 80,
        "true": "next_if_true",
        "false": "next_if_false"
      }
    """
    key = spec.get("key")
    op = spec.get("op", "==")
    value = spec.get("value")

    if key is None:
        raise ValueError("Conditional spec is missing 'key'")

    left = state.get(key)

    if op == "==":
        return left == value
    if op == "!=":
        return left != value
    if op == ">":
        return left > value
    if op == "<":
        return left < value
    if op == ">=":
        return left >= value
    if op == "<=":
        return left <= value

    raise ValueError(f"Unsupported operator in condition: {op}")


async def _call_node(node_fn: NodeFn, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Support both sync and async node functions.
    """
    result = node_fn(state)
    if inspect.isawaitable(result):
        result = await result
    if not isinstance(result, dict):
        raise TypeError(f"Node function {node_fn.__name__} must return a dict, got {type(result)}")
    return result


async def run_graph(graph: Graph, initial_state: Dict[str, Any]) -> RunResult:
    """
    Execute the graph from start_node, following edges and conditionals.
    Supports simple loops by pointing edges back to earlier nodes.
    """
    state: Dict[str, Any] = dict(initial_state)
    log: List[str] = []

    current: Optional[str] = graph.start_node
    steps = 0

    while current is not None and steps < graph.max_steps:
        if current not in graph.nodes:
            raise ValueError(f"Node '{current}' not found in graph")

        node_fn = graph.nodes[current]
        state = await _call_node(node_fn, state)
        log.append(current)

        edge = graph.edges.get(current)
        if edge is None:
            # No outgoing edge — stop
            break

        if isinstance(edge, str) or edge is None:
            # Simple linear edge, or explicit end if None
            current = edge  # may set to None to end
        elif isinstance(edge, dict) and edge.get("type") == "conditional":
            cond_result = _evaluate_condition(state, edge)
            current = edge["true"] if cond_result else edge["false"]
        else:
            raise ValueError(f"Invalid edge specification for node '{current}'")

        steps += 1

    if steps >= graph.max_steps:
        # Soft protection against infinite loops
        state["_warning"] = f"Stopped after reaching max_steps={graph.max_steps}"

    state["_execution_log"] = log
    return RunResult(final_state=state, log=log)
