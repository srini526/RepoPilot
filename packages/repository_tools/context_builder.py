from pathlib import Path

from packages.repository_tools.repository_tools import (
    MAX_FILE_SIZE,
    RepositoryToolError,
    list_files,
    read_file,
)


MAX_CONTEXT_FILES = 8
MAX_CONTEXT_CHARS = 24_000

# Common files that provide useful project context.
PRIORITY_NAMES = {
    "readme.md",
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "main.py",
    "app.py",
}


def collect_repository_context(
    repository_root: str | Path,
    task: str,
    max_files: int = MAX_CONTEXT_FILES,
    max_chars: int = MAX_CONTEXT_CHARS,
) -> dict:
    """Collect bounded, relevant source context for a coding task."""

    if not task or not task.strip():
        raise ValueError("Task must not be empty.")

    if not 1 <= max_files <= MAX_CONTEXT_FILES:
        raise ValueError(
            f"max_files must be between 1 and {MAX_CONTEXT_FILES}."
        )

    if not 1 <= max_chars <= MAX_CONTEXT_CHARS:
        raise ValueError(
            f"max_chars must be between 1 and {MAX_CONTEXT_CHARS}."
        )

    root = Path(repository_root).resolve(strict=True)
    files = list_files(root)

    # Use task keywords to rank likely relevant files.
    keywords = {
        word.strip(".,:;()[]{}'\"`").casefold()
        for word in task.split()
        if len(word.strip(".,:;()[]{}'\"`")) >= 3
    }

    def score(relative_path: str) -> tuple[int, str]:
        path = Path(relative_path)
        name = path.name.casefold()
        path_text = relative_path.casefold()

        value = 0

        if name in PRIORITY_NAMES:
            value += 3

        if any(keyword in path_text for keyword in keywords):
            value += 5

        if path.suffix.casefold() in {
            ".py", ".js", ".jsx", ".ts", ".tsx",
            ".json", ".toml", ".yaml", ".yml",
        }:
            value += 2

        if "test" in path_text:
            value += 1

        return (-value, relative_path.casefold())

    ranked_files = sorted(files, key=score)

    context_files = []
    total_chars = 0

    for relative_path in ranked_files:
        if len(context_files) >= max_files:
            break

        try:
            content = read_file(root, relative_path)
        except RepositoryToolError:
            continue

        remaining = max_chars - total_chars

        if remaining <= 0:
            break

        # Leave room for the file heading.
        heading = f"\n--- FILE: {relative_path} ---\n"
        available = remaining - len(heading)

        if available <= 0:
            break

        if len(content) > available:
            if not context_files:
                content = content[:available]
            else:
                continue

        context_files.append({
            "path": relative_path,
            "content": content,
        })

        total_chars += len(heading) + len(content)

    return {
        "files": context_files,
        "file_count": len(context_files),
        "total_chars": total_chars,
        "truncated": total_chars >= max_chars,
    }