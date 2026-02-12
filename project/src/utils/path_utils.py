"""
Path utilities for consistent file and folder path management.

This module provides centralized path and naming logic used by all tools
to ensure consistent file structure across the project.
"""

import os
from datetime import datetime
from uuid import uuid4


def get_project_root() -> str:
    """
    Returns the absolute path to the project root directory.

    Returns:
        str: Absolute path to project root
    """
    # Navigate up from utils/ -> src/ -> project/ -> root/
    current_file = os.path.abspath(__file__)
    utils_dir = os.path.dirname(current_file)
    src_dir = os.path.dirname(utils_dir)
    project_dir = os.path.dirname(src_dir)
    root_dir = os.path.dirname(project_dir)
    return root_dir


def get_current_date_string() -> str:
    """
    Returns current date in YYYYMMDD format.

    Returns:
        str: Date string (e.g., "20260210")
    """
    return datetime.now().strftime("%Y%m%d")


def get_video_resources_folder_name(video_uuid: str) -> str:
    """
    Generates the video resources folder name.

    Args:
        video_uuid: UUID for the video project

    Returns:
        str: Folder name in format "video_{YYYYMMDD}_{uuid}_resources"
    """
    date_str = get_current_date_string()
    return f"video_{date_str}_{video_uuid}_resources"


def get_video_resources_folder(video_uuid: str) -> str:
    """
    Returns the absolute path to the video resources folder.

    Args:
        video_uuid: UUID for the video project

    Returns:
        str: Absolute path to video resources folder
    """
    root = get_project_root()
    folder_name = get_video_resources_folder_name(video_uuid)
    return os.path.join(root, "project", "resources", folder_name)


def get_videos_folder() -> str:
    """
    Returns the absolute path to the videos output folder.

    Returns:
        str: Absolute path to project/videos/ folder
    """
    root = get_project_root()
    return os.path.join(root, "project", "videos")


def get_ffmpeg_path() -> str:
    """
    Returns the absolute path to ffmpeg.exe in dependencies folder.

    Returns:
        str: Absolute path to ffmpeg.exe
    """
    root = get_project_root()
    return os.path.join(root, "dependencies", "ffmpeg", "bin", "ffmpeg.exe")


def get_pdftotext_path() -> str:
    """
    Returns the absolute path to pdftotext.exe in dependencies folder.

    Returns:
        str: Absolute path to pdftotext.exe
    """
    root = get_project_root()
    return os.path.join(root, "dependencies", "pdftotext", "pdftotext.exe")


def generate_image_filename(image_id: str, extension: str = "jpg") -> str: #type: ignore
    """
    Generates a standardized image filename.

    Args:
        image_id: Specific ID for the image
        extension: File extension without dot (default: "jpg")

    Returns:
        str: Filename in format "paper_image_{id}_generated.{ext}"
    """
    return f"paper_image_{image_id}_generated.{extension}"


def generate_video_filename(video_uuid: str) -> str:
    """
    Generates the output video filename.

    Args:
        video_uuid: UUID for the video project

    Returns:
        str: Filename in format "video_{YYYYMMDD}_{uuid}.mp4"
    """
    date_str = get_current_date_string()
    return f"video_{date_str}_{video_uuid}.mp4"


def parse_time_script(file_path: str) -> dict:
    """
    Parses time_script.txt file into structured data.

    Expected format:
        Line 1: Total duration in seconds (float or int)
        Lines 2+: "timestamp|image_filename" (e.g., "0.0|paper_image_001_generated.jpg")

    Args:
        file_path: Absolute path to time_script.txt

    Returns:
        dict: {
            "duration": float,
            "sections": [
                {"timestamp": float, "image_filename": str},
                ...
            ]
        }

    Raises:
        ValueError: If file format is invalid
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Time script file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if len(lines) < 2:
        raise ValueError("Time script must have at least 2 lines (duration + 1 section)")

    # Parse duration from first line
    try:
        duration = float(lines[0].strip())
    except ValueError:
        raise ValueError(f"First line must be a number (duration in seconds), got: {lines[0].strip()}")

    # Parse sections from remaining lines
    sections = []
    for i, line in enumerate(lines[1:], start=2):
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        if '|' not in line:
            raise ValueError(f"Line {i} must contain '|' separator: {line}")

        parts = line.split('|', 1)
        if len(parts) != 2:
            raise ValueError(f"Line {i} must have format 'timestamp|filename': {line}")

        try:
            timestamp = float(parts[0].strip())
        except ValueError:
            raise ValueError(f"Line {i} timestamp must be a number, got: {parts[0].strip()}")

        image_filename = parts[1].strip()
        if not image_filename:
            raise ValueError(f"Line {i} has empty filename")

        sections.append({
            "timestamp": timestamp,
            "image_filename": image_filename
        })

    if not sections:
        raise ValueError("Time script must have at least one image section")

    return {
        "duration": duration,
        "sections": sections
    }


def get_readonly_sources_path() -> str:
    """
    Returns the absolute path to readonly_sources_of_truth folder.

    Returns:
        str: Absolute path to readonly_sources_of_truth/
    """
    root = get_project_root()
    return os.path.join(root, "readonly_sources_of_truth")


def get_env_file_path() -> str:
    """
    Returns the absolute path to .env file in readonly_sources_of_truth.

    Returns:
        str: Absolute path to .env file
    """
    return os.path.join(get_readonly_sources_path(), ".env")


def get_project_env_file_path() -> str:
    """
    Returns the absolute path to .env file in project/src/.

    Returns:
        str: Absolute path to project/src/.env
    """
    root = get_project_root()
    return os.path.join(root, "project", "src", ".env")
