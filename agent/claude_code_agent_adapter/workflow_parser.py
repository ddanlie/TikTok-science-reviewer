"""
Workflow YAML parser.

Loads the workflow YAML file and produces a list of WorkflowStep
objects that the agent loop can iterate through.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


WORKFLOW_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "workflows",
    "article_discovery_and_content_creation.yaml",
)


@dataclass
class WorkflowAction:
    """A single action within a workflow step."""
    name: str
    tool: Optional[str] = None
    requires_llm: bool = False
    params_template: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class WorkflowStep:
    """One step in the workflow."""
    number: int
    name: str
    description: str
    actions: List[WorkflowAction] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    prompt_template: Optional[str] = None
    prompt_guidelines: List[str] = field(default_factory=list)


def parse_workflow(yaml_path: str = WORKFLOW_PATH) -> List[WorkflowStep]:
    """
    Load and parse the workflow YAML into a list of WorkflowStep objects.

    Args:
        yaml_path: Path to the YAML file.

    Returns:
        List of WorkflowStep objects in step order.
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    steps = []
    for raw_step in raw.get("steps", []):
        steps.append(_parse_step(raw_step))
    return steps


def _parse_step(raw: Dict[str, Any]) -> WorkflowStep:
    """Parse a single step dict from YAML."""
    actions = []

    # Parse actions list if present
    for ra in raw.get("actions", []):
        tool_name = None
        requires_llm = False

        if "tool_call" in ra:
            tc = ra["tool_call"]
            tool_name = tc.get("function")
            params_template = tc.get("params", {})
        elif "tool" in ra:
            # Native LLM tool reference (Read, WebSearch, etc.)
            requires_llm = True
            params_template = ra.get("params", {})
        else:
            requires_llm = True
            params_template = {}

        actions.append(WorkflowAction(
            name=ra.get("action", "unnamed"),
            tool=tool_name,
            requires_llm=requires_llm,
            params_template=params_template,
            description=ra.get("description", ra.get("purpose", "")),
        ))

    # Parse top-level tool_call (some steps define it at step level)
    if "tool_call" in raw and isinstance(raw["tool_call"], dict):
        tc = raw["tool_call"]
        actions.append(WorkflowAction(
            name=tc.get("function", "tool_call"),
            tool=tc.get("function"),
            requires_llm=False,
            params_template=tc.get("params", {}),
            description=f"Execute {tc.get('function')}",
        ))

    # If no explicit actions but step has method/analysis/planning, it's LLM-driven
    if not actions:
        for llm_key in ("method", "analysis", "planning"):
            if llm_key in raw:
                actions.append(WorkflowAction(
                    name=llm_key,
                    requires_llm=True,
                    description=str(raw[llm_key]),
                ))

    return WorkflowStep(
        number=raw["step"],
        name=raw["name"],
        description=raw.get("description", ""),
        actions=actions,
        requirements=raw.get("requirements", []),
        prompt_template=raw.get("prompt_template"),
        prompt_guidelines=raw.get("prompt_guidelines", []),
    )
