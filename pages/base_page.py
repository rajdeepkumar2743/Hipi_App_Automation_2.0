# =========================================================
# FILE: pages/base_page.py
# =========================================================

import time
import random

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    NoSuchElementException,
    WebDriverException,
)

from appium.webdriver.common.appiumby import AppiumBy

from config.config import Config
from utils.logger import LogGen
from utils.gestures import GestureUtils
from utils.screenshot_utils import ScreenshotUtils


class SessionDeadError(Exception):
    """
    Raised when the underlying Appium/UiAutomator2 session itself is
    dead (instrumentation crashed, session terminated, device offline)
    rather than the target element being transiently absent.

    ROOT CAUSE this fixes: click()/send_keys() used to retry a fixed
    number of times AND call recover_app() on every attempt even when
    the error meant the session could never recover on its own (e.g.
    "instrumentation process is not running"). Each doomed retry could
    itself take 10-240s against a hung UiAutomator2 server, which is
    exactly why individual tests were observed taking 4-90 minutes
    instead of failing in seconds. Detecting these markers lets
    click()/send_keys() fail immediately with a clear signal instead
    of burning the rest of the test budget retrying the impossible.
    """
    pass


class BasePage:

    logger = LogGen.loggen()

    # Substrings (lower-cased) that indicate the session/instrumentation
    # itself is dead. Retrying against these is guaranteed to fail again.
    _FATAL_SESSION_MARKERS = (
        "instrumentation process is not running",
        "session is either terminated",
        "a session is either terminated or not started",
        "device offline",
        "connection refused",
        "connection aborted",
        "socket hang up",
        "econnreset",
        "could not proxy command to the remote server",
    )

    # Known out-of-app system dialogs that can interrupt a test at any
    # point (verified live: this app requests a runtime "access music
    # and audio" permission when a feed action button is tapped — if
    # not already granted, this opens a dialog in a different package
    # that no com.zee5.hipi locator can ever match). Package names vary
    # by Android/OEM build.
    _SYSTEM_DIALOG_PACKAGES = (
        "com.google.android.permissioncontroller",
        "com.android.permissioncontroller",
        "com.android.packageinstaller",
    )
    _SYSTEM_DIALOG_ALLOW_LOCATORS = (
        (AppiumBy.ID, "com.android.permissioncontroller:id/permission_allow_button"),
        (AppiumBy.ID, "com.android.permissioncontroller:id/permission_allow_foreground_only_button"),
        (AppiumBy.ID, "com.android.permissioncontroller:id/permission_allow_one_time_button"),
        (AppiumBy.ID, "com.android.packageinstaller:id/permission_allow_button"),
        (AppiumBy.XPATH, "//*[contains(@text,'While using the app')]"),
        (AppiumBy.XPATH, "//*[contains(@text,'Allow')]"),
    )

    def __init__(self, driver):
        self.driver = driver
        self.gestures = GestureUtils(driver)
        self._last_foreground_check = 0.0

    # =====================================================
    # CORE INTERACTION METHODS WITH RETRY & RECOVERY
    # =====================================================

    def wait_for_element(self, locator, timeout=Config.EXPLICIT_WAIT):
        """Waits for an element to be present in the DOM."""
        try:
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))
        except TimeoutException:
            self.logger.error(f"Element not found after {timeout}s: {locator}")
            self.take_error_screenshot(f"element_not_found_{locator[1]}")
            raise

    def wait_for_visible(self, locator, timeout=Config.EXPLICIT_WAIT):
        """Waits for an element to be visible on the screen."""
        try:
            return WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
        except TimeoutException:
            self.logger.error(f"Element not visible after {timeout}s: {locator}")
            self.take_error_screenshot(f"element_not_visible_{locator[1]}")
            raise

    def wait_for_clickable(self, locator, timeout=Config.EXPLICIT_WAIT):
        """Waits for an element to be visible and enabled so that it can be clicked."""
        try:
            return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(locator))
        except TimeoutException:
            self.logger.error(f"Element not clickable after {timeout}s: {locator}")
            self.take_error_screenshot(f"element_not_clickable_{locator[1]}")
            raise

    def wait_for_any_visible(self, locators, timeout=Config.EXPLICIT_WAIT, poll_frequency=0.5):
        """
        Waits until ANY one of the given locators becomes visible.
        Returns the (locator, element) tuple for whichever matched first.
        Raises TimeoutException if none match within the timeout.

        This is the key fix for brittle single-locator "is app ready"
        checks: instead of failing the whole run because one guessed
        locator doesn't exist, we succeed as soon as ANY known-good
        indicator shows up.
        """
        end_time = time.time() + timeout
        last_error = None

        while time.time() < end_time:
            for locator in locators:
                try:
                    elements = self.driver.find_elements(*locator)
                    for el in elements:
                        try:
                            if el.is_displayed():
                                self.logger.info(f"wait_for_any_visible matched: {locator}")
                                return locator, el
                        except StaleElementReferenceException:
                            continue
                except Exception as e:
                    last_error = e
            time.sleep(poll_frequency)

        self.logger.error(
            f"None of the candidate locators became visible within {timeout}s. "
            f"Candidates: {locators}. Last error: {last_error}"
        )
        self.take_error_screenshot("wait_for_any_visible_failed")
        raise TimeoutException(
            f"None of the candidate locators became visible within {timeout}s: {locators}"
        )

    @classmethod
    def _is_fatal_session_error(cls, exc) -> bool:
        """True if `exc` indicates the session/instrumentation is dead
        (not just a transient element-not-found)."""
        msg = str(exc).lower()
        return any(marker in msg for marker in cls._FATAL_SESSION_MARKERS)

    def click(self, locator, timeout=Config.EXPLICIT_WAIT, retry=Config.CLICK_RETRY_COUNT):
        """Performs a click operation with retry mechanism and app recovery."""
        last_exception = None
        self.ensure_app_foreground()
        for attempt in range(retry):
            try:
                element = self.wait_for_clickable(locator, timeout)
                self.human_delay()
                element.click()
                self.logger.info(f"Clicked: {locator}")
                return True
            except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                last_exception = e
                self.logger.warning(f"Retry click {attempt + 1}/{retry} for {locator}: {e.__class__.__name__}")
                time.sleep(1) # Small delay before retry
            except Exception as e:
                last_exception = e
                if self._is_fatal_session_error(e):
                    self.logger.error(
                        f"Fatal session error clicking {locator} — session is "
                        f"dead, not retrying: {e}"
                    )
                    raise SessionDeadError(
                        f"Session/instrumentation dead while clicking {locator}: {e}"
                    ) from e
                self.logger.error(f"Click failed on attempt {attempt + 1} for {locator}: {e}")
                if self._handle_system_dialog_if_present():
                    continue  # dialog cleared — retry immediately, don't burn a full recover_app()
                self.recover_app() # Attempt to recover app state
        self.take_error_screenshot("click_failed")
        raise Exception(f"Unable to click {locator} after {retry} retries. Last exception: {last_exception}")

    def send_keys(self, locator, value, timeout=Config.EXPLICIT_WAIT, retry=Config.TYPE_RETRY_COUNT):
        """Sends text to an element with retry mechanism and app recovery."""
        last_exception = None
        self.ensure_app_foreground()
        for attempt in range(retry):
            try:
                element = self.wait_for_visible(locator, timeout)
                self.human_delay()
                try:
                    element.clear()
                except Exception:
                    pass # Ignore if clear fails, element might not be clearable
                element.send_keys(str(value))
                self.logger.info(f"Entered text '{value}' into {locator}")
                return True
            except StaleElementReferenceException as e:
                last_exception = e
                self.logger.warning(f"Retry send_keys {attempt + 1}/{retry} for {locator}: {e.__class__.__name__}")
                time.sleep(1)
            except Exception as e:
                last_exception = e
                if self._is_fatal_session_error(e):
                    self.logger.error(
                        f"Fatal session error sending keys to {locator} — "
                        f"session is dead, not retrying: {e}"
                    )
                    raise SessionDeadError(
                        f"Session/instrumentation dead while sending keys to {locator}: {e}"
                    ) from e
                self.logger.error(f"Send keys failed on attempt {attempt + 1} for {locator}: {e}")
                if self._handle_system_dialog_if_present():
                    continue
                self.recover_app()
        self.take_error_screenshot("send_keys_failed")
        raise Exception(f"Unable to send keys to {locator} after {retry} retries. Last exception: {last_exception}")

    def get_text(self, locator, timeout=Config.EXPLICIT_WAIT):
        """Retrieves text from an element."""
        try:
            element = self.wait_for_visible(locator, timeout)
            text = element.text
            self.logger.info(f"Text fetched from {locator}: {text}")
            return text
        except Exception as e:
            self.logger.error(f"Failed to get text from {locator}: {e}")
            return ""

    # =====================================================
    # STATE CHECKING & UTILITIES
    # =====================================================

    def is_displayed(self, locator, timeout=5):
        """Checks if an element is displayed without raising an exception."""
        try:
            self.wait_for_visible(locator, timeout)
            return True
        except (TimeoutException, NoSuchElementException):
            return False
        except Exception as e:
            self.logger.warning(f"Error checking display status for {locator}: {e}")
            return False

    def is_any_displayed(self, locators, timeout=5):
        """Checks if ANY of the given locators is displayed, without raising."""
        try:
            self.wait_for_any_visible(locators, timeout)
            return True
        except TimeoutException:
            return False

    def find_elements_safe(self, locator):
        """Finds multiple elements safely, returning an empty list if none are found."""
        try:
            return self.driver.find_elements(*locator)
        except Exception:
            return []

    def wait_until_disappear(self, locator, timeout=Config.EXPLICIT_WAIT):
        """Waits for an element to disappear from the DOM."""
        try:
            WebDriverWait(self.driver, timeout).until_not(EC.presence_of_element_located(locator))
            self.logger.info(f"Element {locator} disappeared.")
            return True
        except TimeoutException:
            self.logger.warning(f"Element {locator} did not disappear within {timeout} seconds.")
            return False

    def hide_keyboard(self):
        """Hides the software keyboard if it's open."""
        try:
            self.driver.hide_keyboard()
            self.logger.info("Keyboard hidden.")
        except WebDriverException:
            pass  # Keyboard may not be open

    def go_back(self):
        """Performs a back action on the device."""
        try:
            self.driver.back()
            self.logger.info("Pressed back button.")
            self.human_delay(1, 2)
        except Exception as e:
            self.logger.error(f"Back action failed: {e}")

    def human_delay(self, min_time=Config.HUMAN_DELAY_MIN, max_time=Config.HUMAN_DELAY_MAX):
        """Introduces a random human-like delay."""
        delay = random.uniform(min_time, max_time)
        time.sleep(delay)
        self.logger.debug(f"Human delay for {delay:.2f}s.")

    def wait_for_app_stable(self, seconds=1):
        """A simple wait to let the app UI settle."""
        self.logger.debug(f"Waiting for app to stabilize for {seconds}s.")
        time.sleep(seconds)

    def wait_page_change(self, old_page_source, timeout=Config.EXPLICIT_WAIT):
        """Waits for the page source to change, indicating a new screen has loaded."""
        self.logger.debug("Waiting for page change...")
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.page_source != old_page_source
            )
            self.logger.info("Page source changed.")
            return True
        except TimeoutException:
            self.logger.warning("Page source did not change within timeout.")
            return False
        except Exception as e:
            self.logger.error(f"Error waiting for page change: {e}")
            return False

    # =====================================================
    # APP STABILITY & RECOVERY
    # =====================================================

    def ensure_app_foreground(self, force=False, min_interval=2.0):
        """
        Ensures the app is in the foreground.

        THROTTLED: `driver.current_package` is an ADB round-trip. The
        previous version called this before every single click()/
        send_keys(), generating a very high volume of ADB traffic that
        measurably contributed to UiAutomator2/adb instability over a
        long run (dozens of extra ADB calls per test, on top of an
        already-loaded emulator). Skips the underlying check if it ran
        within the last `min_interval` seconds unless force=True (used
        by recover_app(), which must know for certain).
        """
        now = time.time()
        if not force and (now - self._last_foreground_check) < min_interval:
            return
        self._last_foreground_check = now

        try:
            current_package = self.driver.current_package
            if current_package != Config.APP_PACKAGE:
                if current_package in self._SYSTEM_DIALOG_PACKAGES:
                    self.logger.warning(
                        f"System dialog in foreground ({current_package}) — clearing it."
                    )
                    self._handle_system_dialog_if_present()
                    return
                self.logger.warning(f"App moved to background ({current_package}). Activating {Config.APP_PACKAGE}.")
                self.driver.activate_app(Config.APP_PACKAGE)
                time.sleep(3)
        except Exception as e:
            self.logger.error(f"Failed to ensure app is in foreground: {e}")
            self.take_error_screenshot("foreground_failure")

    def _handle_system_dialog_if_present(self) -> bool:
        """
        Detects and clears known out-of-app system dialogs (runtime
        permission prompts, etc.) that can interrupt a test at any
        point. Verified live during root-cause analysis: this app
        requests a runtime "access music and audio" permission when a
        feed action button is tapped, which — if not already granted —
        opens a native dialog in a completely different package. No
        com.zee5.hipi locator can ever match while it's showing, so
        every downstream find_element call fails until it's cleared —
        previously nothing in the framework handled this (the existing
        PopupHandler.allow_permissions() was defined but never called
        from anywhere).

        Returns True if a system dialog was found (whether or not a
        known "allow" control could be tapped on it).
        """
        try:
            current_package = self.driver.current_package
        except Exception:
            return False

        if current_package not in self._SYSTEM_DIALOG_PACKAGES:
            return False

        for locator in self._SYSTEM_DIALOG_ALLOW_LOCATORS:
            try:
                elements = self.driver.find_elements(*locator)
            except Exception:
                elements = []
            if elements:
                try:
                    elements[0].click()
                    self.logger.info(f"Cleared system dialog via {locator}")
                    time.sleep(1)
                    self.driver.activate_app(Config.APP_PACKAGE)
                    time.sleep(1)
                    return True
                except Exception as e:
                    self.logger.warning(f"Failed to clear system dialog via {locator}: {e}")

        self.logger.warning(
            f"Unrecognized system dialog in '{current_package}' — no known "
            f"control matched; re-activating app so execution isn't stuck."
        )
        try:
            self.driver.activate_app(Config.APP_PACKAGE)
            time.sleep(1)
        except Exception:
            pass
        return True

    def recover_app(self):
        """Attempts to recover the app state after an unexpected error."""
        self.logger.warning("Attempting to recover application state...")
        try:
            self._handle_system_dialog_if_present()
            self.ensure_app_foreground(force=True)
            self.wait_for_app_stable(3)
            self.logger.info("App recovery attempt completed.")
            return True
        except Exception as e:
            self.logger.error(f"Application recovery failed: {e}")
            self.take_error_screenshot("recovery_failed")
            return False

    # =====================================================
    # GENERIC NAVIGATION RECOVERY
    #
    # If the app accidentally lands on the wrong screen/popup/
    # activity/fragment mid-flow, this detects it and tries to get
    # back to the expected screen automatically instead of failing
    # the whole test outright. Used by FeedPage.wait_for_feed_ready()
    # and available to any page object.
    # =====================================================

    def recover_to_screen(self, expected_locator, timeout=5, max_back_presses=2, nav_actions=None):
        """
        Verifies `expected_locator` is visible; if not, attempts
        automatic recovery in this order:
          1. Clear any known system dialog blocking the app.
          2. Press back up to `max_back_presses` times, re-checking
             after each (dismisses stray bottom sheets/dialogs/screens
             pushed onto the back stack).
          3. Run any caller-supplied `nav_actions` (zero-arg callables,
             e.g. "tap the Home tab"), re-checking after each.

        Returns True if `expected_locator` is visible at the end,
        False otherwise. Never raises — callers decide whether that's
        fatal for their flow.
        """
        if self.is_displayed(expected_locator, timeout=timeout):
            return True

        self.logger.warning(
            f"Not on expected screen ({expected_locator}) — attempting "
            f"automatic navigation recovery."
        )

        if self._handle_system_dialog_if_present() and self.is_displayed(expected_locator, timeout=timeout):
            self.logger.info("Navigation recovery: recovered via system-dialog dismissal.")
            return True

        for i in range(max_back_presses):
            self.go_back()
            if self.is_displayed(expected_locator, timeout=timeout):
                self.logger.info(f"Navigation recovery: recovered via back press #{i + 1}.")
                return True

        for action in (nav_actions or []):
            try:
                action()
            except Exception as e:
                self.logger.warning(f"Navigation recovery action failed: {e}")
                continue
            if self.is_displayed(expected_locator, timeout=timeout):
                self.logger.info("Navigation recovery: recovered via supplied nav action.")
                return True

        self.logger.error(
            f"Navigation recovery FAILED — still not on expected screen "
            f"({expected_locator}) after back-press and nav-action attempts."
        )
        self.take_error_screenshot("navigation_recovery_failed")
        return False

    # =====================================================
    # SCREENSHOT
    # =====================================================

    def take_error_screenshot(self, name="error"):
        """Captures a screenshot and attaches it to the Allure report."""
        ScreenshotUtils.capture(self.driver, name)
        ScreenshotUtils.save_page_source(self.driver, name)