from typing import Dict, Any, List, Optional, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from .engine.registry import tool_registry
from .engine.graph import Graph, run_graph
from .storage import save_graph, get_graph, create_run, get_run

from .workflows.code_review import (
    register_code_review_tools,
    create_code_review_graph,
)
from .workflows.summarization import (
    register_summarization_tools,
    create_summarization_graph,
)
from .workflows.data_quality import (
    register_data_quality_tools,
    create_data_quality_graph,
)

app = FastAPI(title="Minimal Agent Workflow Engine")


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


class NodeSpec(BaseModel):
    name: str
    tool_name: str


class EdgeSpec(BaseModel):
    source: str
    type: Literal["normal", "conditional"] = "normal"
    target: Optional[str] = None
    condition_key: Optional[str] = None
    condition_op: Optional[str] = None
    condition_value: Optional[Any] = None
    true_target: Optional[Optional[str]] = None
    false_target: Optional[Optional[str]] = None


class GraphCreateRequest(BaseModel):
    nodes: List[NodeSpec]
    edges: List[EdgeSpec]
    start_node: str
    max_steps: int = 100


class GraphCreateResponse(BaseModel):
    graph_id: str


class GraphRunRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any] = Field(default_factory=dict)


class GraphRunResponse(BaseModel):
    run_id: str
    final_state: Dict[str, Any]
    log: List[str]


class RunStateResponse(BaseModel):
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    log: List[str]
    status: str


class ToolsListResponse(BaseModel):
    tools: Dict[str, str]


@app.on_event("startup")
def on_startup() -> None:
    register_code_review_tools()
    save_graph(create_code_review_graph(graph_id="code_review_example"))

    register_summarization_tools()
    save_graph(create_summarization_graph(graph_id="summarization_example"))

    register_data_quality_tools()
    save_graph(create_data_quality_graph(graph_id="data_quality_example"))


def build_graph_from_request(req: GraphCreateRequest) -> Graph:
    nodes: Dict[str, Any] = {}
    for n in req.nodes:
        try:
            fn = tool_registry.get(n.tool_name)
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{n.tool_name}' for node '{n.name}' is not registered.",
            )
        nodes[n.name] = fn

    edges: Dict[str, Any] = {}
    for e in req.edges:
        if e.type == "normal":
            if e.target is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Normal edge from '{e.source}' must have 'target'.",
                )
            edges[e.source] = e.target

        elif e.type == "conditional":
            if e.condition_key is None or e.condition_op is None or e.condition_value is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Conditional edge from '{e.source}' is invalid.",
                )
            if e.true_target is None and e.false_target is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Conditional edge from '{e.source}' must have at least one target.",
                )
            edges[e.source] = {
                "type": "conditional",
                "key": e.condition_key,
                "op": e.condition_op,
                "value": e.condition_value,
                "true": e.true_target,
                "false": e.false_target,
            }

    graph_id = str(uuid4())
    graph = Graph(
        graph_id=graph_id,
        nodes=nodes,
        edges=edges,
        start_node=req.start_node,
        max_steps=req.max_steps,
    )

    save_graph(graph)
    return graph


@app.get("/tools", response_model=ToolsListResponse)
async def list_tools() -> ToolsListResponse:
    return ToolsListResponse(tools=tool_registry.list_tools())


@app.post("/graph/create", response_model=GraphCreateResponse)
async def create_graph(req: GraphCreateRequest) -> GraphCreateResponse:
    graph = build_graph_from_request(req)
    return GraphCreateResponse(graph_id=graph.graph_id)


@app.post("/graph/run", response_model=GraphRunResponse)
async def run_graph_endpoint(req: GraphRunRequest) -> GraphRunResponse:
    try:
        graph = get_graph(req.graph_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Graph '{req.graph_id}' not found")

    result = await run_graph(graph, req.initial_state)
    run_id = create_run(req.graph_id, result)

    return GraphRunResponse(
        run_id=run_id,
        final_state=result.final_state,
        log=result.log,
    )


@app.get("/graph/state/{run_id}", response_model=RunStateResponse)
async def get_run_state(run_id: str) -> RunStateResponse:
    try:
        run = get_run(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    return RunStateResponse(
        run_id=run_id,
        graph_id=run["graph_id"],
        state=run["state"],
        log=run["log"],
        status=run["status"],
    )
