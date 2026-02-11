"""
Environment variable utilities for loading and accessing configuration.

This module provides functions for loading environment variables from .env files
and accessing them with validation.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv
from project.src.utils.path_utils import get_project_env_file_path, get_env_file_path


def load_env_from_readonly() -> None:
    """
    Loads environment variables from readonly_sources_of_truth/.env file.

    This function loads the base environment configuration from the
    readonly sources of truth folder.
    """
    readonly_env_path = get_env_file_path()

    if os.path.exists(readonly_env_path):
        load_dotenv(readonly_env_path)


def load_env_from_project() -> None:
    """
    Loads environment variables from project/src/.env file.

    This function loads the project-specific environment configuration
    which may override or extend the readonly configuration.
    """
    project_env_path = get_project_env_file_path()

    if os.path.exists(project_env_path):
        load_dotenv(project_env_path, override=True)


def load_all_env() -> None:
    """
    Loads environment variables from both readonly and project .env files.

    Loads readonly first, then project env (which can override readonly values).
    """
    load_env_from_readonly()
    load_env_from_project()


def get_env_var(key: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
    """
    Gets an environment variable with validation.

    Args:
        key: Environment variable name
        required: If True, raises ValueError if variable not found
        default: Default value if variable not found (only used if required=False)

    Returns:
        str or None: Environment variable value

    Raises:
        ValueError: If required=True and variable not found
    """
    value = os.getenv(key, default)

    if required and value is None:
        raise ValueError(
            f"Required environment variable '{key}' not found. "
            f"Please ensure it is set in project/src/.env or readonly_sources_of_truth/.env"
        )

    return value


def get_runware_api_key() -> str:
    """
    Gets the Runware AI API key from environment.

    Returns:
        str: Runware API key

    Raises:
        ValueError: If RUNWARE_AI_API_KEY not found
    """
    # Try both possible key names
    key = os.getenv("RUNWARE_AI_API_KEY") or os.getenv("RUNWARE_API_KEY")

    if not key:
        raise ValueError(
            "Runware API key not found. Please set RUNWARE_AI_API_KEY or RUNWARE_API_KEY "
            "in project/src/.env or readonly_sources_of_truth/.env"
        )

    return key


def get_tiktok_credentials() -> Dict[str, str]:
    """
    Gets TikTok API credentials from environment.

    Returns:
        dict: {
            "client_key": str,
            "client_secret": str,
            "access_token": str
        }

    Raises:
        ValueError: If any required TikTok credentials are missing
    """
    client_key = get_env_var("TIKTOK_CLIENT_KEY", required=False)
    client_secret = get_env_var("TIKTOK_CLIENT_SECRET", required=False)
    access_token = get_env_var("TIKTOK_ACCESS_TOKEN", required=False)

    missing = []
    if not client_key:
        missing.append("TIKTOK_CLIENT_KEY")
    if not client_secret:
        missing.append("TIKTOK_CLIENT_SECRET")
    if not access_token:
        missing.append("TIKTOK_ACCESS_TOKEN")

    if missing:
        raise ValueError(
            f"Missing TikTok API credentials: {', '.join(missing)}. "
            "Please add these to project/src/.env"
        )

    return {
        "client_key": client_key,
        "client_secret": client_secret,
        "access_token": access_token
    }
