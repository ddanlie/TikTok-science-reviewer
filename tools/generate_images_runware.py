"""
Tool for generating images using Runware AI API.

This tool scans for prompt files and generates images using the Runware AI
image generation model with async/await patterns and timeout protection.
"""

import os
import glob
import asyncio
import requests
from typing import Dict, List
from runware import Runware, IImageInference
from project.src.utils.path_utils import get_video_resources_folder
from project.src.utils.validation_utils import validate_folder_exists
from project.src.utils.env_utils import load_all_env, get_runware_api_key
from project.src.utils.error_utils import create_error_response, create_success_response


async def generate_single_image(
    runware_client: Runware,
    prompt: str,
    output_path: str,
    model_id: str,
    timeout: int = 30
) -> Dict:
    """
    Generates a single image with timeout protection.

    Args:
        runware_client: Connected Runware client
        prompt: Image generation prompt
        output_path: Full path where to save the image
        model_id: Runware model ID
        timeout: Timeout in seconds

    Returns:
        dict: {"success": bool, "path": str, "error": str}
    """
    try:
        # Create image inference request
        request = IImageInference(
            positivePrompt=prompt,
            model=model_id,
            numberResults=1,
            height=1280,
            width=720,
            outputType="URL"  # Get URL to download
        )

        # Generate with timeout
        results = await asyncio.wait_for(
            runware_client.imageInference(requestImage=request),
            timeout=timeout
        )

        if not results or len(results) == 0:
            return {
                "success": False,
                "error": "No image generated"
            }

        # Get the first result
        image_result = results[0]

        # Download the image from URL
        if hasattr(image_result, 'imageURL'):
            image_url = image_result.imageURL
        elif hasattr(image_result, 'imageUrl'):
            image_url = image_result.imageUrl
        else:
            return {
                "success": False,
                "error": "Image URL not found in result"
            }

        # Download image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        # Save image
        with open(output_path, 'wb') as f:
            f.write(response.content)

        return {
            "success": True,
            "path": output_path
        }

    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": f"Timeout after {timeout} seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def generate_all_images_async(
    video_uuid: str,
    model_id: str,
    timeout_per_image: int
) -> Dict:
    """
    Async function to generate all images for a video project.

    Args:
        video_uuid: Video project UUID
        model_id: Runware model ID
        timeout_per_image: Timeout per image in seconds

    Returns:
        dict: Generation results
    """
    generated_images = []
    failed_prompts = []

    resources_folder = get_video_resources_folder(video_uuid)

    # Find all prompt files
    prompt_pattern = os.path.join(resources_folder, "paper_image_*_prompt.txt")
    prompt_files = glob.glob(prompt_pattern)

    if not prompt_files:
        return create_error_response(
            "No prompt files found",
            details={"pattern": prompt_pattern, "folder": resources_folder}
        )

    # Load API key
    try:
        api_key = get_runware_api_key()
    except ValueError as e:
        return create_error_response(str(e))

    # Connect to Runware
    try:
        runware = Runware(api_key=api_key)
        await runware.connect()
    except Exception as e:
        return create_error_response(
            f"Failed to connect to Runware API",
            details={"error": str(e)}
        )

    # Process each prompt file
    for prompt_file in prompt_files:
        # Extract image ID from filename
        # Format: paper_image_{id}_prompt.txt
        filename = os.path.basename(prompt_file)
        image_id = filename.replace("paper_image_", "").replace("_prompt.txt", "")

        # Read prompt
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
        except Exception as e:
            failed_prompts.append({
                "prompt_file": prompt_file,
                "error": f"Failed to read prompt: {str(e)}"
            })
            continue

        # Determine output path
        output_filename = f"paper_image_{image_id}_generated.png"
        output_path = os.path.join(resources_folder, output_filename)

        # Generate image
        result = await generate_single_image(
            runware,
            prompt,
            output_path,
            model_id,
            timeout_per_image
        )

        if result["success"]:
            generated_images.append(output_path)
        else:
            failed_prompts.append({
                "prompt_file": prompt_file,
                "error": result["error"]
            })

    # Disconnect
    try:
        await runware.close()
    except:
        pass  # Ignore disconnect errors

    return create_success_response({
        "generated_images": generated_images,
        "failed_prompts": failed_prompts,
        "total_generated": len(generated_images),
        "total_failed": len(failed_prompts)
    })


def generate_images_runware(video_uuid: str, timeout_per_image: int = 30) -> Dict:
    """
    Generates all images based on prompt files in the video resources folder.

    Scans for all paper_image_*_prompt.txt files and generates corresponding
    images using Runware AI API. Uses one-prompt-one-image protection and
    continues on failures.

    Args:
        video_uuid: UUID for the video project
        timeout_per_image: Max seconds to wait per image (default: 30)

    Returns:
        dict: {
            "success": bool,
            "generated_images": list[str] (absolute paths),
            "failed_prompts": list[dict] (prompt files that failed),
            "total_generated": int,
            "total_failed": int,
            "error": str (if complete failure)
        }
    """
    try:
        # Load environment variables
        load_all_env()

        # Check if folder exists
        resources_folder = get_video_resources_folder(video_uuid)
        if not validate_folder_exists(resources_folder):
            return create_error_response(
                f"Video resources folder does not exist: {resources_folder}",
                details={"solution": "Run download_paper first to create the folder"}
            )

        # Read model ID from readonly sources
        from project.src.utils.path_utils import get_readonly_sources_path
        model_id_file = os.path.join(get_readonly_sources_path(), "runware_ai_api_model_id.txt")

        if os.path.exists(model_id_file):
            with open(model_id_file, 'r', encoding='utf-8') as f:
                model_id = f.read().strip()
        else:
            model_id = "runware:400@4"  # Default fallback

        # Run async generation
        result = asyncio.run(
            generate_all_images_async(video_uuid, model_id, timeout_per_image)
        )

        return result

    except Exception as e:
        return create_error_response(
            f"Unexpected error during image generation",
            details={"error": str(e)}
        )
