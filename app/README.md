# AI Workflow Engine

A minimal agent workflow engine that executes graph-based workflows with
conditional branching, looping, and shared state, exposed via a FastAPI API.

## Features
- Graph-based workflow execution
- Conditional edges and looping
- Shared state between nodes
- Execution logs and run tracking
- FastAPI REST interface with Swagger UI

## Project Structure
app/
engine/
workflows/
main.py
storage.py

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn pydantic

RUN
python -m uvicorn app.main:app --reload

OPEN 
http://127.0.0.1:8000/


{
  "graph_id": "code_review_example",
  "initial_state": {
    "code": "def foo(x):\n    # TODO: fix\n    return x"
  }



