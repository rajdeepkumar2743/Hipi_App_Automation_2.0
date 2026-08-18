# =========================================================
# FILE: locators/login_locators.py
#
# ALL locators verified against page-source XML.
# =========================================================

from appium.webdriver.common.appiumby import AppiumBy


class LoginLocators:

    # =====================================================
    # PROFILE ICON (bottom navigation tab)
    #
    # VERIFIED via page-source XML:
    #   android.view.View clickable=true [661,2183][860,2309]
    #     android.widget.TextView text="Profile" clickable=false
    #
    # The View has NO content-desc and NO resource-id.
    # text("Profile") on UiSelector targets the parent View's
    # text attribute (empty), NOT the child — use XPath with
    # a descendant text match instead.
    # =====================================================
    PROFILE_ICON = (
        AppiumBy.XPATH,
        "//android.view.View[@clickable='true']"
        "[.//android.widget.TextView[@text='Profile']]"
    )

    # Direct coordinate tap fallback — center of Profile tab.
    # Bounds confirmed via XML: [661,2183][860,2309], center (760,2246).
    # Percentage for 1080x2400 screen: 760/1080=0.704, 2246/2400=0.936.
    PROFILE_ICON_TAP_PERCENT = (0.704, 0.936)

    # =====================================================
    # LOGIN / SIGNUP SCREEN ELEMENTS
    # =====================================================
    CONTINUE_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Continue")'
    )
    PHONE_INPUT = (AppiumBy.CLASS_NAME, "android.widget.EditText")
    PROCEED_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Proceed")
    OTP_INPUT = (AppiumBy.CLASS_NAME, "android.widget.EditText")

    # =====================================================
    # VERIFY OTP BUTTON
    # Per Appium Inspector, OTP auto-submits — no verify
    # button. Kept as a defensive fallback only.
    # =====================================================
    VERIFY_OTP_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Verify")'
    )

    # =====================================================
    # HOME PAGE CANDIDATES
    #
    # Used by is_home_page_displayed() to verify the feed
    # loaded after login. ExoPlayer frame is the ONLY
    # reliable indicator: present only when a video is
    # playing on the home feed.
    #
    # REMOVED: descriptionContains("Home") — the Home nav
    # tab View has NO content-desc in the HiPi Compose app,
    # so this selector never matched anything.
    # =====================================================
    HOME_PAGE_CANDIDATES = [
        (AppiumBy.ID, "com.zee5.hipi:id/exo_content_frame"),
    ]

    # =====================================================
    # LOGIN SCREEN CANDIDATES
    # =====================================================
    LOGIN_SCREEN_CANDIDATES = [
        PHONE_INPUT,
        CONTINUE_BUTTON,
    ]

    # =====================================================
    # LOGIN / OTP BOTTOM SHEET INDICATOR
    #
    # content-desc="Close sheet" is ONLY present while the
    # phone-number / OTP bottom sheet is open.
    # =====================================================
    LOGIN_SHEET_INDICATOR = (
        AppiumBy.ACCESSIBILITY_ID,
        "Close sheet"
    )

    # =====================================================
    # TOAST MESSAGE
    # =====================================================
    TOAST_MESSAGE = (AppiumBy.XPATH, "//android.widget.Toast")

    # =====================================================
    # LOGGED-IN PROFILE PAGE INDICATOR
    #
    # "Edit Profile" ONLY appears when logged in and on the
    # profile page. Confirmed via XML: [155,810][346,855].
    # When visible after tapping the profile tab, the login
    # sheet will never appear — session already exists
    # (noReset=true preserved login state).
    # =====================================================
    LOGGED_IN_PROFILE_INDICATOR = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Edit Profile")'
    )

    # =====================================================
    # HOME TAB (bottom navigation)
    #
    # Confirmed via XML:
    #   android.view.View clickable=true [0,2183][200,2309]
    #     android.widget.TextView text="Home" clickable=false
    # =====================================================
    HOME_TAB = (
        AppiumBy.XPATH,
        "//android.view.View[@clickable='true']"
        "[.//android.widget.TextView[@text='Home']]"
    )
