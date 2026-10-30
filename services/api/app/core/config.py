import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

REPOSITORY_ROOT = Path(
    os.getenv(
        "REPILOT_REPOSITORY_ROOT",
        str(PROJECT_ROOT / "sample_repo"),
    )
).resolve()