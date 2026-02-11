#!/usr/bin/env python3
"""
Science Papers TikTok Blogger - Agent Loop Entry Point

Usage:
  python main.py                 Start agent loop (first turn, no input)
  echo '{...}' | python main.py  Process one turn with piped JSON input
  python main.py --reset         Reset state and start fresh
  python main.py --workflow      Print workflow documentation
  python main.py -h / --help     Show this help
"""

import os
import sys

# Ensure project root is on the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _has_stdin_data() -> bool:
    """Check if there's data available on stdin (piped input)."""
    if sys.stdin.isatty():
        return False
    # Non-tty stdin = piped data
    return True


def main():
    # Handle flags
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--workflow":
            _print_workflow()
            return
        elif arg == "--reset":
            from agent.state import WorkflowState
            WorkflowState.reset()
            print("State reset. Run 'python main.py' to start fresh.")
            return
        elif arg in ("-h", "--help"):
            print(__doc__)
            return
        else:
            print(f"Unknown argument: {arg}")
            print(__doc__)
            sys.exit(1)

    # Read stdin if available (piped JSON)
    input_json = None
    if _has_stdin_data():
        input_json = sys.stdin.read().strip()
        if not input_json:
            input_json = None

    # Run one turn
    from agent.loop import process_turn
    output = process_turn(input_json)
    sys.stdout.write(output + "\n")
    sys.stdout.flush()


def _print_workflow():
    """Print the workflow documentation."""
    print("""
================================================================================
      SCIENCE PAPERS TIKTOK BLOGGER - AGENT LOOP
================================================================================

AGENT LOOP MODE:
  python main.py                 First turn (outputs step 1 context)
  echo '{...}' | python main.py  Subsequent turns (process input, output context)
  python main.py --reset         Reset state for a new workflow run

PROTOCOL:
  Adapter outputs JSON context to stdout with current step, tools, state.
  LLM responds with JSON on stdin: tool_call, llm_action, step_complete, etc.
  See agent/protocol.py for the full message specification.

LLM INPUT TYPES:
  tool_call           Execute a Python tool in-process
  llm_action          Report result of a native LLM capability
  message_user        Show a message to the human user
  step_complete       Advance to the next workflow step
  workflow_complete    Finish the workflow

TOOLS AVAILABLE:
  download_paper(url, video_uuid)
  save_script(script_content, video_uuid)
  save_time_script(time_script_content, video_uuid)
  save_image_prompt(prompt_text, image_id, video_uuid)
  download_image(url, video_uuid, image_type="found")
  generate_images_runware(video_uuid, timeout_per_image=30)
  generate_video_ffmpeg(video_uuid, ffmpeg_path=None)
  post_video_tiktok(video_path, title="", hashtags=None)
  calculate_script_word_amount(duration)
  validate_time_script_images_exist(video_uuid)

WORKFLOW STEPS (11):
  1.  web_search_for_papers    Search web for science papers
  2.  generate_video_uuid      Create unique video identifier
  3.  download_paper           Download paper PDF
  4.  read_and_analyze_paper   Read and extract key points
  5.  create_script            Write TikTok script with word budget
  6.  create_time_script       Create image timeline
  7.  find_images              Search web for images
  8.  generate_image_prompts   Create AI image prompts
  9.  generate_images          Generate images via Runware AI
  10. validate_resources       Verify all resources exist
  11. human_handoff            Complete agent phase
================================================================================
    """)


if __name__ == "__main__":
    main()
