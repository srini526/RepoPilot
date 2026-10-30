import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from services.api.app.schemas.agent import ProposedPatch


load_dotenv()


def propose_repair_patch(
    task: str,
    plan: dict,
    source_code: str,
    test_results: dict,
    file_path: str,
) -> dict:
    """Propose a minimal correction based on the latest test failures."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    model = ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=0,
    ).with_structured_output(ProposedPatch, method="json_mode",)

    prompt = f"""
Original task:
{task}

Implementation plan:
{plan}

File allowed to change:
{file_path}

Current source code:
{source_code}

Latest test results:
Exit code: {test_results.get("exit_code")}
Timed out: {test_results.get("timed_out")}
Test output:
{test_results.get("stdout", "")}

Test errors:
{test_results.get("stderr", "")}

Propose the smallest correction that addresses the test failures.

Requirements:
- Modify only the specified file.
- Return original_code as an exact, unique substring of the current source.
- Return proposed_code with the corrected replacement.
- Do not claim tests passed; the test runner must verify that.
- Do not include unrelated changes.
"""

    patch = model.invoke(
        [
            (
                "system",
                "You are a careful debugging agent. Diagnose test failures "
                "and propose minimal, verifiable code corrections.",
            ),
            ("human", prompt),
        ]
    )

    if patch.file_path != file_path:
        raise ValueError("Repair agent proposed a different file.")

    if not patch.original_code:
        raise ValueError("Repair agent returned an empty original_code.")

    if source_code.count(patch.original_code) != 1:
        raise ValueError(
            "Repair patch must match exactly one location in the current source."
        )

    if patch.original_code == patch.proposed_code:
        raise ValueError("Repair agent proposed no code changes.")

    return patch.model_dump()