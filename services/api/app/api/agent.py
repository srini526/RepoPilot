from fastapi import APIRouter, HTTPException

from services.api.app.agent_workflow import build_graph
from services.api.app.schemas.agent import CodeTask

import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/propose")
def propose_code_change(request: CodeTask):
    try:
        graph = build_graph()

        result = graph.invoke({
            "task": request.task,
        })

        return {
            "status": "proposal_ready",
            "plan": result["plan"],
            "patch": result["patch"],
            "applied": False,
            "tests_run": False,
        }

    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except Exception as exc:
        # Avoid exposing provider credentials or internal traces.
        raise HTTPException(
            status_code=502,
            detail="The coding workflow failed. Check the server logs.",
        ) from exc

@router.post("/execute")
def execute_code_task(request: CodeTask):
    try:
        graph = build_graph()

        result = graph.invoke({"task": request.task})

        execution = result.get("execution", {})

        return {
            "status": execution.get("status", "unknown"),
            "plan": result.get("plan"),
            "patch": execution.get("final_patch", result.get("patch")),
            "patch_applied": execution.get("patch_applied", False),
            "tests_passed": execution.get("tests", {}).get("passed", False),
            "retries_used": execution.get("retries_used", 0),
            "attempts": execution.get("attempts", []),
        }

    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # except Exception as exc:
    #     raise HTTPException(
    #         status_code=502,
    #         detail="The coding workflow failed. Check server logs.",
    #     ) from exc

    except Exception:
        logger.exception("Coding workflow failed")
        raise HTTPException(
            status_code=500,
            detail="The coding workflow failed. Check server logs.",
        )