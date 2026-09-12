"""Safe, allow-listed reads for repository-owned text assets."""

from collections.abc import Collection
from pathlib import Path


class UnsafeFilePathError(ValueError):
    """Raised when a requested file escapes its approved directory or type."""


class ApprovedFileNotFoundError(FileNotFoundError):
    """Raised when an approved asset path does not point to a regular file."""


def read_allowed_text(
    path: Path,
    *,
    allowed_root: Path,
    allowed_suffixes: Collection[str],
) -> str:
    """Read UTF-8 text only when the resolved path stays within an allow-listed root."""
    resolved_root = allowed_root.resolve()
    resolved_path = path.resolve()
    normalized_suffixes = {suffix.lower() for suffix in allowed_suffixes}
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise UnsafeFilePathError("File path must stay within its approved directory.") from error
    if resolved_path.suffix.lower() not in normalized_suffixes:
        raise UnsafeFilePathError("File type is not approved for this operation.")
    if not resolved_path.is_file():
        raise ApprovedFileNotFoundError("Approved file does not exist.")
    return resolved_path.read_text(encoding="utf-8")
