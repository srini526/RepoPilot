import os
from pathlib import Path


# Avoid reading unexpectedly large files into memory.
MAX_FILE_SIZE = 1_000_000  # 1 MB

# Directories excluded from repository inspection.
IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
}

# Secret and environment files excluded from inspection.
IGNORED_FILES = {
    ".env",
    ".env.local",
    ".env.production",
}


class RepositoryToolError(Exception):
    """Raised when a repository operation cannot be completed safely."""


def _is_link_or_junction(path: Path) -> bool:
    """Detect symbolic links and Windows directory junctions."""
    if path.is_symlink():
        return True

    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def _resolve_repository_path(
    root: str | Path,
    relative_path: str | Path = ".",
) -> Path:
    """Resolve a path and ensure it stays inside the repository root."""

    try:
        repository_root = Path(root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RepositoryToolError(
            "Repository root is unavailable."
        ) from exc

    if not repository_root.is_dir():
        raise RepositoryToolError(
            "Repository root must be a directory."
        )

    candidate_input = Path(relative_path)

    if (
        candidate_input.is_absolute()
        or candidate_input.drive
        or ".." in candidate_input.parts
    ):
        raise RepositoryToolError(
            "Use a repository-relative path without parent traversal."
        )

    # Inspect the original path components before resolving them.
    # Otherwise, resolve() could hide a symlink in the path.
    current = repository_root

    for part in candidate_input.parts:
        current = current / part

        if _is_link_or_junction(current):
            raise RepositoryToolError(
                "Symbolic links and directory junctions are not allowed."
            )

    try:
        candidate = current.resolve(strict=True)
        candidate.relative_to(repository_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise RepositoryToolError(
            "Path does not exist or is outside the repository."
        ) from exc

    return candidate


def _is_ignored(path: Path) -> bool:
    """Return whether a repository-relative path should be skipped."""

    if any(part in IGNORED_DIRS for part in path.parts):
        return True

    if path.name in IGNORED_FILES:
        return True

    if path.name.startswith(".env."):
        return True

    return False


def list_files(
    root: str | Path,
    relative_path: str | Path = ".",
) -> list[str]:
    """List eligible files relative to the repository root."""

    repository_root = Path(root).resolve(strict=True)
    directory = _resolve_repository_path(repository_root, relative_path)

    if not directory.is_dir():
        raise RepositoryToolError(
            "The requested path is not a directory."
        )

    results: list[str] = []

    for current_root, directories, filenames in os.walk(
        directory,
        followlinks=False,
    ):
        current = Path(current_root)

        directories[:] = sorted(
            name
            for name in directories
            if name not in IGNORED_DIRS
            and not _is_link_or_junction(current / name)
        )

        for filename in sorted(filenames):
            file_path = current / filename
            relative_file = file_path.relative_to(
                repository_root
            )

            if _is_ignored(relative_file):
                continue

            if _is_link_or_junction(file_path):
                continue

            if not file_path.is_file():
                continue

            results.append(relative_file.as_posix())

    return sorted(results)


def read_file(
    root: str | Path,
    relative_path: str | Path,
) -> str:
    """Read a small UTF-8 text file inside the repository."""

    repository_root = Path(root).resolve(strict=True)
    file_path = _resolve_repository_path(
        repository_root,
        relative_path,
    )

    if not file_path.is_file():
        raise RepositoryToolError(
            "The requested path is not a file."
        )

    relative_file = file_path.relative_to(repository_root)

    if _is_ignored(relative_file):
        raise RepositoryToolError(
            "This file is excluded from inspection."
        )

    if file_path.stat().st_size > MAX_FILE_SIZE:
        raise RepositoryToolError(
            "File exceeds the 1 MB size limit."
        )

    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RepositoryToolError(
            "File could not be read as UTF-8 text."
        ) from exc


def search_code(
    root: str | Path,
    query: str,
) -> list[dict[str, str | int]]:
    """Search eligible repository files for matching lines."""

    if not query or not query.strip():
        raise ValueError(
            "Search query must not be empty."
        )

    repository_root = Path(root).resolve(strict=True)
    matches: list[dict[str, str | int]] = []

    for relative_path in list_files(repository_root):
        try:
            content = read_file(
                repository_root,
                relative_path,
            )
        except RepositoryToolError:
            continue

        for line_number, line in enumerate(
            content.splitlines(),
            start=1,
        ):
            if query.casefold() in line.casefold():
                matches.append({
                    "path": relative_path,
                    "line": line_number,
                    "text": line.strip(),
                })

    return matches