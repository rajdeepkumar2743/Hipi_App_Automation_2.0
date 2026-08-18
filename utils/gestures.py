# =========================================================
# FILE: utils/gestures.py
# =========================================================

import time

from utils.logger import LogGen


class GestureUtils:

    logger = LogGen.loggen()

    def __init__(self, driver):
        self.driver = driver

    def get_screen_size(self):
        return self.driver.get_window_size()

    def tap(self, x, y):

        try:

            self.driver.execute_script(
                "mobile: clickGesture",
                {"x": x, "y": y}
            )

            self.logger.info(f"Tap performed at X:{x} Y:{y}")

            return True

        except Exception as e:

            self.logger.error(f"Tap failed: {e}")

            return False

    def double_tap(self, x, y):

        try:

            self.driver.execute_script(
                "mobile: doubleClickGesture",
                {"x": x, "y": y}
            )

            self.logger.info(f"Double tap at X:{x} Y:{y}")

            return True

        except Exception as e:

            self.logger.error(f"Double tap failed: {e}")

            return False

    def long_press(self, x, y, duration=2000):

        try:

            self.driver.execute_script(
                "mobile: longClickGesture",
                {"x": x, "y": y, "duration": duration}
            )

            self.logger.info(f"Long press at X:{x} Y:{y}")

            time.sleep(1)

            return True

        except Exception as e:

            self.logger.error(f"Long press failed: {e}")

            return False

    def swipe_up(self, speed=800):

        try:

            size = self.get_screen_size()

            start_x = size["width"] // 2

            start_y = int(size["height"] * 0.80)

            end_y = int(size["height"] * 0.20)

            self.driver.execute_script(
                "mobile: dragGesture",
                {
                    "startX": start_x,
                    "startY": start_y,
                    "endX": start_x,
                    "endY": end_y,
                    "speed": speed
                }
            )

            self.logger.info("Swipe up performed")

            time.sleep(1)

            return True

        except Exception as e:

            self.logger.error(f"Swipe up failed: {e}")

            return False

    def swipe_down(self, speed=800):

        try:

            size = self.get_screen_size()

            start_x = size["width"] // 2

            start_y = int(size["height"] * 0.20)

            end_y = int(size["height"] * 0.80)

            self.driver.execute_script(
                "mobile: dragGesture",
                {
                    "startX": start_x,
                    "startY": start_y,
                    "endX": start_x,
                    "endY": end_y,
                    "speed": speed
                }
            )

            self.logger.info("Swipe down performed")

            time.sleep(1)

            return True

        except Exception as e:

            self.logger.error(f"Swipe down failed: {e}")

            return False

    def swipe_left(self, speed=800):

        try:

            size = self.get_screen_size()

            start_x = int(size["width"] * 0.80)

            end_x = int(size["width"] * 0.20)

            start_y = int(size["height"] * 0.50)

            self.driver.execute_script(
                "mobile: dragGesture",
                {
                    "startX": start_x,
                    "startY": start_y,
                    "endX": end_x,
                    "endY": start_y,
                    "speed": speed
                }
            )

            self.logger.info("Swipe left performed")

            time.sleep(1)

            return True

        except Exception as e:

            self.logger.error(f"Swipe left failed: {e}")

            return False

    def swipe_right(self, speed=800):

        try:

            size = self.get_screen_size()

            start_x = int(size["width"] * 0.20)

            end_x = int(size["width"] * 0.80)

            start_y = int(size["height"] * 0.50)

            self.driver.execute_script(
                "mobile: dragGesture",
                {
                    "startX": start_x,
                    "startY": start_y,
                    "endX": end_x,
                    "endY": start_y,
                    "speed": speed
                }
            )

            self.logger.info("Swipe right performed")

            time.sleep(1)

            return True

        except Exception as e:

            self.logger.error(f"Swipe right failed: {e}")

            return False

    def tap_by_percentage(self, x_percent, y_percent):

        size = self.get_screen_size()

        x = int(size["width"] * x_percent)

        y = int(size["height"] * y_percent)

        return self.tap(x, y)

    def swipe_custom(self, start_x, start_y, end_x, end_y, speed=800):

        try:

            self.driver.execute_script(
                "mobile: dragGesture",
                {
                    "startX": start_x,
                    "startY": start_y,
                    "endX": end_x,
                    "endY": end_y,
                    "speed": speed
                }
            )

            self.logger.info("Custom swipe performed")

            time.sleep(1)

            return True

        except Exception as e:

            self.logger.error(f"Custom swipe failed: {e}")

            return False