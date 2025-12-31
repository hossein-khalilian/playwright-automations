FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies (runtime only)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    wget \
    tk \
    tcl \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxft2 \
    && rm -rf /var/lib/apt/lists/*

# Create a fixed non-root user
RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Install Playwright system dependencies and browsers
# Set PLAYWRIGHT_BROWSERS_PATH to a system-wide location accessible to all users
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN mkdir -p /ms-playwright && \
    playwright install-deps chromium && \
    playwright install chromium && \
    chmod -R 755 /ms-playwright



# Copy app code
COPY . .

# Fix ownership once
RUN chown -R appuser:appuser /app

# Drop privileges
USER appuser

CMD ["python", "main.py"]
