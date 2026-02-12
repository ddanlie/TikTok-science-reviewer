"""
Tool for extracting text from a downloaded paper PDF using pdftotext.

Uses the pdftotext dependency to convert paper.pdf to paper.txt in the
video resources folder. If the text file already exists, reads and returns it.
"""

import os
import subprocess
from typing import Dict
from project.src.utils.path_utils import get_video_resources_folder, get_pdftotext_path
from project.src.utils.validation_utils import validate_file_exists
from project.src.utils.error_utils import create_error_response, create_success_response


def get_pdf_text(video_uuid: str) -> Dict:
    """
    Extracts text from paper.pdf in the video resources folder.

    If paper.txt already exists, reads and returns its content.
    Otherwise, runs pdftotext to generate it, then reads and returns the text.

    Args:
        video_uuid: UUID for the video project

    Returns:
        dict: {
            "success": bool,
            "text": str (extracted text content),
            "file_path": str (absolute path to paper.txt),
            "cached": bool (True if file already existed),
            "error": str (if success=False)
        }
    """
    try:
        resources_folder = get_video_resources_folder(video_uuid)
        pdf_path = os.path.join(resources_folder, "paper.pdf")
        txt_path = os.path.join(resources_folder, "paper.txt")

        # If text file already exists, just read and return it
        if validate_file_exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return create_success_response({
                "text": text,
                "file_path": txt_path,
                "cached": True
            })

        # Validate paper.pdf exists
        if not validate_file_exists(pdf_path):
            return create_error_response(
                "paper.pdf not found",
                details={
                    "expected_path": pdf_path,
                    "solution": "Run download_paper first to download the PDF"
                }
            )

        # Get pdftotext path and validate
        pdftotext_path = get_pdftotext_path()
        if not validate_file_exists(pdftotext_path):
            return create_error_response(
                "pdftotext not found",
                details={
                    "expected_path": pdftotext_path,
                    "solution": "Ensure pdftotext is installed in dependencies/pdftotext/"
                }
            )

        # Run pdftotext <pdf_path> which generates paper.txt in the same folder
        try:
            result = subprocess.run(
                [pdftotext_path, pdf_path],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return create_error_response(
                    f"pdftotext failed with return code {result.returncode}",
                    details={
                        "stderr": result.stderr[-1000:] if result.stderr else ""
                    }
                )
        except subprocess.TimeoutExpired:
            return create_error_response(
                "pdftotext execution timed out after 60 seconds"
            )
        except Exception as e:
            return create_error_response(
                "Failed to execute pdftotext",
                details={"error": str(e)}
            )

        # pdftotext generates the .txt file next to the pdf with the same name
        if not validate_file_exists(txt_path):
            return create_error_response(
                "pdftotext completed but paper.txt was not created",
                details={"expected_path": txt_path}
            )

        # Read and return the text
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()

        return create_success_response({
            "text": text,
            "file_path": txt_path,
            "cached": False
        })

    except Exception as e:
        return create_error_response(
            "Unexpected error during PDF text extraction",
            details={"error": str(e)}
        )
