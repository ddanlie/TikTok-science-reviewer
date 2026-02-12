"""
Workflow state management with file persistence.

Tracks accumulated state across turns, current step, and history.
State is saved to disk after every mutation so each process invocation
can pick up where the last one left off.
"""

import json
import os
from typing import Any, Dict, List, Optional


STATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".tmp",
)
STATE_FILE = os.path.join(STATE_DIR, "agent_state.json")


class WorkflowState:
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.current_step: int = 1
        self.step_statuses: Dict[str, str] = {"1": "in_progress"}
        self.turn: int = 0
        self.last_result: Optional[Dict[str, Any]] = None
        self.history: List[Dict[str, Any]] = []

    def update(self, updates: Dict[str, Any]) -> None:
        """Merge key-value pairs into the accumulated state."""
        self.data.update(updates)

    def advance_step(self) -> None:
        """Mark current step completed and move to the next."""
        self.step_statuses[str(self.current_step)] = "completed"
        self.current_step += 1
        self.step_statuses[str(self.current_step)] = "in_progress"

    def set_last_result(self, result: Dict[str, Any]) -> None:
        """Store the most recent tool/action result and log it."""
        self.last_result = result
        self.history.append({"turn": self.turn, "result": result})
        self.turn += 1

    def get_step_history(self) -> List[Dict[str, Any]]:
        """Return step history summary for context messages."""
        history = []
        for step_num_str, status in sorted(self.step_statuses.items(), key=lambda x: int(x[0])):
            history.append({
                "step": int(step_num_str),
                "status": status,
            })
        return history

    def save(self, path: str = STATE_FILE) -> None:
        """Persist state to a JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {
            "data": self.data,
            "current_step": self.current_step,
            "step_statuses": self.step_statuses,
            "turn": self.turn,
            "last_result": self.last_result,
            "history": self.history,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str = STATE_FILE) -> "WorkflowState":
        """Restore state from a saved JSON file."""
        state = cls()
        if not os.path.exists(path):
            return state

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        state.data = payload.get("data", {})
        state.current_step = payload.get("current_step", 1)
        state.step_statuses = payload.get("step_statuses", {"1": "in_progress"})
        state.turn = payload.get("turn", 0)
        state.last_result = payload.get("last_result")
        state.history = payload.get("history", [])
        return state

    @staticmethod
    def reset() -> None:
        """Delete the persisted state file to start fresh."""
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
