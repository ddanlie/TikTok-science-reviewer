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


async def _run_inference(
    runware_client: Runware,
    prompt: str,
    output_path: str,
    model: str,
    timeout: int
) -> Dict:
    """
    Runs a single inference request against one model.

    Returns:
        dict: {"success": bool, "path": str, "error": str}
    """
    request = IImageInference(
        positivePrompt=prompt,
        model=model,
        numberResults=1,
        height=1280,
        width=720,
        outputType="URL"
    )

    results = await asyncio.wait_for(
        runware_client.imageInference(requestImage=request),
        timeout=timeout
    )

    if not results or len(results) == 0:
        return {"success": False, "error": "No image generated"}

    image_result = results[0]

    if hasattr(image_result, 'imageURL'):
        image_url = image_result.imageURL
    elif hasattr(image_result, 'imageUrl'):
        image_url = image_result.imageUrl  # type: ignore
    else:
        return {"success": False, "error": "Image URL not found in result"}

    response = requests.get(image_url, timeout=10)  # type: ignore
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        f.write(response.content)

    return {"success": True, "path": output_path}


async def generate_single_image(
    runware_client: Runware,
    prompt: str,
    output_path: str,
    model_id: str,
    default_model_id: str,
    timeout: int = 30
) -> Dict:
    """
    Generates a single image with fallback to default model.

    Tries the main model first. On failure, retries once with the
    default model before giving up.

    Args:
        runware_client: Connected Runware client
        prompt: Image generation prompt
        output_path: Full path where to save the image
        model_id: Primary Runware model ID
        default_model_id: Fallback Runware model ID
        timeout: Timeout in seconds

    Returns:
        dict: {"success": bool, "path": str, "error": str}
    """
    # Try main model
    try:
        result = await _run_inference(runware_client, prompt, output_path, model_id, timeout)
        if result["success"]:
            return result
        main_error = result["error"]
    except asyncio.TimeoutError:
        main_error = f"Timeout after {timeout} seconds"
    except Exception as e:
        main_error = str(e)

    # Fallback to default model if it differs
    if default_model_id != model_id:
        try:
            result = await _run_inference(runware_client, prompt, output_path, default_model_id, timeout)
            if result["success"]:
                return result
            fallback_error = result["error"]
        except asyncio.TimeoutError:
            fallback_error = f"Timeout after {timeout} seconds"
        except Exception as e:
            fallback_error = str(e)

        return {
            "success": False,
            "error": f"Main model ({model_id}): {main_error}; Fallback model ({default_model_id}): {fallback_error}"
        }

    return {"success": False, "error": main_error}


async def generate_all_images_async(
    video_uuid: str,
    model_id: str,
    default_model_id: str,
    timeout_per_image: int
) -> Dict:
    """
    Async function to generate all images for a video project.

    Args:
        video_uuid: Video project UUID
        model_id: Runware model ID
        default_model_id: Runware backup model ID
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
            default_model_id,
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
        await runware.close() # type: ignore
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

        default_model_id = "runware:400@4"
        model_id = default_model_id
        if os.path.exists(model_id_file):
            with open(model_id_file, 'r', encoding='utf-8') as f:
                for _ in range(2):
                    line = f.readline().strip()
                    if not line:
                        continue
                    parts = line.split(" ", 1)
                    if len(parts) != 2:
                        continue
                    model_type, model_value = parts
                    if model_type == "main":
                        model_id = model_value
                    elif model_type == "default":
                        default_model_id = model_value

        # Run async generation
        result = asyncio.run(
            generate_all_images_async(video_uuid, model_id, default_model_id, timeout_per_image)
        )

        return result

    except Exception as e:
        return create_error_response(
            f"Unexpected error during image generation",
            details={"error": str(e)}
        )
