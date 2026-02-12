"""
Agent loop — one-turn-at-a-time entry point.

Each process invocation handles exactly one turn:
  1. Load persisted state
  2. If input provided: parse and dispatch (tool call, llm action, step/workflow complete)
  3. Build context message from current state + workflow step
  4. Save state, print context to stdout
"""

import sys
from dataclasses import asdict
from typing import Optional

from agent.claude_code_agent_adapter.protocol import (
    ContextMessage,
    StepInfo,
    ProtocolError,
    ToolCallRequest,
    LlmActionReport,
    UserMessage,
    StepCompleteSignal,
    WorkflowCompleteSignal,
    parse_input,
    serialize_context,
)
from agent.claude_code_agent_adapter.state import WorkflowState
from agent.claude_code_agent_adapter.tool_registry import ToolRegistry
from agent.claude_code_agent_adapter.workflow_parser import parse_workflow, WorkflowStep


LLM_CAPABILITIES = [
    "web_search",
    "read_file",
    "message_user",
    "generate_uuid",
    "creative_writing",
]


def _step_to_info(step: WorkflowStep) -> StepInfo:
    """Convert a parsed WorkflowStep to a StepInfo for the context message."""
    actions = []
    for a in step.actions:
        actions.append({
            "name": a.name,
            "tool": a.tool,
            "requires_llm": a.requires_llm,
            "params_template": a.params_template,
            "description": a.description,
        })

    return StepInfo(
        number=step.number,
        name=step.name,
        description=step.description,
        actions=actions,
        requirements=step.requirements,
        prompt_template=step.prompt_template,
        prompt_guidelines=step.prompt_guidelines,
    )


def _build_context(
    state: WorkflowState,
    steps: list,
    registry: ToolRegistry,
) -> ContextMessage:
    """Build the full context message for the current state."""
    step_info = None
    if 1 <= state.current_step <= len(steps):
        step_info = _step_to_info(steps[state.current_step - 1])

    return ContextMessage(
        step=step_info,
        tools=registry.get_tool_info(),
        llm_capabilities=LLM_CAPABILITIES,
        state=state.data,
        step_history=state.get_step_history(),
        turn=state.turn,
        last_result=state.last_result,
    )


def process_turn(input_json: Optional[str] = None) -> str:
    """
    Process a single turn of the agent loop.

    Args:
        input_json: JSON string from the LLM (stdin), or None for the first turn.

    Returns:
        JSON string to print to stdout (the context message or final summary).
    """
    # Load workflow and state
    steps = parse_workflow()
    state = WorkflowState.load()
    registry = ToolRegistry()

    # Process input if provided
    if input_json:
        try:
            msg = parse_input(input_json)
        except ProtocolError as e:
            state.set_last_result({
                "type": "error",
                "error": str(e),
                "hint": "Respond with valid JSON. Types: tool_call, llm_action, message_user, step_complete, workflow_complete",
            })
            state.save()
            return serialize_context(_build_context(state, steps, registry))

        # Dispatch by message type
        if isinstance(msg, ToolCallRequest):
            result = registry.execute(msg.tool, msg.params)
            state.set_last_result({
                "type": "tool_result",
                "tool": msg.tool,
                "result": result,
            })
            # Auto-extract state updates from successful results
            auto_updates = registry.get_auto_state_updates(msg.tool, result)
            if auto_updates:
                state.update(auto_updates)

        elif isinstance(msg, LlmActionReport):
            state.set_last_result({
                "type": "llm_action_ack",
                "action": msg.action,
                "acknowledged": True,
            })
            if msg.state_updates:
                state.update(msg.state_updates)

        elif isinstance(msg, UserMessage):
            sys.stderr.write(f"\n{'=' * 60}\n")
            sys.stderr.write(f"AGENT MESSAGE: {msg.message}\n")
            sys.stderr.write(f"{'=' * 60}\n\n")
            sys.stderr.flush()
            state.set_last_result({
                "type": "message_delivered",
                "acknowledged": True,
            })

        elif isinstance(msg, StepCompleteSignal):
            if msg.state_updates:
                state.update(msg.state_updates)
            state.advance_step()
            new_step_name = (
                steps[state.current_step - 1].name
                if state.current_step <= len(steps)
                else "DONE"
            )
            state.set_last_result({
                "type": "step_advanced",
                "new_step": state.current_step,
                "new_step_name": new_step_name,
            })

        elif isinstance(msg, WorkflowCompleteSignal):
            state.set_last_result({
                "type": "workflow_complete",
                "summary": msg.summary,
            })
            state.save()
            return serialize_context(_build_context(state, steps, registry))

    # Save state and return context
    state.save()
    return serialize_context(_build_context(state, steps, registry))
