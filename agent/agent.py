from google.adk.tools import google_search #type: ignore
from google.adk.agents import (
    LlmAgent,
    LoopAgent,
    ParallelAgent,
    SequentialAgent,
)
from .custom_tools import (
    ARTICLE_DISCOVERY_AGENT_TOOLS,
    INSIGHTS_GENERATOR_AGENT_TOOLS,
    VIDEO_SCRIPT_GENERATOR_AGENT_TOOLS,
    PROMPT_ENHANCER_AGENT_TOOLS,
    IMAGE_GENERATOR_AGENT_TOOLS,
    IMAGE_PURE_GENERATOR_AGENT_TOOLS,
    calculate_script_word_amount,
    generate_video_ffmpeg,

)
from project.src.utils.path_utils import get_ffmpeg_path, get_video_resources_folder
from google.genai import types
from google.adk.models import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from pydantic import BaseModel
from . import instructions
from uuid import uuid4
from dotenv import load_dotenv
from typing import AsyncGenerator
import os
import time
import re
import json
from ollama import chat

load_dotenv("./project/src/.env")


class OllamaLlm(BaseLlm):
    """Adapter to use Ollama as the agent LLM."""

    @staticmethod
    def _lower_types(obj: object) -> object:
        if isinstance(obj, dict):
            return {k: (v.lower() if k == "type" and isinstance(v, str) else OllamaLlm._lower_types(v)) for k, v in obj.items()}
        if isinstance(obj, list):
            return [OllamaLlm._lower_types(i) for i in obj]
        return obj

    @staticmethod
    def _schema_to_json_schema(schema: types.Schema) -> dict:
        return dict(OllamaLlm._lower_types(schema.to_json_dict())) # type: ignore[arg-type]

    def _convert_tools(self, llm_request: LlmRequest) -> list[dict] | None:
        if not llm_request.config or not llm_request.config.tools:
            return None
        ollama_tools = []
        for tool in llm_request.config.tools:
            if not isinstance(tool, types.Tool):
                continue
            for fd in (tool.function_declarations or []):
                params = self._schema_to_json_schema(fd.parameters) if fd.parameters else {}
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": fd.name,
                        "description": fd.description or "",
                        "parameters": params,
                    },
                })
        return ollama_tools or None

    def _build_messages(self, llm_request: LlmRequest) -> list[dict]:
        messages = []
        if llm_request.config and llm_request.config.system_instruction:
            si = llm_request.config.system_instruction
            if isinstance(si, types.Content) and si.parts:
                system_text = si.parts[0].text or ""
            else:
                system_text = str(si)
            messages.append({"role": "system", "content": system_text})

        for content in (llm_request.contents or []):
            for part in (content.parts or []):
                if part.function_call:
                    messages.append({
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{
                            "function": {
                                "name": part.function_call.name,
                                "arguments": part.function_call.args or {},
                            }
                        }],
                    })
                elif part.function_response:
                    messages.append({
                        "role": "tool",
                        "content": str(part.function_response.response),
                    })
                elif part.text:
                    role = "assistant" if content.role == "model" else content.role
                    messages.append({"role": role, "content": part.text})
        return messages

    def _get_tool_names(self, llm_request: LlmRequest) -> set[str]:
        names: set[str] = set()
        if not llm_request.config or not llm_request.config.tools:
            return names
        for tool in llm_request.config.tools:
            if isinstance(tool, types.Tool):
                for fd in (tool.function_declarations or []):
                    if fd.name:
                        names.add(fd.name)
        return names

    def _parse_text_tool_calls(self, text: str, tool_names: set[str]) -> list[types.Part]:
        """Fallback: parse tool calls that the model wrote as plain text."""
        parts: list[types.Part] = []
        pattern = r'(\w+)\(([^)]*)\)'
        for match in re.finditer(pattern, text):
            fn_name, raw_args = match.group(1), match.group(2).strip()
            if fn_name not in tool_names:
                continue
            args: dict = {}
            if raw_args:
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    for kv in raw_args.split(","):
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            args[k.strip()] = v.strip().strip("'\"")
                        else:
                            args["agent_name"] = raw_args.strip().strip("'\"")
            parts.append(types.Part(
                function_call=types.FunctionCall(name=fn_name, args=args)
            ))
        return parts

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        messages = self._build_messages(llm_request)
        tools = self._convert_tools(llm_request)

        kwargs: dict = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools

        response = chat(**kwargs)

        parts: list[types.Part] = []
        if response.message.tool_calls:
            for tc in response.message.tool_calls:
                parts.append(types.Part(
                    function_call=types.FunctionCall(
                        name=tc.function.name,
                        args=dict(tc.function.arguments) if tc.function.arguments else {},
                    )
                ))

        text = response.message.content or ""
        # Strip qwen3 thinking tags
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        # Fallback: if no structured tool calls, try parsing from text
        if not parts and text:
            tool_names = self._get_tool_names(llm_request)
            parsed = self._parse_text_tool_calls(text, tool_names)
            if parsed:
                parts.extend(parsed)
            else:
                parts.append(types.Part(text=text))
        elif text:
            parts.append(types.Part(text=text))

        yield LlmResponse(
            content=types.Content(role="model", parts=parts)
        )

