#!/bin/bash

# AWS Compliance Evidence Collector Test Runner
# Runs the full pytest test suite

set -e

# Get project root (directory containing this script)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "AWS Compliance Evidence Collector Tests"
echo "=========================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check if pytest is installed, install if needed
if ! python -m pytest --version &> /dev/null; then
    echo "Installing pytest..."
    pip install -q pytest
fi

echo "Running pytest with verbose output..."
echo ""

# Run pytest on the tests directory
python -m pytest tests/ -v

exit_code=$?

echo ""
echo "=========================================="
if [ $exit_code -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Some tests failed. Exit code: $exit_code"
fi
echo "=========================================="

exit $exit_code
