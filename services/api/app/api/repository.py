from fastapi import APIRouter, HTTPException, Query

from packages.repository_tools.repository_tools import (
    RepositoryToolError,
    list_files,
    read_file,
    search_code,
)
from services.api.app.core.config import REPOSITORY_ROOT

router = APIRouter(prefix="/repository", tags=["Repository"])


def handle_tool_error(exc: RepositoryToolError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/files")
def get_repository_files():
    try:
        return {
            "repository": REPOSITORY_ROOT.name,
            "files": list_files(REPOSITORY_ROOT),
        }
    except RepositoryToolError as exc:
        raise handle_tool_error(exc) from exc


@router.get("/file")
def get_repository_file(
    path: str = Query(..., description="Relative path inside the repository"),
):
    try:
        return {
            "path": path,
            "content": read_file(REPOSITORY_ROOT, path),
        }
    except RepositoryToolError as exc:
        raise handle_tool_error(exc) from exc


@router.get("/search")
def search_repository(
    q: str = Query(..., min_length=1, max_length=200),
):
    try:
        matches = search_code(REPOSITORY_ROOT, q)
        return {
            "query": q,
            "count": len(matches),
            "matches": matches,
        }
    except RepositoryToolError as exc:
        raise handle_tool_error(exc) from exc