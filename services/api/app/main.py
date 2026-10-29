from fastapi import FastAPI

app = FastAPI(
    title="RepoPilot API",
    description="Backend for an autonomous AI software engineer.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "repopilot-api",
    }
