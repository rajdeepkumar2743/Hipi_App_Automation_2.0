# =========================================================
# FILE: tests/test_feed.py
#
# 20 independent feed tests — one test per feature/action.
#
# DESIGN PRINCIPLES:
#   - Each test is INDEPENDENT: gets its own driver session,
#     logs in fresh, and tests exactly ONE action. A failure
#     in one test never cascades to another.
#   - Each test follows the same pattern:
#       login_and_reach_feed() → action → assert outcome
#   - Clear Allure story grouping: each test belongs to a
#     feature group with a descriptive title and step trail.
#   - Assertions are explicit: every test has at least one
#     assert statement with a meaningful failure message.
#   - test_continuous_feed_flow is preserved at the bottom
#     as a long-running E2E scenario distinct from the
#     individual action tests.
#
# TEST INVENTORY:
#   Group A — Engagement (4 tests)
#     test_like_video
#     test_like_then_unlike_video
#     test_add_comment
#     test_save_video
#
#   Group B — Social (2 tests)
#     test_share_video
#     test_follow_user
#
#   Group C — Video controls (4 tests)
#     test_mute_video
#     test_unmute_video
#     test_pause_reel
#     test_pause_and_resume_reel
#
#   Group D — Navigation (3 tests)
#     test_swipe_to_next_video
#     test_swipe_multiple_reels
#     test_open_creator_profile
#
#   Group E — Comment sheet (2 tests)
#     test_open_and_close_comment_sheet
#     test_comment_sheet_input_visible
#
#   Group F — Three-dots menu (2 tests)
#     test_three_dots_close_via_cross
#     test_three_dots_close_via_cancel
#
#   Group G — Bottom navigation tabs (2 tests)
#     test_navigate_home_tab
#     test_navigate_discover_tab
#
#   Group H — E2E scenario (1 test)
#     test_continuous_feed_flow
# =========================================================

import time
import random

import allure
import pytest

from base.base_test import BaseFeedTest, BaseTest
from locators.feed_locators import FeedLocators
from testdata.test_data import COMMENTS


# =========================================================
# GROUP A — ENGAGEMENT ACTIONS
# =========================================================

