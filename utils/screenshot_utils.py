# =========================================================
# FILE: utils/screenshot_utils.py
#
# CHANGES FROM AUDIT:
#   - Now reads screenshot dir from Config.SCREENSHOT_PATH
#     instead of hardcoding "screenshots" 3 times (ISSUE-08)
#   - Added allure_attach() helper so callers can attach
#     a screenshot to the Allure report in one call
#   - All existing method signatures preserved
# =========================================================
from __future__ import annotations

import os
import re
import allure

from datetime import datetime

from utils.logger import LogGen


class ScreenshotUtils:

    logger = LogGen.loggen()

    # ─── Resolve the output directory once ───────────────
    @staticmethod
    def _screenshot_dir() -> str:
        try:
            from config.config import Config
            return Config.SCREENSHOT_PATH
        except ImportError:
            return "reports/screenshots"

    @staticmethod
    def create_directory() -> None:
        os.makedirs(ScreenshotUtils._screenshot_dir(), exist_ok=True)

    # ─── Core capture ────────────────────────────────────

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Strip characters that are illegal in file/path names."""
        return re.sub(r'[/\\:*?"<>|\[\]@\']', '_', name)

    @staticmethod
    def capture(driver, name: str = "screenshot") -> str | None:
        """
        Save a PNG screenshot to the configured screenshots dir.
        Returns the file path on success, None on failure.
        """
        try:
            ScreenshotUtils.create_directory()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{ScreenshotUtils._safe_filename(name)}_{timestamp}.png"
            path = os.path.join(ScreenshotUtils._screenshot_dir(), file_name)

            driver.save_screenshot(path)
            ScreenshotUtils.logger.info(f"Screenshot saved: {path}")
            return path

        except Exception as e:
            ScreenshotUtils.logger.error(f"Screenshot capture failed: {e}")
            return None

    @staticmethod
    def save_page_source(driver, name: str = "page_source") -> str | None:
        """
        Dump the current XML page source to the screenshots dir.
        Returns the file path on success, None on failure.
        """
        try:
            ScreenshotUtils.create_directory()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{ScreenshotUtils._safe_filename(name)}_{timestamp}.xml"
            path = os.path.join(ScreenshotUtils._screenshot_dir(), file_name)

            with open(path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)

            ScreenshotUtils.logger.info(f"Page source saved: {path}")
            return path

        except Exception as e:
            ScreenshotUtils.logger.error(f"Page source save failed: {e}")
            return None

    @staticmethod
    def capture_full_debug(driver, name: str = "debug") -> dict:
        """Capture screenshot + page source together (used on errors)."""
        screenshot_path = ScreenshotUtils.capture(driver, name)
        source_path     = ScreenshotUtils.save_page_source(driver, name)
        return {
            "screenshot":  screenshot_path,
            "page_source": source_path,
        }

    @staticmethod
    def allure_attach(driver, name: str = "screenshot") -> None:
        """
        Capture a screenshot AND attach it directly to the
        current Allure test step. Use this inside page objects
        or test hooks for zero-boilerplate Allure integration.
        """
        path = ScreenshotUtils.capture(driver, name)
        if path:
            try:
                allure.attach.file(
                    path,
                    name=name,
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception as e:
                ScreenshotUtils.logger.warning(
                    f"Allure attach failed (report may not be running): {e}"
                )