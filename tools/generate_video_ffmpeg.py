"""
Tool for generating TikTok videos using FFmpeg.

This tool combines images and audio based on time_script.txt to create
the final TikTok video using FFmpeg.
"""

import os
import subprocess
from typing import Dict, List
from project.src.utils.path_utils import (
    get_video_resources_folder,
    get_videos_folder,
    parse_time_script,
    generate_video_filename,
    get_ffmpeg_path
)
from project.src.utils.validation_utils import (
    validate_folder_exists,
    validate_file_exists,
    validate_time_script_images_exist
)
from project.src.utils.error_utils import create_error_response, create_success_response


def build_ffmpeg_command(
    images: List[Dict],
    audio_path: str,
    output_path: str,
    ffmpeg_path: str
) -> List[str]:
    """
    Builds the FFmpeg command for video generation.

    Args:
        images: List of dicts with {"path": str, "duration": float}
        audio_path: Path to audio file
        output_path: Path for output video
        ffmpeg_path: Path to ffmpeg.exe

    Returns:
        list: Command arguments for subprocess
    """
    cmd = [ffmpeg_path]

    # Add input images (each with loop and duration)
    for img in images:
        cmd.extend([
            '-loop', '1',
            '-t', str(img['duration']),
            '-i', img['path']
        ])

    # Add audio input
    cmd.extend(['-i', audio_path])

    # Build filter_complex for scaling and concatenation
    filter_parts = []

    # Scale all images to 720x1280
    for i in range(len(images)):
        filter_parts.append(f"[{i}:v]scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]")

    # Concatenate all scaled images
    concat_inputs = ''.join([f"[v{i}]" for i in range(len(images))])
    filter_parts.append(f"{concat_inputs}concat=n={len(images)}:v=1:a=0[outv]")

    filter_complex = ';'.join(filter_parts)

    cmd.extend([
        '-filter_complex', filter_complex,
        '-map', '[outv]',
        '-map', f'{len(images)}:a',  # Audio is after all images
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',  # End when shortest stream ends
        '-y',  # Overwrite output file
        output_path
    ])

    return cmd


def generate_video_ffmpeg(video_uuid: str, ffmpeg_path: str = None) -> Dict:
    """
    Generates TikTok video from images and audio using FFmpeg.

    Reads time_script.txt, validates all resources exist, and uses FFmpeg
    to combine images and audio into a final video.

    Args:
        video_uuid: UUID for the video project
        ffmpeg_path: Path to ffmpeg.exe (default: auto-detect from dependencies)

    Returns:
        dict: {
            "success": bool,
            "video_path": str (absolute path in project/videos/),
            "duration": float (seconds),
            "error": str (if success=False)
        }
    """
    try:
        # Get paths
        resources_folder = get_video_resources_folder(video_uuid)
        videos_folder = get_videos_folder()

        # Validate resources folder exists
        if not validate_folder_exists(resources_folder):
            return create_error_response(
                f"Video resources folder does not exist: {resources_folder}",
                details={"solution": "Run download_paper first to create the folder"}
            )

        # Create videos folder if it doesn't exist
        os.makedirs(videos_folder, exist_ok=True)

        # Validate time_script.txt exists
        time_script_path = os.path.join(resources_folder, "time_script.txt")
        if not validate_file_exists(time_script_path):
            return create_error_response(
                f"time_script.txt not found",
                details={"expected_path": time_script_path}
            )

        # Validate generated_voice.mp3 exists
        audio_path = os.path.join(resources_folder, "generated_voice.mp3")
        if not validate_file_exists(audio_path):
            return create_error_response(
                f"generated_voice.mp3 not found",
                details={
                    "expected_path": audio_path,
                    "solution": "Generate voice using Eleven Labs and save as generated_voice.mp3"
                }
            )

        # Parse time script
        try:
            parsed = parse_time_script(time_script_path)
        except Exception as e:
            return create_error_response(
                f"Failed to parse time_script.txt: {str(e)}"
            )

        # Validate all images exist
        validation = validate_time_script_images_exist(video_uuid)
        if not validation["all_exist"]:
            return create_error_response(
                f"Missing images referenced in time_script.txt",
                details={
                    "missing_images": validation["missing_images"],
                    "solution": "Generate or download missing images"
                }
            )

        # Prepare image data for FFmpeg
        sections = parsed["sections"]
        total_duration = parsed["duration"]

        images = []
        for i, section in enumerate(sections):
            image_path = os.path.join(resources_folder, section["image_filename"])

            # Calculate duration for this image
            if i < len(sections) - 1:
                # Duration until next image
                duration = sections[i + 1]["timestamp"] - section["timestamp"]
            else:
                # Last image: duration until end
                duration = total_duration - section["timestamp"]

            images.append({
                "path": image_path,
                "duration": duration
            })

        # Get ffmpeg path
        if ffmpeg_path is None:
            ffmpeg_path = get_ffmpeg_path()

        if not validate_file_exists(ffmpeg_path):
            return create_error_response(
                f"FFmpeg not found",
                details={
                    "expected_path": ffmpeg_path,
                    "solution": "Ensure FFmpeg is installed in dependencies/ffmpeg/bin/"
                }
            )

        # Generate output filename
        output_filename = generate_video_filename(video_uuid)
        output_path = os.path.join(videos_folder, output_filename)

        # Build FFmpeg command
        cmd = build_ffmpeg_command(images, audio_path, output_path, ffmpeg_path)

        # Execute FFmpeg
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                return create_error_response(
                    f"FFmpeg failed with return code {result.returncode}",
                    details={
                        "stderr": result.stderr[-1000:] if result.stderr else ""  # Last 1000 chars
                    }
                )
        except subprocess.TimeoutExpired:
            return create_error_response(
                "FFmpeg execution timed out after 5 minutes"
            )
        except Exception as e:
            return create_error_response(
                f"Failed to execute FFmpeg",
                details={"error": str(e)}
            )

        # Validate output file was created
        if not validate_file_exists(output_path):
            return create_error_response(
                "FFmpeg completed but output video file not found",
                details={"expected_path": output_path}
            )

        # Success
        return create_success_response({
            "video_path": output_path,
            "duration": total_duration
        })

    except Exception as e:
        return create_error_response(
            f"Unexpected error during video generation",
            details={"error": str(e)}
        )
