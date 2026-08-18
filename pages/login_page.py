# =========================================================
# FILE: pages/login_page.py
# =========================================================

import time
from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage

from locators.login_locators import LoginLocators

from utils.logger import LogGen
from utils.screenshot_utils import ScreenshotUtils


class _AlreadyLoggedInError(Exception):
    """
    Raised by open_profile_tab() when the profile tab tap opens
    the logged-in profile page instead of the login sheet.
    Caught by login() to skip credentials entry.
    """
    pass


class LoginPage(BasePage):

    logger = LogGen.loggen()

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self, driver):

        super().__init__(driver)

    # =====================================================
    # OPEN PROFILE TAB
    # =====================================================

    def open_profile_tab(self):

        self.logger.info(
            "Opening profile tab"
        )

        self.wait_for_app_stable()

        max_attempts = 2

        for attempt in range(1, max_attempts + 1):

            self.logger.info(
                f"Profile tab open attempt "
                f"{attempt}/{max_attempts}"
            )

            # =========================================
            # STEP 1: ELEMENT-BASED CLICK
            # =========================================

            try:

                self.click(
                    LoginLocators.PROFILE_ICON,
                    timeout=8,
                    retry=1
                )

                if self.is_any_displayed(
                        [
                            LoginLocators.CONTINUE_BUTTON,
                            LoginLocators.PHONE_INPUT
                        ],
                        timeout=6
                ):

                    self.logger.info(
                        "Profile tab opened "
                        "(element click, verified)"
                    )

                    return True

                # Login sheet didn't appear — check for
                # already-logged-in state BEFORE wasting
                # time on the coordinate tap. This avoids
                # overloading UiAutomator2 with a tap+wait
                # cycle on a page that won't show login.
                if self._check_already_logged_in():
                    raise _AlreadyLoggedInError()

            except _AlreadyLoggedInError:
                raise

            except Exception as e:

                self.logger.warning(
                    f"Element-based click failed: {e}"
                )

                # On click failure, still check logged-in
                # state if UiAutomator2 is responsive.
                try:
                    if self._check_already_logged_in():
                        raise _AlreadyLoggedInError()
                except _AlreadyLoggedInError:
                    raise
                except Exception:
                    pass

            # =========================================
            # STEP 2: COORDINATE TAP (fallback)
            # Only reached if element click failed AND
            # we confirmed we're NOT already logged in.
            # =========================================

            try:

                self.ensure_app_foreground()

                x_percent, y_percent = (
                    LoginLocators.PROFILE_ICON_TAP_PERCENT
                )

                self.gestures.tap_by_percentage(
                    x_percent,
                    y_percent
                )

                self.human_delay()

            except Exception as e:

                self.logger.warning(
                    f"Coordinate tap failed: {e}"
                )

            if self.is_any_displayed(
                    [
                        LoginLocators.CONTINUE_BUTTON,
                        LoginLocators.PHONE_INPUT
                    ],
                    timeout=6
            ):

                self.logger.info(
                    "Profile tab opened "
                    "(coordinate tap, verified)"
                )

                return True

            # =========================================
            # NEITHER APPROACH REACHED THE LOGIN SHEET
            # =========================================

            self.logger.warning(
                f"Attempt {attempt} did not reach the "
                f"login sheet, recovering and retrying..."
            )

            self.recover_app()

            time.sleep(2)

        # =============================================
        # ALL ATTEMPTS EXHAUSTED
        # =============================================

        self.logger.error(
            "Unable to open profile tab / reach login "
            f"sheet after {max_attempts} attempts"
        )

        self.take_error_screenshot(
            "profile_tab_failed"
        )

        raise Exception(
            "Unable to open profile tab / reach login "
            f"sheet after {max_attempts} attempts"
        )

    # =====================================================
    # ALREADY-LOGGED-IN DETECTION & HOME NAVIGATION
    #
    # Returns True if the app is on the logged-in profile
    # page (noReset=true kept session alive). Navigates to
    # the home feed before returning.
    # =====================================================

    def _check_already_logged_in(self):

        # Primary check: profile page loaded (Edit Profile visible)
        if self.is_displayed(
            LoginLocators.LOGGED_IN_PROFILE_INDICATOR,
            timeout=8
        ):
            self.logger.info(
                "Already logged in — 'Edit Profile' visible. "
                "noReset=true preserved a previous session. "
                "Navigating to home feed."
            )
            try:
                self.click(
                    LoginLocators.HOME_TAB,
                    timeout=5,
                    retry=1
                )
                self.logger.info("Navigated to home tab.")
            except Exception as nav_err:
                self.logger.warning(
                    f"Home tab navigation failed: {nav_err}"
                )
            return True

        # Fallback: if the home feed is already showing (exo_content_frame
        # visible), the user is logged in and on the feed — no navigation needed.
        if self.is_displayed(
            LoginLocators.HOME_PAGE_CANDIDATES[0],
            timeout=3
        ):
            self.logger.info(
                "Already logged in — home feed visible (exo_content_frame). "
                "Skipping login flow."
            )
            return True

        return False

    # =====================================================
    # CLICK CONTINUE BUTTON
    # =====================================================

    def click_continue(self):

        self.logger.info(
            "Clicking continue button"
        )

        try:

            self.click(
                LoginLocators.CONTINUE_BUTTON
            )

            self.logger.info(
                "Continue button clicked"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Continue button failed: {e}"
            )

            ScreenshotUtils.capture_full_debug(
                self.driver,
                "continue_button_failed"
            )

            raise

    # =====================================================
    # ENTER MOBILE NUMBER
    # =====================================================

    def enter_mobile_number(
            self,
            mobile_number
    ):

        self.logger.info(
            f"Entering mobile number: "
            f"{mobile_number}"
        )

        try:

            self.send_keys(
                LoginLocators.PHONE_INPUT,
                mobile_number
            )

            self.hide_keyboard()

            # Compose re-measures/re-lays-out the whole sheet when the
            # keyboard closes (the Proceed button's position depends on
            # the keyboard-free height). A fixed short settle wait here
            # is deliberate, not a lazy pad — click_proceed() immediately
            # follows this call, and without it the very next explicit
            # wait can start polling mid-relayout.
            self.wait_for_app_stable(0.5)

            self.logger.info(
                "Mobile number entered"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Mobile number entry failed: {e}"
            )

            ScreenshotUtils.capture_full_debug(
                self.driver,
                "mobile_number_failed"
            )

            raise

    # =====================================================
    # CLICK PROCEED BUTTON
    # =====================================================

    def click_proceed(self):

        self.logger.info(
            "Clicking proceed button"
        )

        try:

            self.click(
                LoginLocators.PROCEED_BUTTON
            )

            self.logger.info(
                "Proceed button clicked"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Proceed button failed: {e}"
            )

            ScreenshotUtils.capture_full_debug(
                self.driver,
                "proceed_button_failed"
            )

            raise

    # =====================================================
    # ENTER OTP
    # =====================================================

    def enter_otp(
            self,
            otp
    ):

        self.logger.info(
            f"Entering OTP: {otp}"
        )

        try:

            if len(str(otp)) < 4:

                raise Exception(
                    "Invalid OTP length"
                )

            self.send_keys(
                LoginLocators.OTP_INPUT,
                otp
            )

            self.hide_keyboard()

            self.logger.info(
                "OTP entered successfully"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"OTP entry failed: {e}"
            )

            ScreenshotUtils.capture_full_debug(
                self.driver,
                "otp_failed"
            )

            raise

    # =====================================================
    # CLICK VERIFY OTP BUTTON
    # OTP auto-submits on this app — no manual verify
    # button. Kept as defensive fallback only.
    # =====================================================

    def click_verify_otp(self):

        self.logger.info(
            "Clicking verify OTP button"
        )

        try:

            self.click(
                LoginLocators.VERIFY_OTP_BUTTON,
                timeout=3,
                retry=1
            )

            self.logger.info(
                "Verify OTP button clicked"
            )

            return True

        except Exception as e:

            self.logger.info(
                f"No manual verify button found (expected - "
                f"OTP auto-verifies on this app): {e}"
            )

            return False

    # =====================================================
    # WAIT FOR LOGIN OUTCOME
    # =====================================================

    def _capture_toast_text_best_effort(self):

        try:

            for toast_element in self.find_elements_safe(
                    LoginLocators.TOAST_MESSAGE
            ):

                if toast_element.is_displayed():

                    text = (
                            toast_element.text or ""
                    ).strip()

                    if text:
                        return text

        except Exception:
            pass

        return None

    def wait_for_login_outcome(
            self,
            timeout=30,
            poll_interval=0.4
    ):

        self.logger.info(
            "Waiting for OTP verification outcome "
            "(sheet closes = success, sheet stays "
            "open = invalid)..."
        )

        end_time = time.time() + timeout

        sheet_present_initially = bool(
            self.find_elements_safe(
                LoginLocators.LOGIN_SHEET_INDICATOR
            )
        )

        self.logger.info(
            f"Login sheet indicator present at start: "
            f"{sheet_present_initially}"
        )

        while time.time() < end_time:

            sheet_present_now = bool(
                self.find_elements_safe(
                    LoginLocators.LOGIN_SHEET_INDICATOR
                )
            )

            if sheet_present_initially and not sheet_present_now:

                self.logger.info(
                    "Login sheet closed -> "
                    "treating as login SUCCESS"
                )

                return (
                    "success",
                    self._capture_toast_text_best_effort()
                )

            time.sleep(poll_interval)

        final_sheet_present = bool(
            self.find_elements_safe(
                LoginLocators.LOGIN_SHEET_INDICATOR
            )
        )

        if sheet_present_initially and final_sheet_present:

            toast_text = self._capture_toast_text_best_effort()

            self.logger.warning(
                f"Timeout with OTP sheet still open -> "
                f"treating as INVALID OTP (toast text: "
                f"'{toast_text}')"
            )

            return (
                "invalid",
                toast_text or
                "(sheet remained open, no toast "
                "text captured)"
            )

        if sheet_present_initially and not final_sheet_present:

            self.logger.info(
                "Login sheet closed at timeout boundary -> "
                "treating as login SUCCESS"
            )

            return (
                "success",
                self._capture_toast_text_best_effort()
            )

        self.logger.warning(
            "Login sheet indicator was never confirmed "
            "present at start - cannot reliably determine "
            "outcome"
        )

        return "timeout", None

    # =====================================================
    # VALIDATE HOME PAGE
    # =====================================================

    def is_home_page_displayed(self, timeout=20):

        self.logger.info("Validating home page")

        # Single reliable indicator: ExoPlayer frame is only
        # present when a video is playing on the home feed.
        result = self.is_displayed(
            LoginLocators.HOME_PAGE_CANDIDATES[0],
            timeout=timeout,
        )

        if result:
            self.logger.info("Home page displayed (exo_content_frame visible)")
        else:
            self.logger.warning("Home page not displayed within timeout")

        return result

    # =====================================================
    # VALIDATE LOGIN SCREEN
    # =====================================================

    def is_login_screen_displayed(self):

        try:

            return self.is_any_displayed(
                LoginLocators.LOGIN_SCREEN_CANDIDATES,
                timeout=5
            )

        except Exception:

            return False

    # =====================================================
    # COMPLETE LOGIN FLOW
    # =====================================================

    def login(
            self,
            mobile_number,
            otp
    ):

        self.logger.info(
            "========== LOGIN FLOW START =========="
        )

        try:

            self.ensure_app_foreground()

            self.wait_for_app_stable()

            # =============================================
            # OPEN PROFILE / DETECT ALREADY LOGGED IN
            # =============================================

            try:
                self.open_profile_tab()
            except _AlreadyLoggedInError:
                self.logger.info(
                    "========== LOGIN SKIPPED "
                    "(ALREADY LOGGED IN) =========="
                )
                return True
            except Exception as profile_err:
                # Late fallback: if open_profile_tab() exhausted
                # all attempts before detecting the logged-in state
                # (e.g. UiAutomator2 recovered just enough), try once
                # more here before propagating.
                if self._check_already_logged_in():
                    self.logger.info(
                        "========== LOGIN SKIPPED "
                        "(ALREADY LOGGED IN — late detection) =========="
                    )
                    return True
                raise profile_err

            # =============================================
            # CONTINUE BUTTON
            # =============================================

            try:

                if self.is_displayed(
                        LoginLocators.CONTINUE_BUTTON,
                        timeout=5
                ):

                    self.click_continue()

            except Exception:
                pass

            # =============================================
            # ENTER MOBILE
            # =============================================

            self.enter_mobile_number(
                mobile_number
            )

            # =============================================
            # PROCEED
            # =============================================

            self.click_proceed()

            # =============================================
            # ENTER OTP (AUTO-VERIFIES ON THIS APP)
            # =============================================

            self.enter_otp(otp)

            # =============================================
            # WAIT FOR OUTCOME
            # =============================================

            outcome, detail = self.wait_for_login_outcome(
                timeout=30
            )

            if outcome == "invalid":

                ScreenshotUtils.capture_full_debug(
                    self.driver,
                    "invalid_otp_toast"
                )

                raise Exception(
                    f"Login failed - invalid OTP "
                    f"(toast shown: '{detail}')"
                )

            if outcome == "timeout":

                # OTP may have auto-verified so fast that the login
                # sheet was never detected in the DOM. Check if we
                # landed on the home feed before treating as failure.
                if self.is_home_page_displayed(timeout=10):
                    self.logger.info(
                        "========== LOGIN SUCCESS "
                        "(OTP auto-verified — home feed visible) =========="
                    )
                    return True

                ScreenshotUtils.capture_full_debug(
                    self.driver,
                    "otp_outcome_timeout"
                )

                raise Exception(
                    "Login failed - no invalid-OTP toast and "
                    "no home page detected after OTP entry"
                )

            self.logger.info(
                "========== LOGIN SUCCESS =========="
            )

            return True

        except TimeoutException as e:

            self.logger.error(
                f"Login timeout: {e}"
            )

            ScreenshotUtils.capture_full_debug(
                self.driver,
                "login_timeout"
            )

            raise

        except Exception as e:

            self.logger.error(
                f"Login flow failed: {e}"
            )

            ScreenshotUtils.capture_full_debug(
                self.driver,
                "login_failed"
            )

            raise

    # =====================================================
    # LOGOUT
    # =====================================================

    def logout(self):

        self.logger.info(
            "Logout functionality placeholder"
        )

        return True
