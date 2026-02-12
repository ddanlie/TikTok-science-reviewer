"""
Tool for web search using DuckDuckGo.

Replaces Google Search (Gemini-only) with a model-agnostic alternative.
"""

import time
from typing import Dict
from ddgs import DDGS


BACKENDS = ["auto", "html", "lite"]


def web_search(query: str, max_results: int = 5) -> Dict:
    """
    Searches the web using DuckDuckGo and returns results.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)

    Returns:
        dict: {
            "success": bool,
            "results": list of {"title": str, "url": str, "snippet": str},
            "error": str (if success=False)
        }
    """
    last_error = None
    for backend in BACKENDS:
        try:
            ddgs = DDGS()
            raw = ddgs.text(
                query,
                region="wt-wt",
                max_results=max_results,
                backend=backend,
            )
            results = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
                for r in raw
            ]
            if results:
                return {"success": True, "results": results}
            # Empty results — try next backend after a short pause
            time.sleep(1)
        except Exception as e:
            last_error = e
            time.sleep(1)
            continue

    error_msg = f"All backends returned empty results. Last error: {last_error}" if last_error else "All backends returned empty results."
    return {"success": False, "results": [], "error": error_msg}
