"""
Protocol message definitions and JSON serialization for the agent loop adapter.

Defines the contract between the adapter (stdout) and the LLM (stdin).
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union


class ProtocolError(Exception):
    """Raised when LLM input cannot be parsed."""
    pass


# --- Adapter → LLM messages (stdout) ---

@dataclass
class StepInfo:
    number: int
    name: str
    description: str
    actions: List[Dict[str, Any]]
    requirements: List[str] = field(default_factory=list)
    prompt_template: Optional[str] = None
    prompt_guidelines: List[str] = field(default_factory=list)


@dataclass
class ContextMessage:
    step: Optional[StepInfo]
    tools: List[Dict[str, Any]]
    llm_capabilities: List[str]
    state: Dict[str, Any]
    step_history: List[Dict[str, Any]]
    turn: int
    last_result: Optional[Dict[str, Any]]


def serialize_context(ctx: ContextMessage) -> str:
    """Serialize a ContextMessage to a single-line JSON string."""
    data = {
        "type": "context",
        "step": asdict(ctx.step) if ctx.step else None,
        "tools": ctx.tools,
        "llm_capabilities": ctx.llm_capabilities,
        "state": ctx.state,
        "step_history": ctx.step_history,
        "turn": ctx.turn,
        "last_result": ctx.last_result,
    }
    return json.dumps(data, ensure_ascii=False)


# --- LLM → Adapter messages (stdin) ---

@dataclass
class ToolCallRequest:
    type: str  # "tool_call"
    tool: str
    params: Dict[str, Any]


@dataclass
class LlmActionReport:
    type: str  # "llm_action"
    action: str
    state_updates: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class UserMessage:
    type: str  # "message_user"
    message: str


@dataclass
class StepCompleteSignal:
    type: str  # "step_complete"
    state_updates: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowCompleteSignal:
    type: str  # "workflow_complete"
    summary: str = ""


LlmInput = Union[
    ToolCallRequest,
    LlmActionReport,
    UserMessage,
    StepCompleteSignal,
    WorkflowCompleteSignal,
]


def parse_input(raw: str) -> LlmInput:
    """
    Parse a JSON string from stdin into the appropriate message dataclass.

    Raises ProtocolError on invalid input.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ProtocolError(f"Invalid JSON: {e}")

    if not isinstance(data, dict):
        raise ProtocolError("Input must be a JSON object")

    msg_type = data.get("type")
    if not msg_type:
        raise ProtocolError("Missing 'type' field")

    if msg_type == "tool_call":
        tool = data.get("tool")
        params = data.get("params", {})
        if not tool:
            raise ProtocolError("tool_call requires 'tool' field")
        if not isinstance(params, dict):
            raise ProtocolError("'params' must be a dict")
        return ToolCallRequest(type=msg_type, tool=tool, params=params)

    elif msg_type == "llm_action":
        action = data.get("action")
        if not action:
            raise ProtocolError("llm_action requires 'action' field")
        return LlmActionReport(
            type=msg_type,
            action=action,
            state_updates=data.get("state_updates", {}),
            description=data.get("description", ""),
        )

    elif msg_type == "message_user":
        message = data.get("message", "")
        return UserMessage(type=msg_type, message=message)

    elif msg_type == "step_complete":
        return StepCompleteSignal(
            type=msg_type,
            state_updates=data.get("state_updates", {}),
        )

    elif msg_type == "workflow_complete":
        return WorkflowCompleteSignal(
            type=msg_type,
            summary=data.get("summary", ""),
        )

    else:
        raise ProtocolError(
            f"Unknown message type '{msg_type}'. "
            f"Expected: tool_call, llm_action, message_user, step_complete, workflow_complete"
        )
