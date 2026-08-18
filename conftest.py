# =========================================================
# FILE: conftest.py
#
# ROOT CAUSES FIXED:
#
# ISSUE 5 — load_dotenv() never called
#   Added at top of file. conftest.py is the first file
#   pytest loads, so calling it here guarantees .env is
#   available before any test module is imported.
#
# ISSUE 7 — App readiness probe burns 33s per test
#   The probe used wait_for_any_visible() with 3 locators.
#   On a Jetpack Compose app, each find_elements() tree walk
#   takes ~5–10s, so 3 locators × 5s = ~15s per poll cycle.
#   A "5 second timeout" wall-clock was actually 33 seconds.
#   FIX: probe replaced with a single fast current_package
#   check (one ADB call, <1s) — no accessibility tree walk.
#   The probe is informational only; it never blocked tests.
#
# ISSUE 8 — Duplicate teardown logs on rerun
#   Caused by pytest-rerunfailures re-attaching the first
#   run's log output. No code fix possible — documented.
# =========================================================

import os
import subprocess
import time

import pytest
import allure
from dotenv import load_dotenv

# ── Load .env FIRST — before any test module is imported ──
# This ensures os.getenv("TEST_PHONE") etc. work everywhere.
load_dotenv()

from config.config import Config
from core.driver_factory import DriverFactory
from core.popup_handler import PopupHandler
from utils.logger import LogGen
from utils.screenshot_utils import ScreenshotUtils

logger = LogGen.loggen()


# ─── CLI options ─────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption(
        "--device",
        action="store",
        default="emulator",
        help="Device key from config/device_config.py",
    )
    parser.addoption(
        "--env",
        action="store",
        default="qa",
        help="Environment key from config/environments.py",
    )


# ─── Credential guard (collection-time check) ────────────

def pytest_configure(config):
    """
    Verify required credentials exist before any test runs.
    Fails immediately at collection time with a clear message
    instead of failing mid-test with a cryptic Appium error.

    ONLY triggers for test runs that actually need login
    (i.e. not when running --collect-only or dry runs).
    """
    # Skip check during pure collection / help / version calls
    if config.option.__dict__.get("help") or \
            config.option.__dict__.get("version") or \
            config.option.__dict__.get("collectonly"):
        return

    phone = os.getenv("TEST_PHONE", "").strip()
    otp   = os.getenv("TEST_OTP",   "").strip()

    if not phone or not otp:
        missing = []
        if not phone:
            missing.append("TEST_PHONE")
        if not otp:
            missing.append("TEST_OTP")

        pytest.exit(
            f"\n\n"
            f"  ✗  Missing required credentials: {', '.join(missing)}\n"
            f"\n"
            f"  Create a .env file in your project root:\n"
            f"    TEST_PHONE=9876543210\n"
            f"    TEST_OTP=5186\n"
            f"\n"
            f"  See .env.example for all required variables.\n",
            returncode=4,  # 4 = usage error, distinct from test failure (1)
        )


# ─── Internal helpers ────────────────────────────────────

