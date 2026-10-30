from pathlib import Path

import pytest

from packages.repository_tools.repository_tools import (
    RepositoryToolError,
    list_files,
    read_file,
    search_code,
)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    (tmp_path / "calculator.py").write_text(
        "def divide(a, b):\n    return a * b\n",
        encoding="utf-8",
    )

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_calculator.py").write_text(
        "from calculator import divide\n",
        encoding="utf-8",
    )

    (tmp_path / ".env").write_text(
        "SECRET=do-not-read",
        encoding="utf-8",
    )

    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text(
        "internal git data",
        encoding="utf-8",
    )

    return tmp_path


def test_list_files(repository: Path):
    files = list_files(repository)

    assert "calculator.py" in files
    assert "tests/test_calculator.py" in files
    assert ".env" not in files
    assert ".git/config" not in files


def test_read_file(repository: Path):
    content = read_file(repository, "calculator.py")

    assert "return a * b" in content


def test_search_code(repository: Path):
    matches = search_code(repository, "divide")

    assert matches
    assert matches[0]["path"] == "calculator.py"
    assert matches[0]["line"] == 1


def test_reject_parent_directory(repository: Path):
    with pytest.raises(RepositoryToolError):
        read_file(repository, "../outside.txt")


def test_reject_absolute_path(repository: Path):
    with pytest.raises(RepositoryToolError):
        read_file(repository, str(repository / "calculator.py"))


def test_reject_secret_file(repository: Path):
    with pytest.raises(RepositoryToolError):
        read_file(repository, ".env")