MODEL_NAME = OllamaLlm(model="deepseek-v3.1:671b-cloud")#OllamaLlm(model="qwen3-vl:235b-cloud")#OllamaLlm(model="qwen3:8b")

KEY_CURRENT_PROJECT_VIDEO_UUID = "current_project_video_uuid"
KEY_SCRIPT_INSIGHTS = "script_insights"
KEY_DRAFT_PROMPTS = "draft_prompts"
KEY_PROMPTS = "prompts"

KEY_TO_DOWNLOAD = "to_download"

ARTICLE_DISCOVERY_AGENT_MAX_TOOL_CALLS = len(ARTICLE_DISCOVERY_AGENT_TOOLS) * 3 # 3 cycles of full tools list usage

CURRENT_UUID = None

class InsightsSchema(BaseModel):
    duration: int
    hook: str
    sequential_inspiration: list[str]
    illustrations_insights: list[str]


class ImgPromptsSchema(BaseModel):
    class ImagePromptAndNameSchema(BaseModel):
        id: str
        prompt: str
        is_real: bool
    drafts: list[ImagePromptAndNameSchema]


class ImgPromptsSchema2(BaseModel):
    class ImagePromptAndNameSchema(BaseModel):
        id: str
        prompt: str
    drafts: list[ImagePromptAndNameSchema]

def after_any_tool_delay(tool, args, tool_context, tool_response):
    time.sleep(2)
    tool_context.state[KEY_CURRENT_PROJECT_VIDEO_UUID] = CURRENT_UUID

def before_any_agent_delay(callback_context):
    time.sleep(2)
    callback_context.state[KEY_CURRENT_PROJECT_VIDEO_UUID] = CURRENT_UUID

def set_initial_state_variables(callback_context):
    global CURRENT_UUID
    callback_context.state[KEY_CURRENT_PROJECT_VIDEO_UUID] = f"{str(uuid4()).split("-")[0]}"
    CURRENT_UUID = callback_context.state[KEY_CURRENT_PROJECT_VIDEO_UUID]

def after_article_discovery_agent_tool(tool, args, tool_context, tool_response):
    tool_context.state["_article_discoverer_agent_tool_call_count"] = tool_context.state.get("_article_discoverer_agent_tool_call_count", 0) + 1
    if tool_context.state["_article_discoverer_agent_tool_call_count"] >= ARTICLE_DISCOVERY_AGENT_MAX_TOOL_CALLS:
        tool_context.state["_stop_tools"] = True  # flag to stop further calls

def after_insights_generator_agent(callback_context):
    callback_context.state["words_amount"] = calculate_script_word_amount(
        callback_context.state[KEY_SCRIPT_INSIGHTS]["duration"]
    )["words_amount"]

def after_continuer_agent(callback_context):
    global CURRENT_UUID
    CURRENT_UUID = callback_context.state[KEY_CURRENT_PROJECT_VIDEO_UUID]

def after_coordinator_agent(callback_context):
    pass
    # can't generate it yet - voice need to generate
    # uuid = callback_context.state[KEY_CURRENT_PROJECT_VIDEO_UUID]
    # generate_video_ffmpeg(uuid, get_ffmpeg_path())

