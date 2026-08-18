# =========================================================
# FILE: testdata/test_data.py
#
# ROOT CAUSE FIXED (ISSUE 5 + 6):
#   - Added load_dotenv() so .env file is actually read.
#     Previously python-dotenv was installed but never called,
#     so os.getenv() always returned "" for TEST_PHONE/TEST_OTP.
#   - Added _require() guard that raises immediately at import
#     time with a clear human-readable message, BEFORE any
#     driver or UI interaction starts.
#     Old behaviour: empty string passed all the way through
#     enter_mobile_number() → click_proceed() → enter_otp()
#     (~15s wasted) then crashed with "Invalid OTP length".
#     New behaviour: crash at collection time with:
#     "CredentialError: TEST_PHONE is not set. Add it to .env"
# =========================================================

import os
from dotenv import load_dotenv

# Load .env file from project root.
# Calling this here guarantees credentials are available
# regardless of which file is imported first.
load_dotenv()


class CredentialError(Exception):
    """Raised when a required test credential is missing."""
    pass


def _require(env_var: str) -> str:
    """
    Read an environment variable and raise a clear error if missing.
    Fails immediately at import/collection time, not mid-test.
    """
    value = os.getenv(env_var, "").strip()
    if not value:
        raise CredentialError(
            f"\n\n"
            f"  ✗  Required credential '{env_var}' is not set.\n"
            f"\n"
            f"  Fix: create a .env file in your project root:\n"
            f"    {env_var}=your_value_here\n"
            f"\n"
            f"  See .env.example for all required variables.\n"
        )
    return value


# ─── Valid login credentials ──────────────────────────────
# Set these in your .env file:
#   TEST_PHONE=9876543210
#   TEST_OTP=5186
#
# NEVER commit real values to git — .env is git-ignored.
# ─────────────────────────────────────────────────────────

VALID_LOGIN = {
    "mobile": _require("TEST_PHONE"),
    "otp":    _require("TEST_OTP"),
}

# ─── Invalid OTP scenarios ───────────────────────────────
# Uses a non-sensitive placeholder number — safe in source.

INVALID_OTP_USERS = [
    ("9876543210", "1111"),
    ("9876543210", "9999"),
]

# ─── Short / incomplete OTP scenarios ────────────────────

SHORT_OTP_USERS = [
    ("9876543210", "0"),
    ("9876543210", "57"),
    ("9876543210", "575"),
]

# ─── Feed actions ────────────────────────────────────────

FEED_ACTIONS = [
    "like",
    "comment",
    "share",
    "save",
    "mute",
    "pause",
    "follow",
    "three_dots_cross",
    "three_dots_cancel",
]

# ─── Comments ────────────────────────────────────────────

COMMENTS = [
    "Awesome 🔥",
    "Nice ❤️",
    "Amazing 😍",
    "Superb 🔥",
    "Cool Video 😎",
    "Great Reel 🚀",
]