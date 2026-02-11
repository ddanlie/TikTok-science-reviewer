#!/usr/bin/env python3
"""
Science Papers TikTok Blogger - MVP Entry Point

This is a semi-automated workflow for creating TikTok videos from science papers.
The workflow involves both AI agent work and human intervention.

For MVP, this file serves as documentation and workflow guidance.

Author: Built with Claude Code
License: MIT
"""

import sys
import os


def print_workflow():
    """Prints the complete MVP workflow."""
    print("""
================================================================================
          SCIENCE PAPERS TIKTOK BLOGGER - MVP WORKFLOW
================================================================================

This project helps you create TikTok videos reviewing science papers through
a semi-automated workflow combining AI agent work and human input.

--------------------------------------------------------------------------------
PHASE 1: SETUP (One-time)
--------------------------------------------------------------------------------

1. Activate virtual environment:

   Windows:
     .venv\\Scripts\\activate

   Linux/Mac:
     source .venv/bin/activate

2. Install Python dependencies:

   pip install -r requirements.txt

3. Configure environment variables:

   Edit: project/src/.env

   Required:
   - RUNWARE_AI_API_KEY (already set from readonly sources)

   Optional (for automatic TikTok posting):
   - TIKTOK_CLIENT_KEY
   - TIKTOK_CLIENT_SECRET
   - TIKTOK_ACCESS_TOKEN

--------------------------------------------------------------------------------
PHASE 2: CONTENT DISCOVERY & CREATION (Agent Phase)
--------------------------------------------------------------------------------

In this phase, you work with Claude Code agent in chat to:

1. WEB SEARCH FOR PAPERS
   - Topics are listed in: readonly_sources_of_truth/science_papers_topics.txt
   - Look for papers that are:
     * Free to access
     * Mainstream relevant (current hype)
     * TikTok-friendly (not too long/complex)
     * Tell an interesting story

2. DOWNLOAD PAPER
   Agent uses tool: download_paper(url, video_uuid)
   - Creates folder: project/resources/video_{date}_{uuid}_resources/
   - Downloads PDF as: paper.pdf

3. CREATE SCRIPT
   Agent reads paper and creates TikTok script
   Agent uses tool: save_script(script_content, video_uuid)
   - Saves as: script.txt
   - Format: Hook for first 2 seconds, dynamic, interesting
   - Pure text for voice generation (no comments/symbols)

4. CREATE TIME SCRIPT
   Agent creates timeline for images
   Agent uses tool: save_time_script(time_script_content, video_uuid)
   - Saves as: time_script.txt
   - Format:
     Line 1: Total duration in seconds
     Lines 2+: timestamp|image_filename

5. FIND IMAGES
   Agent searches web for scenario-appropriate images
   Agent uses tool: download_image(url, video_uuid)
   - Tries to find article main page for first seconds
   - Format: TikTok 9:16 or 3:4, resolution >= 720x1280
   - Saves as: paper_image_{id}_found.jpg/png

6. GENERATE IMAGE PROMPTS
   Agent creates prompts for remaining images
   Agent uses tool: save_image_prompt(prompt_text, image_id, video_uuid)
   - Saves as: paper_image_{id}_prompt.txt
   - Professional prompts for weak/fast generator model
   - Minimalistic, clear style and scene description

7. GENERATE IMAGES
   Agent uses tool: generate_images_runware(video_uuid)
   - Reads all prompt files
   - Generates images using Runware AI (model: runware:400@4)
   - Saves as: paper_image_{id}_generated.png
   - Size: 720x1280 (TikTok format)
   - Continues on failures (timeout protection)

--------------------------------------------------------------------------------
PHASE 3: VOICE GENERATION (Human Phase)
--------------------------------------------------------------------------------

At this point, the agent hands off to you.

1. READ SCRIPT
   - Open: project/resources/video_{date}_{uuid}_resources/script.txt

2. GENERATE VOICE
   - Use Eleven Labs (or other voice generator)
   - Input: script.txt content
   - Output: Save as generated_voice.mp3
   - Location: Same folder as script.txt

--------------------------------------------------------------------------------
PHASE 4: VIDEO GENERATION (Human Phase)
--------------------------------------------------------------------------------

1. GENERATE VIDEO
   Run the video generation adapter:

   python project/generate_video.py <video_uuid>

   Example:
   python project/generate_video.py abc123def456

   This will:
   - Parse time_script.txt
   - Validate all images and audio exist
   - Use FFmpeg to combine images + audio
   - Create: project/videos/video_{date}_{uuid}.mp4

2. REVIEW VIDEO
   - Watch the generated video
   - Check timing, transitions, audio sync
   - Regenerate if needed

--------------------------------------------------------------------------------
PHASE 5: PUBLISHING (Human Phase)
--------------------------------------------------------------------------------

1. POST TO TIKTOK
   Run the posting adapter:

   python project/post_video.py <video_path> [options]

   Example with title and hashtags:
   python project/post_video.py "project/videos/video_20260210_abc123.mp4" \\
       --title "Mind-Blowing Physics Discovery" \\
       --hashtags "science,physics,viral,edutok"

   If TikTok API is configured, video will be posted automatically.
   Otherwise, you'll get instructions for manual upload.

2. MANUAL UPLOAD (if needed)
   - Open TikTok app or https://www.tiktok.com/upload
   - Upload the generated video
   - Copy caption from adapter output
   - Publish!

================================================================================
TOOLS AVAILABLE FOR AGENTS
================================================================================

All tools can be imported and used by Claude Code or future autonomous agents:

From tools/:
  - download_paper(url, video_uuid)
  - save_script(script_content, video_uuid)
  - save_time_script(time_script_content, video_uuid)
  - save_image_prompt(prompt_text, image_id, video_uuid)
  - download_image(url, video_uuid, image_type="found")
  - generate_images_runware(video_uuid, timeout_per_image=30)
  - generate_video_ffmpeg(video_uuid, ffmpeg_path=None)
  - post_video_tiktok(video_path, title="", hashtags=None)

From project/src/utils/:
  - Path utilities (path_utils.py)
  - Validation utilities (validation_utils.py)
  - Error handling (error_utils.py)
  - Environment management (env_utils.py)

================================================================================
TROUBLESHOOTING
================================================================================

Common Issues:

1. "Module not found" errors
   → Ensure virtual environment is activated
   → Run: pip install -r requirements.txt

2. "Runware API key not found"
   → Check: project/src/.env has RUNWARE_AI_API_KEY
   → Should be copied from readonly_sources_of_truth/.env

3. "FFmpeg not found"
   → FFmpeg should be in: dependencies/ffmpeg/bin/ffmpeg.exe
   → Check the file exists

4. "Missing images in time_script.txt"
   → Ensure generate_images_runware completed successfully
   → Check all images exist in resources folder

5. "generated_voice.mp3 not found"
   → This file must be created manually by you using Eleven Labs
   → Save it in: project/resources/video_{date}_{uuid}_resources/

================================================================================
PROJECT STRUCTURE
================================================================================

.
├── main.py                          # This file - workflow documentation
├── requirements.txt                 # Python dependencies
│
├── tools/                           # Agent-reusable tools
│   ├── download_paper.py
│   ├── save_script.py
│   ├── save_time_script.py
│   ├── save_image_prompt.py
│   ├── download_image.py
│   ├── generate_images_runware.py
│   ├── generate_video_ffmpeg.py
│   └── post_video_tiktok.py
│
├── project/
│   ├── generate_video.py            # Human adapter for video gen
│   ├── post_video.py                # Human adapter for posting
│   ├── src/
│   │   ├── .env                     # Environment configuration
│   │   └── utils/                   # Utility functions
│   ├── resources/                   # Video project folders
│   │   └── video_{date}_{uuid}_resources/
│   │       ├── paper.pdf
│   │       ├── script.txt
│   │       ├── time_script.txt
│   │       ├── generated_voice.mp3
│   │       ├── paper_image_*_found.{jpg|png}
│   │       ├── paper_image_*_prompt.txt
│   │       └── paper_image_*_generated.png
│   └── videos/                      # Final generated videos
│       └── video_{date}_{uuid}.mp4
│
├── dependencies/
│   └── ffmpeg/                      # FFmpeg binaries
│
├── readonly_sources_of_truth/
│   ├── .env                         # Base environment config
│   ├── science_papers_topics.txt   # Topics to search
│   ├── runware_ai_api_model_id.txt
│   └── runware_ai_api_docs_reference_startpoint.txt
│
├── workflows/                       # (Reserved for future agents)
├── agent/                           # (Reserved for future agents)
└── .venv/                          # Python virtual environment

================================================================================
NEXT STEPS
================================================================================

To start creating videos:

1. Ensure setup is complete (Phase 1)
2. Chat with Claude Code to discover and create content (Phase 2)
3. Generate voice file (Phase 3)
4. Run generate_video.py (Phase 4)
5. Run post_video.py (Phase 5)

Happy video creation!

================================================================================
    """)


def print_help():
    """Prints help information."""
    print("""
Usage: python main.py [--workflow]

Options:
  --workflow    Display the complete workflow guide

For full workflow documentation, run:
  python main.py --workflow
    """)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--workflow":
            print_workflow()
        elif sys.argv[1] in ["-h", "--help"]:
            print_help()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print_help()
    else:
        print_workflow()


if __name__ == "__main__":
    main()