def after_scripts_generator_agent(callback_context):
    tmp = callback_context.state[KEY_DRAFT_PROMPTS]
    callback_context.state[KEY_DRAFT_PROMPTS] = [
        {
            "id": draft["id"],
            "prompt": draft["prompt"]
        }
        for draft in tmp["drafts"]
    ]
    callback_context.state[KEY_TO_DOWNLOAD] = [
        {
            "id": draft["id"],
            "prompt": draft["prompt"]
        }
        for draft in tmp["drafts"]
        if draft["is_real"] is True
    ]

image_generator_agent = LlmAgent(
    name="ImageGeneratorAgent",
    model=MODEL_NAME,
    instruction=instructions.IMAGE_GENERATOR_AGENT_INSTRUCTIONS,
    description="Generates AI images via Runware and downloads real images from the internet",
    tools=IMAGE_GENERATOR_AGENT_TOOLS, #type: ignore
    before_agent_callback=before_any_agent_delay,
    after_tool_callback=after_any_tool_delay,
)

prompt_enhancer_agent = LlmAgent(
    name="PromptEnhancerAgent",
    model=MODEL_NAME,
    instruction=instructions.PROMPT_ENHANCER_AGENT_INSTRUCITONS,
    description="Enhances draft image prompts into professional generation-ready prompts and saves them",
    output_key=KEY_PROMPTS,
    output_schema=ImgPromptsSchema2,
    tools=PROMPT_ENHANCER_AGENT_TOOLS, #type: ignore
    before_agent_callback=before_any_agent_delay,
    after_tool_callback=after_any_tool_delay,
)

video_script_generator_agent = LlmAgent(
    name="ScriptGeneratorAgent",
    model=MODEL_NAME,
    instruction=instructions.VIDEO_SCRIPT_GENERATOR_AGENT_INSTRUCTIONS,
    description="Reviews insights, generates 2 scripts - text and image time sequence, makes images prompt drafts",
    output_key=KEY_DRAFT_PROMPTS,
    output_schema=ImgPromptsSchema,
    before_agent_callback=before_any_agent_delay,
    after_agent_callback=after_scripts_generator_agent,
    after_tool_callback=after_any_tool_delay,
    tools=VIDEO_SCRIPT_GENERATOR_AGENT_TOOLS #type: ignore
)

insights_generator_agent = LlmAgent(
    name="InsightsGeneratorAgent",
    model=MODEL_NAME,
    instruction=instructions.INSIGHTS_GENERATOR_AGENT_INSTRUCTIONS,
    description="Analyses the article and comes up with ideas and insights for the video script",
    output_key=KEY_SCRIPT_INSIGHTS,
    output_schema=InsightsSchema,
    before_agent_callback=before_any_agent_delay,
    after_agent_callback=after_insights_generator_agent,
    after_tool_callback=after_any_tool_delay,
    tools=INSIGHTS_GENERATOR_AGENT_TOOLS #type: ignore
)

article_discovery_agent = LlmAgent(
    name="ArticleDiscoveryAgent",
    model=MODEL_NAME,
    instruction=instructions.ARTICLE_DISCOVERY_AGENT_INSTRUCTIONS,
    before_agent_callback=before_any_agent_delay,
    after_tool_callback=[after_article_discovery_agent_tool, after_any_tool_delay],
    description="Discovers articles for given topics and downloads a pdf paper",
    tools=ARTICLE_DISCOVERY_AGENT_TOOLS,
)

video_resources_generation_workflow = SequentialAgent(
    name="VideoResourcesGenerationWorkflow",
    description="Runs sequence of actions",
    sub_agents=[
        article_discovery_agent,
        insights_generator_agent,
        video_script_generator_agent,
        prompt_enhancer_agent,
        image_generator_agent,
    ]
)

continuer_insights_agent = LlmAgent(
    name="ContinuerInsightsAgent",
    model=MODEL_NAME,
    instruction=instructions.INSIGHTS_GENERATOR_AGENT_INSTRUCTIONS,
    description="Analyses the article and comes up with ideas and insights for the video script",
    output_key=KEY_SCRIPT_INSIGHTS,
    output_schema=InsightsSchema,
    before_agent_callback=before_any_agent_delay,
    after_agent_callback=after_insights_generator_agent,
    after_tool_callback=after_any_tool_delay,
    tools=INSIGHTS_GENERATOR_AGENT_TOOLS #type: ignore
)

