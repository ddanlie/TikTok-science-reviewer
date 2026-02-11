"""
Tool for downloading science papers (PDF files) from URLs.

This tool creates the video resources folder and downloads a paper PDF
into it with proper validation.
"""

import os
import requests
from typing import Dict
from project.src.utils.path_utils import get_video_resources_folder
from project.src.utils.validation_utils import validate_pdf
from project.src.utils.error_utils import create_error_response, create_success_response


def download_paper(url: str, video_uuid: str, timeout: int = 30) -> Dict:
    """
    Downloads a science paper PDF from a URL.

    Creates the video resources folder if it doesn't exist, downloads
    the PDF, validates it, and saves it as 'paper.pdf'.

    Args:
        url: Direct download link to the PDF file
        video_uuid: UUID for the video project
        timeout: Download timeout in seconds (default: 30)

    Returns:
        dict: {
            "success": bool,
            "file_path": str (absolute path to downloaded PDF),
            "folder_path": str (absolute path to video resources folder),
            "error": str (if success=False)
        }
    """
    try:
        # Get resources folder path
        resources_folder = get_video_resources_folder(video_uuid)

        # Create folder if it doesn't exist
        os.makedirs(resources_folder, exist_ok=True)

        # Construct output file path
        output_file = os.path.join(resources_folder, "paper.pdf")

        # Download the file
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        # Check Content-Type header if available
        content_type = response.headers.get('Content-Type', '').lower()
        if content_type and 'pdf' not in content_type and 'octet-stream' not in content_type:
            return create_error_response(
                f"URL does not point to a PDF file (Content-Type: {content_type})"
            )

        # Write the file
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Validate that it's actually a PDF
        if not validate_pdf(output_file):
            # Delete invalid file
            try:
                os.remove(output_file)
            except:
                pass

            return create_error_response(
                "Downloaded file is not a valid PDF (magic bytes check failed)"
            )

        # Success
        return create_success_response({
            "file_path": output_file,
            "folder_path": resources_folder
        })

    except requests.exceptions.RequestException as e:
        return create_error_response(
            f"Failed to download paper from URL",
            details={"url": url, "error": str(e)}
        )
    except Exception as e:
        return create_error_response(
            f"Unexpected error while downloading paper",
            details={"error": str(e)}
        )
