"""
Error handling utilities for standardized error responses and exit handling.

This module provides functions for creating consistent error/success responses
and handling exit scenarios with proper error messages.
"""

import sys
from typing import Dict, Optional


def create_error_response(message: str, details: Optional[Dict] = None) -> Dict:
    """
    Creates a standardized error response dictionary.

    Args:
        message: Error message describing what went wrong
        details: Optional dictionary with additional error details

    Returns:
        dict: {
            "success": False,
            "error": str,
            "details": dict (if provided)
        }
    """
    response = {
        "success": False,
        "error": message
    }

    if details:
        response["details"] = details

    return response


def create_success_response(data: Optional[Dict] = None) -> Dict:
    """
    Creates a standardized success response dictionary.

    Args:
        data: Optional dictionary with response data

    Returns:
        dict: {
            "success": True,
            ...data fields
        }
    """
    response = {"success": True}

    if data:
        response.update(data)

    return response


def exit_with_error(message: str, details: Optional[Dict] = None) -> None:
    """
    Prints an error message and exits the program with code 1.

    This function is used by human-facing adapter scripts to exit gracefully
    with clear error messages.

    Args:
        message: Error message describing what went wrong
        details: Optional dictionary with additional error details
    """
    print(f"\nERROR: {message}\n")

    if details:
        print("Details:")
        for key, value in details.items():
            print(f"  {key}: {value}")
        print()

    sys.exit(1)


def format_error_message(component: str, issue: str, solution: str = None) -> str:
    """
    Formats an error message with consistent structure.

    Args:
        component: Component or function where error occurred
        issue: Description of what went wrong
        solution: Optional suggestion for how to fix the issue

    Returns:
        str: Formatted error message
    """
    message = f"[{component}] - {issue}"

    if solution:
        message += f"\nSolution: {solution}"

    return message
