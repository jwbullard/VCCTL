# Makefile for VCCTL packaging and distribution
# Supports building for Linux, Windows, and macOS

.PHONY: help clean build build-linux build-windows build-macos test package install dev-setup check-deps

# Configuration
PYTHON := python3
PIP := pip3
PROJECT_NAME := vcctl
VERSION := 1.0.0

# Directories
SRC_DIR := src
BUILD_DIR := build
DIST_DIR := dist
SCRIPTS_DIR := scripts

# Platform detection
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PLATFORM := linux
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM := macos
endif
ifdef OS
    ifeq ($(OS),Windows_NT)
        PLATFORM := windows
    endif
endif

# Default target
help:
	@echo "VCCTL Build System"
	@echo "=================="
	@echo ""
	@echo "Available targets:"
	@echo "  help           - Show this help message"
	@echo "  clean          - Clean build artifacts"
	@echo "  dev-setup      - Set up development environment"
	@echo "  check-deps     - Check system dependencies"
	@echo "  test           - Run test suite"
	@echo "  build          - Build for current platform"
	@echo "  build-linux    - Build Linux AppImage"
	@echo "  build-windows  - Build Windows installer"
	@echo "  build-macos    - Build macOS DMG"
	@echo "  package        - Create distribution packages"
	@echo "  install        - Install VCCTL locally"
	@echo ""
	@echo "Current platform: $(PLATFORM)"
	@echo "Python version: $(shell $(PYTHON) --version)"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR) $(DIST_DIR)
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Build artifacts cleaned"

# Development environment setup
dev-setup:
	@echo "🔧 Setting up development environment..."
	@$(PIP) install -r requirements.txt
	@$(PIP) install -e .
	@$(PIP) install pytest black flake8 mypy
	@echo "✅ Development environment ready"

# Check system dependencies
check-deps:
	@echo "🔍 Checking system dependencies..."
	@$(PYTHON) check_requirements.py
	@echo "✅ Dependency check completed"

# Run tests
test:
	@echo "🧪 Running test suite..."
	@$(PYTHON) -m pytest tests/ -v
	@echo "✅ Tests completed"

# Install locally
install:
	@echo "📦 Installing VCCTL locally..."
	@$(PIP) install .
	@echo "✅ VCCTL installed"

# Build for current platform
build: check-deps
ifeq ($(PLATFORM),linux)
	@$(MAKE) build-linux
else ifeq ($(PLATFORM),macos)
	@$(MAKE) build-macos
else ifeq ($(PLATFORM),windows)
	@$(MAKE) build-windows
else
	@echo "❌ Unknown platform: $(PLATFORM)"
	@exit 1
endif

# Build Linux AppImage
build-linux:
	@echo "🐧 Building Linux AppImage..."
	@chmod +x $(SCRIPTS_DIR)/build_linux.sh
	@$(SCRIPTS_DIR)/build_linux.sh

# Build Windows installer
build-windows:
	@echo "🪟 Building Windows installer..."
	@$(SCRIPTS_DIR)/build_windows.bat

# Build macOS DMG
build-macos:
	@echo "🍎 Building macOS DMG..."
	@chmod +x $(SCRIPTS_DIR)/build_macos.sh
	@$(SCRIPTS_DIR)/build_macos.sh

# Create all distribution packages
package: clean
	@echo "📦 Creating distribution packages..."
	@mkdir -p $(DIST_DIR)
	
	# Create source distribution
	@$(PYTHON) setup.py sdist
	@mv dist/*.tar.gz $(DIST_DIR)/ 2>/dev/null || true
	
	# Create wheel
	@$(PYTHON) setup.py bdist_wheel
	@mv dist/*.whl $(DIST_DIR)/ 2>/dev/null || true
	
	@echo "✅ Distribution packages created in $(DIST_DIR)/"

# Development targets
lint:
	@echo "🔍 Running linters..."
	@black --check $(SRC_DIR)/
	@flake8 $(SRC_DIR)/
	@mypy $(SRC_DIR)/

format:
	@echo "🎨 Formatting code..."
	@black $(SRC_DIR)/

# CI/CD targets
ci-test: dev-setup test lint

ci-build: clean build

# Documentation targets
docs:
	@echo "📚 Building documentation..."
	@cd docs && make html

docs-serve:
	@echo "🌐 Serving documentation..."
	@cd docs/_build/html && $(PYTHON) -m http.server 8000

# Release targets
version:
	@echo "Current version: $(VERSION)"

bump-version:
	@echo "📈 Bumping version..."
	# This would update version in setup.py and other files
	@echo "Manual version bump required"

release: clean test build package
	@echo "🚀 Release ready in $(DIST_DIR)/"

# Platform-specific install targets
install-linux: build-linux
	@echo "🐧 Installing on Linux..."
	@chmod +x $(DIST_DIR)/VCCTL-x86_64.AppImage
	@mkdir -p ~/.local/bin
	@cp $(DIST_DIR)/VCCTL-x86_64.AppImage ~/.local/bin/vcctl
	@echo "✅ VCCTL installed to ~/.local/bin/vcctl"

install-macos: build-macos
	@echo "🍎 Installing on macOS..."
	@cp -R $(DIST_DIR)/VCCTL.app /Applications/
	@echo "✅ VCCTL installed to /Applications/"

# Debug targets
debug-info:
	@echo "Debug Information"
	@echo "================="
	@echo "Platform: $(PLATFORM)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "PWD: $(PWD)"
	@echo "Build dir: $(BUILD_DIR)"
	@echo "Dist dir: $(DIST_DIR)"
	@echo "Git branch: $(shell git branch --show-current 2>/dev/null || echo 'unknown')"
	@echo "Git commit: $(shell git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

# Requirements
requirements:
	@echo "📋 Updating requirements..."
	@$(PIP) freeze > requirements.txt
	@echo "✅ Requirements updated"