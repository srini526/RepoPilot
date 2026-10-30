from packages.repository_tools.patch_tools import apply_replacement
from packages.repository_tools.repository_tools import read_file
from packages.repository_tools.test_runner import run_pytest
from packages.repository_tools.workspace import create_workspace
from services.api.app.repair_agent import propose_repair_patch


def execute_patch(
    repository_root,
    file_path,
    original_code,
    proposed_code,
    task="",
    plan=None,
    max_retries=2,
) -> dict:
    if not 0 <= max_retries <= 2:
        raise ValueError("max_retries must be between 0 and 2.")

    workspace = create_workspace(repository_root)

    current_patch = {
        "file_path": file_path,
        "original_code": original_code,
        "proposed_code": proposed_code,
    }

    attempts = []

    for attempt in range(max_retries + 1):
        apply_replacement(
            workspace=workspace,
            relative_path=current_patch["file_path"],
            original_code=current_patch["original_code"],
            proposed_code=current_patch["proposed_code"],
        )

        test_results = run_pytest(workspace)

        attempts.append({
            "attempt": attempt + 1,
            "tests": test_results,
            "patch": current_patch,
        })

        if test_results["passed"]:
            return {
                "status": "passed",
                "patch_applied": True,
                "tests": test_results,
                "workspace": str(workspace),
                "attempts": attempts,
                "retries_used": attempt,
                "final_patch": current_patch,
            }

        if test_results["timed_out"]:
            return {
                "status": "timed_out",
                "patch_applied": True,
                "tests": test_results,
                "workspace": str(workspace),
                "attempts": attempts,
                "retries_used": attempt,
                "final_patch": current_patch,
            }

        if attempt == max_retries:
            break

        # Read the latest code from the same workspace for the next repair.
        current_source = read_file(workspace, file_path)

        current_patch = propose_repair_patch(
            task=task,
            plan=plan or {},
            source_code=current_source,
            test_results=test_results,
            file_path=file_path,
        )

    return {
        "status": "tests_failed",
        "patch_applied": True,
        "tests": attempts[-1]["tests"],
        "workspace": str(workspace),
        "attempts": attempts,
        "retries_used": len(attempts) - 1,
        "final_patch": current_patch,
    }