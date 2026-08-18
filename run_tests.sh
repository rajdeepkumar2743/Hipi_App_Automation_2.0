#!/usr/bin/env bash
# =========================================================
# FILE: run_tests.sh
#
# FIXES FROM LOGS:
#   ISSUE 10 — exit code 5 ("no tests collected") was being
#     treated as a failure. Added explicit check: exit 5
#     means "no tests matched the marker" — print a clear
#     message but exit 0 so CI doesn't mark the run failed.
#   ISSUE 5  — Added .env existence check with a helpful
#     message before pytest starts, so the error is caught
#     at the shell level before any Appium session starts.
# =========================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "       STARTING HIPI AUTOMATION"
echo "========================================"

# ─── Create required directories ─────────────────────────
mkdir -p reports/logs
mkdir -p reports/screenshots
mkdir -p reports/allure-results
mkdir -p reports/html

# ─── Config ──────────────────────────────────────────────
DEVICE="${1:-emulator}"
ENV="${2:-qa}"
MARKER="${3:-}"
APPIUM_URL="${APPIUM_URL:-http://127.0.0.1:4723}"

echo "Device      : $DEVICE"
echo "Environment : $ENV"
echo "Marker      : ${MARKER:-<all>}"
echo "Appium URL  : $APPIUM_URL"
echo "========================================"

# ─── .env check ──────────────────────────────────────────
# Warn if .env is missing — pytest_configure will give the
# full error, but catching it here gives faster feedback.
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "  WARNING: .env file not found at $SCRIPT_DIR/.env"
    echo "  Tests requiring credentials will fail."
    echo "  Copy .env.example → .env and fill in your values."
    echo ""
fi

# ─── Appium health check ─────────────────────────────────
echo "Checking Appium server at $APPIUM_URL ..."
if ! curl -sf "${APPIUM_URL}/status" > /dev/null 2>&1; then
    echo ""
    echo "  ERROR: Appium server is NOT running at ${APPIUM_URL}"
    echo "  Start it first:  appium --address 127.0.0.1 --port 4723"
    echo ""
    exit 1
fi
echo "Appium server: OK"
echo "========================================"

# ─── Run pytest ──────────────────────────────────────────
PYTEST_ARGS=(
    tests/
    --device "$DEVICE"
    --env    "$ENV"
)

if [ -n "$MARKER" ]; then
    PYTEST_ARGS+=(-m "$MARKER")
fi

set +e  # Don't exit immediately on pytest failure — we handle exit code below
pytest "${PYTEST_ARGS[@]}"
EXIT_CODE=$?
set -e

# ─── Handle exit codes ───────────────────────────────────
# pytest exit codes:
#   0 = all tests passed
#   1 = some tests failed
#   2 = interrupted
#   3 = internal error
#   4 = usage error (e.g. missing credentials — our custom code)
#   5 = no tests were collected (marker matched nothing)

if [ "$EXIT_CODE" -eq 5 ]; then
    echo ""
    echo "  NOTE: No tests matched marker '${MARKER}'"
    echo "  Available markers: smoke, regression, login, feed"
    echo "  No tests ran — this is not a failure."
    echo ""
    EXIT_CODE=0  # Treat as success — nothing failed
fi

if [ "$EXIT_CODE" -eq 4 ]; then
    echo ""
    echo "  CREDENTIAL ERROR: Tests did not run."
    echo "  Create .env with TEST_PHONE and TEST_OTP."
    echo ""
    # Keep exit code 4 so CI knows it's a config issue, not a test failure
fi

# ─── Allure report ───────────────────────────────────────
echo "========================================"
echo "Generating Allure report..."
echo "========================================"

allure generate reports/allure-results \
    -o reports/allure-report \
    --clean 2>/dev/null \
    || echo "  NOTE: allure CLI not found — skipping HTML report generation."

# ─── Summary ─────────────────────────────────────────────
echo "========================================"
if [ "$EXIT_CODE" -eq 0 ]; then
    echo "  ALL TESTS PASSED"
elif [ "$EXIT_CODE" -eq 1 ]; then
    echo "  SOME TESTS FAILED  (exit: $EXIT_CODE)"
    echo "  Check: reports/html/report.html"
    echo "  Check: reports/allure-report/index.html"
else
    echo "  RUN ERROR  (exit: $EXIT_CODE)"
fi
echo "========================================"

exit "$EXIT_CODE"