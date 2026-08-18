# =========================================================
# FILE: utils/logger.py
#
# CHANGES FROM AUDIT:
#   - Added threading.Lock() to fix race condition in
#     parallel execution (pytest-xdist) (ISSUE-14)
#   - Log directory now uses Config.LOG_PATH instead of
#     hardcoded "logs/" (aligns with Config centralisation)
#   - Added DEBUG level support via LOG_LEVEL env var
#   - Added log rotation (10 MB max, 5 backups) to prevent
#     unbounded log file accumulation (ISSUE M-01)
#   - All other existing behaviour preserved
# =========================================================

import os
import logging
import threading

from datetime import datetime
from logging.handlers import RotatingFileHandler


class LogGen:
    """
    Thread-safe singleton logger for the HiPi automation framework.

    Usage:
        logger = LogGen.loggen()
        logger.info("message")
    """

    _logger: logging.Logger = None
    _lock: threading.Lock = threading.Lock()

    @staticmethod
    def loggen() -> logging.Logger:
        """
        Returns the shared logger instance.
        Thread-safe: uses a lock to prevent duplicate
        initialisation when pytest-xdist spawns workers.
        """

        # Fast path — already initialised (no lock needed)
        if LogGen._logger is not None:
            return LogGen._logger

        with LogGen._lock:
            # Double-checked locking: another thread may
            # have initialised while we waited for the lock
            if LogGen._logger is not None:
                return LogGen._logger

            # ─── Read config ─────────────────────────────
            # Import inside method to avoid circular imports
            # at module load time
            try:
                from config.config import Config
                log_dir   = Config.LOG_PATH
                log_level = getattr(
                    logging,
                    os.getenv("LOG_LEVEL", "INFO").upper(),
                    logging.INFO
                )
            except ImportError:
                log_dir   = "reports/logs"
                log_level = logging.INFO

            os.makedirs(log_dir, exist_ok=True)

            # ─── Logger instance ──────────────────────────
            logger = logging.getLogger("HiPiAutomation")
            logger.setLevel(log_level)
            logger.propagate = False

            if logger.handlers:
                logger.handlers.clear()

            # ─── Formatter ───────────────────────────────
            formatter = logging.Formatter(
                fmt=(
                    "%(asctime)s "
                    "[%(levelname)-8s] "
                    "%(filename)s:%(lineno)d "
                    "— %(message)s"
                ),
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            # ─── Rotating file handler ───────────────────
            # Max 10 MB per file, keep 5 backups
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            log_file  = os.path.join(log_dir, f"hipi_{timestamp}.log")

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)

            # ─── Console handler ─────────────────────────
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

            LogGen._logger = logger

        return LogGen._logger