# =========================================================
# FILE: config/device_config.py
#
# CHANGES (iOS support / driver-management improvement):
#   - Added "platform": "Android" | "iOS" to every device
#     entry. driver_factory.py now reads this to decide
#     which Appium Options class (UiAutomator2Options vs
#     XCUITestOptions) and capability set to build, instead
#     of relying solely on the global Config.PLATFORM_NAME
#     env var. This means --device alone is now enough to
#     pick the right platform end-to-end — you can't
#     accidentally point an Android device entry at iOS
#     capabilities or vice versa.
#   - Added iOS simulator/device placeholder entries.
#     UDIDs are placeholders — replace with real simulator
#     UDIDs (`xcrun simctl list devices`) or a real device
#     UDID before running iOS tests.
# =========================================================

DEVICES = {

    # =====================================================
    # ANDROID EMULATOR
    # =====================================================

    "emulator": {
        "platform":   "Android",
        "deviceName": "Android Emulator",
        "udid":       "emulator-5554",
    },

    # =====================================================
    # ANDROID REAL DEVICE 1
    # =====================================================

    "real_device_1": {
        "platform":   "Android",
        "deviceName": "Android",
        "udid":       "xxxxxxxxxxxxxxxx",
    },

    # =====================================================
    # ANDROID REAL DEVICE 2
    # =====================================================

    "real_device_2": {
        "platform":   "Android",
        "deviceName": "OPPO",
        "udid":       "INONEM4XHQQGT8U4",
    },

    # =====================================================
    # iOS SIMULATOR
    #
    # PLACEHOLDER — udid must be replaced with a real
    # simulator UDID before use:
    #   xcrun simctl list devices
    # platformVersion should match an installed runtime.
    # =====================================================

    "ios_simulator": {
        "platform":         "iOS",
        "deviceName":        "iPhone 15",
        "platformVersion":   "17.5",
        "udid":              "REPLACE_WITH_SIMULATOR_UDID",
    },

    # =====================================================
    # iOS REAL DEVICE
    #
    # PLACEHOLDER — udid, xcodeOrgId, and xcodeSigningId
    # must be filled in with real values from your Apple
    # Developer account / provisioning profile before use.
    # =====================================================

    "ios_real_device": {
        "platform":        "iOS",
        "deviceName":       "iPhone",
        "udid":             "REPLACE_WITH_REAL_DEVICE_UDID",
        "xcodeOrgId":       "REPLACE_WITH_TEAM_ID",
        "xcodeSigningId":   "iPhone Developer",
    },

    # =====================================================
    # CLOUD / REAL-DEVICE-FARM EXAMPLES (BrowserStack)
    #
    # PLACEHOLDER — for actual real-device execution, not
    # local emulator/simulator. Requires:
    #   1. A BrowserStack App Automate account.
    #   2. BROWSERSTACK_USERNAME / BROWSERSTACK_ACCESS_KEY
    #      set as env vars (never hardcode these).
    #   3. Your .apk/.ipa uploaded to BrowserStack first —
    #      "app" below is the returned bs://<hash> value,
    #      not a local file path.
    #   4. cloud_driver_factory.py's command_executor pointed
    #      at BrowserStack's hub (see that file).
    #
    # Sauce Labs / LambdaTest follow the identical shape —
    # only the capability namespace changes:
    #   BrowserStack -> "bstack:options"
    #   Sauce Labs   -> "sauce:options"
    #   LambdaTest   -> "lt:options"
    # =====================================================

    "browserstack_android": {
        "platform":    "Android",
        "cloud":       "browserstack",
        "deviceName":  "Google Pixel 8",
        "osVersion":   "14.0",
        "app":         "REPLACE_WITH_BROWSERSTACK_APP_HASH",  # e.g. "bs://abc123..."
    },

    "browserstack_ios": {
        "platform":    "iOS",
        "cloud":       "browserstack",
        "deviceName":  "iPhone 15",
        "osVersion":   "17",
        "app":         "REPLACE_WITH_BROWSERSTACK_APP_HASH",
    },
}
