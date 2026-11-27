FROM python:3.12-slim

# Install uv and unzip
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends unzip curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Download FDA Orange Book flat files (patents, exclusivities, products)
COPY scripts/download_orangebook.sh ./scripts/
RUN bash scripts/download_orangebook.sh /app/data/orangebook

# Copy dependency files and metadata files (required by pyproject.toml)
COPY pyproject.toml uv.lock LICENSE README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY medical_mcps/ ./medical_mcps/

# Expose port
EXPOSE 8000

# Set environment variables
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV PYTHONUNBUFFERED=1
ENV ORANGE_BOOK_DIR=/app/data/orangebook

# Start from /app using the installed dependencies without resolving at runtime.
CMD ["/app/.venv/bin/python", "-m", "medical_mcps.http_server"]

