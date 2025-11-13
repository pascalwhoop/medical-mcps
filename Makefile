.PHONY: server server-no-reload help test-watch test

export SENTRY_DSN=https://14d9c0d3d267359f2f8e3f1513f019c0@o4510353175085056.ingest.de.sentry.io/4510353181769808

install: 
	uv sync
# Start the MCP server with uvicorn and livereload
server:
	uv run uvicorn medical_mcps.http_server:app --reload --host 0.0.0.0 --port 8000

# Start the MCP server without auto-reload
server-no-reload:
	uv run uvicorn medical_mcps.http_server:app --host 0.0.0.0 --port 8000

# Run pytest-watch to automatically run tests on file changes
test-watch:
	uv run ptw --runner "uv run pytest"

# Run all tests (excluding slow Pathway Commons tests)
test: install
	uv run pytest tests/ --ignore=tests/test_pathwaycommons_tools.tavern.yaml

# Run slow tests (Pathway Commons) with extended timeout
test-slow: install
	uv run pytest tests/test_pathwaycommons_tools.tavern.yaml --timeout=200

# Run all tests including slow ones
test-all: install
	uv run pytest tests/ --timeout=200

inspector: 
	npx @modelcontextprotocol/inspector@latest