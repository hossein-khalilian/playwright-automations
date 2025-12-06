FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on \
    PATH="/opt/venv/bin:$PATH"

# Install basic tools needed for playwright install-deps
RUN apt-get update && apt-get install -y \
    wget \
    tk \
    tcl \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxft2 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual env
RUN python -m venv /opt/venv

WORKDIR /app

COPY requirements.txt .

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright system dependencies and browsers
RUN --mount=type=cache,target=/ms-playwright \
    playwright install-deps chromium && \
    playwright install chromium

COPY . .

