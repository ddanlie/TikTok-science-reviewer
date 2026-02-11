"""
Tool for downloading images from URLs.

This tool downloads images with proper naming convention for found images
that will be used in video generation.
"""

import os
import requests
from uuid import uuid4
from typing import Dict
from project.src.utils.path_utils import get_video_resources_folder, generate_image_filename
from project.src.utils.validation_utils import validate_image, validate_folder_exists
from project.src.utils.error_utils import create_error_response, create_success_response


def download_image(url: str, video_uuid: str, image_type: str = "found", timeout: int = 30) -> Dict:
    """
    Downloads an image from URL with proper naming convention.

    The image is validated to ensure it's a valid JPG or PNG file.
    Filename format: paper_image_{uuid4}_{type}.{ext}

    Args:
        url: Image URL
        video_uuid: UUID for the video project
        image_type: "found" or "generated" (default: "found")
        timeout: Download timeout in seconds (default: 30)

    Returns:
        dict: {
            "success": bool,
            "file_path": str (absolute path to downloaded image),
            "filename": str (e.g., "paper_image_abc123_found.jpg"),
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

        # Download the file
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        # Detect extension from URL or Content-Type
        extension = "jpg"  # Default
        if url.lower().endswith('.png'):
            extension = "png"
        elif url.lower().endswith('.jpg') or url.lower().endswith('.jpeg'):
            extension = "jpg"
        else:
            # Try to detect from Content-Type header
            content_type = response.headers.get('Content-Type', '').lower()
            if 'png' in content_type:
                extension = "png"

        # Generate unique filename
        image_id = str(uuid4())[:8]  # Use first 8 characters of UUID
        filename = generate_image_filename(image_type, image_id, extension)
        output_file = os.path.join(resources_folder, filename)

        # Write the file
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Validate that it's actually an image
        if not validate_image(output_file):
            # Delete invalid file
            try:
                os.remove(output_file)
            except:
                pass

            return create_error_response(
                "Downloaded file is not a valid image (magic bytes check failed)",
                details={"url": url}
            )

        # Success
        return create_success_response({
            "file_path": output_file,
            "filename": filename
        })

    except requests.exceptions.RequestException as e:
        return create_error_response(
            f"Failed to download image from URL",
            details={"url": url, "error": str(e)}
        )
    except Exception as e:
        return create_error_response(
            f"Unexpected error while downloading image",
            details={"error": str(e)}
        )