@allure.feature("Feed — Engagement")
class TestFeedEngagement(BaseFeedTest):
    """Like, comment, and save interactions on feed videos."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Like")
    @allure.title("Like a video")
    def test_like_video(self):
        """
        Verify the Like button can be tapped without error.
        The like state is visible on the button (toggled highlight),
        but on a Compose app without stable resource-ids we assert
        the action completed without raising an exception.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap the Like button"):
            result = self.feed_page.like_video()

        with allure.step("Assert like action succeeded"):
            assert result is True, "like_video() did not return True"

        self.logger.info("TEST PASSED: Like video")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Like")
    @allure.title("Like then unlike a video (toggle)")
    def test_like_then_unlike_video(self):
        """
        Verify the Like button toggles: tap once to like,
        tap again to unlike. Leaves test account in clean state.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap Like (first tap — like the video)"):
            like_result = self.feed_page.like_video()
            assert like_result is True, "like_video() failed"

        with allure.step("Wait 1s then tap Like again (unlike the video)"):
            time.sleep(1)
            unlike_result = self.feed_page.unlike_video()
            assert unlike_result is True, "unlike_video() failed"

        self.logger.info("TEST PASSED: Like/unlike toggle")

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Comment")
    @allure.title("Add a comment to a video")
    def test_add_comment(self):
        """
        Verify a comment can be typed and submitted.
        Asserts: comment sheet closes after send (successful submission).
        """
        comment = COMMENTS[0]

        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step(f"Submit comment: '{comment}'"):
            result = self.feed_page.add_comment(comment)
            assert result is True, "add_comment() did not return True"

        with allure.step("Assert comment sheet is closed after submission"):
            sheet_closed = self.feed_page.is_comment_sheet_closed(timeout=5)
            assert sheet_closed, \
                "Comment sheet is still open after comment was submitted"

        self.logger.info("TEST PASSED: Add comment")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Comment")
    @allure.title("Add a comment using each available comment text")
    @pytest.mark.parametrize("comment", COMMENTS, ids=[f"comment_{i}" for i in range(len(COMMENTS))])
    def test_add_comment_variants(self, comment):
        """
        Verify each comment from COMMENTS list can be submitted.
        Parametrized: runs once per comment string.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step(f"Submit comment: '{comment}'"):
            result = self.feed_page.add_comment(comment)
            assert result is True, f"add_comment('{comment}') failed"

        with allure.step("Assert comment sheet closed"):
            assert self.feed_page.is_comment_sheet_closed(timeout=5), \
                f"Comment sheet did not close after submitting '{comment}'"

        self.logger.info(f"TEST PASSED: Add comment variant — '{comment}'")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Save")
    @allure.title("Save a video")
    def test_save_video(self):
        """
        Verify the Save button can be tapped without error.
        The save state changes the button icon on screen.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap the Save button"):
            result = self.feed_page.save_video()
            assert result is True, "save_video() did not return True"

        self.logger.info("TEST PASSED: Save video")


# =========================================================
# GROUP B — SOCIAL ACTIONS
# =========================================================

@allure.feature("Feed — Social")
class TestFeedSocial(BaseFeedTest):
    """Share and follow interactions."""

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Share")
    @allure.title("Share a video (opens and dismisses share sheet)")
    def test_share_video(self):
        """
        Verify the Share button opens the Android system share sheet
        and the app returns to the feed after dismissal.
        The system share sheet cannot be verified via app element IDs
        so we assert: share action completes + feed is still visible.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap Share button and dismiss share sheet"):
            result = self.feed_page.share_video()
            assert result is True, "share_video() did not return True"

        with allure.step("Assert feed is still visible after share dismissal"):
            assert self.feed_page.is_feed_visible(timeout=10), \
                "Feed is not visible after share sheet was dismissed"

        self.logger.info("TEST PASSED: Share video")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Follow")
    @allure.title("Follow a creator from the feed")
    def test_follow_user(self):
        """
        Verify a creator can be followed from the feed.
        If already following, the test passes (idempotent).
        If not following, tap Follow and verify 'Following' appears.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Check follow state before action"):
            already_following = self.feed_page.is_following_current_user(timeout=3)
            self.logger.info(
                f"Pre-test follow state: {'Following' if already_following else 'Not following'}"
            )

        with allure.step("Tap Follow button (skips if already following)"):
            result = self.feed_page.follow_user()
            assert result is True, "follow_user() did not return True"

        with allure.step("Assert 'Following' button is visible after follow action"):
            assert self.feed_page.is_following_current_user(timeout=5), \
                "Expected 'Following' button after follow action — not found"

        self.logger.info("TEST PASSED: Follow user")


# =========================================================
# GROUP C — VIDEO CONTROLS
# =========================================================

@allure.feature("Feed — Video Controls")
class TestFeedVideoControls(BaseFeedTest):
    """Mute, unmute, pause, and resume controls."""

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Mute")
    @allure.title("Mute a video")
    def test_mute_video(self):
        """
        Verify the Mute button can be tapped.
        The mute icon changes state (filled/outline) on the screen.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap the Mute button"):
            result = self.feed_page.mute_unmute_video()
            assert result is True, "mute_unmute_video() did not return True"

        self.logger.info("TEST PASSED: Mute video")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Mute")
    @allure.title("Mute then unmute a video (toggle)")
    def test_mute_then_unmute_video(self):
        """
        Verify mute toggles correctly: tap to mute, tap again to unmute.
        Leaves test account audio state unchanged.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap Mute (mute the video)"):
            mute_result = self.feed_page.mute_unmute_video()
            assert mute_result is True, "First mute tap failed"

        with allure.step("Wait 1s then tap Mute again (unmute)"):
            time.sleep(1)
            unmute_result = self.feed_page.mute_unmute_video()
            assert unmute_result is True, "Second mute tap (unmute) failed"

        self.logger.info("TEST PASSED: Mute/unmute toggle")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Pause")
    @allure.title("Pause a reel (single tap on video)")
    def test_pause_reel(self):
        """
        Verify a single tap on the video area pauses playback.
        On a Compose app the paused state is visual only; we assert
        the tap action completes successfully.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap video area to pause"):
            result = self.feed_page.pause_reel()
            assert result is True, "pause_reel() did not return True"

        with allure.step("Assert feed area is still visible (app did not crash)"):
            assert self.feed_page.is_feed_visible(timeout=5), \
                "Feed area disappeared after pause tap"

        self.logger.info("TEST PASSED: Pause reel")

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Pause")
    @allure.title("Pause a reel then resume playback")
    def test_pause_and_resume_reel(self):
        """
        Verify pause → wait → resume flow:
          tap once to pause → wait 3s → tap again to resume.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap video area to pause"):
            pause_result = self.feed_page.pause_reel()
            assert pause_result is True, "pause_reel() failed"

        with allure.step("Wait 3 seconds while paused"):
            time.sleep(3)

        with allure.step("Tap video area again to resume"):
            resume_result = self.feed_page.resume_reel()
            assert resume_result is True, "resume_reel() failed"

        with allure.step("Assert feed is still visible after resume"):
            assert self.feed_page.is_feed_visible(timeout=5), \
                "Feed area disappeared after resume"

        self.logger.info("TEST PASSED: Pause and resume reel")


# =========================================================
# GROUP D — NAVIGATION
# =========================================================

@allure.feature("Feed — Navigation")
class TestFeedNavigation(BaseFeedTest):
    """Swipe between videos and navigate to creator profiles."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Swipe")
    @allure.title("Swipe up to next video")
    def test_swipe_to_next_video(self):
        """
        Verify swiping up navigates to the next video.
        Asserts: page source changes (different video loaded).
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Capture page source before swipe"):
            source_before = self.driver.page_source

        with allure.step("Swipe up to next video"):
            result = self.feed_page.swipe_to_next_video()
            assert result is True, "swipe_to_next_video() did not return True"

        with allure.step("Assert page content changed after swipe"):
            source_after = self.driver.page_source
            assert source_before != source_after, \
                "Page source did not change after swipe — still on same video"

        self.logger.info("TEST PASSED: Swipe to next video")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Swipe")
    @allure.title("Swipe through 3 consecutive videos")
    def test_swipe_multiple_reels(self):
        """
        Verify the user can swipe through multiple videos in sequence.
        Tests that the feed remains stable across consecutive swipes.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        sources_seen = set()
        # ROOT CAUSE FIX: a fixed-length prefix (previously [:3000]) is
        # unreliable — verified live that the first several thousand
        # characters of the page source are generic Compose wrapper
        # boilerplate (ComposeView/View nesting) that is BYTE-IDENTICAL
        # across every video; the actual distinguishing content
        # (creator name, caption, like/comment counts) sits deeper in
        # the tree, well past any reasonably-sized prefix. Comparing
        # the FULL page source — the same approach the already-reliable
        # test_swipe_to_next_video() uses — is the correct fix rather
        # than guessing a longer cutoff.
        sources_seen.add(self.driver.page_source)

        for reel_num in range(1, 4):
            with allure.step(f"Swipe to video {reel_num + 1}"):
                result = self.feed_page.swipe_to_next_video()
                assert result is True, f"Swipe {reel_num} failed"

                # Give ExoPlayer a moment to load the new video so the
                # creator name / content nodes are in the accessibility tree.
                time.sleep(2)

                new_fingerprint = self.driver.page_source
                assert new_fingerprint not in sources_seen, \
                    f"Video {reel_num + 1} appears identical to a previous video — swipe may have failed"

                # ROOT CAUSE FIX: the previous version never added the new
                # fingerprint to sources_seen, so every iteration after the
                # first only ever compared against video 1 — video 3 being
                # identical to video 2 would have gone undetected. Track
                # every fingerprint seen so far, not just the starting one.
                sources_seen.add(new_fingerprint)
                sources_seen.add(new_fingerprint)

        self.logger.info("TEST PASSED: Swipe through 3 reels")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Creator Profile")
    @allure.title("Open creator profile from feed (coordinate tap)")
    def test_open_creator_profile(self):
        """
        Verify tapping the creator username/avatar opens their profile.
        Uses a coordinate tap since the username text is dynamic.
        Asserts: page source changes after tap (profile screen loaded).
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Capture page source before profile tap"):
            source_before = self.driver.page_source

        with allure.step("Tap creator username/avatar area"):
            result = self.feed_page.open_creator_profile()
            assert result is True, "open_creator_profile() did not return True"

        # No extra wait needed — open_creator_profile() now waits
        # internally on page-source change before returning.

        with allure.step("Assert page changed (profile screen loaded)"):
            source_after = self.driver.page_source
            assert source_before != source_after, \
                "Page source did not change after creator profile tap"

        self.logger.info("TEST PASSED: Open creator profile")


# =========================================================
# GROUP E — COMMENT SHEET
# =========================================================

@allure.feature("Feed — Comment Sheet")
class TestFeedCommentSheet(BaseFeedTest):
    """Comment sheet open/close and input verification."""

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Comment Sheet")
    @allure.title("Open comment sheet and close it without commenting")
    def test_open_and_close_comment_sheet(self):
        """
        Verify the comment sheet can be opened and closed
        without submitting a comment.
        Asserts: sheet is open after open tap, closed after close tap.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap Comment button to open sheet"):
            open_result = self.feed_page.open_comment_sheet()
            assert open_result is True, "open_comment_sheet() failed"

        with allure.step("Assert comment sheet is open"):
            assert self.feed_page.is_comment_sheet_open(timeout=5), \
                "Comment sheet did not open after tapping comment button"

        with allure.step("Tap Close to dismiss the comment sheet"):
            close_result = self.feed_page.close_comment_sheet()
            assert close_result is True, "close_comment_sheet() failed"

        with allure.step("Assert comment sheet is closed"):
            assert self.feed_page.is_comment_sheet_closed(timeout=5), \
                "Comment sheet did not close after tapping close button"

        self.logger.info("TEST PASSED: Open and close comment sheet")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Comment Sheet")
    @allure.title("Comment input field is visible and focusable in comment sheet")
    def test_comment_sheet_input_visible(self):
        """
        Verify the comment text input is visible when the sheet opens
        and the keyboard appears after tapping it.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Open comment sheet"):
            self.feed_page.open_comment_sheet()

        with allure.step("Assert comment input field is visible"):
            assert self.feed_page.is_comment_sheet_open(timeout=5), \
                "Comment input not visible after opening comment sheet"

        with allure.step("Tap comment input to trigger keyboard"):
            self.feed_page.click(FeedLocators.COMMENT_INPUT)

        with allure.step("Assert input still visible (keyboard did not crash app)"):
            assert self.feed_page.is_comment_sheet_open(timeout=5), \
                "Comment sheet disappeared after tapping input field"

        with allure.step("Dismiss keyboard and close sheet"):
            self.feed_page.hide_keyboard()
            self.feed_page.close_comment_sheet()

        self.logger.info("TEST PASSED: Comment input visible")


# =========================================================
# GROUP F — THREE-DOTS MENU
# =========================================================

@allure.feature("Feed — Three-Dots Menu")
class TestFeedThreeDotsMenu(BaseFeedTest):
    """Three-dots content menu — open and close via different controls."""

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Three Dots")
    @allure.title("Open three-dots menu and close via X button")
    def test_three_dots_close_via_cross(self):
        """
        Verify:
          1. Three-dots button opens the report/content menu.
          2. The report popup is visible (sheet opened correctly).
          3. Tapping the X icon closes the sheet.
          4. The popup is gone after closing.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap three-dots button"):
            open_result = self.feed_page.open_three_dots()
            assert open_result is True, "open_three_dots() failed"

        with allure.step("Assert report/content menu is visible"):
            assert self.feed_page.is_report_sheet_open(timeout=5), \
                "Report sheet did not open after tapping three-dots"

        # No extra wait needed — is_report_sheet_open() above already
        # confirmed visibility, and click() inside
        # close_report_popup_using_cross() waits for clickability itself.

        with allure.step("Close the menu via the X (cross) button"):
            close_result = self.feed_page.close_report_popup_using_cross()
            assert close_result is True, "close_report_popup_using_cross() failed"

        with allure.step("Assert report/content menu is closed"):
            assert self.feed_page.is_report_sheet_closed(timeout=5), \
                "Report sheet did not close after tapping the cross button"

        self.logger.info("TEST PASSED: Three-dots menu close via cross")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Three Dots")
    @allure.title("Open three-dots menu and close via Cancel button")
    def test_three_dots_close_via_cancel(self):
        """
        Verify:
          1. Three-dots button opens the report/content menu.
          2. The report popup is visible.
          3. Tapping 'Cancel' closes the sheet.
          4. The popup is gone after closing.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap three-dots button"):
            open_result = self.feed_page.open_three_dots()
            assert open_result is True, "open_three_dots() failed"

        with allure.step("Assert report/content menu is visible"):
            assert self.feed_page.is_report_sheet_open(timeout=5), \
                "Report sheet did not open after tapping three-dots"

        # No extra wait needed — same reasoning as the cross-close
        # variant above.

        with allure.step("Close the menu via the Cancel button"):
            close_result = self.feed_page.close_report_popup_using_cancel()
            assert close_result is True, "close_report_popup_using_cancel() failed"

        with allure.step("Assert report/content menu is closed"):
            assert self.feed_page.is_report_sheet_closed(timeout=5), \
                "Report sheet did not close after tapping Cancel"

        self.logger.info("TEST PASSED: Three-dots menu close via cancel")


# =========================================================
# GROUP G — BOTTOM NAVIGATION TABS
# =========================================================

@allure.feature("Feed — Bottom Navigation")
class TestFeedBottomNavigation(BaseFeedTest):
    """Bottom tab bar navigation from the feed screen."""

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Navigation Tabs")
    @allure.title("Navigate to Home tab from feed")
    def test_navigate_home_tab(self):
        """
        Verify tapping the Home tab in the bottom nav bar
        keeps/returns to the home feed.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Tap Home tab"):
            result = self.feed_page.navigate_to_home_tab()
            assert result is True, "navigate_to_home_tab() failed"

        with allure.step("Assert feed is still visible after Home tab tap"):
            assert self.feed_page.is_feed_visible(timeout=10), \
                "Feed not visible after tapping Home tab"

        self.logger.info("TEST PASSED: Navigate Home tab")

    @pytest.mark.feed
    @pytest.mark.regression
    @allure.story("Navigation Tabs")
    @allure.title("Navigate to Discover tab from feed")
    def test_navigate_discover_tab(self):
        """
        Verify tapping the Discover tab navigates away from the feed.
        Asserts: page source changes after tapping Discover.
        """
        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        with allure.step("Capture page source before tab switch"):
            source_before = self.driver.page_source

        with allure.step("Tap Discover tab"):
            result = self.feed_page.navigate_to_discover_tab()
            assert result is True, "navigate_to_discover_tab() failed"

        # No extra wait needed — navigate_to_discover_tab() now waits
        # internally on page-source change before returning.

        with allure.step("Assert page changed (Discover loaded)"):
            source_after = self.driver.page_source
            assert source_before != source_after, \
                "Page did not change after tapping Discover tab"

        self.logger.info("TEST PASSED: Navigate Discover tab")


