#!/usr/bin/env python3
"""
Human adapter for TikTok video posting.

This script provides a simple command-line interface for humans to post
generated videos to TikTok.

Usage:
    python project/post_video.py <video_path> [--title "Your title"] [--hashtags "tag1,tag2"]

Examples:
    python project/post_video.py "project/videos/video_20260210_abc123.mp4"
    python project/post_video.py "project/videos/video_20260210_abc123.mp4" --title "Amazing Science Discovery"
    python project/post_video.py "project/videos/video_20260210_abc123.mp4" --title "Cool Physics" --hashtags "science,physics,viral"
"""

import sys
import os
import argparse

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tools.post_video_tiktok import post_video_tiktok
from project.src.utils.error_utils import exit_with_error


def main():
    """Main entry point for video posting."""

    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Post TikTok video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python project/post_video.py "project/videos/video_20260210_abc123.mp4"
  python project/post_video.py "project/videos/video_20260210_abc123.mp4" --title "Amazing Discovery"
  python project/post_video.py "project/videos/video_20260210_abc123.mp4" --title "Physics Explained" --hashtags "science,physics"
        """
    )

    parser.add_argument(
        "video_path",
        help="Path to video file (absolute or relative)"
    )

    parser.add_argument(
        "--title",
        default="",
        help="Video title/caption"
    )

    parser.add_argument(
        "--hashtags",
        default="",
        help="Comma-separated hashtags (without # symbol)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Convert relative path to absolute
    video_path = os.path.abspath(args.video_path)

    # Parse hashtags
    hashtags = [h.strip() for h in args.hashtags.split(",")] if args.hashtags else []

    print("=" * 60)
    print("Science Papers TikTok Blogger - Video Posting")
    print("=" * 60)
    print()
    print(f"Video: {video_path}")
    print(f"Title: {args.title if args.title else '(none)'}")
    print(f"Hashtags: {', '.join(['#' + h for h in hashtags]) if hashtags else '(none)'}")
    print()
    print("Posting video to TikTok...")
    print()

    # Call the posting tool
    result = post_video_tiktok(video_path, args.title, hashtags)

    # Handle result
    if result["success"]:
        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print()

        # Check if manual upload is required
        if result.get("manual_upload"):
            print("MANUAL UPLOAD REQUIRED")
            print()
            print(result.get("message", "TikTok API not configured"))
            print()
            print("Video details:")
            print(f"  Path: {result.get('video_path', video_path)}")
            if result.get("caption"):
                print(f"  Caption: {result['caption']}")
            print()
            print("Please upload this video manually via:")
            print("  - TikTok mobile app")
            print("  - TikTok web interface (https://www.tiktok.com/upload)")
            print()
        else:
            # Automatic posting succeeded
            print(f"Video posted successfully!")
            print()
            if result.get("video_url"):
                print(f"Video URL: {result['video_url']}")
            if result.get("video_id"):
                print(f"Video ID: {result['video_id']}")
            print()
    else:
        print()
        exit_with_error(
            result.get("error", "Unknown error"),
            details=result.get("details")
        )


if __name__ == "__main__":
    main()
