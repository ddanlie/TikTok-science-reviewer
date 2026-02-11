#!/usr/bin/env python3
"""
Human adapter for video generation.

This script provides a simple command-line interface for humans to generate
TikTok videos from prepared resources using FFmpeg.

Usage:
    python project/generate_video.py <video_uuid>

Example:
    python project/generate_video.py abc123def456
"""

import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tools.generate_video_ffmpeg import generate_video_ffmpeg
from project.src.utils.error_utils import exit_with_error


def main():
    """Main entry point for video generation."""

    # Check arguments
    if len(sys.argv) != 2:
        print("ERROR: Invalid arguments")
        print()
        print("Usage: python project/generate_video.py <video_uuid>")
        print()
        print("Example:")
        print("  python project/generate_video.py abc123def456")
        print()
        sys.exit(1)

    video_uuid = sys.argv[1]

    print("=" * 60)
    print("Science Papers TikTok Blogger - Video Generation")
    print("=" * 60)
    print()
    print(f"Video Project UUID: {video_uuid}")
    print()
    print("Generating video from resources...")
    print()

    # Call the video generation tool
    result = generate_video_ffmpeg(video_uuid)

    # Handle result
    if result["success"]:
        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print()
        print(f"Video generated at: {result['video_path']}")
        print(f"Duration: {result['duration']} seconds")
        print()
        print("Next steps:")
        print("1. Review the generated video")
        print("2. If satisfied, post to TikTok using:")
        print(f"   python project/post_video.py \"{result['video_path']}\" --title \"Your title\" --hashtags \"tag1,tag2\"")
        print()
    else:
        print()
        exit_with_error(
            result.get("error", "Unknown error"),
            details=result.get("details")
        )


if __name__ == "__main__":
    main()
