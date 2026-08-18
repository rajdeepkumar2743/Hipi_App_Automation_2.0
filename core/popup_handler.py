# =========================================================
# FILE: core/popup_handler.py
#
# CHANGES FROM AUDIT:
#   - Removed `for _ in range(1): ... break` anti-pattern
#     (ISSUE-19). This was `if:` in disguise — replaced with
#     direct conditional blocks, same behaviour, honest code
#   - Tightened clickability timeout to 2s (was already 2s
#     but now explicit and documented)
#   - All method signatures preserved
# =========================================================

import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from appium.webdriver.common.appiumby import AppiumBy

from utils.logger import LogGen
from utils.screenshot_utils import ScreenshotUtils

logger = LogGen.loggen()


class PopupHandler:

    def __init__(self, driver):
        self.driver = driver

    # ─── Permission popups ───────────────────────────────

    def allow_permissions(self) -> None:
        """
        Handles Android runtime permission dialogs.
        NOTE: With AUTO_GRANT_PERMISSION=True in capabilities,
        these dialogs never appear. Method kept for edge-cases
        (e.g. re-install without full_reset on real device).
        """
        logger.info("Checking for permission popups...")

        permission_locators = [
            (AppiumBy.ID,
             "com.android.permissioncontroller:id/permission_allow_button"),
            (AppiumBy.ID,
             "com.android.packageinstaller:id/permission_allow_button"),
            (AppiumBy.XPATH,
             "//*[contains(@text, 'Allow')]"),
        ]

        for locator in permission_locators:
            elements = self.driver.find_elements(*locator)
            if not elements:
                continue

            try:
                allow_btn = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable(locator)
                )
                allow_btn.click()
                logger.info(f"Clicked 'Allow' permission: {locator[1]}")
                time.sleep(1)  # Allow next permission dialog to appear
            except TimeoutException:
                logger.warning(
                    f"Permission button found but not clickable: {locator[1]}"
                )
                ScreenshotUtils.capture(
                    self.driver, "permission_not_clickable"
                )
            except Exception as e:
                logger.warning(f"Permission handling error: {e}")

        logger.info("Permission popup check complete.")

    # ─── Generic popups ──────────────────────────────────

    def close_all_popups(self) -> None:
        """
        Closes known generic popups (Skip, Later, close icons).
        NOTE: Disabled by default in conftest.py since
        AUTO_GRANT_PERMISSION handles most cases and these
        locators were guesses for a Jetpack Compose app.
        Re-enable if a specific popup is confirmed via Inspector.
        """
        logger.info("Checking for generic popups...")

        generic_locators = [
            (AppiumBy.ID,    "com.zee5.hipi:id/ivClose"),
            (AppiumBy.XPATH, "//*[contains(@text, 'Skip')]"),
            (AppiumBy.XPATH, "//*[contains(@text, 'Later')]"),
        ]

        for locator in generic_locators:
            elements = self.driver.find_elements(*locator)
            if not elements:
                continue

            try:
                close_btn = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable(locator)
                )
                close_btn.click()
                logger.info(f"Closed generic popup: {locator[1]}")
                time.sleep(1)
            except TimeoutException:
                logger.warning(
                    f"Generic popup button found but not clickable: {locator[1]}"
                )
            except Exception as e:
                logger.warning(f"Popup close error: {e}")

        logger.info("Generic popup check complete.")

    # ─── Get Started screen ──────────────────────────────

    def handle_get_started_screen(self) -> bool:
        """
        Clicks the 'Get Started' button if the onboarding screen appears.
        Returns True if handled, False if screen was not present.
        """
        logger.info("Checking for 'Get Started' screen...")
        try:
            btn = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable(
                    (AppiumBy.XPATH, "//*[contains(@text,'Get Started')]")
                )
            )
            btn.click()
            logger.info("'Get Started' screen dismissed.")
            time.sleep(3)
            return True
        except TimeoutException:
            logger.info("'Get Started' screen not present — skipping.")
            return False
        except Exception as e:
            logger.error(f"'Get Started' handling failed: {e}")
            ScreenshotUtils.capture(self.driver, "get_started_error")
            return False