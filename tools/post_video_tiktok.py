"""
Tool for posting videos to TikTok using the TikTok API.

This tool validates the video and uploads it to TikTok using the
Content Posting API. For MVP, includes manual upload fallback.
"""

import os
from typing import Dict, List, Optional
from project.src.utils.validation_utils import validate_video_file
from project.src.utils.env_utils import load_all_env, get_tiktok_credentials
from project.src.utils.error_utils import create_error_response, create_success_response


def post_video_tiktok(
    video_path: str,
    title: str = "",
    hashtags: Optional[List[str]] = None
) -> Dict:
    """
    Posts video to TikTok using the Content Posting API.

    For MVP, this validates the video and prepares it for posting.
    If TikTok API credentials are available, it attempts to post.
    Otherwise, it provides instructions for manual upload.

    Args:
        video_path: Absolute path to video file
        title: Video title/caption (default: "")
        hashtags: List of hashtags without # symbol (default: None)

    Returns:
        dict: {
            "success": bool,
            "video_url": str (TikTok URL if available),
            "video_id": str (TikTok video ID if available),
            "manual_upload": bool (True if manual upload required),
            "error": str (if success=False)
        }
    """
    try:
        # Load environment variables
        load_all_env()

        # Validate video file exists
        if not validate_video_file(video_path):
            return create_error_response(
                f"Video file not found or invalid",
                details={
                    "path": video_path,
                    "solution": "Ensure video file exists and is a valid .mp4 file"
                }
            )

        # Format hashtags if provided
        if hashtags:
            hashtag_str = ' '.join([f"#{tag}" for tag in hashtags])
            if title:
                full_caption = f"{title}\n\n{hashtag_str}"
            else:
                full_caption = hashtag_str
        else:
            full_caption = title

        # Try to get TikTok credentials
        try:
            credentials = get_tiktok_credentials()
            has_credentials = True
        except ValueError:
            has_credentials = False

        # MVP: Manual upload fallback
        if not has_credentials:
            return create_success_response({
                "video_path": video_path,
                "manual_upload": True,
                "caption": full_caption,
                "message": (
                    "TikTok API credentials not configured. "
                    "Please upload the video manually via TikTok app or web interface."
                )
            })

        # TikTok API Integration (placeholder for future implementation)
        # TODO: Implement actual TikTok Content Posting API call
        # This would involve:
        # 1. Initialize upload session
        # 2. Upload video file
        # 3. Publish with metadata (title, hashtags, etc.)
        # 4. Return video URL and ID

        # For now, return success with manual upload instruction
        return create_success_response({
            "video_path": video_path,
            "manual_upload": True,
            "caption": full_caption,
            "message": (
                "TikTok API integration not yet implemented in MVP. "
                "Please upload the video manually via TikTok app or web interface."
            ),
            "todo": "Implement TikTok Content Posting API integration"
        })

        # Example of what the API integration would look like:
        # import requests
        #
        # # Step 1: Initialize upload
        # init_response = requests.post(
        #     "https://open.tiktokapis.com/v2/post/publish/video/init/",
        #     headers={
        #         "Authorization": f"Bearer {credentials['access_token']}",
        #         "Content-Type": "application/json"
        #     },
        #     json={
        #         "post_info": {
        #             "title": full_caption,
        #             "privacy_level": "PUBLIC_TO_EVERYONE",
        #             "disable_duet": False,
        #             "disable_comment": False,
        #             "disable_stitch": False,
        #             "video_cover_timestamp_ms": 1000
        #         },
        #         "source_info": {
        #             "source": "FILE_UPLOAD",
        #             "video_size": os.path.getsize(video_path),
        #             "chunk_size": 10000000,
        #             "total_chunk_count": 1
        #         }
        #     }
        # )
        #
        # # Step 2: Upload video
        # # ... upload implementation ...
        #
        # # Step 3: Publish
        # # ... publish implementation ...
        #
        # return create_success_response({
        #     "video_url": published_video_url,
        #     "video_id": published_video_id,
        #     "manual_upload": False
        # })

    except Exception as e:
        return create_error_response(
            f"Unexpected error during TikTok posting",
            details={"error": str(e)}
        )
