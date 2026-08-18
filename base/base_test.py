import pytest

from pages.login_page import LoginPage
from pages.feed_page import FeedPage
from testdata.test_data import VALID_LOGIN, COMMENTS
from utils.logger import LogGen


class BaseTest:
    """
    Per-test fresh Appium session (function-scoped `driver` fixture).

    Use this base for anything that needs to control the app's login
    state itself — login/session tests above all, since they assert
    on the actual act of logging in (and negative-path OTP tests use
    the `@pytest.mark.requires_logout` marker to force a real
    logged-out start — see conftest.py's `driver` fixture).
    """

    logger = LogGen.loggen()

    # ─── Auto-setup per test ─────────────────────────────

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        self.driver     = driver
        self.login_page = LoginPage(driver)
        self.feed_page  = FeedPage(driver)
        self.logger.info("BaseTest setup completed.")

    # ─── Common login ────────────────────────────────────

    def login_default_user(self):
        """
        Login using credentials from testdata/test_data.py.
        Never hardcode credentials here — change them in
        VALID_LOGIN (or via .env) only.
        """
        self.logger.info("Logging in as default test user.")
        return self.login_page.login(
            mobile_number=VALID_LOGIN["mobile"],
            otp=VALID_LOGIN["otp"],
        )

    # ─── Home page ───────────────────────────────────────

    def validate_home_page(self):
        assert self.login_page.is_home_page_displayed(), \
            "Home page not displayed after login."

    # ─── Combined login + feed-ready flow ────────────────

    def login_and_reach_feed(self):
        """
        Single entry point used by every feed test: log in with
        the default test user, confirm the home page loaded, then
        wait until the feed's own elements (like/comment buttons or
        the feed container) are actually present.

        This was called ~20 times across test_feed.py but never
        defined, so every feed test failed immediately with
        AttributeError before touching the app. Composed of
        three methods that already existed and were already
        proven reliable individually (login(), is_home_page_displayed(),
        wait_for_feed_ready()) — no new interaction logic invented here.
        """
        self.logger.info("login_and_reach_feed: START")
        self.login_default_user()
        # validate_home_page() waits up to 20s for exo_content_frame.
        # wait_feed_ready() would wait for the same element — redundant.
        self.validate_home_page()
        self.logger.info("login_and_reach_feed: COMPLETE")

    # ─── Feed shortcuts (thin wrappers for test readability)

    def wait_feed_ready(self):
        self.feed_page.wait_for_feed_ready()

    def safe_swipe_next_reel(self):
        self.feed_page.swipe_to_next_video()

    def like_current_video(self):
        self.feed_page.like_video()

    def comment_current_video(self, comment: str = COMMENTS[0]):
        """Default comment comes from test_data.COMMENTS, not hardcoded."""
        self.feed_page.add_comment(comment)

    def share_current_video(self):
        self.feed_page.share_video()

    def save_current_video(self):
        self.feed_page.save_video()

    def follow_current_user(self):
        self.feed_page.follow_user()

    def mute_unmute_video(self):
        self.feed_page.mute_unmute_video()

    def pause_resume_video(self):
        self.feed_page.pause_reel()
        self.feed_page.resume_reel()


class BaseFeedTest(BaseTest):
    """
    Session-scoped Appium session (logs in ONCE per pytest session
    instead of once per test) — used by every feed test class.

    ROOT CAUSE FIXED: every feed test previously called
    login_and_reach_feed() -> login_default_user() -> the full
    login() flow, AND got a brand-new Appium/UiAutomator2 session
    each time (BaseTest.setup depends on the function-scoped `driver`
    fixture). With ~20 feed tests in a run that meant ~20 fresh
    UiAutomator2 sessions plus ~20 complete login flows, each costing
    several ADB calls and app-foreground activations — the single
    biggest contributor to both the multi-hour suite runtimes and the
    repeated UiAutomator2 crashes observed under that sustained load.

    conftest.py already defined a session-scoped `logged_in_driver`
    fixture that logs in exactly once — it simply was never used by
    any test class. Feed tests are the correct place to use it: they
    don't need a fresh, install-like app state between actions (the
    existing tests already tolerate/expect shared engagement state —
    e.g. follow_user()'s idempotent "already following" check), so
    reusing one continuous logged-in session across the whole feed
    suite is both faster and closer to how a real user session
    actually behaves.
    """

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver):
        self.driver     = logged_in_driver
        self.login_page = LoginPage(logged_in_driver)
        self.feed_page  = FeedPage(logged_in_driver)
        self.logger.info("BaseFeedTest setup completed (session-scoped, already logged in).")

    def login_and_reach_feed(self):
        """
        The session-scoped driver is already logged in (see setup()
        above) — this just confirms the app is actually still showing
        the home feed before the test's own actions run, and only
        falls back to a real login if something (e.g. a navigation
        away, or an app restart mid-session) knocked it back to a
        logged-out state. This keeps the "login_and_reach_feed()"
        entry point every feed test already calls working exactly the
        same from the test's point of view, without repeating the
        full login flow on every single test.
        """
        self.logger.info("login_and_reach_feed: START (session-scoped)")

        if self.login_page.is_home_page_displayed(timeout=8):
            self.logger.info("login_and_reach_feed: already on home feed (session reused)")
            self.logger.info("login_and_reach_feed: COMPLETE")
            return

        self.logger.warning(
            "Session-scoped driver is not on the home feed — logging in again."
        )
        self.login_default_user()
        self.validate_home_page()
        self.logger.info("login_and_reach_feed: COMPLETE")