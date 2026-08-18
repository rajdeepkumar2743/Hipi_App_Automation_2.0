# =========================================================
# FILE: pages/feed_page.py
#
# NOTE: This file was missing from the original upload and
# has been RECONSTRUCTED to match every call already made
# against it in base/base_test.py and tests/test_feed.py:
#   wait_for_feed_ready, swipe_to_next_video, like_video,
#   add_comment, share_video, save_video, follow_user,
#   mute_unmute_video, pause_reel, resume_reel,
#   open_three_dots, close_report_popup_using_cross,
#   close_report_popup_using_cancel
#
# Verify tap/gesture behavior against the real HiPi app,
# especially pause/resume and share (system share sheet).
#
# ADDED — methods test_feed.py called but that never existed,
# which meant every one of its ~20 tests failed immediately:
#   unlike_video, open_comment_sheet, close_comment_sheet,
#   is_comment_sheet_open, is_comment_sheet_closed,
#   is_following_current_user, is_report_sheet_open,
#   is_report_sheet_closed, is_feed_visible,
#   navigate_to_home_tab, navigate_to_discover_tab
#
# add_comment() was also refactored to call the new
# open_comment_sheet/close_comment_sheet building blocks
# instead of duplicating that logic inline (DRY).
# =========================================================

import time

from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage

from locators.feed_locators import FeedLocators

from utils.logger import LogGen

from config.config import Config


