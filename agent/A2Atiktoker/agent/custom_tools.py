"""
Google ADK tool definitions for the A2A TikToker agent.

Imports all tools from the tools/ package and the validation utility,
wrapping each as a google.adk FunctionTool for use by LLM agents.
"""

from google.adk.tools import FunctionTool, google_search, tool #type: ignore

from tools.download_paper import download_paper
from tools.save_script import save_script
from tools.save_time_script import save_time_script
from tools.save_image_prompt import save_image_prompt
from tools.download_image import download_image
from tools.generate_images_runware import generate_images_runware
from tools.generate_video_ffmpeg import generate_video_ffmpeg
from tools.post_video_tiktok import post_video_tiktok
from tools.calculate_script_word_amount import calculate_script_word_amount
from tools.get_pdf_text import get_pdf_text
from tools.get_paper_topics import get_paper_topics
from project.src.utils.validation_utils import (
    validate_folder_exists,
    validate_file_exists,
    validate_pdf,
    validate_image,
    validate_video_resources_complete,
    validate_time_script_images_exist,
    validate_video_file,
)


# Tools from tools/ package
download_paper_tool = FunctionTool(download_paper)
save_script_tool = FunctionTool(save_script)
save_time_script_tool = FunctionTool(save_time_script)
save_image_prompt_tool = FunctionTool(save_image_prompt)
download_image_tool = FunctionTool(download_image)
generate_images_runware_tool = FunctionTool(generate_images_runware)
generate_video_ffmpeg_tool = FunctionTool(generate_video_ffmpeg)
post_video_tiktok_tool = FunctionTool(post_video_tiktok)
calculate_script_word_amount_tool = FunctionTool(calculate_script_word_amount)
get_pdf_text_tool = FunctionTool(get_pdf_text)
get_paper_topics_tool = FunctionTool(get_paper_topics)

# Validation tools
validate_folder_exists_tool = FunctionTool(validate_folder_exists)
validate_file_exists_tool = FunctionTool(validate_file_exists)
validate_pdf_tool = FunctionTool(validate_pdf)
validate_image_tool = FunctionTool(validate_image)
validate_video_resources_complete_tool = FunctionTool(validate_video_resources_complete)
validate_time_script_images_exist_tool = FunctionTool(validate_time_script_images_exist)
validate_video_file_tool = FunctionTool(validate_video_file)

ALL_TOOLS = [
    download_paper_tool,
    save_script_tool,
    save_time_script_tool,
    save_image_prompt_tool,
    download_image_tool,
    generate_images_runware_tool,
    generate_video_ffmpeg_tool,
    post_video_tiktok_tool,
    calculate_script_word_amount_tool,
    get_pdf_text_tool,
    get_paper_topics_tool,
    validate_folder_exists_tool,
    validate_file_exists_tool,
    validate_pdf_tool,
    validate_image_tool,
    validate_video_resources_complete_tool,
    validate_time_script_images_exist_tool,
    validate_video_file_tool,
    google_search,
]

ARTICLE_DISCOVERY_AGENT_TOOLS = [
    google_search,
    get_paper_topics_tool,
    download_paper_tool,
]

INSIGHTS_GENERATOR_AGENT_TOOLS = [
    get_pdf_text_tool,
]

VIDEO_SCRIPT_GENERATOR_AGENT_TOOLS = [
    get_pdf_text_tool,
    save_script_tool,
    save_time_script_tool,
]

PROMPT_ENHANCER_AGENT_TOOLS = [
    save_image_prompt_tool,
]

IMAGE_GENERATOR_AGENT_TOOLS = [
    download_image_tool,
    google_search,
]
