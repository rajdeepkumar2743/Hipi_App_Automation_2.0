# =========================================================
# FILE: core/driver_factory.py
#
# CHANGES (iOS support / driver-management improvement):
#   - Platform is now derived from the selected device's
#     "platform" key (device_config.py) rather than only
#     from the global Config.PLATFORM_NAME env var. This
#     means --device alone picks the right Appium Options
#     class end-to-end (UiAutomator2Options vs
#     XCUITestOptions) and the right per-env app identity
#     (environments.py's nested "android"/"ios" blocks) —
#     you can no longer point an Android device entry at
#     iOS capabilities by mistake.
#   - Capability building for Android vs iOS is split into
#     two small private methods (_build_android_options /
#     _build_ios_options) instead of one long branch, so
#     each platform's capability set can be read, tested,
#     and extended independently. This is a Simple Factory
#     specializing by platform (matches your existing
#     factory pattern for device/env — not a departure
#     from it).
#   - create_driver()'s public signature and return value
#     are UNCHANGED (still create_driver(device, env) ->
#     driver), so no caller (conftest.py, etc.) needs to
#     change.
# =========================================================

import time

from appium import webdriver

from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions

from config.config import Config
from config.device_config import DEVICES
from config.environments import ENVIRONMENTS

from utils.logger import LogGen


