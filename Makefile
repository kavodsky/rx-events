.PHONY: help install install-dev test test-cov lint format clean build publish upload upload-testpypi

# Default target
help:
	@echo "Available targets:"
	@echo "  install       - Install production dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  test          - Run tests"
	@echo "  test-cov      - Run tests with coverage"
	@echo "  lint          - Run linting checks"
	@echo "  format        - Format code with black"
	@echo "  clean         - Clean build artifacts and cache"
	@echo "  build         - Build the package"
	@echo "  upload        - Upload built package to PyPI (requires build first)"
	@echo "  upload-testpypi - Upload built package to TestPyPI (requires build first)"
	@echo "  publish       - Build and publish to PyPI (requires credentials)"

# Install production dependencies
install:
	uv pip install -e .
	@echo "✅ Production dependencies installed"

# Install development dependencies
install-dev:
	uv pip install -e ".[dev]"
	@echo "✅ Development dependencies installed"

# Run tests
test:
	uv run pytest tests/ -v

# Run tests with coverage
test-cov:
	uv run pytest tests/ --cov=rx_events --cov-report=html --cov-report=term
	@echo "📊 Coverage report generated in htmlcov/index.html"

# Run linting
lint:
	uv run mypy rx_events/
	@echo "✅ Linting complete"

# Format code
format:
	uv run black rx_events/ tests/
	@echo "✅ Code formatted"

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "🧹 Cleaned build artifacts"

# Build the package
build: clean
	uv build
	@echo "📦 Package built in dist/"

# Upload to PyPI (requires build first and proper credentials)
upload: build
	@echo "⚠️  Make sure you have PyPI credentials configured"
	@if command -v twine >/dev/null 2>&1; then \
		twine upload dist/*; \
	else \
		echo "⚠️  twine not found. Installing twine..."; \
		uv pip install twine; \
		twine upload dist/*; \
	fi
	@echo "🚀 Package uploaded to PyPI"

# Upload to TestPyPI (requires build first and proper credentials)
upload-testpypi: build
	@echo "⚠️  Make sure you have TestPyPI credentials configured"
	@if command -v twine >/dev/null 2>&1; then \
		twine upload --repository testpypi dist/*; \
	else \
		echo "⚠️  twine not found. Installing twine..."; \
		uv pip install twine; \
		twine upload --repository testpypi dist/*; \
	fi
	@echo "🚀 Package uploaded to TestPyPI"

# Publish to PyPI (builds and publishes in one step)
publish: build
	@echo "⚠️  Make sure you have PyPI credentials configured"
	uv publish
	@echo "🚀 Package published to PyPI"

# Setup: install everything needed for development
setup: install-dev
	@echo "🚀 Development environment ready!"

# Run all checks (format, lint, test)
check: format lint test
	@echo "✅ All checks passed!"
