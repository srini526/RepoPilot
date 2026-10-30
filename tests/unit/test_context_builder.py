from packages.repository_tools.context_builder import (
    collect_repository_context,
)


def test_collects_relevant_files(tmp_path):
    (tmp_path / "calculator.py").write_text(
        "def divide(a, b):\n    return a / b\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "# Calculator project\n",
        encoding="utf-8",
    )

    result = collect_repository_context(
        tmp_path,
        "Fix divide in calculator.py",
    )

    paths = [item["path"] for item in result["files"]]

    assert "calculator.py" in paths
    assert result["file_count"] == len(result["files"])


def test_respects_max_files(tmp_path):
    for name in ["a.py", "b.py", "c.py"]:
        (tmp_path / name).write_text(
            f"# {name}\n",
            encoding="utf-8",
        )

    result = collect_repository_context(
        tmp_path,
        "inspect Python files",
        max_files=2,
    )

    assert result["file_count"] <= 2


def test_respects_context_character_limit(tmp_path):
    (tmp_path / "large.py").write_text(
        "x" * 500,
        encoding="utf-8",
    )

    result = collect_repository_context(
        tmp_path,
        "inspect large.py",
        max_chars=100,
    )

    assert result["total_chars"] <= 100


def test_does_not_include_secret_files(tmp_path):
    (tmp_path / "app.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        "API_KEY=secret\n",
        encoding="utf-8",
    )

    result = collect_repository_context(
        tmp_path,
        "inspect app.py and .env",
    )

    paths = [item["path"] for item in result["files"]]

    assert "app.py" in paths
    assert ".env" not in paths


def test_rejects_empty_task(tmp_path):
    try:
        collect_repository_context(tmp_path, " ")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for an empty task")