.PHONY: server server-no-reload help test-watch test

# Default target
help:
	@echo "Available targets:"
	@echo "  make server           - Start MCP server with uvicorn and livereload"
	@echo "  make server-no-reload - Start MCP server without auto-reload"
	@echo "  make test-watch       - Run pytest-watch to automatically run tests on file changes"
	@echo "  make test             - Run all tests"
	@echo "  make help             - Show this help message"

# Start the MCP server with uvicorn and livereload
server:
	uv run uvicorn medical_mcps.http_server:app --reload --host 0.0.0.0 --port 8000

# Start the MCP server without auto-reload
server-no-reload:
	uv run uvicorn medical_mcps.http_server:app --host 0.0.0.0 --port 8000

# Run pytest-watch to automatically run tests on file changes
test-watch:
	uv run ptw --runner "uv run pytest"

# Run all tests
test:
	uv run pytest tests/

