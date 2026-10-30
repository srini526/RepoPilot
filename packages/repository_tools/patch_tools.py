from packages.repository_tools.repository_tools import (
    RepositoryToolError,
    _resolve_repository_path,
    read_file,
)


def apply_replacement(
    workspace,
    relative_path,
    original_code,
    proposed_code,
) -> str:
    if not original_code:
        raise RepositoryToolError("Original code cannot be empty.")

    if original_code == proposed_code:
        raise RepositoryToolError("Patch does not change the code.")

    # Validate that the target is an eligible, readable repository file.
    file_path = _resolve_repository_path(workspace, relative_path)
    source = read_file(workspace, relative_path)

    if not file_path.is_file():
        raise RepositoryToolError("Target file does not exist.")

    if source.count(original_code) != 1:
        raise RepositoryToolError(
            "Original code must match exactly one location in the current file."
        )

    updated_source = source.replace(original_code, proposed_code, 1)

    # Verify the file has not changed before writing.
    if file_path.read_text(encoding="utf-8") != source:
        raise RepositoryToolError(
            "File changed while the patch was being prepared."
        )

    file_path.write_text(updated_source, encoding="utf-8")
    return updated_source