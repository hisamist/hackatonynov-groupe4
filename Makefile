.PHONY: up down logs build open

# Start the stack and auto-open the chat + demo pages in a browser.
up:
	./start.sh

# Build images without starting.
build:
	docker compose build

# Stop and remove containers.
down:
	docker compose down

# Follow logs.
logs:
	docker compose logs -f

# Open the pages without (re)starting the stack.
open:
	@WEB_PORT=$${WEB_PORT:-5050}; \
	xdg-open "http://localhost:$$WEB_PORT/" 2>/dev/null || open "http://localhost:$$WEB_PORT/" 2>/dev/null || echo "Open http://localhost:$$WEB_PORT/ manually"; \
	xdg-open "http://localhost:$$WEB_PORT/demo" 2>/dev/null || open "http://localhost:$$WEB_PORT/demo" 2>/dev/null || echo "Open http://localhost:$$WEB_PORT/demo manually"
