from pydantic import BaseModel, Field


class CodeTask(BaseModel):
    task: str = Field(min_length=5, max_length=2000)


from pydantic import BaseModel, Field, model_validator


class CodePlan(BaseModel):
    summary: str = Field(
        description="Summary of the proposed change."
    )
    files_to_inspect: list[str] = Field(
        description="Repository-relative paths to inspect."
    )
    steps: list[str] = Field(
        description="Ordered implementation steps."
    )
    acceptance_criteria: list[str] = Field(
        description="List of verifiable success criteria."
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data):
        if not isinstance(data, dict):
            return data

        data = data.copy()

        # Accept the known alternative field name.
        if "files_to_inspect" not in data and "files_to_modify" in data:
            data["files_to_inspect"] = data.pop("files_to_modify")

        # Normalize a single criterion into a list.
        criteria = data.get("acceptance_criteria")
        if isinstance(criteria, str):
            data["acceptance_criteria"] = [criteria]

        # Normalize a single path into a list.
        paths = data.get("files_to_inspect")
        if isinstance(paths, str):
            data["files_to_inspect"] = [paths]

        # Reject malformed list fields rather than guessing.
        for field in ("steps", "acceptance_criteria", "files_to_inspect"):
            value = data.get(field)
            if value is not None and not isinstance(value, list):
                raise ValueError(f"{field} must be a list or a supported string.")

        return data


class ProposedPatch(BaseModel):
    file_path: str
    explanation: str
    original_code: str
    proposed_code: str