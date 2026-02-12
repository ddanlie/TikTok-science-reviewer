"""
Tool for reading available science paper topics from the readonly sources.

Parses science_papers_topics.txt and returns the list of topics
an agent can choose from when searching for papers.
"""

import os
from typing import Dict
from project.src.utils.path_utils import get_readonly_sources_path
from project.src.utils.error_utils import create_error_response, create_success_response


def get_paper_topics() -> Dict:
    """
    Reads and returns the list of science paper topics.

    Parses readonly_sources_of_truth/science_papers_topics.txt where
    each non-empty line is a topic name.

    Returns:
        dict: {
            "success": bool,
            "topics": list[str] (e.g. ["Physics", "Computer Science", ...]),
            "count": int,
            "error": str (if success=False)
        }
    """
    try:
        topics_file = os.path.join(get_readonly_sources_path(), "science_papers_topics.txt")

        if not os.path.exists(topics_file):
            return create_error_response(
                "science_papers_topics.txt not found",
                details={"expected_path": topics_file}
            )

        with open(topics_file, 'r', encoding='utf-8') as f:
            topics = [line.strip() for line in f if line.strip()]

        if not topics:
            return create_error_response("science_papers_topics.txt is empty")

        return create_success_response({
            "topics": topics,
            "count": len(topics)
        })

    except Exception as e:
        return create_error_response(
            "Failed to read science paper topics",
            details={"error": str(e)}
        )
