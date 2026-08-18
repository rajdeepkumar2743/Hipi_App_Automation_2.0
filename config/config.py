# =========================================================
# FILE: config/config.py
#
# CHANGES FROM AUDIT:
#   - Removed EXPECTED_PACKAGE (identical to APP_PACKAGE → dead duplication, ISSUE M-07)
#   - Added os.getenv() support for every value so CI/CD
#     can override without touching code (ISSUE-09)
#   - Kept all existing field names — zero breaking changes
# =========================================================

import os


class Config:

    # =====================================================
    # APPIUM
    # =====================================================

    APPIUM_SERVER = os.getenv("APPIUM_SERVER", "http://127.0.0.1:4723")

    # =====================================================
    # PLATFORM
    # =====================================================

    PLATFORM_NAME     = os.getenv("PLATFORM_NAME", "Android")
    AUTOMATION_NAME   = os.getenv("AUTOMATION_NAME", "UiAutomator2")

    # =====================================================
    # DEVICE (overridden per-run via --device CLI flag)
    # =====================================================

    DEVICE_NAME       = os.getenv("DEVICE_NAME", "Android Device")
    UDID              = os.getenv("UDID", "emulator-5554")

    # =====================================================
    # APP
    # =====================================================

    APP_PACKAGE       = os.getenv("APP_PACKAGE", "com.zee5.hipi")
    APP_ACTIVITY      = os.getenv("APP_ACTIVITY", "com.creatoreconomy.MainActivity")
    APP_WAIT_ACTIVITY = os.getenv("APP_WAIT_ACTIVITY", "com.creatoreconomy.MainActivity")

    # =====================================================
    # RESET
    # =====================================================

    NO_RESET          = os.getenv("NO_RESET", "false").lower() == "true"
    FULL_RESET        = os.getenv("FULL_RESET", "false").lower() == "true"

    # =====================================================
    # TIMEOUTS (optimized for speed)
    # =====================================================

    IMPLICIT_WAIT     = int(os.getenv("IMPLICIT_WAIT", "5"))
    EXPLICIT_WAIT     = int(os.getenv("EXPLICIT_WAIT", "10"))

    # Separate longer timeout for cold-start app-ready check
    APP_READY_TIMEOUT = int(os.getenv("APP_READY_TIMEOUT", "15"))

    NEW_COMMAND_TIMEOUT                  = int(os.getenv("NEW_COMMAND_TIMEOUT", "120"))
    ADB_EXEC_TIMEOUT                     = int(os.getenv("ADB_EXEC_TIMEOUT", "20000"))
    UIAUTOMATOR2_SERVER_INSTALL_TIMEOUT  = int(os.getenv("UIAUTOMATOR2_SERVER_INSTALL_TIMEOUT", "60000"))
    UIAUTOMATOR2_SERVER_LAUNCH_TIMEOUT   = int(os.getenv("UIAUTOMATOR2_SERVER_LAUNCH_TIMEOUT", "60000"))

    # ROOT CAUSE FIX for the repeated "timeout of 240000ms exceeded" /
    # "Could not proxy command to the remote server" failures seen in
    # historical runs, where a single hung UiAutomator2 command could
    # block a test for a full 4 minutes: Appium's UiAutomator2 driver
    # defaults uiautomator2ServerReadTimeout to 240000ms (4 min) when
    # this capability isn't set. Lowering it means a genuinely dead/
    # hung UiA2 instrumentation process is detected and surfaced in
    # ~20-30s instead of 4 minutes, so the existing retry/recovery
    # logic (conftest._create_driver_with_retry, BasePage.recover_app)
    # gets a chance to actually run within a sane test timeout instead
    # of the whole test budget being consumed by one hung command.
    UIAUTOMATOR2_SERVER_READ_TIMEOUT     = int(os.getenv("UIAUTOMATOR2_SERVER_READ_TIMEOUT", "25000"))

    # =====================================================
    # RETRY
    # =====================================================

    CLICK_RETRY_COUNT = int(os.getenv("CLICK_RETRY_COUNT", "3"))
    TYPE_RETRY_COUNT  = int(os.getenv("TYPE_RETRY_COUNT", "3"))

    # =====================================================
    # HUMAN DELAY
    # =====================================================

    HUMAN_DELAY_MIN   = float(os.getenv("HUMAN_DELAY_MIN", "0.1"))
    HUMAN_DELAY_MAX   = float(os.getenv("HUMAN_DELAY_MAX", "0.5"))

    # =====================================================
    # ANDROID FLAGS
    # =====================================================

    AUTO_GRANT_PERMISSION               = os.getenv("AUTO_GRANT_PERMISSION", "true").lower() == "true"
    DISABLE_WINDOW_ANIMATION            = os.getenv("DISABLE_WINDOW_ANIMATION", "true").lower() == "true"
    IGNORE_HIDDEN_API_POLICY_ERROR      = os.getenv("IGNORE_HIDDEN_API_POLICY_ERROR", "true").lower() == "true"
    SKIP_DEVICE_INITIALIZATION          = os.getenv("SKIP_DEVICE_INITIALIZATION", "false").lower() == "true"
    SKIP_SERVER_INSTALLATION            = os.getenv("SKIP_SERVER_INSTALLATION", "false").lower() == "true"
    ENSURE_WEBVIEWS_HAVE_PAGES          = os.getenv("ENSURE_WEBVIEWS_HAVE_PAGES", "true").lower() == "true"

    # =====================================================
    # PATHS
    # All paths are relative to project root.
    # =====================================================

    SCREENSHOT_PATH   = os.getenv("SCREENSHOT_PATH", "reports/screenshots")
    LOG_PATH          = os.getenv("LOG_PATH", "reports/logs")
    ALLURE_RESULTS    = os.getenv("ALLURE_RESULTS", "reports/allure-results")