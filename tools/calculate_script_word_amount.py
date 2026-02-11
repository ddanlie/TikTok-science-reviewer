import os
from typing import Dict
from project.src.utils.path_utils import get_readonly_sources_path
from project.src.utils.error_utils import create_error_response, create_success_response


def calculate_script_word_amount(duration: int) -> Dict:
    """
    Calculate the number of words needed for a script of a given duration.

    Args:
        duration: Target video duration in seconds

    Returns:
        dict: {"success": bool, "words_amount": int, "words_per_second": int, "duration": int}
    """
    speed_file = os.path.join(get_readonly_sources_path(), "voice_generator_speech_speed.txt")

    if not os.path.exists(speed_file):
        return create_error_response(
            "Speech speed file not found",
            details={"path": speed_file}
        )

    try:
        with open(speed_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                key, value = line.split(":")
                if key.strip() == "words per second":
                    speed = int(value.strip())
                    break
            else:
                return create_error_response("'words per second' entry not found in speed file")
    except Exception as e:
        return create_error_response(
            "Failed to read speech speed file",
            details={"error": str(e)}
        )

    words_amount = duration * speed

    return create_success_response({
        "words_amount": words_amount,
        "words_per_second": speed,
        "duration": duration
    })