def _kill_uiautomator2(udid: str) -> None:
    """
    Force-stop the UiAutomator2 server processes on the device before
    creating a new Appium session. A crashed UiAutomator2 server from
    a previous session can interfere with the new session even after
    driver.quit() — this ensures a clean slate.

    ADB reconnect is attempted first so that a transiently offline
    emulator is recovered before the force-stop commands run.
    """
    try:
        subprocess.run(
            ["adb", "reconnect"],
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            ["adb", "-s", udid, "wait-for-device"],
            capture_output=True,
            timeout=15,
        )
    except Exception:
        pass

    for pkg in ("io.appium.uiautomator2.server",
                "io.appium.uiautomator2.server.test"):
        try:
            subprocess.run(
                ["adb", "-s", udid, "shell", "am", "force-stop", pkg],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass


def _create_driver_with_retry(
        device_name: str, env_name: str, max_attempts: int = 3
):
    """
    Attempt driver creation up to max_attempts times.
    UiAutomator2 can transiently crash under emulator load.
    Kills the UiAutomator2 server before each attempt so a
    crashed server from the previous test doesn't survive.
    """
    from config.device_config import DEVICES
    udid = DEVICES.get(device_name, {}).get("udid", "emulator-5554")

    last_error = None
    driver = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Driver creation attempt {attempt}/{max_attempts}")
            _kill_uiautomator2(udid)
            driver = DriverFactory.create_driver(
                device=device_name, env=env_name
            )
            return driver
        except Exception as e:
            last_error = e
            logger.error(f"Attempt {attempt} failed: {e}")
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = None
            if attempt < max_attempts:
                error_str = str(last_error).lower()
                if any(x in error_str for x in [
                    "offline", "could not find", "connection aborted",
                    "no activity", "connection refused"
                ]):
                    logger.info(
                        "Emulator appears offline — restarting ADB server..."
                    )
                    try:
                        subprocess.run(
                            ["adb", "kill-server"],
                            capture_output=True, timeout=10
                        )
                        time.sleep(2)
                        subprocess.run(
                            ["adb", "start-server"],
                            capture_output=True, timeout=15
                        )
                        time.sleep(5)
                    except Exception as adb_err:
                        logger.warning(f"ADB server restart failed: {adb_err}")
                logger.info("Waiting 3s before retry...")
                time.sleep(3)

    raise RuntimeError(
        f"Driver creation failed after {max_attempts} attempts: {last_error}"
    )


def _clear_app_data(udid: str) -> bool:
    """
    Clears HiPi's app data via `adb shell pm clear`, forcing a
    logged-out state without needing a full uninstall/reinstall
    (FULL_RESET=true) or globally disabling NO_RESET for the whole
    suite (which would slow down and destabilize every other test).

    ROOT CAUSE FIXED: invalid/short-OTP login tests were previously
    unconditionally skipped whenever NO_RESET=true (the default),
    because the app's persisted login session made login() take the
    already-logged-in fast path and never reach OTP entry at all —
    "test execution not running expected scenarios". Reset should
    happen automatically ONLY where it's genuinely required; this
    function is invoked ONLY for tests marked
    `@pytest.mark.requires_logout` (see the `driver` fixture below) —
    every other suite is completely unaffected and keeps the fast
    noReset path.
    """
    try:
        result = subprocess.run(
            ["adb", "-s", udid, "shell", "pm", "clear", Config.APP_PACKAGE],
            capture_output=True, timeout=20, text=True,
        )
        output = (result.stdout or "") + (result.stderr or "")
        ok = "Success" in output
        if ok:
            logger.info(f"Cleared app data for {Config.APP_PACKAGE} (logged-out state guaranteed).")
        else:
            logger.warning(f"'pm clear' did not report Success: {output!r}")
        return ok
    except Exception as e:
        logger.error(f"Failed to clear app data for {Config.APP_PACKAGE}: {e}")
        return False


def _relaunch_app_via_adb(udid: str) -> bool:
    """
    Launches HiPi's launcher activity via `adb shell monkey`, without
    needing an Appium/UiAutomator2 session. Used immediately after
    _clear_app_data() as the "relaunch" half of the suite-start
    reset-and-relaunch sequence (see _reset_and_relaunch_app_for_suite
    below) — deliberately adb-only so it works before any driver/
    session exists yet.
    """
    try:
        result = subprocess.run(
            [
                "adb", "-s", udid, "shell", "monkey",
                "-p", Config.APP_PACKAGE,
                "-c", "android.intent.category.LAUNCHER", "1",
            ],
            capture_output=True, timeout=20, text=True,
        )
        ok = result.returncode == 0
        if not ok:
            logger.warning(
                f"App relaunch via monkey returned code {result.returncode}: "
                f"{result.stdout!r} {result.stderr!r}"
            )
        return ok
    except Exception as e:
        logger.error(f"Failed to relaunch {Config.APP_PACKAGE}: {e}")
        return False


def _reset_and_relaunch_app_for_suite(config) -> None:
    """
    Resets (clears app data) and relaunches HiPi ONCE at the very
    start of every pytest invocation — regardless of which marker is
    run (smoke, sanity, regression, login, feed, feed_e2e) — so every
    suite run starts from the same clean, consistent app state instead
    of inheriting whatever was left over from a previous run.

    Deliberately a ONE-TIME, session-start action (not per-test): a
    per-test reset was evaluated and rejected — it would mean every
    single test re-does a real login from scratch, which is both far
    slower and defeats the noReset-based session reuse
    (logged_in_driver / requires_logout) already built for the tests
    that specifically need it. This targets the level the request
    actually operates at: "whenever a test suite is started."

    Skipped for --collect-only / --help / --version (no device
    interaction needed just to list tests), matching the existing
    credential-guard skip in pytest_configure() above.
    """
    if config.option.__dict__.get("help") or \
            config.option.__dict__.get("version") or \
            config.option.__dict__.get("collectonly"):
        return

    from config.device_config import DEVICES

    device_name = config.getoption("--device")
    udid = DEVICES.get(device_name, {}).get("udid", "emulator-5554")

    logger.info("=" * 50)
    logger.info(f"SUITE START: resetting and relaunching {Config.APP_PACKAGE} "
                f"on '{device_name}' ({udid}) for a clean run...")
    logger.info("=" * 50)

    cleared = _clear_app_data(udid)
    relaunched = _relaunch_app_via_adb(udid) if cleared else False

    if cleared and relaunched:
        logger.info("SUITE START: app reset and relaunched successfully.")
        # Give the freshly-launched app a moment to settle before the
        # first test's driver fixture attaches an Appium session to it.
        time.sleep(3)
    else:
        logger.warning(
            "SUITE START: reset-and-relaunch did not fully succeed "
            f"(cleared={cleared}, relaunched={relaunched}) — continuing "
            "anyway; the first test's driver fixture will still attempt "
            "to launch the app normally. This is logged, not fatal, so "
            "a device/adb hiccup at suite start doesn't block the whole "
            "run over what the per-test driver retry logic can likely "
            "recover from anyway."
        )


def _probe_app_ready(driver) -> None:
    """
    Fast informational probe — checks the current package
    via a single ADB call (<1s) instead of walking the
    Compose accessibility tree (which takes 5–10s per locator).

    FIXED: Previous version used wait_for_any_visible() with
    3 locators. Each find_elements() call on a Compose app
    takes ~5–10s for a tree walk. Result: a "5s timeout"
    was actually taking 33s wall-clock every single test run.
    """
    try:
        current_pkg = driver.current_package
        if current_pkg == Config.APP_PACKAGE:
            logger.info(
                f"App readiness probe: HiPi is in foreground ({current_pkg})."
            )
        else:
            logger.warning(
                f"App readiness probe: unexpected package '{current_pkg}' "
                f"(expected '{Config.APP_PACKAGE}')."
            )
    except Exception as e:
        logger.debug(f"App readiness probe skipped: {e}")


def _resolve_device(request) -> str:
    """
    Resolves which device key (from device_config.py) this test
    process should use.

    SEQUENTIAL RUN (no pytest-xdist): always returns --device as
    given on the CLI. Unchanged behaviour from before.

    PARALLEL RUN (pytest-xdist, e.g. `pytest -n 3`): xdist sets the
    PYTEST_XDIST_WORKER env var to "gw0", "gw1", "gw2"... for each
    worker process. Without this function, EVERY worker would still
    resolve to the same --device UDID and all fight over one
    emulator/real device — xdist parallelizes test *collection and
    scheduling*, it does nothing about device contention on its own.

    To actually run in parallel, set PARALLEL_DEVICES to a comma-
    separated list of device keys with as many entries as workers,
    e.g.:
        PARALLEL_DEVICES=emulator,real_device_1,real_device_2 \\
        pytest -n 3 tests/ --device emulator --env qa

    Each worker then gets its own device by index. --device is
    still required by pytest_addoption but becomes the fallback for
    any worker index beyond the configured list (logged as a
    warning, not a silent failure).
    """
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")  # "gw0", "gw1", ... or None
    parallel_devices_raw = os.getenv("PARALLEL_DEVICES", "").strip()

    if worker_id and parallel_devices_raw:
        devices = [d.strip() for d in parallel_devices_raw.split(",") if d.strip()]
        try:
            worker_index = int(worker_id.replace("gw", ""))
        except ValueError:
            worker_index = 0

        if worker_index < len(devices):
            resolved = devices[worker_index]
            logger.info(
                f"Worker '{worker_id}' -> device '{resolved}' "
                f"(from PARALLEL_DEVICES index {worker_index})"
            )
            return resolved

        logger.warning(
            f"Worker '{worker_id}' has no matching entry in PARALLEL_DEVICES "
            f"('{parallel_devices_raw}', {len(devices)} device(s) listed) — "
            f"falling back to --device. This worker WILL contend with "
            f"whichever other worker also falls back to the same device."
        )

    return request.config.getoption("--device")


# ─── Base driver fixture (per test) ──────────────────────

@pytest.fixture(scope="function")
def driver(request):
    """
    Creates a fresh Appium session for each test function.
    Use for smoke / login tests that need a clean app state.
    """
    logger.info("=" * 50)
    logger.info("DRIVER SETUP START")
    logger.info("=" * 50)

    driver = None

    try:
        device_name = _resolve_device(request)
        env_name    = request.config.getoption("--env")

        # Intelligent, automatic, per-test reset: only tests explicitly
        # marked as needing a logged-out app state pay the cost of a
        # data clear. Every other test (the vast majority) keeps the
        # fast noReset session untouched — reset happens only where
        # genuinely required, never unnecessarily.
        if request.node.get_closest_marker("requires_logout"):
            from config.device_config import DEVICES
            udid = DEVICES.get(device_name, {}).get("udid", "emulator-5554")
            logger.info(
                f"Test '{request.node.name}' is marked requires_logout — "
                f"clearing app data before session start."
            )
            _clear_app_data(udid)

        driver = _create_driver_with_retry(device_name, env_name)
        logger.info("Driver created successfully.")

        # With noReset=true the app is already running; activate_app()
        # just brings it to foreground. 3s is enough for it to settle.
        driver.activate_app(Config.APP_PACKAGE)
        time.sleep(3)

        popup_handler = PopupHandler(driver)
        popup_handler.handle_get_started_screen()

        # Fast readiness probe (single ADB call, <1s)
        _probe_app_ready(driver)

        logger.info("DRIVER SETUP COMPLETE")
        yield driver

    except Exception as e:
        logger.error(f"Driver fixture setup failed: {e}")
        if driver:
            ScreenshotUtils.capture_full_debug(driver, "driver_setup_failure")
        pytest.fail(f"Driver setup failed: {e}")

    finally:
        if driver:
            logger.info("Closing driver session.")
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Driver quit failed: {e}")


# ─── Pre-logged-in driver fixture (per session) ──────────

# Module-level cache for the shared feed-test driver. Deliberately NOT
# a plain pytest session-scoped fixture — see logged_in_driver() below
# for why: a session-scoped fixture caches ONE instance for the whole
# run with no way to replace it if it dies mid-suite, which is exactly
# what caused a single UiAutomator2 crash to cascade into every
# remaining feed test failing (observed live: 24/26 failures from one
# early crash, versus 2/26 genuine failures when the shared session
# stayed healthy for the whole run).
_shared_feed_session = {"driver": None}


def _feed_driver_is_alive(driver) -> bool:
    """Cheap liveness check — current_package is a single fast ADB call."""
    try:
        driver.current_package
        return True
    except Exception:
        return False


def _create_and_login_driver(device_name: str, env_name: str):
    from testdata.test_data import VALID_LOGIN
    from pages.login_page import LoginPage

    driver = _create_driver_with_retry(device_name, env_name)
    driver.activate_app(Config.APP_PACKAGE)
    time.sleep(3)

    popup_handler = PopupHandler(driver)
    popup_handler.handle_get_started_screen()

    login_page = LoginPage(driver)
    login_page.login(
        mobile_number=VALID_LOGIN["mobile"],
        otp=VALID_LOGIN["otp"],
    )
    return driver


@pytest.fixture(scope="function")
def logged_in_driver(request):
    """
    Self-healing shared driver for feed tests: reuses ONE Appium
    session/login across the whole run for speed (login runs once
    instead of once per test — saves ~30s/test in a large suite), but
    with automatic recovery if that session dies mid-suite.

    ROOT CAUSE FIX: a plain scope="session" fixture caches its yielded
    driver for the entire run with no way to swap it out. Observed
    live: when the shared UiAutomator2 instrumentation crashed on test
    #2 of a 26-test run, every one of the remaining 24 tests failed
    too, because they all kept reusing the same now-dead driver
    reference pytest had cached — a single environmental crash
    cascaded into a near-total suite failure. This fixture is function-
    scoped (runs its body before every test) but checks a module-level
    cache first: if the cached driver is missing OR fails a liveness
    check, it quits the dead one and transparently creates + logs into
    a fresh one before handing it to the test. Healthy runs pay only
    the cost of one cheap ADB call per test; a crash costs one fresh
    driver + login (a few seconds), affecting only the test that
    happened to trigger the check — not every test after it.
    """
    device_name = _resolve_device(request)
    env_name    = request.config.getoption("--env")

    driver = _shared_feed_session["driver"]

    if driver is not None and not _feed_driver_is_alive(driver):
        logger.warning(
            "Shared feed session is dead (UiAutomator2 crash or "
            "similar) — recreating it instead of failing every "
            "remaining feed test."
        )
        try:
            driver.quit()
        except Exception:
            pass
        driver = None

    if driver is None:
        logger.info("LOGGED-IN DRIVER: creating shared feed session...")
        try:
            driver = _create_and_login_driver(device_name, env_name)
            _shared_feed_session["driver"] = driver
            logger.info("LOGGED-IN DRIVER: login successful.")
        except Exception as e:
            logger.error(f"logged_in_driver setup failed: {e}")
            if driver:
                ScreenshotUtils.capture_full_debug(
                    driver, "logged_in_driver_setup_failure"
                )
            pytest.fail(f"logged_in_driver setup failed: {e}")

    yield driver

    # No per-test teardown — the driver is intentionally kept alive
    # across tests. Cleaned up once at session end (see
    # pytest_sessionfinish below).


# ─── Screenshot on failure ───────────────────────────────

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report  = outcome.get_result()

    if report.when == "call" and report.failed:
        driver = (
                item.funcargs.get("driver", None)
                or item.funcargs.get("logged_in_driver", None)
        )

        if driver:
            try:
                screenshot_path = ScreenshotUtils.capture(driver, item.name)
                if screenshot_path:
                    allure.attach.file(
                        screenshot_path,
                        name="Failure Screenshot",
                        attachment_type=allure.attachment_type.PNG,
                    )

                source_path = ScreenshotUtils.save_page_source(
                    driver, item.name
                )
                if source_path:
                    allure.attach.file(
                        source_path,
                        name="Page Source",
                        attachment_type=allure.attachment_type.XML,
                    )

                logger.error(f"Test FAILED: {item.name}")
            except Exception as e:
                logger.error(f"Failure screenshot capture failed: {e}")


# ─── Session hooks ───────────────────────────────────────

def pytest_sessionstart(session):
    logger.info("=" * 50)
    logger.info("PYTEST SESSION START")
    logger.info("=" * 50)
    _reset_and_relaunch_app_for_suite(session.config)


def pytest_sessionfinish(session, exitstatus):
    # Clean up the self-healing shared feed session (see logged_in_driver
    # in the "Pre-logged-in driver fixture" section) — it has no
    # per-test teardown by design, so it must be closed once here.
    shared_driver = _shared_feed_session.get("driver")
    if shared_driver:
        logger.info("Closing shared feed session.")
        try:
            shared_driver.quit()
        except Exception as e:
            logger.error(f"Shared feed session quit failed: {e}")
        _shared_feed_session["driver"] = None

    logger.info("=" * 50)
    logger.info(f"PYTEST SESSION END | Exit status: {exitstatus}")
    logger.info("=" * 50)