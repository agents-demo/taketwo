# Sandbox image for TakeTwo jobs: run reproduction workers in isolation.
#   docker build -t taketwo-sandbox .
#   SANDBOX_IMAGE=taketwo-sandbox  (interfaces/runner.py wraps the worker in it)
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt \
    && python -m playwright install --with-deps chromium

COPY . .
RUN pip install -e .

# The runner appends `-m taketwo.interfaces.worker <args>`.
ENTRYPOINT ["python"]