class DriverFactory:

    logger = LogGen.loggen()

    # =====================================================
    # CREATE DRIVER
    # =====================================================

    @staticmethod
    def create_driver(device="emulator", env="qa"):

        DriverFactory.logger.info("========== DRIVER CREATION START ==========")

        # =================================================
        # DEVICE / ENV VALIDATION
        # =================================================

        if device not in DEVICES:
            raise Exception(f"Invalid device: {device}")

        if env not in ENVIRONMENTS:
            raise Exception(f"Invalid environment: {env}")

        device_info = DEVICES[device]
        env_info = ENVIRONMENTS[env]

        platform = device_info.get("platform", Config.PLATFORM_NAME)

        DriverFactory.logger.info(f"Device: {device} | Env: {env} | Platform: {platform}")

        # =================================================
        # BUILD PLATFORM-SPECIFIC OPTIONS
        # =================================================

        if platform.lower() == "android":
            options = DriverFactory._build_android_options(device_info, env_info["android"])
        elif platform.lower() == "ios":
            options = DriverFactory._build_ios_options(device_info, env_info["ios"])
        else:
            raise Exception(
                f"Unsupported platform '{platform}' for device '{device}'. "
                f"Expected 'Android' or 'iOS' in device_config.py."
            )

        # =================================================
        # CREATE DRIVER
        # =================================================

        driver = webdriver.Remote(
            command_executor=Config.APPIUM_SERVER,
            options=options
        )

        # Explicit waits (WebDriverWait) handle all timing.
        # Implicit wait=0 lets find_elements() return immediately when
        # nothing is found — prevents 5s-per-locator delays in poll loops
        # like wait_for_any_visible() that call find_elements() repeatedly.
        driver.implicitly_wait(0)

        # =================================================
        # APP LAUNCH & STABILIZATION
        #
        # NOTE: this sleep is a deliberate, previously-tuned
        # fix (see prior audit notes) for a real cold-start
        # race on this Compose app — not an arbitrary pad.
        # Kept as-is; not part of the "remove hardcoded
        # waits" cleanup because it protects against a
        # specific observed failure, not laziness.
        # =================================================

        DriverFactory.logger.info("App launched by driver. Waiting for stabilization...")
        time.sleep(2)

        DriverFactory.logger.info("========== DRIVER CREATED SUCCESSFULLY ==========")

        return driver

    # =====================================================
    # ANDROID OPTIONS
    # =====================================================

    @staticmethod
    def _build_android_options(device_info: dict, android_env: dict) -> UiAutomator2Options:

        options = UiAutomator2Options()

        # ── Platform ──────────────────────────────────
        options.platform_name = "Android"
        options.automation_name = Config.AUTOMATION_NAME

        # ── Device ────────────────────────────────────
        options.device_name = device_info["deviceName"]
        options.udid = device_info["udid"]

        DriverFactory.logger.info(f"Device Name: {device_info['deviceName']}")
        DriverFactory.logger.info(f"UDID: {device_info['udid']}")

        # ── App ───────────────────────────────────────
        options.app_package = android_env["appPackage"]
        
        # Only set appActivity if we're resetting the app.
        # When noReset=true, the app is already running, so appActivity
        # is unnecessary and may fail if the activity name doesn't match.
        if not Config.NO_RESET:
            options.app_activity = android_env["appActivity"]
            options.app_wait_activity = android_env["appActivity"]
            DriverFactory.logger.info(f"App Package: {android_env['appPackage']}")
            DriverFactory.logger.info(f"App Activity: {android_env['appActivity']}")
        else:
            DriverFactory.logger.info(f"App Package: {android_env['appPackage']} (noReset=true, activity not set)")

        # ── Reset strategy ────────────────────────────
        options.no_reset = Config.NO_RESET
        options.full_reset = Config.FULL_RESET

        # ── Timeouts ──────────────────────────────────
        options.new_command_timeout = Config.NEW_COMMAND_TIMEOUT
        options.adb_exec_timeout = Config.ADB_EXEC_TIMEOUT
        options.uiautomator2_server_install_timeout = Config.UIAUTOMATOR2_SERVER_INSTALL_TIMEOUT
        options.uiautomator2_server_launch_timeout = Config.UIAUTOMATOR2_SERVER_LAUNCH_TIMEOUT

        # ROOT CAUSE FIX — see config.py UIAUTOMATOR2_SERVER_READ_TIMEOUT
        # for full context. Without this, Appium waits up to its
        # built-in 240000ms default for a hung UiA2 command to respond,
        # which is exactly the "timeout of 240000ms exceeded" failure
        # signature seen repeatedly in historical runs.
        options.uiautomator2_server_read_timeout = Config.UIAUTOMATOR2_SERVER_READ_TIMEOUT

        # ── Stability settings ────────────────────────
        options.auto_grant_permissions = Config.AUTO_GRANT_PERMISSION
        options.disable_window_animation = Config.DISABLE_WINDOW_ANIMATION
        options.ignore_hidden_api_policy_error = Config.IGNORE_HIDDEN_API_POLICY_ERROR

        # ── HiPi-specific performance fix ─────────────
        # (Compose apps generate a lot of idle-state churn;
        # these two settings were tuned against real timeouts.)
        options.wait_for_idle_timeout = 0
        options.disable_android_watchers = True

        # ── Performance settings ──────────────────────
        options.skip_device_initialization = Config.SKIP_DEVICE_INITIALIZATION
        options.skip_server_installation = Config.SKIP_SERVER_INSTALLATION
        options.ensure_webviews_have_pages = Config.ENSURE_WEBVIEWS_HAVE_PAGES

        return options

    # =====================================================
    # iOS OPTIONS
    #
    # NOTE: capability set here is a reasonable starting
    # point for a first iOS run, NOT yet validated against
    # the real HiPi iOS build (no iOS-side locators exist
    # in locators/ yet either — see rollout notes). Expect
    # to tune newCommandTimeout / autoAcceptAlerts and add
    # xcodeOrgId/xcodeSigningId handling once running
    # against a real device rather than a simulator.
    # =====================================================

    @staticmethod
    def _build_ios_options(device_info: dict, ios_env: dict) -> XCUITestOptions:

        options = XCUITestOptions()

        # ── Platform ──────────────────────────────────
        options.platform_name = "iOS"
        options.automation_name = "XCUITest"

        # ── Device ────────────────────────────────────
        options.device_name = device_info["deviceName"]
        options.udid = device_info["udid"]

        if "platformVersion" in device_info:
            options.platform_version = device_info["platformVersion"]

        DriverFactory.logger.info(f"Device Name: {device_info['deviceName']}")
        DriverFactory.logger.info(f"UDID: {device_info['udid']}")

        # ── App ───────────────────────────────────────
        options.bundle_id = ios_env["bundleId"]

        # Real devices need an .ipa/.app path to install from;
        # simulators can often attach to an already-installed
        # bundle via bundle_id alone. Set app path when provided.
        if ios_env.get("appPath"):
            options.app = ios_env["appPath"]

        DriverFactory.logger.info(f"Bundle ID: {ios_env['bundleId']}")

        # ── Real-device signing (no-op on simulators) ─
        if device_info.get("xcodeOrgId"):
            options.xcode_org_id = device_info["xcodeOrgId"]
        if device_info.get("xcodeSigningId"):
            options.xcode_signing_id = device_info["xcodeSigningId"]

        # ── Reset strategy ────────────────────────────
        options.no_reset = Config.NO_RESET
        options.full_reset = Config.FULL_RESET

        # ── Timeouts ──────────────────────────────────
        options.new_command_timeout = Config.NEW_COMMAND_TIMEOUT

        # ── Stability settings ─────────────────────────
        options.auto_accept_alerts = True

        return options

    # =====================================================
    # QUIT DRIVER
    # =====================================================

    @staticmethod
    def quit_driver(driver):
        try:
            if driver:
                DriverFactory.logger.info("Closing driver session")
                driver.quit()
                DriverFactory.logger.info("Driver closed successfully")
        except Exception as e:
            DriverFactory.logger.error(f"Driver quit failed: {e}")

    # =====================================================
    # RESTART APP
    # =====================================================

    @staticmethod
    def restart_app(driver):
        try:
            DriverFactory.logger.info("Restarting HiPi application")
            driver.terminate_app(Config.APP_PACKAGE)
            driver.activate_app(Config.APP_PACKAGE)
            DriverFactory.logger.info("Application restarted")
            return True
        except Exception as e:
            DriverFactory.logger.error(f"Restart app failed: {e}")
            return False
