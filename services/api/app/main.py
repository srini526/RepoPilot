from fastapi import FastAPI

from services.api.app.api.agent import router as agent_router
from services.api.app.api.repository import router as repository_router

app = FastAPI(
    title="RepoPilot API",
    description="Backend for an autonomous AI software engineer.",
    version="0.2.0",
)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "repopilot-api",
    }


app.include_router(repository_router)
app.include_router(agent_router)