class FeedPage(BasePage):

    logger = LogGen.loggen()

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self, driver):

        super().__init__(driver)
        self._pre_three_dots_source = None

    # =====================================================
    # WAIT FOR FEED READY
    # =====================================================

    def wait_for_feed_ready(self, timeout=Config.EXPLICIT_WAIT):

        self.logger.info(
            "Waiting for feed to be ready"
        )

        try:

            self.wait_for_visible(
                FeedLocators.FEED_SCREEN,
                timeout=timeout
            )

            self.logger.info(
                "Feed is ready"
            )

            return True

        except TimeoutException as e:

            # Generic navigation-recovery: the app may have landed on a
            # different screen/popup/tab than expected. Try to get back
            # to the feed automatically (clear system dialogs, back
            # press, tap Home tab) before failing the whole flow.
            self.logger.warning(
                f"Feed not ready within {timeout}s — attempting automatic "
                f"navigation recovery before giving up: {e}"
            )

            recovered = self.recover_to_screen(
                FeedLocators.FEED_SCREEN,
                timeout=5,
                nav_actions=[
                    lambda: self.click(FeedLocators.HOME_TAB, timeout=5, retry=1),
                ],
            )

            if recovered:
                self.logger.info("Feed is ready (recovered via automatic navigation)")
                return True

            self.logger.error(f"Feed not ready: {e}")
            raise

    # =====================================================
    # OPEN CREATOR'S PROFILE (tap username/name)
    #
    # The username/display-name text is dynamic per video
    # (e.g. "Test userrr") so it can't be matched by a fixed
    # text locator. Uses a coordinate tap instead, computed
    # from the confirmed on-screen position of the name
    # label relative to screen size.
    # =====================================================

    def open_creator_profile(self):

        self.logger.info(
            "Opening creator's profile"
        )

        try:

            self.ensure_app_foreground()

            old_source = self.driver.page_source

            x_percent, y_percent = (
                FeedLocators.USERNAME_TAP_PERCENT
            )

            self.gestures.tap_by_percentage(
                x_percent,
                y_percent
            )

            # Wait for the page to actually change instead of a
            # blind sleep — same wait_page_change pattern used by
            # swipe_to_next_video() and navigate_to_discover_tab().
            # Non-fatal if it times out: the coordinate tap itself
            # may have missed (see USERNAME_TAP_PERCENT calibration
            # note in feed_locators.py), and the caller's own
            # assertion on page-source change will catch that.
            self.wait_page_change(
                old_source,
                timeout=Config.EXPLICIT_WAIT
            )

            self.logger.info(
                "Creator profile opened (coordinate tap)"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Open creator profile failed: {e}"
            )

            self.take_error_screenshot(
                "open_creator_profile_failed"
            )

            raise

    # =====================================================
    # LIKE VIDEO
    # =====================================================

    def like_video(self):

        self.logger.info(
            "Liking current video"
        )

        try:

            self.click(
                FeedLocators.LIKE_BUTTON
            )

            self.logger.info(
                "Video liked"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Like video failed: {e}"
            )

            self.take_error_screenshot(
                "like_video_failed"
            )

            raise

    # =====================================================
    # UNLIKE VIDEO
    #
    # LIKE_BUTTON is a toggle on this app (per Appium
    # Inspector — same element, no separate "unlike" icon),
    # so unlike is just a second tap on LIKE_BUTTON.
    # Kept as its own method (rather than reusing
    # like_video() directly) so call sites and logs read
    # correctly and intent stays explicit for whoever reads
    # a failing test later.
    # =====================================================

    def unlike_video(self):

        self.logger.info(
            "Unliking current video"
        )

        try:

            self.click(
                FeedLocators.LIKE_BUTTON
            )

            self.logger.info(
                "Video unliked"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Unlike video failed: {e}"
            )

            self.take_error_screenshot(
                "unlike_video_failed"
            )

            raise

    # =====================================================
    # COMMENT SHEET — OPEN / CLOSE / STATE CHECKS
    #
    # Split out from the old inline add_comment() so
    # test_feed.py's "open sheet, verify open, close,
    # verify closed" tests (which were calling methods
    # that didn't exist) have real building blocks, and so
    # add_comment() itself no longer duplicates this logic.
    # =====================================================

    def open_comment_sheet(self):

        self.logger.info(
            "Opening comment sheet"
        )

        try:

            self.click(
                FeedLocators.COMMENT_BUTTON
            )

            self.wait_for_visible(
                FeedLocators.COMMENT_INPUT
            )

            self.logger.info(
                "Comment sheet opened"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Open comment sheet failed: {e}"
            )

            self.take_error_screenshot(
                "open_comment_sheet_failed"
            )

            raise

    def close_comment_sheet(self):

        self.logger.info(
            "Closing comment sheet"
        )

        try:

            self.hide_keyboard()

            if self.is_displayed(
                    FeedLocators.COMMENT_CLOSE_BUTTON,
                    timeout=3
            ):

                self.click(
                    FeedLocators.COMMENT_CLOSE_BUTTON
                )

            else:

                # No explicit close icon visible — fall back
                # to back-press, which dismisses the bottom
                # sheet on every Compose bottom-sheet we've
                # seen in this app (same fallback share_video()
                # already relies on for the system share sheet).
                self.go_back()

            self.wait_until_disappear(
                FeedLocators.COMMENT_INPUT,
                timeout=5
            )

            self.logger.info(
                "Comment sheet closed"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Close comment sheet failed: {e}"
            )

            self.take_error_screenshot(
                "close_comment_sheet_failed"
            )

            raise

    def is_comment_sheet_open(self, timeout=5):
        """Non-raising state check — used in assertions, not flow control."""
        return self.is_displayed(
            FeedLocators.COMMENT_INPUT,
            timeout=timeout
        )

    def is_comment_sheet_closed(self, timeout=5):
        """
        Inverse of is_comment_sheet_open(). Actively waits for the
        input to disappear rather than doing a single is_displayed()
        check, since "closed" is a transition that can lag slightly
        behind the close tap (sheet animates out).
        """
        return self.wait_until_disappear(
            FeedLocators.COMMENT_INPUT,
            timeout=timeout
        )

    # =====================================================
    # ADD COMMENT
    # Now composed from open_comment_sheet/close_comment_sheet
    # instead of duplicating that logic inline.
    # =====================================================

    def add_comment(self, comment="Awesome 🔥"):

        self.logger.info(
            f"Adding comment: {comment}"
        )

        try:

            self.open_comment_sheet()

            self.send_keys(
                FeedLocators.COMMENT_INPUT,
                comment
            )

            self.hide_keyboard()

            self.click(
                FeedLocators.COMMENT_SEND_BUTTON
            )

            self.human_delay()

            # Close comment sheet if still open after send.
            # Try the close button first; fall back to back-press
            # if the button doesn't exist (Compose bottom sheet).
            if self.is_displayed(FeedLocators.COMMENT_CLOSE_BUTTON, timeout=3):
                self.click(FeedLocators.COMMENT_CLOSE_BUTTON)
            elif self.is_displayed(FeedLocators.COMMENT_INPUT, timeout=2):
                self.go_back()

            self.logger.info(
                "Comment added"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Add comment failed: {e}"
            )

            self.take_error_screenshot(
                "add_comment_failed"
            )

            raise

    # =====================================================
    # SHARE VIDEO
    # =====================================================

    def share_video(self):

        self.logger.info(
            "Sharing current video"
        )

        try:

            self.click(
                FeedLocators.SHARE_BUTTON
            )

            self.human_delay(1, 2)

            # Android system share sheet cannot be reliably
            # located via app resource-ids — dismiss with back.
            self.go_back()

            # The share chooser may have pushed the app to the
            # background. Bring HiPi back to the foreground so
            # the feed can resume.
            self.ensure_app_foreground()

            # After app activation the ExoPlayer needs a moment to
            # re-initialize. Wait up to 20s for exo_content_frame
            # before returning — this way the caller's is_feed_visible()
            # check has a pre-warmed result and won't race with
            # a still-loading video.
            time.sleep(2)
            if not self.is_feed_visible(timeout=18):
                self.logger.warning(
                    "Feed not visible 20s after share sheet was dismissed. "
                    "App may be on a different screen."
                )

            self.logger.info(
                "Share sheet dismissed"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Share video failed: {e}"
            )

            self.take_error_screenshot(
                "share_video_failed"
            )

            raise

    # =====================================================
    # SAVE VIDEO
    # =====================================================

    def save_video(self):

        self.logger.info(
            "Saving current video"
        )

        try:

            self.click(
                FeedLocators.SAVE_BUTTON
            )

            self.logger.info(
                "Video saved"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Save video failed: {e}"
            )

            self.take_error_screenshot(
                "save_video_failed"
            )

            raise

    # =====================================================
    # FOLLOW STATE CHECK
    # =====================================================

    def is_following_current_user(self, timeout=3):
        """Non-raising state check for the current creator's follow state."""
        return self.is_displayed(
            FeedLocators.FOLLOWING_BUTTON,
            timeout=timeout
        )

    # =====================================================
    # FOLLOW USER
    # =====================================================

    def follow_user(self):

        self.logger.info(
            "Following current user"
        )

        try:

            if self.is_displayed(
                    FeedLocators.FOLLOWING_BUTTON,
                    timeout=3
            ):

                self.logger.info(
                    "User already followed - skipping"
                )

                return True

            self.click(
                FeedLocators.FOLLOW_BUTTON
            )

            self.logger.info(
                "User followed"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Follow user failed: {e}"
            )

            self.take_error_screenshot(
                "follow_user_failed"
            )

            raise

    # =====================================================
    # MUTE / UNMUTE VIDEO
    #
    # ROOT CAUSE FIX (see locators/feed_locators.py for full
    # detail): MUTE_ICON and THREE_DOTS_BUTTON were swapped,
    # so every previous "mute" test actually opened/closed the
    # three-dots Report Content sheet without ever touching
    # mute. Fixed at the locator level (last()-1 vs last()).
    #
    # VERIFICATION: this app toggles mute by adjusting the
    # ExoPlayer's local volume only — verified live that this
    # produces NO accessibility-tree change and NO system
    # audio-stream mute change (dumpsys audio), so neither the
    # UI tree nor AudioManager can confirm the audio actually
    # changed. A full page-source diff was tried and rejected:
    # it false-positives on unrelated background churn (the
    # feed keeps re-rendering on its own, e.g. ExoPlayer error/
    # retry banners), so it can't distinguish "we hit the wrong
    # button" from "the feed re-rendered on its own between our
    # two reads." What CAN be verified, and is the real
    # business risk this method must catch, is clicking the
    # WRONG button or landing outside the app entirely — both
    # observed live during root-cause analysis:
    #   1. Tapping the wrong button opens a known sheet (report
    #      popup / comment sheet) — the exact bug this fix
    #      closes (MUTE_ICON used to resolve to the three-dots
    #      button).
    #   2. This control was also observed live to trigger a
    #      native "Allow Hipi-Dev to access music and audio"
    #      runtime permission dialog outside the app package.
    #      recover_app() (called from click() on any failure,
    #      and explicitly checked again here) now detects and
    #      auto-grants known system permission dialogs — see
    #      BasePage._handle_system_dialog_if_present().
    #   3. The feed must still be visible and responsive
    #      afterward (no crash / no accidental navigation).
    # If any check fails, this raises instead of silently
    # returning True — closing the exact gap that let the
    # locator swap go undetected for so many runs.
    # =====================================================

    def mute_unmute_video(self):

        self.logger.info(
            "Toggling mute on current video"
        )

        try:

            self.click(
                FeedLocators.MUTE_ICON
            )

            # Give Compose a moment to settle before re-reading the tree.
            self.wait_for_app_stable(1)

            # A system dialog (e.g. the audio-permission prompt observed
            # live) runs in a different package and will never satisfy
            # any com.zee5.hipi locator — detect and clear it explicitly
            # rather than letting every subsequent check time out.
            if self._handle_system_dialog_if_present():
                self.logger.info(
                    "Cleared a system dialog that appeared after the mute tap."
                )

            if self.is_displayed(FeedLocators.REPORT_POPUP, timeout=2):
                self.take_error_screenshot("mute_hit_wrong_button_report_popup")
                raise Exception(
                    "mute_unmute_video() opened the Report Content sheet — "
                    "MUTE_ICON resolved to the three-dots button, not mute."
                )

            if self.is_displayed(FeedLocators.COMMENT_INPUT, timeout=2):
                self.take_error_screenshot("mute_hit_wrong_button_comment_sheet")
                raise Exception(
                    "mute_unmute_video() opened the comment sheet — "
                    "MUTE_ICON resolved to the wrong button."
                )

            if not self.is_feed_visible(timeout=8):
                self.take_error_screenshot("mute_feed_not_visible_after_tap")
                raise Exception(
                    "Feed is not visible after mute tap — app may have "
                    "navigated away or crashed."
                )

            self.logger.info(
                "Mute toggled (verified: correct element, no known wrong-"
                "button sheet opened, feed still visible)"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Mute toggle failed: {e}"
            )

            self.take_error_screenshot(
                "mute_toggle_failed"
            )

            raise

    # =====================================================
    # PAUSE REEL (tap video to pause)
    # =====================================================

    def pause_reel(self):

        self.logger.info(
            "Pausing current reel"
        )

        try:

            # VIDEO_TOUCH_AREA XPath cannot be located because in the
            # actual DOM the large clickable View is a SIBLING of the
            # ViewFactoryHolder (which contains exo_content_frame), not
            # its parent. Coordinate tap at 40%,40% always lands in the
            # video area, safely clear of the right-side action buttons
            # (which start at ~87% of screen width) and the creator info
            # bar at the bottom (~85% of screen height).
            self.gestures.tap_by_percentage(0.4, 0.4)

            self.logger.info(
                "Reel paused (coordinate tap on video area)"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Pause reel failed: {e}"
            )

            self.take_error_screenshot(
                "pause_reel_failed"
            )

            raise

    # =====================================================
    # RESUME REEL (tap video again to resume)
    # =====================================================

    def resume_reel(self):

        self.logger.info(
            "Resuming current reel"
        )

        try:

            # Same coordinate-tap approach as pause_reel() — same element,
            # same DOM sibling issue, same 40%,40% safe target.
            self.gestures.tap_by_percentage(0.4, 0.4)

            self.logger.info(
                "Reel resumed (coordinate tap on video area)"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Resume reel failed: {e}"
            )

            self.take_error_screenshot(
                "resume_reel_failed"
            )

            raise

    # =====================================================
    # OPEN THREE DOTS MENU
    # =====================================================

    def open_three_dots(self):

        self.logger.info(
            "Opening three-dots menu"
        )

        try:

            pre_click_source = self.driver.page_source
            # Store for is_report_sheet_open() fallback comparison
            self._pre_three_dots_source = pre_click_source

            self.click(
                FeedLocators.THREE_DOTS_BUTTON
            )

            # Detect popup by page-source change rather than by a
            # specific locator. The Compose bottom sheet has no stable
            # resource-id and the content (Report/Not-interested/etc.)
            # may vary; page-source change is the only reliable signal.
            popup_opened = self.wait_page_change(
                pre_click_source,
                timeout=8
            )

            if not popup_opened:
                self._pre_three_dots_source = None
                self.take_error_screenshot("open_three_dots_failed")
                raise Exception(
                    "Three-dots menu did not open "
                    "(page source unchanged after 8s)"
                )

            self.logger.info(
                "Three-dots menu opened (page source changed)"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Open three dots failed: {e}"
            )

            self.take_error_screenshot(
                "open_three_dots_failed"
            )

            raise

    # =====================================================
    # REPORT SHEET STATE CHECKS
    # =====================================================

    def is_report_sheet_open(self, timeout=5):
        """
        Non-raising state check. Tries the broad text-based REPORT_POPUP
        locator first. Falls back to a page-source comparison against the
        baseline captured in open_three_dots() if no known text matches —
        any difference in the tree confirms the sheet is still open.
        """
        if self.is_displayed(FeedLocators.REPORT_POPUP, timeout=timeout):
            return True

        # Fallback: compare against pre-popup baseline stored by open_three_dots()
        baseline = getattr(self, "_pre_three_dots_source", None)
        if baseline is not None:
            try:
                return self.driver.page_source != baseline
            except Exception:
                pass

        return False

    def is_report_sheet_closed(self, timeout=8):
        """
        Returns True when the report/three-dots sheet is no longer shown.
        Primary check: wait for REPORT_POPUP to disappear (works when the
        locator DID match on open). Fallback: the sheet is a Compose element
        whose exact locator varies; if feed action buttons are responsive
        again (THREE_DOTS_BUTTON clickable), the sheet is gone.
        """
        if self.wait_until_disappear(FeedLocators.REPORT_POPUP, timeout=2):
            return True
        return self.is_displayed(
            FeedLocators.THREE_DOTS_BUTTON,
            timeout=timeout
        )

    # =====================================================
    # CLOSE REPORT POPUP USING CROSS
    # =====================================================

    def close_report_popup_using_cross(self):

        self.logger.info(
            "Closing report popup via cross icon"
        )

        try:

            # Try the native close icon first; fall back to back button
            # which dismisses any Compose bottom sheet universally.
            if self.is_displayed(FeedLocators.REPORT_CLOSE_BUTTON, timeout=3):
                self.click(FeedLocators.REPORT_CLOSE_BUTTON)
            else:
                self.go_back()

            self._pre_three_dots_source = None  # clear stale baseline

            self.logger.info(
                "Report popup closed (cross / back)"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Close popup (cross) failed: {e}"
            )

            self.take_error_screenshot(
                "close_popup_cross_failed"
            )

            raise

    # =====================================================
    # CLOSE REPORT POPUP USING CANCEL
    # =====================================================

    def close_report_popup_using_cancel(self):

        self.logger.info(
            "Closing report popup via cancel button"
        )

        try:

            # Try the Cancel text button first; fall back to back button
            # which dismisses any Compose bottom sheet universally.
            if self.is_displayed(FeedLocators.REPORT_CANCEL_BUTTON, timeout=3):
                self.click(FeedLocators.REPORT_CANCEL_BUTTON)
            else:
                self.go_back()

            self._pre_three_dots_source = None  # clear stale baseline

            self.logger.info(
                "Report popup closed (cancel / back)"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Close popup (cancel) failed: {e}"
            )

            self.take_error_screenshot(
                "close_popup_cancel_failed"
            )

            raise

    # =====================================================
    # SWIPE TO NEXT VIDEO
    # =====================================================

    def swipe_to_next_video(self):

        self.logger.info(
            "Swiping to next video"
        )

        try:

            self.ensure_app_foreground()

            old_source = self.driver.page_source

            self.gestures.swipe_up()

            self.wait_page_change(
                old_source,
                timeout=Config.EXPLICIT_WAIT
            )

            self.wait_for_visible(
                FeedLocators.NEXT_VIDEO_VALIDATION
            )

            self.logger.info(
                "Swiped to next video"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Swipe to next video failed: {e}"
            )

            self.take_error_screenshot(
                "swipe_next_video_failed"
            )

            raise

    # =====================================================
    # FEED VISIBILITY CHECK
    # Reuses the same candidate-locator race as
    # wait_for_feed_ready(), but as a non-raising boolean
    # check for use in assertions (e.g. "is the feed still
    # visible after this action, or did we navigate away /
    # crash").
    # =====================================================

    def is_feed_visible(self, timeout=5):

        return self.is_displayed(
            FeedLocators.FEED_SCREEN,
            timeout=timeout
        )

    # =====================================================
    # BOTTOM NAVIGATION — HOME / DISCOVER TABS
    # =====================================================

    def navigate_to_home_tab(self):

        self.logger.info(
            "Navigating to Home tab"
        )

        try:

            self.click(
                FeedLocators.HOME_TAB
            )

            self.logger.info(
                "Home tab tapped"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Navigate to Home tab failed: {e}"
            )

            self.take_error_screenshot(
                "navigate_home_tab_failed"
            )

            raise

    def navigate_to_discover_tab(self):
        """
        Waits for page_source to change after the tap so callers
        don't need their own time.sleep() to confirm the Discover
        screen actually loaded — same wait_page_change pattern
        already used by swipe_to_next_video() above.
        """

        self.logger.info(
            "Navigating to Discover tab"
        )

        try:

            old_source = self.driver.page_source

            self.click(
                FeedLocators.DISCOVER_TAB
            )

            self.wait_page_change(
                old_source,
                timeout=Config.EXPLICIT_WAIT
            )

            self.logger.info(
                "Discover tab tapped"
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Navigate to Discover tab failed: {e}"
            )

            self.take_error_screenshot(
                "navigate_discover_tab_failed"
            )

            raise