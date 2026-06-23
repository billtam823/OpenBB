"""API key authentication extension for the OpenBB Platform API.

Each request must carry a valid key in the `x-api-key` header. Keys come from
the OPENBB_API_KEYS env var (JSON object mapping client name -> key) or a file
referenced by OPENBB_API_KEYS_FILE. Revoke a client by removing its entry and
redeploying. Selected with OPENBB_API_AUTH_EXTENSION=apikey_auth; requires
OPENBB_API_AUTH=true so the command routes invoke the hook.
"""

import json
import logging
import os
import secrets
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from openbb_core.app.model.user_settings import UserSettings
from openbb_core.app.service.user_service import UserService

logger = logging.getLogger("uvicorn.error")

API_KEY_HEADER_NAME = "x-api-key"

# auto_error=False so a missing header reaches our handler (uniform 401) rather
# than FastAPI raising 403 before our code runs.
_api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)

# The loader requires a `router` attribute. We expose no extra endpoints
# (the default /user/me is intentionally not re-exposed).
router = APIRouter()


def _load_keys() -> dict:
    """Load the client->key map from env/file. Returns {} on any problem (fail closed)."""
    raw = os.environ.get("OPENBB_API_KEYS")
    if not raw:
        path = os.environ.get("OPENBB_API_KEYS_FILE")
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as file:
                raw = file.read()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        logger.error("OPENBB_API_KEYS is not valid JSON; rejecting all requests.")
        return {}
    if not isinstance(data, dict):
        logger.error("OPENBB_API_KEYS must be a JSON object; rejecting all requests.")
        return {}
    return {str(k): str(v) for k, v in data.items()}


def _is_valid(api_key: Optional[str]) -> bool:
    """Constant-time check of the presented key against every configured key."""
    if not api_key:
        return False
    valid = False
    for value in _load_keys().values():
        # Evaluate all entries (no early return) to keep timing uniform.
        if secrets.compare_digest(api_key, value):
            valid = True
    return valid


async def auth_hook(
    api_key: Annotated[Optional[str], Depends(_api_key_header)],
) -> None:
    """Reject the request unless a valid API key is presented."""
    if not _is_valid(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": API_KEY_HEADER_NAME},
        )


async def user_settings_hook(
    _: Annotated[None, Depends(auth_hook)],
) -> UserSettings:
    """After auth passes, return the server's user settings (provider creds, etc.)."""
    return UserService.read_from_file()
