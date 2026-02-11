"""
Tool registry mapping tool names to Python callables.

Handles lazy imports, parameter validation, and execution.
All tools return Dict with a 'success' field per project convention.
"""

import importlib
from typing import Any, Callable, Dict, List


TOOL_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "download_paper": {
        "module": "tools.download_paper",
        "function": "download_paper",
        "params": [
            {"name": "url", "type": "str", "required": True},
            {"name": "video_uuid", "type": "str", "required": True},
            {"name": "timeout", "type": "int", "required": False, "default": 30},
        ],
    },
    "save_script": {
        "module": "tools.save_script",
        "function": "save_script",
        "params": [
            {"name": "script_content", "type": "str", "required": True},
            {"name": "video_uuid", "type": "str", "required": True},
        ],
    },
    "save_time_script": {
        "module": "tools.save_time_script",
        "function": "save_time_script",
        "params": [
            {"name": "time_script_content", "type": "str", "required": True},
            {"name": "video_uuid", "type": "str", "required": True},
        ],
    },
    "save_image_prompt": {
        "module": "tools.save_image_prompt",
        "function": "save_image_prompt",
        "params": [
            {"name": "prompt_text", "type": "str", "required": True},
            {"name": "image_id", "type": "str", "required": True},
            {"name": "video_uuid", "type": "str", "required": True},
        ],
    },
    "download_image": {
        "module": "tools.download_image",
        "function": "download_image",
        "params": [
            {"name": "url", "type": "str", "required": True},
            {"name": "video_uuid", "type": "str", "required": True},
            {"name": "image_type", "type": "str", "required": False, "default": "found"},
            {"name": "timeout", "type": "int", "required": False, "default": 30},
        ],
    },
    "generate_images_runware": {
        "module": "tools.generate_images_runware",
        "function": "generate_images_runware",
        "params": [
            {"name": "video_uuid", "type": "str", "required": True},
            {"name": "timeout_per_image", "type": "int", "required": False, "default": 30},
        ],
    },
    "generate_video_ffmpeg": {
        "module": "tools.generate_video_ffmpeg",
        "function": "generate_video_ffmpeg",
        "params": [
            {"name": "video_uuid", "type": "str", "required": True},
            {"name": "ffmpeg_path", "type": "str", "required": False, "default": None},
        ],
    },
    "post_video_tiktok": {
        "module": "tools.post_video_tiktok",
        "function": "post_video_tiktok",
        "params": [
            {"name": "video_path", "type": "str", "required": True},
            {"name": "title", "type": "str", "required": False, "default": ""},
            {"name": "hashtags", "type": "list", "required": False, "default": None},
        ],
    },
    "calculate_script_word_amount": {
        "module": "tools.calculate_script_word_amount",
        "function": "calculate_script_word_amount",
        "params": [
            {"name": "duration", "type": "int", "required": True},
        ],
    },
    "validate_time_script_images_exist": {
        "module": "project.src.utils.validation_utils",
        "function": "validate_time_script_images_exist",
        "params": [
            {"name": "video_uuid", "type": "str", "required": True},
        ],
    },
}

# Maps successful tool results to state keys for auto-extraction
AUTO_STATE_KEYS: Dict[str, Dict[str, str]] = {
    "download_paper": {"file_path": "paper_path", "folder_path": "resources_folder"},
    "save_script": {"file_path": "script_path"},
    "save_time_script": {"file_path": "time_script_path"},
    "generate_images_runware": {"generated_images": "generated_images", "failed_prompts": "failed_prompts"},
}


class ToolRegistry:
    def __init__(self):
        self._cache: Dict[str, Callable] = {}

    def get_tool_info(self) -> List[Dict[str, Any]]:
        """Return tool info dicts for the context message."""
        return [
            {
                "name": name,
                "params": [
                    {
                        "name": p["name"],
                        "required": p["required"],
                        "default": p.get("default"),
                    }
                    for p in defn["params"]
                ],
            }
            for name, defn in TOOL_DEFINITIONS.items()
        ]

    def execute(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with the given parameters.

        Returns the tool's Dict result. Never raises — errors are
        returned as {"success": False, "error": "..."}.
        """
        if tool_name not in TOOL_DEFINITIONS:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        defn = TOOL_DEFINITIONS[tool_name]

        # Validate required params
        for p in defn["params"]:
            if p["required"] and p["name"] not in params:
                return {
                    "success": False,
                    "error": f"Missing required parameter '{p['name']}' for tool '{tool_name}'",
                }

        # Build call params with defaults
        call_params = {}
        for p in defn["params"]:
            if p["name"] in params:
                call_params[p["name"]] = params[p["name"]]
            elif not p["required"]:
                call_params[p["name"]] = p.get("default")

        # Lazy import and call
        if tool_name not in self._cache:
            try:
                module = importlib.import_module(defn["module"])
                self._cache[tool_name] = getattr(module, defn["function"])
            except Exception as e:
                return {"success": False, "error": f"Failed to import tool '{tool_name}': {e}"}

        try:
            return self._cache[tool_name](**call_params)
        except Exception as e:
            return {"success": False, "error": f"Tool execution error: {e}"}

    def get_auto_state_updates(self, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract state updates from a successful tool result."""
        if not result.get("success") or tool_name not in AUTO_STATE_KEYS:
            return {}

        updates = {}
        for result_key, state_key in AUTO_STATE_KEYS[tool_name].items():
            if result_key in result:
                updates[state_key] = result[result_key]
        return updates
