FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir pytest==9.2.0 \
    && useradd --uid 10001 --create-home runner

WORKDIR /workspace

USER 10001:10001

ENTRYPOINT ["python", "-m", "pytest"]