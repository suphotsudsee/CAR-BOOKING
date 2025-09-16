"""File handling helpers used across the application."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def build_static_file_url(relative_path: Optional[str | Path]) -> Optional[str]:
    """Return the public static URL for *relative_path* under the upload root."""
    if relative_path in (None, ""):
        return None

    if isinstance(relative_path, Path):
        path = relative_path
    else:
        path = Path(str(relative_path))

    # Normalise to POSIX style and strip any leading slashes to avoid directory
    # traversal and duplicated separators when constructing the static URL.
    relative = path.as_posix().lstrip("/")
    return f"/static/{relative}" if relative else "/static"


__all__ = ["build_static_file_url"]
