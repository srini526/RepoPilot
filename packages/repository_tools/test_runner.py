import subprocess
import uuid
from pathlib import Path


IMAGE_NAME = "repopilot-test-runner:py312"
DEFAULT_TIMEOUT_SECONDS = 30


def _tail(value, limit: int) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value or "")[-limit:]


def run_pytest(
    workspace,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    workspace_root = Path(workspace).resolve(strict=True)

    if not workspace_root.is_dir():
        raise ValueError("Workspace must be a valid directory.")

    container_name = f"repopilot-test-{uuid.uuid4().hex[:12]}"

    command = [
        "docker", "run",
        "--rm",
        "--name", container_name,
        "--network", "none",
        "--memory", "256m",
        "--cpus", "1",
        "--pids-limit", "64",
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", "10001:10001",
        "--mount",
        f"type=bind,source={workspace_root},target=/workspace,readonly",
        "--workdir", "/workspace",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        IMAGE_NAME,
        "-v",
        "-p", "no:cacheprovider",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": _tail(result.stdout, 12000),
            "stderr": _tail(result.stderr, 4000),
            "timed_out": False,
        }

    except subprocess.TimeoutExpired as exc:
        # The Docker CLI may time out while its container is still running.
        subprocess.run(
            ["docker", "kill", container_name],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        return {
            "exit_code": None,
            "passed": False,
            "stdout": _tail(exc.stdout, 12000),
            "stderr": _tail(exc.stderr, 4000),
            "timed_out": True,
        }