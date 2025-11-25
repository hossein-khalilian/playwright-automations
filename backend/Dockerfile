FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on \
    PATH="/opt/venv/bin:$PATH"

# Create virtual env
RUN python -m venv /opt/venv

WORKDIR /app

COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

COPY . .

