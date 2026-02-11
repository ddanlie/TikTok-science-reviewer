"""
Tool for saving video script text files.

This tool saves the pure text script for TikTok video narration.
"""

import os
from typing import Dict
from project.src.utils.path_utils import get_video_resources_folder
from project.src.utils.validation_utils import validate_folder_exists
from project.src.utils.error_utils import create_error_response, create_success_response


def save_script(script_content: str, video_uuid: str) -> Dict:
    """
    Saves the video script as pure text.

    The script should be clean text suitable for voice generation,
    with no comments, no extra symbols, and proper intonation written out.

    Args:
        script_content: Pure text script for TikTok video
        video_uuid: UUID for the video project

    Returns:
        dict: {
            "success": bool,
            "file_path": str (absolute path to script.txt),
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

        # Construct output file path
        output_file = os.path.join(resources_folder, "script.txt")

        # Save the script with UTF-8 encoding
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # Success
        return create_success_response({
            "file_path": output_file
        })

    except Exception as e:
        return create_error_response(
            f"Failed to save script",
            details={"error": str(e)}
        )
