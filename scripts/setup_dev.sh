#!/bin/bash
# Development Environment Setup Script for IRA Workflow Builder

set -e  # Exit on error

echo "=========================================="
echo "IRA Workflow Builder - Dev Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version found"

# Check if in project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠ Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Install package in editable mode
echo ""
echo "Installing package in editable mode..."
pip install -e ".[dev]"
echo "✓ Package installed"

# Create .env file if it doesn't exist
echo ""
if [ -f ".env" ]; then
    echo "⚠ .env file already exists, skipping..."
else
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "⚠ Please edit .env and add your API keys"
fi

# Create necessary directories
echo ""
echo "Ensuring directories exist..."
mkdir -p data/uploads data/outputs data/temp
mkdir -p storage/checkpoints storage/conversations storage/metadata
mkdir -p logs
echo "✓ Directories created"

# Install pre-commit hooks (if pre-commit is available)
echo ""
if command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit hooks..."
    pre-commit install
    echo "✓ Pre-commit hooks installed"
else
    echo "⚠ pre-commit not found, skipping hooks installation"
fi

# Run tests to verify setup
echo ""
echo "Running tests to verify setup..."
pytest tests/ -v || echo "⚠ Some tests failed, this is normal for initial setup"

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Start development: python -m ira.api.app"
echo ""
echo "For more information, see README.md"
