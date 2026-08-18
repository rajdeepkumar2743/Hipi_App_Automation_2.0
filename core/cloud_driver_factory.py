# =========================================================
# FILE: core/cloud_driver_factory.py
#
# Real-device-farm execution (BrowserStack shown; Sauce Labs
# and LambdaTest follow the identical shape — see notes in
# config/device_config.py).
#
# Kept as a SEPARATE module from driver_factory.py rather
# than a third branch inside it, so:
#   - The local emulator/real-device path (the one you'll
#     actually use day-to-day) is completely untouched and
#     can't be broken by a cloud-capability change.
#   - Credentials handling lives in exactly one place.
#   - Swapping providers later means adding one function
#     here, not touching the core factory.
#
# NOT wired into DriverFactory.create_driver() automatically.
# conftest.py would need an explicit branch (see comment at
# bottom of this file) to call this instead of
# DriverFactory.create_driver() when device_info.get("cloud")
# is set. Left as an explicit opt-in rather than silent
# magic, since pointing at a cloud grid by accident (and
# burning real-device-farm minutes) is worse than a one-line
# manual wire-up.
# =========================================================

import os

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions

from config.config import Config
from utils.logger import LogGen

logger = LogGen.loggen()

BROWSERSTACK_HUB_URL = "https://hub-cloud.browserstack.com/wd/hub"


def _browserstack_credentials() -> tuple[str, str]:
    username = os.getenv("BROWSERSTACK_USERNAME", "").strip()
    access_key = os.getenv("BROWSERSTACK_ACCESS_KEY", "").strip()

    if not username or not access_key:
        raise RuntimeError(
            "BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY must be set "
            "as environment variables to run against BrowserStack. "
            "Never hardcode these in device_config.py."
        )
    return username, access_key


def create_browserstack_driver(device_info: dict, env: str = "qa"):
    """
    Creates an Appium session against BrowserStack App Automate.

    device_info comes straight from device_config.py's
    "browserstack_android" / "browserstack_ios" entries.
    """
    username, access_key = _browserstack_credentials()
    platform = device_info["platform"]

    bstack_options = {
        "userName": username,
        "accessKey": access_key,
        "projectName": "HiPi Mobile Automation",
        "buildName": f"HiPi-{env}-build",
        "sessionName": f"{device_info['deviceName']} - {platform}",
        "deviceName": device_info["deviceName"],
        "osVersion": device_info["osVersion"],
        "debug": True,
        "networkLogs": True,
    }

    if platform.lower() == "android":
        options = UiAutomator2Options()
        options.platform_name = "Android"
    elif platform.lower() == "ios":
        options = XCUITestOptions()
        options.platform_name = "iOS"
    else:
        raise ValueError(f"Unsupported platform for BrowserStack: {platform}")

    options.app = device_info["app"]  # bs://... hash from an already-uploaded build
    options.set_capability("bstack:options", bstack_options)

    logger.info(
        f"Creating BrowserStack driver: {device_info['deviceName']} "
        f"({platform} {device_info['osVersion']})"
    )

    driver = webdriver.Remote(
        command_executor=BROWSERSTACK_HUB_URL,
        options=options,
    )
    driver.implicitly_wait(Config.IMPLICIT_WAIT)
    return driver


# =========================================================
# WIRE-UP NOTE (not applied automatically — see module
# docstring above for why):
#
# In conftest.py's _create_driver_with_retry(), add:
#
#   from config.device_config import DEVICES
#   from core.cloud_driver_factory import create_browserstack_driver
#
#   device_info = DEVICES[device_name]
#   if device_info.get("cloud") == "browserstack":
#       driver = create_browserstack_driver(device_info, env_name)
#   else:
#       driver = DriverFactory.create_driver(device=device_name, env=env_name)
# =========================================================
