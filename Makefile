# plann Makefile

.PHONY: help install dev test lint clean uninstall

PYTHON ?= python3
VENV = venv

help:
	@echo "plann - Command-line interface to calendars"
	@echo ""
	@echo "Installation:"
	@echo "  sudo make install                  Install system-wide"
	@echo "  make install                       Install for current user"
	@echo "  make uninstall                     Uninstall plann"
	@echo ""
	@echo "Development:"
	@echo "  make dev                           Install in development mode"
	@echo "  make test                          Run tests"
	@echo "  make lint                          Run linter"
	@echo "  make clean                         Clean build artifacts"

# Create virtual environment
venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
		$(VENV)/bin/pip install --upgrade pip; \
	fi

# Install package: auto-detects root, uv, pipx, or falls back to pip --user
install:
	@if [ "$$(id -u)" = "0" ]; then \
		echo "Installing plann system-wide..."; \
		pip install .; \
	elif command -v uv >/dev/null 2>&1; then \
		echo "Installing with uv..."; \
		uv tool install .; \
	elif command -v pipx >/dev/null 2>&1; then \
		echo "Installing with pipx..."; \
		pipx install .; \
	else \
		echo "Tip: install uv or pipx for isolated installs (pacman -S uv, apt install pipx)"; \
		PIP_BREAK_SYSTEM_PACKAGES=1 pip install --user .; \
	fi

# Uninstall plann
uninstall:
	@if [ "$$(id -u)" = "0" ]; then \
		pip uninstall --break-system-packages -y plann; \
	else \
		pip uninstall -y plann; \
	fi

# Install in development mode
dev:
	@echo "Installing in development mode..."
	@PIP_BREAK_SYSTEM_PACKAGES=1 pip install -e ".[dev]"
	@echo ""
	@echo "Installed! Run: plann --help"

# Run tests
test:
	@python -m pytest tests/ -v

# Run linter
lint:
	@python -m ruff check .

# Clean build artifacts
clean:
	@rm -rf $(VENV) build dist *.egg-info .pytest_cache .ruff_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
