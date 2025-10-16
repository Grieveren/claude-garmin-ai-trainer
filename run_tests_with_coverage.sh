#!/bin/bash
#
# Run comprehensive test suite with coverage reporting
# Phase 2 - Track 2E: Automated Testing
#
# Usage: ./run_tests_with_coverage.sh [options]
#
# Options:
#   --unit          Run only unit tests
#   --integration   Run only integration tests
#   --scenario      Run only scenario tests
#   --performance   Run only performance tests
#   --all           Run all tests (default)
#   --quick         Skip slow tests
#   --verbose       Verbose output
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/brettgray/Coding/Garmin AI"
COVERAGE_THRESHOLD=80
GARMIN_SERVICE_COVERAGE=90
DATA_ACCESS_COVERAGE=85
DATA_PROCESSOR_COVERAGE=90

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI Training Optimizer - Test Suite${NC}"
echo -e "${BLUE}Phase 2 - Track 2E: Automated Testing${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Change to project directory
cd "$PROJECT_ROOT"

# Parse arguments
TEST_MARKER=""
SKIP_SLOW=""
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_MARKER="-m unit"
            shift
            ;;
        --integration)
            TEST_MARKER="-m integration"
            shift
            ;;
        --scenario)
            TEST_MARKER="-m scenario"
            shift
            ;;
        --performance)
            TEST_MARKER="-m performance"
            shift
            ;;
        --all)
            TEST_MARKER=""
            shift
            ;;
        --quick)
            SKIP_SLOW="-m 'not slow'"
            shift
            ;;
        --verbose)
            VERBOSE="-vv"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Activate virtual environment if it exists
if [ -d "venv/bin" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}ERROR: pytest not found. Install dependencies first:${NC}"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Clean previous coverage data
echo -e "${YELLOW}Cleaning previous coverage data...${NC}"
rm -rf .coverage htmlcov/ coverage.xml .pytest_cache/

# Run tests
echo ""
echo -e "${GREEN}Running tests...${NC}"
echo "Test markers: ${TEST_MARKER:-all tests}"
echo "Skip slow: ${SKIP_SLOW:-no}"
echo ""

# Run pytest with coverage
pytest $TEST_MARKER $SKIP_SLOW $VERBOSE \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --cov-fail-under=$COVERAGE_THRESHOLD \
    --tb=short \
    --maxfail=5 \
    --durations=10 \
    -ra

TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Results Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
fi

# Display coverage summary
echo ""
echo -e "${YELLOW}Coverage Summary:${NC}"
coverage report --skip-covered --sort=Cover | tail -20

# Check module-specific coverage
echo ""
echo -e "${YELLOW}Module-Specific Coverage Targets:${NC}"

# Extract coverage for specific modules
GARMIN_COV=$(coverage report 2>/dev/null | grep "app/services/garmin" | awk '{print $NF}' | sed 's/%//' || echo "0")
DATA_ACCESS_COV=$(coverage report 2>/dev/null | grep "app/services/data_access" | awk '{print $NF}' | sed 's/%//' || echo "0")
DATA_PROCESSOR_COV=$(coverage report 2>/dev/null | grep "app/services/data_processor" | awk '{print $NF}' | sed 's/%//' || echo "0")

echo -e "  Garmin Service: ${GARMIN_COV}% (target: >${GARMIN_SERVICE_COVERAGE}%)"
echo -e "  Data Access: ${DATA_ACCESS_COV}% (target: >${DATA_ACCESS_COVERAGE}%)"
echo -e "  Data Processor: ${DATA_PROCESSOR_COV}% (target: >${DATA_PROCESSOR_COVERAGE}%)"

echo ""
echo -e "${YELLOW}Coverage Report:${NC}"
echo "  HTML Report: file://${PROJECT_ROOT}/htmlcov/index.html"
echo "  XML Report: ${PROJECT_ROOT}/coverage.xml"

# Open HTML report in browser (optional)
if command -v open &> /dev/null; then
    echo ""
    read -p "Open HTML coverage report in browser? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "${PROJECT_ROOT}/htmlcov/index.html"
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Quality Metrics${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Count total tests
TOTAL_TESTS=$(pytest --collect-only -q 2>/dev/null | tail -1 | awk '{print $1}')
echo -e "Total Tests: ${TOTAL_TESTS}"

# Count by marker
UNIT_TESTS=$(pytest --collect-only -q -m unit 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
INTEGRATION_TESTS=$(pytest --collect-only -q -m integration 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
SCENARIO_TESTS=$(pytest --collect-only -q -m scenario 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
PERFORMANCE_TESTS=$(pytest --collect-only -q -m performance 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")

echo -e "  Unit Tests: ${UNIT_TESTS}"
echo -e "  Integration Tests: ${INTEGRATION_TESTS}"
echo -e "  Scenario Tests: ${SCENARIO_TESTS}"
echo -e "  Performance Tests: ${PERFORMANCE_TESTS}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Testing Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

exit $TEST_EXIT_CODE
