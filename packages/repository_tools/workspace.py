import shutil
import tempfile
from pathlib import Path

from packages.repository_tools.repository_tools import RepositoryToolError


def create_workspace(source: str | Path) -> Path:
    """Create a temporary copy of a sample repository."""

    source_root = Path(source).resolve(strict=True)

    if not source_root.is_dir():
        raise RepositoryToolError("Source repository must be a directory.")

    temporary_root = Path(tempfile.mkdtemp(prefix="repopilot-"))

    try:
        destination = temporary_root / "workspace"

        shutil.copytree(
            source_root,
            destination,
            ignore=shutil.ignore_patterns(
                ".git",
                ".venv",
                "__pycache__",
                ".pytest_cache",
                ".env",
                ".env.*",
            ),
        )

        return destination

    except Exception:
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise
