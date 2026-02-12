from google.adk.tools import google_search #type: ignore
from google.adk.agents import (
    LlmAgent,
    LoopAgent,
    ParallelAgent,
    SequentialAgent,
)
from custom_tools import (
    ARTICLE_DISCOVERY_AGENT_TOOLS,
    INSIGHTS_GENERATOR_AGENT_TOOLS,
    VIDEO_SCRIPT_GENERATOR_AGENT_TOOLS,
)
from google.genai import types
from . import instructions
from uuid import uuid4


MODEL_NAME = "gemini-2.0-flash"

KEY_SCRIPT_INSIGHTS = "script_insights"
KEY_SCRIPT_TEXTS = "script_texts"
KEY_CURRENT_PROJECT_VIDEO_UUID = "current_project_video_uuid"

ARTICLE_DISCOVERY_AGENT_MAX_TOOL_CALLS = len(ARTICLE_DISCOVERY_AGENT_TOOLS) * 3 # 3 cycles of full tools list usage

def set_initial_state_variables(callback_context, llm_request):
    callback_context.state[KEY_CURRENT_PROJECT_VIDEO_UUID] = f"{str(uuid4()).split("-")[0]}"

def after_article_discoverer_tool(tool, result, context):
    context.state["_article_discoverer_agent_tool_call_count"] = context.get("_article_discoverer_agent_tool_call_count", 0) + 1
    if context["_article_discoverer_agent_tool_call_count"] >= MAX_TOOL_CALLS:
        context["_stop_tools"] = True  # flag to stop further calls

video_script_generator_agent = LlmAgent(
    name="ScriptGeneratorAgent",
    model=MODEL_NAME,
    instruction=instructions.,
    description="",
    output_key=KEY_SCRIPT_TEXTS,
    tools=VIDEO_SCRIPT_GENERATOR_AGENT_TOOLS
)

insights_generator_agent = LlmAgent(
    name="InsightsGeneratorAgent",
    model=MODEL_NAME,
    instruction=instructions.INSIGHTS_GENERATOR_AGENT_INSTRUCTIONS,
    description="Analyses the article and comes up with ideas and insights for the video script",
    output_key=KEY_SCRIPT_INSIGHTS,
    tools=INSIGHTS_GENERATOR_AGENT_TOOLS #type: ignore
)

article_discovery_agent = LlmAgent(
    name="ArticleDiscoveryAgent",
    model=MODEL_NAME,
    instruction=instructions.ARTICLE_DISCOVERY_AGENT_INSTRUCTIONS,
    description="Discovers articles for given topics and downloads a pdf paper",


    tools=ARTICLE_DISCOVERY_AGENT_TOOLS
)

video_resources_generation_workflow = SequentialAgent(
    name="VideoResourcesGenerationWorkflow",
    description="Runs sequence of actions",
    sub_agents=[
        article_discovery_agent, 
        insights_generator_agent,
        video_script_generator_agent,
    ]
)

coordinator_agent = LlmAgent(
    name="CoordinatorAgent",
    model=MODEL_NAME,
    instruction=instructions.COORDINATOR_AGENT_INSTRUCTIONS,
    before_model_callback=set_initial_state_variables,
    description="Coordinates work of article review tiktok video creation",
    sub_agents=[video_resources_generation_workflow]
)

root_agent = SequentialAgent(
    name="RootWorkflow",
    sub_agents=[coordinator_agent],
    description="End-to-end video generation pipeline",
)