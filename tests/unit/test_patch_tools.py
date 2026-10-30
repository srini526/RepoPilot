from pathlib import Path

import pytest

from packages.repository_tools.patch_tools import apply_replacement
from packages.repository_tools.repository_tools import RepositoryToolError


def test_apply_valid_patch(tmp_path: Path):
    source = "def divide(a, b):\n    return a * b\n"
    target = tmp_path / "calculator.py"
    target.write_text(source, encoding="utf-8")

    result = apply_replacement(
        tmp_path,
        "calculator.py",
        "return a * b",
        "return a / b",
    )

    assert "return a / b" in result
    assert target.read_text(encoding="utf-8") == result


def test_allows_another_repository_file(tmp_path: Path):
    target = tmp_path / "other.py"
    target.write_text("x = 1\n", encoding="utf-8")

    updated = apply_replacement(
        workspace=tmp_path,
        relative_path="other.py",
        original_code="x = 1",
        proposed_code="x = 2",
    )

    assert updated == "x = 2\n"
    assert target.read_text(encoding="utf-8") == "x = 2\n"


def test_reject_non_unique_original_code(tmp_path: Path):
    (tmp_path / "calculator.py").write_text(
        "return a * b\nreturn a * b\n",
        encoding="utf-8",
    )

    with pytest.raises(RepositoryToolError):
        apply_replacement(
            tmp_path,
            "calculator.py",
            "return a * b",
            "return a / b",
        )

def test_allows_another_repository_file(tmp_path):
    from packages.repository_tools.patch_tools import apply_replacement

    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")

    updated = apply_replacement(
        workspace=tmp_path,
        relative_path="app.py",
        original_code="VALUE = 1",
        proposed_code="VALUE = 2",
    )

    assert updated == "VALUE = 2\n"
    assert target.read_text(encoding="utf-8") == "VALUE = 2\n"