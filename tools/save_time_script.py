"""
Tool for saving time-stamped image script files.

This tool saves the time script that coordinates images with timestamps
for video generation.
"""

import os
from typing import Dict
from project.src.utils.path_utils import get_video_resources_folder, parse_time_script
from project.src.utils.validation_utils import validate_folder_exists
from project.src.utils.error_utils import create_error_response, create_success_response


def save_time_script(time_script_content: str, video_uuid: str) -> Dict:
    """
    Saves time script with duration and image timestamps.

    Expected format:
        Line 1: Total duration in seconds (e.g., "45" or "45.5")
        Lines 2+: "timestamp|image_filename" (e.g., "0.0|paper_image_001_found.jpg")

    Args:
        time_script_content: Multi-line string with format described above
        video_uuid: UUID for the video project

    Returns:
        dict: {
            "success": bool,
            "file_path": str (absolute path to time_script.txt),
            "parsed_sections": list (parsed sections for validation),
            "duration": float (total duration),
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
        output_file = os.path.join(resources_folder, "time_script.txt")

        # Save the time script with UTF-8 encoding
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(time_script_content)

        # Validate format by parsing
        try:
            parsed = parse_time_script(output_file)
        except ValueError as e:
            # Delete invalid file
            try:
                os.remove(output_file)
            except:
                pass

            return create_error_response(
                f"Time script format is invalid: {str(e)}",
                details={"expected_format": "Line 1: duration\\nLines 2+: timestamp|filename"}
            )

        # Success - return with parsed data for validation
        return create_success_response({
            "file_path": output_file,
            "parsed_sections": parsed["sections"],
            "duration": parsed["duration"]
        })

    except Exception as e:
        return create_error_response(
            f"Failed to save time script",
            details={"error": str(e)}
        )
