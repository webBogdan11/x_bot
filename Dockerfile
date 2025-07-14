# Dockerfile
###############################################
# Base Image
###############################################
FROM python:3.13-slim AS python_base

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYSETUP_PATH="/code" \
    VENV_PATH="/code/.venv" \
    PATH="/code/.venv/bin:$PATH"

###############################################
# Builder / Production Image
###############################################
# We only need one stage here, since uv sync will populate the venv
FROM python_base

# bring in uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR $PYSETUP_PATH

# 1) Install all deps into .venv
COPY uv.lock pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

RUN playwright install --with-deps chromium

# 2) Copy the rest of your application
#    this includes src/, alembic/, Makefile, etc.
COPY . .

# no ENTRYPOINT or CMD—everything will be
# overridden by docker-compose / Makefile