continuer_script_generator_agent = LlmAgent(
    name="ContinuerScriptGeneratorAgent",
    model=MODEL_NAME,
    instruction=instructions.VIDEO_SCRIPT_GENERATOR_AGENT_INSTRUCTIONS,
    description="Reviews insights, generates 2 scripts - text and image time sequence, makes images prompt drafts",
    output_key=KEY_DRAFT_PROMPTS,
    output_schema=ImgPromptsSchema,
    before_agent_callback=before_any_agent_delay,
    after_agent_callback=after_scripts_generator_agent,
    after_tool_callback=after_any_tool_delay,
    tools=VIDEO_SCRIPT_GENERATOR_AGENT_TOOLS #type: ignore
)

continuer_prompt_enhancer_agent = LlmAgent(
    name="ContinuerPromptEnhancerAgent",
    model=MODEL_NAME,
    instruction=instructions.PROMPT_ENHANCER_AGENT_INSTRUCITONS,
    description="Enhances draft image prompts into professional generation-ready prompts and saves them",
    output_key=KEY_PROMPTS,
    output_schema=ImgPromptsSchema2,
    tools=PROMPT_ENHANCER_AGENT_TOOLS, #type: ignore
    before_agent_callback=before_any_agent_delay,
    after_tool_callback=after_any_tool_delay,
)

continuer_image_generator_agent = LlmAgent(
    name="ContinuerImageGeneratorAgent",
    model=MODEL_NAME,
    instruction=instructions.IMAGE_GENERATOR_AGENT_INSTRUCTIONS,
    description="Generates AI images via Runware and downloads real images from the internet",
    tools=IMAGE_GENERATOR_AGENT_TOOLS, #type: ignore
    before_agent_callback=before_any_agent_delay,
    after_tool_callback=after_any_tool_delay,
)

continuer_insights_sequential_agent = SequentialAgent(
    name="ContinuerInsightsSequentialAgent",
    sub_agents=[
        continuer_insights_agent,
        continuer_script_generator_agent,
        continuer_prompt_enhancer_agent,
        continuer_image_generator_agent,
    ],
    description="Runs insights through full pipeline when continuing a project",
)

continuer_image_pure_generator_agent = LlmAgent(
    name="ContinuerImagePureGeneratorAgent",
    model=MODEL_NAME,
    instruction=instructions.IMAGE_PURE_GENERATOR_AGENT_INSTRUCTIONS,
    description="Generates AI images",
    tools=IMAGE_PURE_GENERATOR_AGENT_TOOLS, #type: ignore
    before_agent_callback=before_any_agent_delay,
    after_tool_callback=after_any_tool_delay,
)

def bnnefore_project_continuer_agent(callback_context):
    callback_context.state[KEY_CURRENT_PROJECT_VIDEO_UUID] = None
    
project_continuer_agent = LlmAgent(
    name="ProjecctContinuerAgent",
    model=MODEL_NAME, #type: ignore
    instruction=instructions.CONTINUER_AGENT_INSTRUCTIONS,
    before_agent_callback=[bnnefore_project_continuer_agent, before_any_agent_delay],
    description="Finds out what stage user project failed on and transfers to corresponding agent",
    sub_agents=[
        continuer_insights_sequential_agent,
        continuer_image_pure_generator_agent
    ],
    output_key=KEY_CURRENT_PROJECT_VIDEO_UUID,
    after_agent_callback=after_continuer_agent,
    after_tool_callback=after_any_tool_delay,
)

coordinator_agent = LlmAgent(
    name="CoordinatorAgent",
    model=MODEL_NAME, #type: ignore
    instruction=instructions.COORDINATOR_AGENT_INSTRUCTIONS,
    before_agent_callback=[before_any_agent_delay, set_initial_state_variables],
    after_agent_callback=after_coordinator_agent,
    description="Coordinates work of article review tiktok video creation. If asked to continue the work - uses continuer agent.",
    sub_agents=[video_resources_generation_workflow, project_continuer_agent],
    after_tool_callback=after_any_tool_delay,
)

root_agent = SequentialAgent(
    name="RootWorkflow",
    sub_agents=[coordinator_agent],
    description="End-to-end video generation pipeline",
)