"""
Tool for saving image generation prompts.

This tool saves prompts that will be used by Runware AI to generate images.
"""

import os
from typing import Dict
from project.src.utils.path_utils import get_video_resources_folder
from project.src.utils.validation_utils import validate_folder_exists
from project.src.utils.error_utils import create_error_response, create_success_response


def save_image_prompt(prompt_text: str, image_id: str, video_uuid: str) -> Dict:
    """
    Saves an image generation prompt for Runware AI.

    The prompt should be carefully crafted for a weak but fast generation model,
    with clear style, scene description, and minimal text generation reliance.

    Args:
        prompt_text: Detailed prompt for image generation
        image_id: Specific ID for this image (e.g., "001", "abc123")
        video_uuid: UUID for the video project

    Returns:
        dict: {
            "success": bool,
            "file_path": str (absolute path to prompt file),
            "expected_output_filename": str (e.g., "paper_image_001_generated.png"),
            "error": str (if success=False)
        }
    """
    try:
        # Get resources folder path
        resources_folder = get_video_resources_folder(video_uuid)

        # Check if folder exists
        if not validate_folder_exists(resources_folder):
            return create_error_response(
                f"Video resources folder does not exist: {resources_folder}",
                details={"solution": "Run download_paper first to create the folder"}
            )

        # Construct prompt file path
        prompt_filename = f"paper_image_{image_id}_prompt.txt"
        prompt_file = os.path.join(resources_folder, prompt_filename)

        # Save the prompt with UTF-8 encoding
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_text)

        # Expected output filename for coordination
        expected_output = f"paper_image_{image_id}_generated.png"

        # Success
        return create_success_response({
            "file_path": prompt_file,
            "expected_output_filename": expected_output
        })

    except Exception as e:
        return create_error_response(
            f"Failed to save image prompt",
            details={"error": str(e)}
        )
