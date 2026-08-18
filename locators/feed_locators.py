# =========================================================
# FILE: locators/feed_locators.py
#
# ALL locators verified against page-source XML captured
# during live test runs (reports/screenshots/*.xml).
#
# This is a Jetpack Compose app — native resource-ids like
# ivLike / ivComment / clFeedContainer / playerView do NOT
# exist. Elements are Compose-rendered with no stable IDs.
#
# For comment sheet / three-dots sheet, locators use XPath
# union patterns that cover both native resource-id (if
# present) and class/text fallbacks, so tests remain
# stable even if bottom sheets are Compose-rendered.
# =========================================================

from appium.webdriver.common.appiumby import AppiumBy


class FeedLocators:

    # =====================================================
    # FEED SCREEN / VIDEO PLAYER
    #
    # com.zee5.hipi:id/exo_content_frame is the ExoPlayer
    # FrameLayout — the only stable resource-id on the feed
    # screen. Confirmed present in XML: [0,132][1080,2153]
    # =====================================================
    FEED_SCREEN = (AppiumBy.ID, "com.zee5.hipi:id/exo_content_frame")
    VIDEO_CONTAINER = (AppiumBy.ID, "com.zee5.hipi:id/exo_content_frame")

    # =====================================================
    # VIDEO TOUCH AREA (tap to pause / resume)
    #
    # The large clickable View that wraps the entire feed
    # item (video + action buttons + creator info).
    # Confirmed from XML: android.view.View clickable=true
    # [0,132][1080,2127], parent of exo_content_frame.
    # =====================================================
    VIDEO_TOUCH_AREA = (
        AppiumBy.XPATH,
        "//android.view.View[@clickable='true']"
        "[.//android.widget.FrameLayout"
        "[@resource-id='com.zee5.hipi:id/exo_content_frame']]"
    )

    # =====================================================
    # RIGHT-SIDE ACTION BUTTONS
    #
    # Compose renders these as android.widget.Button with
    # NO resource-id, NO content-desc, and NO exposed
    # checkable/checked/selected semantics (verified live —
    # every one of the 6 buttons reports checkable=false,
    # checked=false, selected=false regardless of state).
    #
    # ROOT CAUSE (confirmed via live device inspection,
    # 2026-08-17): the previous mapping below was WRONG —
    # instance(4)/instance(5) were swapped:
    #
    #   OLD (wrong):
    #     instance(4) [934,1761][1060,1887] -> "Three-dots menu"
    #     instance(5) [934,1908][1060,2034] -> "Mute"
    #
    #   VERIFIED LIVE:
    #     tapping instance(5) [934,1908][1060,2034] opened the
    #     "Report Content" / "Flag as inappropriate" / "Cancel"
    #     bottom sheet (i.e. it IS the three-dots/more-options
    #     button, not mute).
    #     tapping instance(4) [934,1761][1060,1887] produced NO
    #     accessibility-tree change and NO system audio-stream
    #     mute change (dumpsys audio) — consistent with the real
    #     mute control, which toggles the ExoPlayer's local
    #     volume only (never exposed via the a11y tree or
    #     AudioManager, so it can't be verified through those
    #     channels — see mute_unmute_video() for what IS
    #     verified instead).
    #
    # This swap is exactly why prior test runs reported
    # "mute/unmute executed successfully" while only ever
    # opening and closing the three-dots report sheet.
    #
    # PERMANENT FIX: anchor Mute/Three-dots from the END of
    # the button list (last() / last()-1) instead of a fixed
    # numeric instance. This survives a leading button
    # (Like/Comment/Share/Save) being absent for some video
    # states, since Mute and Three-dots are always the last
    # two buttons in the vertical action rail, in that order.
    #
    # Like/Comment/Share/Save are left as front-anchored
    # instance() selectors — proven stable across many runs
    # and not implicated in any reported failure.
    # =====================================================
    LIKE_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.Button").instance(0)'
    )
    COMMENT_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.Button").instance(1)'
    )
    SHARE_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.Button").instance(2)'
    )
    SAVE_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.Button").instance(3)'
    )
    MUTE_ICON = (
        AppiumBy.XPATH,
        "(//android.widget.Button)[last()-1]"
    )
    THREE_DOTS_BUTTON = (
        AppiumBy.XPATH,
        "(//android.widget.Button)[last()]"
    )

    # =====================================================
    # PAUSE / RESUME OVERLAYS
    # Compose toggles play state via a tap on the video
    # area — same element for both pause and resume.
    # =====================================================
    PAUSE_BUTTON = VIDEO_TOUCH_AREA
    RESUME_BUTTON = VIDEO_TOUCH_AREA
    PAUSE_OVERLAY = VIDEO_TOUCH_AREA

    # =====================================================
    # USER / CONTENT INFO
    #
    # Creator name: clickable TextView in bottom-left.
    # Confirmed: android.widget.TextView clickable=true
    # text="Test userrr" [194,1916][461,2023]
    # =====================================================

    # Avatar/creator image — targeted as the first clickable View
    # descendant of the video container that has no child TextView
    # or FrameLayout (the avatar circle image has no labelled children).
    # Note: open_creator_profile() uses USERNAME_TAP_PERCENT (coordinate
    # tap) instead of this locator; this is kept for direct-element access.
    PROFILE_IMAGE = (
        AppiumBy.XPATH,
        "//android.view.View[@clickable='true']"
        "[.//android.widget.FrameLayout"
        "[@resource-id='com.zee5.hipi:id/exo_content_frame']]"
        "//android.view.View[@clickable='true']"
        "[not(.//android.widget.TextView)]"
        "[not(.//android.widget.FrameLayout)]"
    )
    FOLLOW_BUTTON = (
        AppiumBy.XPATH,
        "//android.view.View[@clickable='true']"
        "[.//android.widget.TextView[@text='Follow']]"
    )
    FOLLOWING_BUTTON = (
        AppiumBy.XPATH,
        "//android.view.View[@clickable='true']"
        "[.//android.widget.TextView[@text='Following']]"
    )
    USERNAME = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.TextView")'
        '.clickable(true).instance(0)'
    )
    CAPTION_TEXT = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.TextView")'
        '.clickable(true).instance(1)'
    )
    MUSIC_NAME = (AppiumBy.ID, "com.zee5.hipi:id/tvMusicName")

    # =====================================================
    # USERNAME_TAP_PERCENT
    # Coordinate tap for creator profile — center of creator
    # name TextView.
    # Confirmed via XML: text="Test userrr" [194,1916][461,2023]
    # Center: (327, 1969) → on 1080x2400: (0.30, 0.82)
    # =====================================================
    USERNAME_TAP_PERCENT = (0.30, 0.82)

    # =====================================================
    # BOTTOM NAVIGATION TABS
    # Same XPath pattern as login_locators.HOME_TAB.
    # =====================================================
    HOME_TAB = (
        AppiumBy.XPATH,
        "//android.view.View[@clickable='true']"
        "[.//android.widget.TextView[@text='Home']]"
    )
    DISCOVER_TAB = (
        AppiumBy.XPATH,
        "//android.view.View[@clickable='true']"
        "[.//android.widget.TextView[@text='Discover']]"
    )
    REELS_TAB = (
        AppiumBy.XPATH,
        "//android.view.View[@clickable='true']"
        "[.//android.widget.TextView[@text='Reels']]"
    )

    # =====================================================
    # COMMENT SECTION
    #
    # XPath union: tries native resource-id first, falls
    # back to any EditText in the HiPi package so comment
    # tests remain stable whether the sheet is a native
    # Android view (with etComment) or a Compose bottom
    # sheet (with an untagged EditText).
    # =====================================================
    COMMENT_INPUT = (
        AppiumBy.XPATH,
        "//*[@resource-id='com.zee5.hipi:id/etComment'"
        " or (@class='android.widget.EditText'"
        " and @package='com.zee5.hipi')]"
    )
    COMMENT_SEND_BUTTON = (
        AppiumBy.XPATH,
        "//*[@resource-id='com.zee5.hipi:id/ivSend'"
        " or (@content-desc='Send' and @package='com.zee5.hipi')]"
    )
    COMMENT_CLOSE_BUTTON = (
        AppiumBy.XPATH,
        "//*[@resource-id='com.zee5.hipi:id/ivClose'"
        " or (@content-desc='Close' and @package='com.zee5.hipi')]"
    )

    # =====================================================
    # THREE-DOTS / REPORT POPUP
    #
    # Broad text-based detection: the Compose bottom sheet
    # has no stable resource-id (clBottomSheet does NOT exist
    # in the Compose build). Matching any known menu-option
    # text gives the widest chance of detection regardless
    # of which options the app renders for this video.
    # =====================================================
    REPORT_POPUP = (
        AppiumBy.XPATH,
        "//*[@package='com.zee5.hipi' and ("
        "contains(@text,'Report') or "
        "contains(@text,'Not interested') or "
        "contains(@text,'Not Interested') or "
        "contains(@text,'Cancel') or "
        "contains(@text,'Hide') or "
        "contains(@text,'Block') or "
        "contains(@text,'Spam')"
        ")]"
    )
    REPORT_BUTTON = (
        AppiumBy.XPATH,
        "//*[@package='com.zee5.hipi' and contains(@text,'Report')]"
    )
    REPORT_CLOSE_BUTTON = (
        AppiumBy.XPATH,
        "//*[@resource-id='com.zee5.hipi:id/ivClose'"
        " or (@content-desc='Close' and @package='com.zee5.hipi')]"
    )
    REPORT_CANCEL_BUTTON = (
        AppiumBy.XPATH,
        "//*[@package='com.zee5.hipi'"
        " and contains(@text,'Cancel') and @clickable='true']"
    )

    # =====================================================
    # MISC
    # =====================================================
    TOAST_MESSAGE = (AppiumBy.XPATH, "//android.widget.Toast")
    NEXT_VIDEO_VALIDATION = (AppiumBy.ID, "com.zee5.hipi:id/exo_content_frame")
    VIDEO_DURATION = (AppiumBy.ID, "com.zee5.hipi:id/tvDuration")
    LIKE_COUNT = (AppiumBy.ID, "com.zee5.hipi:id/tvLikeCount")
    COMMENT_COUNT = (AppiumBy.ID, "com.zee5.hipi:id/tvCommentCount")
    SHARE_COUNT = (AppiumBy.ID, "com.zee5.hipi:id/tvShareCount")
