"""
Validation utilities for file and folder checks.

This module provides validation functions for checking file existence,
file types (magic bytes), and resource completeness.
"""

import os
from typing import Dict, List
from project.src.utils.path_utils import (
    get_video_resources_folder,
    parse_time_script
)


def validate_folder_exists(folder_path: str) -> bool:
    """
    Checks if a folder exists.

    Args:
        folder_path: Absolute path to folder

    Returns:
        bool: True if folder exists, False otherwise
    """
    return os.path.exists(folder_path) and os.path.isdir(folder_path)


def validate_file_exists(file_path: str) -> bool:
    """
    Checks if a file exists.

    Args:
        file_path: Absolute path to file

    Returns:
        bool: True if file exists, False otherwise
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)


def validate_pdf(file_path: str) -> bool:
    """
    Validates that a file is a PDF by checking magic bytes.

    PDF files start with %PDF (bytes: 25 50 44 46)

    Args:
        file_path: Absolute path to file

    Returns:
        bool: True if file is a valid PDF, False otherwise
    """
    if not validate_file_exists(file_path):
        return False

    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except Exception:
        return False


def validate_image(file_path: str) -> bool:
    """
    Validates that a file is a JPG or PNG image by checking magic bytes.

    JPG files start with: FF D8 FF
    PNG files start with: 89 50 4E 47

    Args:
        file_path: Absolute path to file

    Returns:
        bool: True if file is a valid JPG or PNG, False otherwise
    """
    if not validate_file_exists(file_path):
        return False

    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)

            # Check for JPG (FF D8 FF)
            if len(header) >= 3 and header[:3] == b'\xff\xd8\xff':
                return True

            # Check for PNG (89 50 4E 47 0D 0A 1A 0A)
            if len(header) >= 4 and header[:4] == b'\x89PNG':
                return True

        return False
    except Exception:
        return False


def validate_video_resources_complete(video_uuid: str) -> Dict[str, any]:
    """
    Checks if all required files exist for a video project.

    Required files:
    - paper.pdf
    - script.txt
    - time_script.txt
    - generated_voice.mp3

    Args:
        video_uuid: UUID for the video project

    Returns:
        dict: {
            "complete": bool,
            "missing_files": list[str],
            "found_files": list[str]
        }
    """
    resources_folder = get_video_resources_folder(video_uuid)

    required_files = [
        "paper.pdf",
        "script.txt",
        "time_script.txt",
        "generated_voice.mp3"
    ]

    missing_files = []
    found_files = []

    for filename in required_files:
        file_path = os.path.join(resources_folder, filename)
        if validate_file_exists(file_path):
            found_files.append(filename)
        else:
            missing_files.append(filename)

    return {
        "complete": len(missing_files) == 0,
        "missing_files": missing_files,
        "found_files": found_files
    }


def validate_time_script_images_exist(video_uuid: str) -> Dict[str, any]:
    """
    Checks if all images referenced in time_script.txt exist.

    Args:
        video_uuid: UUID for the video project

    Returns:
        dict: {
            "all_exist": bool,
            "missing_images": list[str],
            "existing_images": list[str],
            "error": str (if time_script.txt is invalid)
        }
    """
    resources_folder = get_video_resources_folder(video_uuid)
    time_script_path = os.path.join(resources_folder, "time_script.txt")

    if not validate_file_exists(time_script_path):
        return {
            "all_exist": False,
            "missing_images": [],
            "existing_images": [],
            "error": f"time_script.txt not found at {time_script_path}"
        }

    try:
        parsed = parse_time_script(time_script_path)
    except Exception as e:
        return {
            "all_exist": False,
            "missing_images": [],
            "existing_images": [],
            "error": f"Failed to parse time_script.txt: {str(e)}"
        }

    missing_images = []
    existing_images = []

    for section in parsed["sections"]:
        image_filename = section["image_filename"]
        image_path = os.path.join(resources_folder, image_filename)

        if validate_file_exists(image_path):
            existing_images.append(image_filename)
        else:
            missing_images.append(image_filename)

    return {
        "all_exist": len(missing_images) == 0,
        "missing_images": missing_images,
        "existing_images": existing_images
    }


def validate_video_file(file_path: str) -> bool:
    """
    Validates that a file is a video file (basic check for .mp4 extension and existence).

    Args:
        file_path: Absolute path to video file

    Returns:
        bool: True if file exists and has .mp4 extension, False otherwise
    """
    if not validate_file_exists(file_path):
        return False

    return file_path.lower().endswith('.mp4')