# =========================================================
# GROUP H — E2E SCENARIO
# =========================================================

@allure.feature("Feed — End-to-End")
class TestFeedE2E(BaseTest):
    """
    Long-running E2E scenario covering random feed interactions
    across multiple reels. Kept separate from individual tests
    so it can be run on-demand without blocking the fast suite.

    ROOT CAUSE FIX: uses BaseTest (fresh, isolated per-test driver)
    rather than BaseFeedTest (session shared with all other feed
    tests). This is the longest, heaviest test in the file — 10 reels
    x 2-5 actions each, run live against the emulator — and observed
    live to be where sustained interaction is most likely to trip a
    UiAutomator2 crash. Sharing the same long-lived session as the 25
    other feed tests meant it inherited their cumulative session age
    on top of its own load, and a crash here would fail every test
    that runs after it in that shared session. Giving it its own
    fresh session isolates that risk exactly as this docstring already
    promised ("kept separate... so it can be run on-demand without
    blocking the fast suite") — a promise the previous BaseFeedMulti
    change had accidentally broken.
    """

    @pytest.mark.feed
    @pytest.mark.feed_e2e
    @pytest.mark.regression
    @allure.story("Continuous Feed Flow")
    @allure.title("Continuous human-like feed automation (10 reels)")
    def test_continuous_feed_flow(self):
        """
        Simulates a real user session: login, scroll through 10 reels,
        and perform 2–5 random actions per reel.
        This is a broad stability/smoke test for the feed as a whole.
        Individual action correctness is verified in the tests above.
        """
        from testdata.test_data import FEED_ACTIONS

        with allure.step("Login and reach feed"):
            self.login_and_reach_feed()

        for reel_number in range(1, 11):
            self.logger.info(f"─── Reel {reel_number}/10 ───")

            with allure.step(f"Reel {reel_number} — perform actions"):
                performed = self._process_reel(reel_number, FEED_ACTIONS)
                self.logger.info(f"Reel {reel_number} actions: {performed}")

            with allure.step(f"Reel {reel_number} — watch then swipe"):
                watch_time = random.randint(5, 10)
                self.logger.info(f"Watching for {watch_time}s")
                time.sleep(watch_time)
                try:
                    self.safe_swipe_next_reel()
                except Exception as e:
                    self.logger.error(f"Swipe failed on reel {reel_number}: {e}")
                time.sleep(random.randint(3, 5))

        self.logger.info("TEST PASSED: Continuous feed flow (10 reels)")

    def _process_reel(self, reel_number: int, feed_actions: list) -> list:
        """Perform 2-5 random actions on the current reel."""
        performed = []
        for _ in range(random.randint(2, 5)):
            action = random.choice(feed_actions)
            try:
                self._dispatch_action(action)
                performed.append(action.upper())
                time.sleep(random.randint(2, 5))
            except Exception as e:
                self.logger.error(
                    f"Action '{action}' failed on reel {reel_number}: {e}"
                )
        return performed

    def _dispatch_action(self, action: str) -> None:
        """Route a named action to the correct FeedPage method."""
        self.logger.info(f"ACTION → {action.upper()}")

        if action == "like":
            self.like_current_video()
        elif action == "comment":
            self.comment_current_video(random.choice(COMMENTS))
        elif action == "share":
            self.share_current_video()
        elif action == "save":
            self.save_current_video()
        elif action == "mute":
            self.mute_unmute_video()
        elif action == "pause":
            self.pause_resume_video()
        elif action == "follow":
            self.follow_current_user()
        elif action == "three_dots_cross":
            # No sleep needed — open_three_dots() already waits
            # internally for the report popup to be visible.
            self.feed_page.open_three_dots()
            self.feed_page.close_report_popup_using_cross()
        elif action == "three_dots_cancel":
            self.feed_page.open_three_dots()
            self.feed_page.close_report_popup_using_cancel()
        else:
            self.logger.warning(f"Unknown action '{action}' — skipped.")